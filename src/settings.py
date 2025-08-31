from typing import Dict, Hashable

DEFAULTS: Dict = {
    "minutes_required": 60,
}

class Settings:
    def __init__(self) -> None:
        self.data = DEFAULTS.copy()
    
    def update_setting(self, key: str, value: Hashable) -> None:
        self.data[key] = value

settings = Settings()