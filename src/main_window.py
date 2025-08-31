from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QIcon, QFont
from PySide6.QtWidgets import QLabel, QMainWindow, QProgressBar, QPushButton, QTabWidget, QVBoxLayout, QWidget

from .config import REQUIRED_MINUTES
from .utils import format_time

class MainWindow(QMainWindow):
    refresh_requested = Signal()
    
    def __init__(self, on_refresh: Callable | None) -> None:
        super().__init__()
        self.on_refresh = on_refresh
        self.current_seconds = 0
        
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("Time Spent Coding")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        self.time_label = QLabel("You've coded for 00h 00m 00s today")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(REQUIRED_MINUTES * 60)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("⏳ Keep coding to unblock apps")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(lambda: self.refresh_requested.emit())
        layout.addWidget(refresh_btn)
        
        tab.setLayout(layout)
        return tab
    
    def update_progress(self, seconds: int) -> None:
        self.current_seconds = seconds
        
        self.progress_bar.setValue(seconds)
        
        if seconds >= REQUIRED_MINUTES * 60:
            self.status_label.setText("🎉 Apps are unblocked!")
            self.status_label.setStyleSheet("color: green;")
        else:
            remaining_seconds = REQUIRED_MINUTES * 60 - seconds
            self.status_label.setText(f"⏳ {format_time(remaining_seconds)} remaining to unblock apps")
            self.status_label.setStyleSheet("color: red;")
        
        self.time_label.setText(f"You've coded {format_time(seconds)} today")
    
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if a0 is not None:
            a0.ignore()
        self.hide()