#!/bin/python

from os import path, getcwd
from time import sleep
from json import load, loads, dump
from threading import Thread

import requests
from pystray import Icon, Menu
from PIL import Image, ImageDraw, ImageFont
from pytimeparse import parse as time_parse

__location__ = path.realpath(path.join(getcwd(), path.dirname(__file__)))
sid = None
icon_path = path.join(__location__, "./icon_classic_128.png")
setting_path = path.join(__location__, "./settings.json")

setting = {
    "sid": None,
    "url": "http://localhost/tt-rss/api/",
    "passive_time": "15m",
    "active_time": "5s",
    "font_size": 80,
    "notification_size": 60,
    "position": "bottom-right",
}

positions = dict()


def _setup_positions():
    global positions
    with Image.open(icon_path) as image:
        positions["top-left"] = (0, 0)
        positions["bottom-left"] = (0, image.width - setting["notification_size"])
        positions["top-right"] = (image.height - setting["notification_size"], 0)
        positions["bottom-right"] = (
            image.height - setting["notification_size"],
            image.width - setting["notification_size"],
        )


def login(username=None, password=None):
    if username is None:
        username = input("username: ")
    if password is None:
        password = input("password: ")
    payload = {"op": "login", "user": username, "password": password}
    res = requests.post(setting["url"], json=payload)
    return loads(res.text)["content"]["session_id"]


def get_unreads():
    payload = {"sid": setting["sid"], "op": "getUnread"}
    res = requests.post(setting["url"], json=payload)
    return loads(res.text)["content"]["unread"]


def setup_icon():
    icon = Icon("tt-rss-tray", Image.open(icon_path))
    return icon


def draw_unreads(n):
    # Create a new image with white background
    size = setting["notification_size"]
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
    last_unreads = -1
    while True:
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
        sleep(time_parse(setting["passive_time"]))


def setup():
    global setting
    _setup_positions()
    with open(setting_path, "r") as f:
        setting = load(f)


def main():
    global sid
    setup()
    if setting["sid"] == None:
        sid = login()
        setting["sid"] = sid
    with open(setting_path, "w") as f:
        dump(setting, f, indent=4)
    icon = setup_icon()
    Thread(target=icon.run).start()
    main_loop(icon)


if __name__ == "__main__":
    main()
