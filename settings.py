from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")
DEV_KEY = os.getenv("API_KEY_DEV")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
