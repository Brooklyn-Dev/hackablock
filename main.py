from datetime import datetime
import logging
import os
import time

logging.basicConfig(
    filename="hackablock.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

from dotenv import load_dotenv
import requests

load_dotenv()

WAKATIME_API_KEY = os.getenv("WAKATIME_API_KEY")
BLOCKED_APPS = os.getenv("BLOCKED_APPS")
REQUIRED_MINUTES = int(os.getenv("REQUIRED_MINUTES"))

HACKATIME_API_URL = "https://hackatime.hackclub.com/api/hackatime/v1"
CHECK_INTERVAL = 60  # sec

class HackatimeError(Exception):
    pass

def timestamped_print(msg: str) -> None:
    time_str = datetime.now().strftime("%H:%M:%S")
    print(f"[{time_str}] {msg}")

def get_coding_time() -> int:
    try:
        res = requests.get(
            f"{HACKATIME_API_URL}/users/current/statusbar/today",
            headers={"Authorization": f"Bearer {WAKATIME_API_KEY}"},
            timeout=10
        )
        res.raise_for_status()
        
        data = res.json()
        return int(data["data"]["grand_total"]["total_seconds"])
    
    except requests.RequestException as e:
        raise HackatimeError(f"Network/API error: {e}") from e
    except KeyError as e:
        raise HackatimeError(f"Unexpected response format: {e}") from e
    except ValueError as e:
        raise HackatimeError(f"Bad data in API response: {e}") from e

def main() -> None:
    while True:
        try:
            seconds = get_coding_time()
            logging.info(f"Fetched coding time: {seconds} seconds")
            minutes = seconds // 60
            
            if minutes < REQUIRED_MINUTES:
                remaining = REQUIRED_MINUTES - minutes
                logging.info(f"{minutes} minutes recorded, {remaining} more required to unblock apps.")
                timestamped_print(f"⏳ You need {remaining} more minutes to meet today's requirement.")
                sleep_time = max(remaining * 60, 60)
            else:
                logging.info(f"{REQUIRED_MINUTES} minute requirement met.")
                timestamped_print(f"🎉 Requirement met! You've coded {minutes} minutes today. Re-enabling blocked apps.")
                return None
            
        except HackatimeError as e:
            logging.error(f"Fetch failed: {e}")
            timestamped_print(f"❌ Could not fetch coding time. See 'hackablock.log'.")
            sleep_time = CHECK_INTERVAL

        time.sleep(sleep_time)
    
if __name__ == "__main__":
    main()