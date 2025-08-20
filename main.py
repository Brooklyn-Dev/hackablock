from datetime import datetime
import logging
import os
import threading
import time

logging.basicConfig(
    filename="hackablock.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

from dotenv import load_dotenv
import pythoncom
import requests
import wmi

load_dotenv()

WAKATIME_API_KEY = os.getenv("WAKATIME_API_KEY")
BLOCKED_APPS = os.getenv("BLOCKED_APPS")
REQUIRED_MINUTES = int(os.getenv("REQUIRED_MINUTES"))

HACKATIME_API_URL = "https://hackatime.hackclub.com/api/hackatime/v1"
CHECK_INTERVAL = 60  # sec

requirement_met_event = threading.Event()

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

def watch_processes() -> None:
    pythoncom.CoInitialize()
    
    try:
        c = wmi.WMI()
        proc_watcher = c.Win32_Process.watch_for("creation")
        
        while not requirement_met_event.is_set():
            try:
                new_proc = proc_watcher(timeout_ms=5000)
                
                if not requirement_met_event.is_set() and new_proc.Name.lower() in BLOCKED_APPS:
                    try:
                        new_proc.Terminate()
                        timestamped_print(f"🚫 Blocked {new_proc.Name}")
                        logging.info(f"Terminated process: {new_proc.Name} (pid={new_proc.ProcessId})")
                    except (OSError, AttributeError) as e:
                        logging.warning(f"Could not terminate {new_proc.Name}: {e}")
                    except Exception as e:
                        logging.error(f"Unexpected error terminating {new_proc.Name}: {e}")
                        
            except wmi.x_wmi_timed_out:
                continue
            except wmi.x_wmi as e:
                logging.error(f"WMI error in process watcher: {e}")
                time.sleep(3)
            except Exception as e:
                logging.error(f"Unexpected error in process watcher: {e}")
                time.sleep(1)
            
        logging.info(f"Process watcher stopped due to requirement being met.")
        timestamped_print("✅ Process watcher stopped.")
                
    except wmi.x_wmi as e:
        logging.error(f"Failed to initialise WMI: {e}")
        timestamped_print("❌ Failed to start process watcher. See 'hackablock.log'.")
    except Exception as e:
        logging.error(f"Failed to start process watcher: {e}")
        timestamped_print("❌ Failed to start process watcher. See 'hackablock.log'.")
    finally:
        pythoncom.CoUninitialize()

def main() -> None:
    total_seconds = 0
    last_seconds = 0
    
    logging.info("Booting hackablock...")
    timestamped_print("🔃 Loaded hackablock. Session starting...")
    
    watcher_thread = threading.Thread(target=watch_processes, daemon=False)
    watcher_thread.start()
    
    while True:
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
                logging.info(f"{minutes} minutes recorded, {remaining} more required to unblock apps.")
                timestamped_print(f"⏳ You need {remaining} more minutes to meet today's requirement.")
    
                sleep_time = max(remaining * 60, CHECK_INTERVAL)
            else:
                requirement_met_event.set()
                logging.info(f"{REQUIRED_MINUTES} minute requirement met.")
                timestamped_print(f"🎉 Time requirement met! You've coded {minutes} minutes today.")
                
                timestamped_print(f"👀 Shutting down process watcher...")
                watcher_thread.join(timeout=5)
                
                if watcher_thread.is_alive():
                    logging.warning("Watcher thread didn't exit within timeout")
                    timestamped_print("⚠️ Process watcher didn't shut down cleanly.")
                
                logging.info("Terminating hackablock...")
                timestamped_print("🏁 Session complete. Exiting hackablock...")
                return None
            
        except HackatimeError as e:
            logging.error(f"Fetch failed: {e}")
            timestamped_print(f"❌ Could not fetch coding time. See 'hackablock.log'.")
            sleep_time = CHECK_INTERVAL

        time.sleep(sleep_time)
    
if __name__ == "__main__":
    main()