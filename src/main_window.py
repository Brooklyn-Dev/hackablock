from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QIcon, QFont
from PySide6.QtWidgets import QLabel, QMainWindow, QProgressBar, QPushButton, QTabWidget, QVBoxLayout, QWidget

from .config import REQUIRED_MINUTES
from .utils import pluralise

class MainWindow(QMainWindow):
    refresh_requested = Signal()
    
    def __init__(self, on_refresh: Callable | None) -> None:
        super().__init__()
        self.on_refresh = on_refresh
        self.current_minutes = 0
        
        self.setWindowTitle("Hackablock")
        self.setFixedSize(400, 300)
        self.setWindowIcon(QIcon("./assets/favicon.ico"))
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
                
        layout = QVBoxLayout()
        
        tabs = QTabWidget()
        tabs.addTab(self._create_progress_tab(), "Progress")
    
        layout.addWidget(tabs)
        central_widget.setLayout(layout)
        
        if self.on_refresh:
            self.refresh_requested.connect(self.on_refresh)
    
    def _create_progress_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Today's Progress")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        self.minutes_label = QLabel("Minutes coded: 0")
        self.minutes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.minutes_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(REQUIRED_MINUTES)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Apps are blocked")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(lambda: self.refresh_requested.emit())
        layout.addWidget(refresh_btn)
        
        tab.setLayout(layout)
        return tab
    
    def update_progress(self, minutes: int) -> None:
        self.current_minutes = minutes
        self.minutes_label.setText(f"Minutes coded: {minutes}")
        self.progress_bar.setValue(min(minutes, REQUIRED_MINUTES))
        
        if minutes >= REQUIRED_MINUTES:
            self.status_label.setText("🎉 Apps are unblocked!")
            self.status_label.setStyleSheet("color: green;")
        else:
            remaining = REQUIRED_MINUTES - minutes
            self.status_label.setText(f"Need {remaining} more {pluralise("minute", remaining)}")
            self.status_label.setStyleSheet("color: red;")
    
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if a0 is not None:
            a0.ignore()
        self.hide()