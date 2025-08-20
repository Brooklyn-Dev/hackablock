from datetime import datetime
import logging
import threading
import time

import psutil
import pythoncom
import requests
import wmi

from .config import WAKATIME_API_KEY, BLOCKED_APPS, REQUIRED_MINUTES
from .tray import Tray

logging.basicConfig(
    filename="hackablock.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

HACKATIME_API_URL = "https://hackatime.hackclub.com/api/hackatime/v1"
CHECK_INTERVAL = 60  # sec

requirement_met_event = threading.Event()
shutdown_event = threading.Event()

tray: Tray | None = None

class HackatimeError(Exception):
    pass

def pluralise(text: str, value: int) -> str:
    return f"{text}{"s" if value > 1 else ""}"

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

def watch_processes() -> None:
    pythoncom.CoInitialize()
    
    try:
        c = wmi.WMI()
        proc_watcher = c.Win32_Process.watch_for("creation")
        
        while not (requirement_met_event.is_set() or shutdown_event.is_set()):
            try:
                new_proc = proc_watcher(timeout_ms=5000)
                
                if not (requirement_met_event.is_set() or shutdown_event.is_set()) and new_proc.Name.lower() in BLOCKED_APPS:
                    try:
                        new_proc.Terminate()
                        timestamped_print(f"🚫 Blocked {new_proc.Name} from opening")
                        logging.info(f"Terminated process: {new_proc.Name} (pid={new_proc.ProcessId})")
                    except (OSError, AttributeError) as e:
                        logging.warning(f"Could not terminate {new_proc.Name}: {e}")
                    except Exception as e:
                        logging.error(f"Unexpected error terminating {new_proc.Name}: {e}")
                        
            except wmi.x_wmi_timed_out:
                continue
            except wmi.x_wmi as e:
                if not shutdown_event.is_set():
                    logging.error(f"WMI error in process watcher: {e}")
                    time.sleep(3)
            except Exception as e:
                if not shutdown_event.is_set():
                    logging.error(f"Unexpected error in process watcher: {e}")
                    time.sleep(1)
            
        if requirement_met_event.is_set():
            logging.info("Process watcher stopped due to requirement being met.")
            timestamped_print("✅ Process watcher stopped - requirement met.")
        elif shutdown_event.is_set():
            logging.info("Process watcher stopped due to shutdown being requested.")
            timestamped_print("✅ Process watcher stopped - shutdown requested.")
                
    except wmi.x_wmi as e:
        logging.error(f"Failed to initialise WMI: {e}")
        timestamped_print("❌ Failed to start process watcher. See 'hackablock.log'.")
    except Exception as e:
        logging.error(f"Failed to start process watcher: {e}")
        timestamped_print("❌ Failed to start process watcher. See 'hackablock.log'.")
    finally:
        pythoncom.CoUninitialize()

def shutdown_watcher(watcher_thread: threading.Thread) -> None:
    timestamped_print("👀 Shutting down process watcher...")
    watcher_thread.join(timeout=5)
    
    if watcher_thread.is_alive():
        logging.warning("Watcher thread didn't exit within timeout")
        timestamped_print("⚠️ Process watcher didn't shut down cleanly.")

def block_running_processes() -> None:
    killed_apps = set()
    failed_kills = []
    
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            proc_name, proc_pid = proc.info["name"], proc.info["pid"]
            if proc_name and proc_name.lower() in BLOCKED_APPS:         
                logging.info(f"Killing running process: {proc_name} (pid={proc_pid})")
                proc.kill()
                killed_apps.add(proc_name)
                
        except psutil.AccessDenied:
            logging.warning(f"Access denied killing {proc_name} (pid={proc_pid})")
            failed_kills.append(f"{proc_name} (access denied)")
        except psutil.NoSuchProcess:
            continue

    if killed_apps:
        apps_list = ", ".join(killed_apps)
        timestamped_print(f"🚫 Blocked running apps: {apps_list}")
    
    if failed_kills:
        failed_list = ", ".join(failed_kills)
        timestamped_print(f"⚠️ Could not kill: {failed_list}")
    
    if not killed_apps and not failed_kills:
        timestamped_print("✅ No blocked apps currently running")

def handle_quit() -> None:
    timestamped_print("🛑 Quit requested from system tray.")
    shutdown_event.set()

def main() -> None:
    total_seconds = 0
    last_seconds = 0
    
    logging.info("Booting hackablock...")
    timestamped_print("🔃 Loaded hackablock. Session starting...")
    
    watcher_thread = threading.Thread(target=watch_processes, daemon=False)
    watcher_thread.start()
    
    block_running_processes()
    
    tray = Tray(on_quit=handle_quit)
    tray.start()
    
    try:
        while not shutdown_event.is_set():
            try:
                seconds = get_coding_time()
                logging.info(f"Fetched coding time: {seconds} seconds")
                
                if seconds >= last_seconds:
                    total_seconds += seconds - last_seconds
                else:
                    # Midnight reset
                    total_seconds += seconds
                
                minutes = total_seconds // 60
                last_seconds = seconds
                
                if minutes < REQUIRED_MINUTES:
                    remaining = REQUIRED_MINUTES - minutes
                    logging.info(f"{minutes} {pluralise("minute", minutes)} recorded, {remaining} more required to unblock apps.")
                    timestamped_print(f"⏳ You need {remaining} more {pluralise("minute", remaining)} to meet today's requirement.")
        
                    sleep_time = max(remaining * 60, CHECK_INTERVAL)
                else:
                    requirement_met_event.set()
                    logging.info(f"{REQUIRED_MINUTES} minute requirement met.")
                    timestamped_print(f"🎉 Time requirement met! You've coded {minutes} {pluralise("minute", minutes)} today.")
                            
                    shutdown_watcher(watcher_thread)
                    return None
                
            except HackatimeError as e:
                logging.error(f"Fetch failed: {e}")
                timestamped_print("❌ Could not fetch coding time. See 'hackablock.log'.")
                sleep_time = CHECK_INTERVAL

            for _ in range(sleep_time):
                if shutdown_event.is_set():
                    shutdown_watcher(watcher_thread)
                    return None
                time.sleep(1)
    
    except KeyboardInterrupt:
        timestamped_print("🛑 Recieved interrupt signal. Shutting down...")
        logging.info("Received KeyboardInterrupt. Shutting down gracefully.")
        
        shutdown_event.set()

        shutdown_watcher(watcher_thread)
        return None
    
    finally:
        timestamped_print("👋 Exiting hackablock...")
        logging.info("Terminating hackablock...\n")
    
if __name__ == "__main__":
    main()