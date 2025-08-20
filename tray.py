import threading
from typing import Any, Callable

from PIL import Image
from pystray import Icon, Menu, MenuItem

class Tray:
    def __init__(
        self,
        on_quit: Callable | None = None
    ) -> None:
        self.on_quit = on_quit
        
        self.icon: Any | None = None
        self.tray_thread: threading.Thread | None = None
        self._is_blocking = True
    
    def _create_menu(self) -> Menu:
        return Menu(
            MenuItem("Quit", self._quit_handler),
        )
        
    def _quit_handler(self) -> None:
        if self.on_quit:
            self.on_quit()
        if self.icon:
            self.icon.stop()
        
    def start(self) -> None:
        if self.tray_thread and self.tray_thread.is_alive():
            return
        
        def run_tray() -> None:
            image = Image.open("./favicon.ico")
            menu = self._create_menu()
            
            self.icon = Icon("hb", image, "hackablock", menu)
            self.icon.run()

        self.tray_thread = threading.Thread(target=run_tray, daemon=True)
        self.tray_thread.start()
        
    def stop(self) -> None:
        if self.icon:
            self.icon.stop()
        if self.tray_thread:
            self.tray_thread.join(timeout=2)