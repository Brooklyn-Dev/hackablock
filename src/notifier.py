from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QSystemTrayIcon

class Notifier(QObject):
    notify_signal: Signal = Signal(str, str)
    
    def __init__(self, tray: QSystemTrayIcon):
        super().__init__()
        self._tray = tray
        self.notify_signal.connect(self._show_message)
        
    def _show_message(self, title: str, message: str):
        self._tray.showMessage(title, message)
    
    def notify(self, title: str, message: str):
        self.notify_signal.emit(title, message)