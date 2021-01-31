from dotenv import load_dotenv
import os
import json

load_dotenv()

API_KEY = os.getenv("API_KEY")
SUMMONER_NAMES = json.loads(os.getenv("SUMMONER_NAMES"))
DEV_KEY = os.getenv("API_KEY_DEV")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
