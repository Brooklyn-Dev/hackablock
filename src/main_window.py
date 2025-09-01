import threading
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QIcon, QFont
from PySide6.QtWidgets import QGroupBox,QHBoxLayout,  QLabel, QLineEdit, QListWidget, QMainWindow, QProgressBar, QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget

from .settings import settings
from .utils import format_time

class MainWindow(QMainWindow):
    refresh_requested = Signal()
    block_requested = Signal()
    
    def __init__(self, requirement_met_event: threading.Event, on_refresh: Callable | None) -> None:
        super().__init__()
        self.requirement_met_event = requirement_met_event
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
        tabs.addTab(self._create_blocked_apps_tab(), "Blocked Apps")
        tabs.addTab(self._create_settings_tab(), "Settings")
    
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
        self.progress_bar.setMaximum(settings.data["minutes_required"] * 60)
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
    
    def _create_blocked_apps_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("Blocked Apps")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        self.blocked_list = QListWidget()
        self.blocked_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for app in settings.data["blocked_apps"]:
            self.blocked_list.addItem(app)
        layout.addWidget(self.blocked_list)
        
        input_layout =  QHBoxLayout()
        self.new_app_input = QLineEdit()
        self.new_app_input.setPlaceholderText("Enter process name (e.g., steam.exe)")
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_blocked_app)
        input_layout.addWidget(self.new_app_input)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)
        
        delete_btn = QPushButton("Delete selected")
        delete_btn.clicked.connect(self._delete_selected_blocked_apps)
        layout.addWidget(delete_btn)
        
        tab.setLayout(layout)
        return tab
    
    def _create_settings_tab(self) -> QWidget:
        def _create_general_group(self) -> QGroupBox:
            general_group = QGroupBox("General")
            general_layout = QVBoxLayout()
            
            self.api_key = QLineEdit()
            self.api_key.setPlaceholderText("Paste your Hackatime API key here")
            self.api_key.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
            self.api_key.setText(settings.data["hackatime_api_key"])
            
            self.required_minutes = QSpinBox()
            self.required_minutes.setRange(1, 720)
            self.required_minutes.setValue(settings.data["minutes_required"])
            
            apply_btn = QPushButton("Apply")
            apply_btn.clicked.connect(self._apply_general_settings)
            
            general_layout.addWidget(QLabel(f"Hackatime API key:"))
            general_layout.addWidget(self.api_key)
            general_layout.addWidget(QLabel(f"Daily required coding time (minutes):"))
            general_layout.addWidget(self.required_minutes)
            general_layout.addWidget(apply_btn)
            
            general_group.setLayout(general_layout)
            return general_group
        
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = QLabel("Settings")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addWidget(_create_general_group(self))
        
        tab.setLayout(layout)
        return tab
    
    def _apply_general_settings(self) -> None:
        settings.update_setting("hackatime_api_key", self.api_key.text())
        settings.update_setting("minutes_required", self.required_minutes.value())
        self.progress_bar.setMaximum(settings.data["minutes_required"] * 60)
        settings.save()
        
        if self.on_refresh:
            self.on_refresh()
    
    def _add_blocked_app(self) -> None:
        if not (new_app := self.new_app_input.text().strip()):
            return

        blocked_apps = settings.data.get("blocked_apps", [])
        if new_app.lower() not in [a.lower() for a in blocked_apps]:
            blocked_apps.append(new_app)
            settings.update_setting("blocked_apps", blocked_apps)
            settings.save()
            self.blocked_list.addItem(new_app)
            self.new_app_input.clear()
        
            if not self.requirement_met_event.is_set():
                self.block_requested.emit()
    
    def _delete_selected_blocked_apps(self) -> None:
        for item in self.blocked_list.selectedItems():
            self.blocked_list.takeItem(self.blocked_list.row(item))
            settings.data["blocked_apps"].remove(item.text())
        settings.save()
    
    def update_progress(self, seconds: int) -> None:
        self.current_seconds = seconds
        
        if seconds >= settings.data["minutes_required"] * 60:
            self.status_label.setText("🎉 Apps are unblocked!")
            self.status_label.setStyleSheet("color: green;")
            self.progress_bar.setValue(settings.data["minutes_required"] * 60)
        else:
            remaining_seconds = settings.data["minutes_required"] * 60 - seconds
            self.status_label.setText(f"⏳ {format_time(remaining_seconds)} remaining to unblock apps")
            self.status_label.setStyleSheet("color: red;")
        self.progress_bar.setValue(seconds)
        
        self.time_label.setText(f"You've coded {format_time(seconds)} today")
    
    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if a0 is not None:
            a0.ignore()
        self.hide()