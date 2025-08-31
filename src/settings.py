import json
import logging
from typing import Callable, Dict, Hashable

from .utils import get_app_path

SETTINGS_FILE = get_app_path() / "hackablock.json"

VALIDATION_RULES: Dict[str, Callable] = {
    "minutes_required": lambda v: isinstance(v, int) and 1 <= v <= 720
}

DEFAULTS: Dict = {
    "minutes_required": 60,
}

class Settings:
    def __init__(self) -> None:
        self._load()
    
    def save(self) -> None:
        try:
            SETTINGS_FILE.write_text(json.dumps(self.data, indent=2))
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
    
    def _load(self) -> None:
        if not SETTINGS_FILE.exists():
            return
        
        try:
            data = json.loads(SETTINGS_FILE.read_text())
            if not isinstance(data, dict):
                raise ValueError("Settings file is not a dict")
        except Exception as e:
            logging.warning(f"Failed to load settings: {e}. Using default values.")
            self.data = DEFAULTS.copy()
            return
        
        validated = {}
        for key, default_value in DEFAULTS.items():
            value = data.get(key, default_value)
            rule = VALIDATION_RULES.get(key, lambda _: True)
            if not rule(value):
                logging.warning(f"Invalid type for {key}: {value}. Using default {default_value}")
                value = default_value
            validated[key] = value
        
        self.data = validated
    
    def update_setting(self, key: str, value: Hashable) -> None:
        self.data[key] = value

settings = Settings()