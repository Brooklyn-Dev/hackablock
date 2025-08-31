import os

from dotenv import load_dotenv

load_dotenv()

BLOCKED_APPS = os.getenv("BLOCKED_APPS", "").split(",")