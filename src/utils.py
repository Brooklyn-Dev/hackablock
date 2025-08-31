from datetime import datetime, timedelta
import os
from pathlib import Path
import platform
import subprocess
import sys

def format_time(seconds: int, full_format: bool = False, pad: bool = False) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    
    if pad:
        h_str, m_str, s_str = f"{hours:02d}h", f"{minutes:02d}m", f"{secs:02d}s"
    else:
        h_str, m_str, s_str = f"{hours}h", f"{minutes}m", f"{secs}s"

    if not full_format and hours == 0:
        return f"{m_str} {s_str}"
    
    return f"{h_str} {m_str} {s_str}"

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

def timestamped_print(msg: str) -> None:
    time_str = datetime.now().strftime("%H:%M:%S")
    print(f"[{time_str}] {msg}")
    
def time_until_tomorrow() -> int:
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((tomorrow - now).total_seconds())