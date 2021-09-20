import api_calls
from api_calls import call_api
import json
from PIL import Image
import os

import settings

if settings.ENABLE_SCREENSHOT:
    from pyvirtualdisplay import Display

from selenium import webdriver


def get_image(game_id):
    # start display
    if settings.ENABLE_SCREENSHOT:
        vdisplay = Display(visible=0, size=(2560, 1440))
        vdisplay.start()

    # start browser
    selenium = webdriver.Firefox()
    selenium.maximize_window()

    selenium.get(f'https://www.leagueofgraphs.com/match/na/{game_id}')
    selenium.save_screenshot(f"screenshot_{game_id}.png")

    selenium.quit()

    if settings.ENABLE_SCREENSHOT:
        vdisplay.stop()


def crop_image_post_game(game_id):
    img = Image.open(f"screenshot_{game_id}.png")

    # Setting the points for cropped image
    top = 380
    left = 320
    right = 1680
    bottom = 920

    img.crop((left, top, right, bottom)).save(f"cropped_{game_id}.png")


def remove_images(game_id):
    if os.path.exists(f"screenshot_{game_id}.png"):
        os.remove(f"screenshot_{game_id}.png")

    if os.path.exists(f"cropped_{game_id}.png"):
        os.remove(f"cropped_{game_id}.png")


if __name__ == "__main__":
    game_id = "4046823128"
    # get_image(game_id)
    crop_image_post_game(game_id)
