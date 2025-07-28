import os
import threading

try:
    from PIL import Image, ImageDraw
    from pystray import Icon, MenuItem, Menu
except ImportError:  
    Image = ImageDraw = Icon = MenuItem = Menu = None  

import functools


@functools.lru_cache(maxsize=1)
def create_key_icon():
    if not Image:
        return None

    image = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((10, 22, 30, 42), fill="black")
    draw.rectangle((28, 30, 54, 34), fill="black")
    draw.rectangle((40, 34, 44, 38), fill="black")
    draw.rectangle((46, 34, 50, 38), fill="black")
    return image


def quit_app(icon, _item):
    icon.stop()
    os._exit(0)


def show_message(icon):
    try:
        icon.notify("Account Manager is running.", "Running in background")
    except Exception:
        pass


def run_tray_icon() -> None:
    """Blocking call that shows a tray-icon; safe if dependencies missing."""
    if not Icon:
        print("pystray/Pillow not installed – tray icon disabled")
        return

    menu = Menu(MenuItem("Quit", quit_app))
    icon = Icon("AccountManager", create_key_icon(), "Account Manager", menu)
    threading.Timer(1, lambda: show_message(icon)).start()
    try:
        icon.run()
    except Exception as exc:
        print(f"Tray icon error: {exc}")