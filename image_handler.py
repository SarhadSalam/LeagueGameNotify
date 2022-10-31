import api_calls
from api_calls import call_api
import json
from PIL import Image
import os
import sys

import settings

from selenium import webdriver


def get_image(game_id):
    # print("Getting image")
    # start browser
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized"); 
    options.add_argument("enable-automation"); 
    options.add_argument("--disable-browser-side-navigation");
    options.add_argument("--disable-gpu");
    selenium = webdriver.Chrome(options=options)
    selenium.set_window_size(1280, 950)
    selenium.maximize_window()

    # print("Have browser")
    selenium.get(f'https://www.leagueofgraphs.com/match/na/{game_id}')
    # print("Send request")

    selenium.save_screenshot(f"screenshot_{game_id}.png")
    # print("Save")

    selenium.quit()

def crop_image_post_game(game_id):
    img = Image.open(f"screenshot_{game_id}.png")

    # Setting the points for cropped image
    top = 380
    left = 250
    right = 1250
    bottom = 950

    img.crop((left, top, right, bottom)).save(f"cropped_{game_id}.png")


def remove_images(game_id):
    if os.path.exists(f"screenshot_{game_id}.png"):
        os.remove(f"screenshot_{game_id}.png")

    if os.path.exists(f"cropped_{game_id}.png"):
        os.remove(f"cropped_{game_id}.png")


if __name__ == "__main__":
    game_id = sys.argv[1]
    get_image(game_id)
    crop_image_post_game(game_id)
