from typing import Callable

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

class Tray(QSystemTrayIcon):
    def __init__(
        self,
        on_show_progress: Callable | None = None,
        on_show_logs: Callable | None = None,
        on_quit: Callable | None = None
    ) -> None:
        super().__init__(QIcon("./assets/favicon.ico"))
        
        self._on_show_progress = on_show_progress
        self._on_show_logs = on_show_logs
        self._on_quit = on_quit
        
        self.setToolTip("Hackablock")
        
        self.activated.connect(self._handle_click)
        
        self.messageClicked.connect(self._on_message_clicked)
        
        self._menu = self._create_menu()
        self.setContextMenu(self._menu)
    
    def _create_menu(self) -> QMenu:
        menu = QMenu()
        
        if show_progress_action := menu.addAction("📊 Show Progress"):
            show_progress_action.triggered.connect(self._on_show_progress)
        
        if show_logs_action := menu.addAction("📂 Show Logs"):
            show_logs_action.triggered.connect(self._on_show_logs)
        
        menu.addSeparator()
        
        if quit_action := menu.addAction("❌ Quit"):
            quit_action.triggered.connect(self._on_quit)
        
        return menu
        
    def _handle_click(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        match reason:
            case QSystemTrayIcon.ActivationReason.Trigger:
                if self._on_show_progress:
                    self._on_show_progress()

    def _on_message_clicked(self) -> None:
        if self._on_show_progress:
            self._on_show_progress()