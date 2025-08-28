from datetime import datetime, timedelta
import os
from pathlib import Path
import platform
import subprocess
import sys

def get_app_path(app_name: str = "hackablock") -> Path:
    if getattr(sys, "frozen", False):
        # Production
        system = platform.system()
        if system == "Windows":
            base_dir = Path(os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")) / app_name
        elif system == "Darwin":
            base_dir = Path.home() / "Library" / "Application Support" / app_name
        else:
            base_dir = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / app_name
    else:
        # Development
        base_dir = Path.cwd()
        
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def open_folder(path: Path) -> None:
    path = path.resolve()
    
    system = platform.system()
    if system == "Windows":
        os.startfile(str(path))
    elif system == "Darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])    

def pluralise(text: str, value: int) -> str:
    return f"{text}{"s" if value > 1 else ""}"

def timestamped_print(msg: str) -> None:
    time_str = datetime.now().strftime("%H:%M:%S")
    print(f"[{time_str}] {msg}")
    
def time_until_tomorrow() -> int:
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((tomorrow - now).total_seconds())