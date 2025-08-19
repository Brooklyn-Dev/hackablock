import os
import time

from dotenv import load_dotenv
import requests

load_dotenv()

WAKATIME_API_KEY = os.getenv("WAKATIME_API_KEY")
BLOCKED_APPS = os.getenv("BLOCKED_APPS")
REQUIRED_MINUTES = os.getenv("REQUIRED_MINUTES")

HACKATIME_API_URL = "https://hackatime.hackclub.com/api/hackatime/v1"
CHECK_INTERVAL = 60  # sec

class HackatimeError(Exception):
    pass

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
            print(f"You've coded {seconds//60} minutes today.")
        except HackatimeError as e:
            print(f"Error fetching coding time: {e}")
        
        time.sleep(CHECK_INTERVAL)
    
if __name__ == "__main__":
    main()