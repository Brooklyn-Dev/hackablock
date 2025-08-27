import logging
import sys
import threading
import time
from typing import List, Set, Tuple

import psutil

from .coding_time_tracker import CodingTimeTracker
from .config import BLOCKED_APPS, REQUIRED_MINUTES
from .hackatime_error import HackatimeError
from .tray import Tray
from .utils import get_app_path, notify, open_folder, pluralise, timestamped_print, time_until_tomorrow
from .watchers import watch_processes

CHECK_INTERVAL = 60  # sec

class App:
    def __init__(self) -> None:
        self.requirement_met_event: threading.Event = threading.Event()
        self.shutdown_event: threading.Event = threading.Event()

        self.tray: Tray | None = None
        self.watcher_thread: threading.Thread | None = None
        
        self.tracker: CodingTimeTracker = CodingTimeTracker()

    # ENTRY POINT
    def run(self) -> None:
        self._startup()
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self._handle_shutdown_request()
        finally:
            timestamped_print("👋 Exiting hackablock...")
            logging.info("Terminating hackablock...\n")

    # APP LIFECYCLE
    def _startup(self) -> None:
        logging.info("Booting hackablock...")
        timestamped_print("🔃 Loaded hackablock. Session starting...")
        
        self._start_process_watcher()
        self._block_running_processes()
        self._start_tray()

    def _start_process_watcher(self) -> None:
        if watch_processes:
            self.watcher_thread = threading.Thread(
                target=watch_processes,
                args=(self.shutdown_event, self.requirement_met_event),
                daemon=False
            )
            self.watcher_thread.start()
        else:
            timestamped_print(f"⚠️ Process watching is unsupported on this platform: {sys.platform}")

    def _start_tray(self) -> None:
        self.tray = Tray(on_show_logs=self._handle_show_logs, on_quit=self._handle_quit)
        self.tray.start()
        
    def _shutdown_watcher(self) -> None:
        if not self.watcher_thread or not self.watcher_thread.is_alive():
            return
        
        timestamped_print("👀 Shutting down process watcher...")
        self.shutdown_event.set()
        self.watcher_thread.join(timeout=5)
        
        if self.watcher_thread.is_alive():
            logging.warning("Watcher thread didn't exit within timeout")
            timestamped_print("⚠️ Process watcher didn't shut down cleanly.")

    # BUSINESS LOGIC       
    def _get_minutes_coded(self) -> int:
        seconds = self.tracker.fetch_coding_seconds()
        return self.tracker.update(seconds)
        
    def _handle_progress_update(self, minutes: int) -> int:
        if minutes < REQUIRED_MINUTES:
            self._set_requirement_unmet()
            
            remaining = REQUIRED_MINUTES - minutes
            logging.info(f"{minutes} {pluralise("minute", minutes)} recorded, {remaining} more required to unblock apps.")
            timestamped_print(f"⏳ You need {remaining} more {pluralise("minute", remaining)} to meet today's requirement.")
        else:
            self._set_requirement_met()
            
            logging.info(f"{REQUIRED_MINUTES} minute requirement met.")
            timestamped_print(f"🎉 Time requirement met! You've coded {minutes} {pluralise("minute", minutes)} today.")
            notify("🎉 Time requirement met!", f"You've coded {minutes} {pluralise("minute", minutes)} today. Apps are unblocked!") 
        
        return self._calculate_sleep_time(minutes)
    
    def _block_running_processes(self) -> None:
        killed_apps, failed_kills = self._kill_blocked_processes()
        self._report_processing_blocking_results(killed_apps, failed_kills)

    # STATE MANAGEMENT
    def _set_requirement_met(self) -> None:
        self.requirement_met_event.set()
    
    def _set_requirement_unmet(self) -> None:
        self.requirement_met_event.clear()
        
    # EVENT HANDLERS
    def _handle_show_logs(self) -> None:
        path = get_app_path()
        timestamped_print("📂 Opening 'hackablock.log' in File Explorer.")
        try:
            open_folder(path)
        except Exception as e:
            logging.error(f"Unexpected error opening folder {path}: {e}")
            timestamped_print(f"⚠️ Failed to open folder {path}. See 'hackablock.log'.")

    def _handle_quit(self) -> None:
        timestamped_print("🛑 Quit requested from system tray.")
        self.shutdown_event.set()

    def _handle_fetch_error(self, error: HackatimeError) -> None:
        logging.error(f"Fetch failed: {error}")
        timestamped_print("❌ Could not fetch coding time. See 'hackablock.log'.")

    def _handle_shutdown_request(self) -> None:
        timestamped_print("🛑 Recieved interrupt signal. Shutting down...")
        logging.info("Received KeyboardInterrupt. Shutting down gracefully.")
        self._shutdown_watcher()
    
    # INTERNAL HELPERS           
    def _main_loop(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                minutes = self._get_minutes_coded()
                sleep_time = self._handle_progress_update(minutes)
            except HackatimeError as e:
                self._handle_fetch_error(e)
                sleep_time = CHECK_INTERVAL

            for _ in range(sleep_time):
                if self.shutdown_event.is_set():
                    return None
                time.sleep(1)
            
    def _calculate_sleep_time(self, minutes: int) -> int:
        if minutes < REQUIRED_MINUTES:
            remaining = REQUIRED_MINUTES - minutes
            return max(remaining * 60, CHECK_INTERVAL)
        else:
            return time_until_tomorrow()
    
    def _kill_blocked_processes(self) -> Tuple[Set[str], List[str]]:
        killed_apps = set()
        failed_kills = []
        
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name, pid = proc.info["name"], proc.info["pid"]
                if name and name.lower() in BLOCKED_APPS:         
                    logging.info(f"Killing running process: {name} (pid={pid})")
                    proc.kill()
                    killed_apps.add(name)
                    
            except psutil.AccessDenied:
                logging.warning(f"Access denied killing {name} (pid={pid})")
                failed_kills.append(f"{name} (access denied)")
            except psutil.NoSuchProcess:
                continue
        
        return killed_apps, failed_kills

    def _report_processing_blocking_results(self, killed_apps: Set[str], failed_kills: List[str]) -> None:
        if killed_apps:
            apps_list = ", ".join(killed_apps)
            timestamped_print(f"🚫 Blocked running apps: {apps_list}")
            notify("🚫 Blocked running apps:", apps_list)
        if failed_kills:
            failed_list = ", ".join(failed_kills)
            timestamped_print(f"⚠️ Could not kill: {failed_list}")
            notify("⚠️ Could not kill:", failed_list)
        if not killed_apps and not failed_kills:
            timestamped_print("✅ No blocked apps currently running")