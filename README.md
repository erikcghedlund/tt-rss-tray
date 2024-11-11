# tt-rss-tray

A tray application for seeing the number of unread articles in your Tiny Tiny RSS feed

## Description

*tt-rss-tray* is, as the name might suggest, a tray application. More specifically, it is a tray application for viewing the number of unread posts
have in your *Tiny Tiny RSS Feed*.

### Features

- Support for automatic log in.
- Support for launching of custom clients
- Sane defaults

## Getting started

### Prerequisites

- Python 3 (tested with Python 3.12.7)
- A Tiny Tiny RSS Server running with [API enabled](https://tt-rss.org/ApiReference/).

### Install

```bash
# Clone the repo
git clone git@github.com:erikcghedlund/tt-rss-tray.git
cd  tt-rss-tray

# Install the requirements
python -m pip install -r requirements.txt

# Create a settings file or pass options from the command line
# And run the program
./main.py
```

### Configure

The program supports both configuration through a json file or through passing arguments. The precedence of the configuration is
*command line argument* > *settings-file* > *defaults*, with the exception that the settings-file will take precedence over
a command line argument if it is equal to the default value. The settings file must be named `settings.json` and be placed in
the same folder as the program file.

#### Example configuration

```jsonc
{
    "sid": null, # Session ID Given by the Tiny Tiny RSS-API. Update automatically
    "url": "http://localhost/tt-rss/", // URL of you Tiny Tiny RSS-Server (Default: "http://localhost/tt-rss/")
    "sleep_time": "5m", // The time inbetween checking for new posts (Default: "5m")
    "position": "bottom-right", // Where the number of unread posts are drawn on the icon. Should be top-left, bottom-left, top-right or bottom-right (Default: "bottom-right")
    "client": null // Custom command to open the client, if any. Will open in webbrowser if null (Default: null)
}
```

### Disclaimer

This project is currently feature complete for my usage, so ongoing development might be slow. Still, feel more than welcome to open a issue if you have feature requests/bug discoveries
and I might get to it.

### License

This project is licensed under the [GPL-3.0 License](LICENSE.md).
