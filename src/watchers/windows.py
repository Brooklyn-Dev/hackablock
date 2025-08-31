import logging
import sys
import time
import threading

if sys.platform == "win32":
    import pythoncom
    import wmi
else:
    pythoncom = None
    wmi = None

from ..config import BLOCKED_APPS
from ..notifier import Notifier
from ..settings import settings
from ..utils import timestamped_print

def watch_processes(shutdown_event: threading.Event, requirement_met_event: threading.Event, notifier: Notifier | None = None) -> None:
    pythoncom.CoInitialize()
    
    try:
        c = wmi.WMI()
        proc_watcher = c.Win32_Process.watch_for("creation")
        
        while not shutdown_event.is_set():
            if requirement_met_event.is_set():
                shutdown_event.wait(timeout=1)
                continue
            
            try:
                new_proc = proc_watcher(timeout_ms=3000)
                
                if not shutdown_event.is_set() and new_proc.Name.lower() in BLOCKED_APPS:
                    try:
                        new_proc.Terminate()
                        timestamped_print(f"🚫 Blocked {new_proc.Name} from opening")
                        if notifier:
                            notifier.notify(f"🚫 Blocked {new_proc.Name} from opening", f"Code a total of {settings.data["required_minutes"]} minutes to unblock apps.")
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
            
        if shutdown_event.is_set():
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