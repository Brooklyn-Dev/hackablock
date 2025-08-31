import logging

import requests

from .hackatime_error import HackatimeError
from .settings import settings

HACKATIME_API_URL = "https://hackatime.hackclub.com/api/hackatime/v1"

class CodingTimeTracker:
    def __init__(self) -> None:
        self.total_seconds: int = 0
        self.last_seconds: int = 0
    
    @staticmethod
    def fetch_coding_seconds() -> int:
        try:
            res = requests.get(
                f"{HACKATIME_API_URL}/users/current/statusbar/today",
                headers={"Authorization": f"Bearer {settings.data["hackatime_api_key"]}"},
                timeout=10
            )
            res.raise_for_status()
            
            data = res.json()
            total_seconds = int(data["data"]["grand_total"]["total_seconds"])
            logging.info(f"Fetched coding time: {total_seconds} seconds")
            return total_seconds
        
        except requests.RequestException as e:
            raise HackatimeError(f"Network/API error: {e}") from e
        except KeyError as e:
            raise HackatimeError(f"Unexpected response format: {e}") from e
        except ValueError as e:
            raise HackatimeError(f"Bad data in API response: {e}") from e
    
    def update(self, seconds: int) -> int:
        if seconds >= self.last_seconds:
            self.total_seconds += seconds - self.last_seconds
        else: # Midnight reset
            self.total_seconds += seconds
        self.last_seconds = seconds
        return self.total_seconds