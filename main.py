#!/bin/python

from os import path, getcwd
from sys import argv
from time import sleep
from json import load, loads, dump
import logging
from threading import Thread
from subprocess import run
from webbrowser import open_new_tab
from argparse import ArgumentParser

import requests
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw, ImageFont
from pytimeparse import parse as time_parse

__location__ = path.realpath(path.join(getcwd(), path.dirname(__file__)))
icon_path = path.join(__location__, "./icon_classic_128.png")
setting_path = path.join(__location__, "./settings.json")
logger = logging.getLogger(__name__)
FONT_SIZE = 80
NOTIFICATION_SIZE = 60

setting = dict()
positions = dict()


def _setup_positions():
    global positions
    with Image.open(icon_path) as image:
        positions["top-left"] = (0, 0)
        positions["bottom-left"] = (0, image.width - NOTIFICATION_SIZE)
        positions["top-right"] = (image.height - NOTIFICATION_SIZE, 0)
        positions["bottom-right"] = (
            image.height - NOTIFICATION_SIZE,
            image.width - NOTIFICATION_SIZE,
        )


def _setup_parser():
    parser = ArgumentParser(
        "TT RSS Tray",
        description="A tray application for seeing the number of unread articles in your Tiny Tiny RSS feed",
    )
    parser.add_argument("-i", "--sid")
    parser.add_argument("-u", "--user")
    parser.add_argument("-p", "--pass")
    parser.add_argument("-l", "--url", default="http://localhost/tt-rss/")
    parser.add_argument("-s", "--sleep", default="5m")
    parser.add_argument("-k", "--client")
    parser.add_argument(
        "-n", "--position", default="bottom-right", choices=positions.keys()
    )
    return parser


def _maybe_post(url, payload, level):
    try:
        return requests.post(url, json=payload, timeout=30)
    except requests.exceptions.ConnectionError as e:
        level('Failed to establish connection with server: "{}"'.format(e))
        return None
    except requests.exceptions.Timeout:
        level("Connection to server timed out")
        return None


def login(username=None, password=None):
    if username is None:
        username = input("username: ")
    if password is None:
        password = input("password: ")
    payload = {"op": "login", "user": username, "password": password}
    url = setting["url"] + "api/"
    res = _maybe_post(url, payload, logger.fatal)
    if res is None:
        return None
    json_obj = loads(res.text)
    if json_obj["status"] == 1:
        logger.fatal('Failed to log in user "{}"'.format(username))
        return None
    return json_obj["content"]["session_id"]


def get_unreads():
    payload = {"sid": setting["sid"], "op": "getUnread"}
    url = setting["url"] + "api/"
    res = _maybe_post(url, payload, logger.warning)
    if res is None:
        return 0
    json_obj = loads(res.text)
    if json_obj["status"] == 1:
        logger.warning("API error: {}".format(json_obj["content"]["error"]))
        return None
    return json_obj["content"]["unread"]


def check_login():
    if setting["sid"] is None:
        return False
    payload = {"sid": setting["sid"], "op": "isLoggedIn"}
    url = setting["url"] + "api/"
    res = _maybe_post(url, payload, logger.fatal)
    if res is None:
        return None
    json_obj = loads(res.text)
    if json_obj["status"] == 1:
        logger.warning("API error: {}".format(json_obj["content"]["error"]))
        return None
    return json_obj["content"]["status"]


def open_client(self):
    if setting["client"] is None:
        open_new_tab(setting["url"])
    else:
        run(setting["client"], shell=True, check=True)


def exit_app(self):
    global alive
    alive = False


def setup_icon():
    icon = Icon(
        "tt-rss-tray",
        Image.open(icon_path),
        menu=Menu(
            MenuItem("Open client", open_client, default=True),
            MenuItem("Quit", exit_app),
        ),
    )
    return icon


def draw_unreads(n):
    # Create a new image with white background
    size = setting[NOTIFICATION_SIZE]
    image = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    # Draw a circle
    draw.circle((size / 2, size / 2), size / 2, outline="black", width=5, fill="red")

    text_height = int(size * (5 / 8))

    # Get a font
    font = ImageFont.load_default(size=text_height)

    # Get text size
    text_width = draw.textlength(str(n), font)

    # Position the text in the center of the circle
    text_x = (size - text_width) // 2
    text_y = (size - text_height - (1 / 4) * text_height) // 2

    # Draw the integer n in the center of the circle
    draw.text((text_x, text_y), str(n), font=font, fill="black")

    return image


def main_loop(icon):
    global alive
    alive = True
    last_unreads = -1
    actual_sleep = time_parse("5s")
    wait_iterations = int(time_parse(setting["sleep"]) / actual_sleep)
    while alive:
        unreads = get_unreads()
        if unreads == last_unreads:
            continue
        last_unreads = unreads
        image = Image.open("/tmp/icon_tt_rss.png")
        if unreads != 0:
            image.paste(draw_unreads(unreads), positions[setting["position"]])

        # This is hacky but I could not get it to work the proper way...
        icon.icon = image
        icon._update_icon()
        for _ in range(wait_iterations):
            if not alive:
                break
            sleep(actual_sleep)
    icon.stop()


def setup():
    global setting
    _setup_positions()
    parser = _setup_parser()
    logging.basicConfig(level=logging.DEBUG)
    if path.exists(setting_path):
        with open(setting_path, "r") as f:
            setting = dict(setting, **load(f))
            logger.debug("loaded settings {}".format(setting))
    known = parser.parse_args(argv[1:])
    for key, value in vars(known).items():
        if key in setting.keys() and parser.get_default(key) == value:
            continue
        logger.debug("Overwriting setting {} with {}".format(key, value))
        setting[key] = value


def close():
    if not path.exists(setting_path):
        setting["user"] = (
            None  # We should probably not store the password in plain text...
        )
        setting["pass"] = None
        with open(setting_path, "w") as f:
            dump(setting, f, indent=4)


def main():
    setup()
    sid_is_valid = check_login()
    if sid_is_valid is None:
        return  # If true, we failed to establish a connection to the server
    if sid_is_valid is False:
        logger.info("session id is expired, invalid or absent, requesting new login")
        maybe_sid = login(setting["user"], setting["pass"])
        if maybe_sid is None:
            return
        logger.info('setting session id to "{}"'.format(maybe_sid))
        setting["sid"] = maybe_sid
    icon = setup_icon()
    Thread(target=icon.run).start()
    main_loop(icon)
    close()


if __name__ == "__main__":
    main()
