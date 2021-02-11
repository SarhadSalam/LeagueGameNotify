from dotenv import load_dotenv
import os
import json

load_dotenv()

API_KEY = os.getenv("API_KEY")
SUMMONER_NAMES = json.loads(os.getenv("SUMMONER_NAMES"))
DISCORD_IDS = json.loads(os.getenv("DISCORD_IDS"))
DEV_KEY = os.getenv("API_KEY_DEV")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
LEAGUE_PATH = os.getenv("LEAGUE_PATH")
TEMPLATE_SCRIPT_FILE = os.getenv("TEMPLATE_SCRIPT_FILE")
GENERATED_SCRIPT_FILE = os.getenv("GENERATED_SCRIPT_FILE")
PARENT_DRIVE = os.getenv("PARENT_DRIVE")
DISCORD_APP_TOKEN = os.getenv("DISCORD_APP_TOKEN")
