import os

from dotenv import load_dotenv

load_dotenv()

WAKATIME_API_KEY = os.getenv("WAKATIME_API_KEY")
BLOCKED_APPS = os.getenv("BLOCKED_APPS", "").split(",")
REQUIRED_MINUTES = int(os.getenv("REQUIRED_MINUTES", 60))