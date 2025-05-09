import sys
import os
import time
import threading
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QProgressBar, 
                            QMessageBox, QStackedWidget, QTableWidget, 
                            QTableWidgetItem, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, Qt, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QIcon, QPixmap, QMovie, QPainter, QColor

# Import necessary modules from the backend code
sys.path.append('..')  # Add parent directory to path if needed
from client import ECUUpdateClient
from enums import ClientStatus, ClientDownloadStatus
from shared_models import CarInfo

class SignalHandler(QObject):
    """Class to handle Qt signals across threads"""
    status_changed = pyqtSignal(str)
    download_progress = pyqtSignal(int, int)  # downloaded_size, total_size
    flash_progress = pyqtSignal(int, int)  # completed_ecus, total_ecus
    download_completed = pyqtSignal()
    flash_completed = pyqtSignal()
    update_available = pyqtSignal(dict)  # ecu_updates dictionary
    connection_failed = pyqtSignal()
    pending_download = pyqtSignal(object)  # ClientDownloadRequest object
    pending_flash = pyqtSignal(object)  # ClientDownloadRequest object

class AnimatedLogo(QLabel):
    """Animated car logo widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(300, 300)
        self.setAlignment(Qt.AlignCenter)
        
        # Create a movie with the GIF animation
        # In a real app, replace with actual path to GIF
        self.movie = QMovie("car_logo.gif")
        if not os.path.exists("car_logo.gif"):
            # If GIF doesn't exist, create a placeholder animation
            self.setStyleSheet("background-color: #3498db; border-radius: 100px;")
            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(2000)
            self.animation.setLoopCount(-1)  # Infinite loop
            
            def start_animation():
                current_geo = self.geometry()
                self.animation.setStartValue(current_geo)
                end_geo = QRect(current_geo.x(), current_geo.y()-20, 
                               current_geo.width(), current_geo.height())
                self.animation.setEndValue(end_geo)
                self.animation.start()
                
            QTimer.singleShot(100, start_animation)
        else:
            self.setMovie(self.movie)
            self.movie.start()

class WelcomeScreen(QWidget):
    """Welcome screen with animation and connecting status"""
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Car Software Update System")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        
        # Logo animation
        self.logo = AnimatedLogo()
        
        # Status message
        self.status_label = QLabel("Connecting to update server...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setStyleSheet("color: #7f8c8d;")
        
        # Add widgets to layout
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(self.logo)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.status_changed.connect(self.update_status)
    
    def update_status(self, status):
        self.status_label.setText(status)

class UpdateNotificationScreen(QWidget):
    """Screen to notify user about available updates and ask for permission"""
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        self.updates = {}  # Will store ecu_name -> (old_version, new_version)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Software Updates Available")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        
        # Description
        description = QLabel("The following Electronic Control Units (ECUs) have updates available:")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setFont(QFont("Arial", 12))
        
        # Table for updates
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ECU", "Current Version", "New Version"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setStyleSheet("QTableWidget { border: none; }")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.download_button = QPushButton("Download Updates")
        self.download_button.setFont(QFont("Arial", 12))
        self.download_button.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: white; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        
        self.skip_button = QPushButton("Skip Now")
        self.skip_button.setFont(QFont("Arial", 12))
        self.skip_button.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #c0392b; }"
        )
        
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.download_button)
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(description)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(self.table)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.update_available.connect(self.show_updates)
    
    def show_updates(self, updates):
        self.updates = updates
        self.table.setRowCount(len(updates))
        
        row = 0
        for ecu_name, versions in updates.items():
            old_version, new_version = versions
            
            ecu_item = QTableWidgetItem(ecu_name)
            old_version_item = QTableWidgetItem(old_version)
            new_version_item = QTableWidgetItem(new_version)
            
            self.table.setItem(row, 0, ecu_item)
            self.table.setItem(row, 1, old_version_item)
            self.table.setItem(row, 2, new_version_item)
            
            row += 1
        
        self.table.resizeColumnsToContents()

class DownloadScreen(QWidget):
    """Screen to show download progress"""
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Downloading Updates")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        
        # Progress information
        self.progress_label = QLabel("Downloading: 0%")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setFont(QFont("Arial", 14))
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #bdc3c7; border-radius: 5px; text-align: center; }"
            "QProgressBar::chunk { background-color: #3498db; }"
        )
        
        # Details
        self.details_label = QLabel("Please wait while the system downloads the updates...")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setWordWrap(True)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(QFont("Arial", 12))
        self.cancel_button.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #c0392b; }"
        )
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.details_label)
        layout.addStretch()
        layout.addWidget(self.cancel_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.download_progress.connect(self.update_progress)
    
    def update_progress(self, downloaded_size, total_size):
        if total_size > 0:
            percent = int((downloaded_size / total_size) * 100)
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f"Downloading: {percent}%")
            self.details_label.setText(
                f"Downloaded {self.format_size(downloaded_size)} of {self.format_size(total_size)}"
            )
    
    def format_size(self, size_bytes):
        """Format bytes into human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.1f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f} GB"

class FlashConsentScreen(QWidget):
    """Screen to ask for user consent to flash the ECUs"""
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Ready to Install Updates")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        
        # Message
        message = QLabel("All updates have been downloaded successfully. Are you ready to install them?")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setFont(QFont("Arial", 14))
        
        # Warning
        warning = QLabel("⚠️ WARNING: Do not turn off the engine or leave the vehicle during the update process.")
        warning.setAlignment(Qt.AlignCenter)
        warning.setWordWrap(True)
        warning.setFont(QFont("Arial", 12, QFont.Bold))
        warning.setStyleSheet("color: #e67e22;")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.flash_button = QPushButton("Install Updates")
        self.flash_button.setFont(QFont("Arial", 12))
        self.flash_button.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: white; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        
        self.later_button = QPushButton("Install Later")
        self.later_button.setFont(QFont("Arial", 12))
        self.later_button.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #c0392b; }"
        )
        
        button_layout.addWidget(self.later_button)
        button_layout.addWidget(self.flash_button)
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(message)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addWidget(warning)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class FlashingScreen(QWidget):
    """Screen to show flashing progress"""
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Installing Updates")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        
        # Status icon/animation
        self.status_widget = QLabel()
        self.status_widget.setAlignment(Qt.AlignCenter)
        self.status_widget.setMinimumSize(100, 100)
        self.status_widget.setStyleSheet("background-color: #3498db; border-radius: 50px;")
        
        # Current ECU label
        self.current_ecu_label = QLabel("Preparing...")
        self.current_ecu_label.setAlignment(Qt.AlignCenter)
        self.current_ecu_label.setFont(QFont("Arial", 14, QFont.Bold))
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 1px solid #bdc3c7; border-radius: 5px; text-align: center; }"
            "QProgressBar::chunk { background-color: #3498db; }"
        )
        
        # Details
        self.details_label = QLabel("Please wait while the system installs the updates...")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setWordWrap(True)
        
        # Warning message
        warning = QLabel("⚠️ DO NOT TURN OFF THE ENGINE OR LEAVE THE VEHICLE")
        warning.setAlignment(Qt.AlignCenter)
        warning.setFont(QFont("Arial", 14, QFont.Bold))
        warning.setStyleSheet("color: #e74c3c;")
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(self.status_widget, alignment=Qt.AlignCenter)
        layout.addWidget(self.current_ecu_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.details_label)
        layout.addStretch()
        layout.addWidget(warning)
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.flash_progress.connect(self.update_progress)
    
    def update_progress(self, completed_ecus, total_ecus):
        if total_ecus > 0:
            percent = int((completed_ecus / total_ecus) * 100)
            self.progress_bar.setValue(percent)
            self.details_label.setText(f"Installing ECU {completed_ecus} of {total_ecus}")

class CompletionScreen(QWidget):
    """Screen to show completion of the update process"""
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout()
        
        # Success icon
        success_icon = QLabel("✓")
        success_icon.setAlignment(Qt.AlignCenter)
        success_icon.setFont(QFont("Arial", 72))
        success_icon.setStyleSheet("color: #2ecc71;")
        
        # Header
        header = QLabel("Updates Installed Successfully")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 20, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        
        # Message
        message = QLabel("All ECUs have been updated to the latest version. Your vehicle is now up to date.")
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setFont(QFont("Arial", 14))
        
        # Done button
        self.done_button = QPushButton("Done")
        self.done_button.setFont(QFont("Arial", 12))
        self.done_button.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: white; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        
        # Add all components to main layout
        layout.addStretch()
        layout.addWidget(success_icon)
        layout.addWidget(header)
        layout.addWidget(message)
        layout.addStretch()
        layout.addWidget(self.done_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)

class PendingRequestsScreen(QWidget):
    """Screen to show pending download or flashing requests"""
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        
        layout = QVBoxLayout()
        
        # Header
        self.header = QLabel("Pending Update Requests")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setFont(QFont("Arial", 20, QFont.Bold))
        self.header.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        
        # Description
        self.description = QLabel("You have pending update operations:")
        self.description.setAlignment(Qt.AlignCenter)
        self.description.setWordWrap(True)
        self.description.setFont(QFont("Arial", 14))
        
        # Details frame
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.StyledPanel)
        details_frame.setStyleSheet("QFrame { background-color: #ecf0f1; border-radius: 10px; padding: 10px; }")
        
        details_layout = QVBoxLayout(details_frame)
        
        self.request_type_label = QLabel("Request Type: Unknown")
        self.request_type_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.request_date_label = QLabel("Date: Unknown")
        self.request_date_label.setFont(QFont("Arial", 12))
        
        self.request_progress_label = QLabel("Progress: 0%")
        self.request_progress_label.setFont(QFont("Arial", 12))
        
        details_layout.addWidget(self.request_type_label)
        details_layout.addWidget(self.request_date_label)
        details_layout.addWidget(self.request_progress_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.resume_button = QPushButton("Resume")
        self.resume_button.setFont(QFont("Arial", 12))
        self.resume_button.setStyleSheet(
            "QPushButton { background-color: #2ecc71; color: white; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #27ae60; }"
        )
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(QFont("Arial", 12))
        self.cancel_button.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; padding: 10px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #c0392b; }"
        )
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.resume_button)
        
        # Add all components to main layout
        layout.addWidget(self.header)
        layout.addWidget(self.description)
        layout.addWidget(details_frame)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.pending_download.connect(self.show_pending_download)
        self.signal_handler.pending_flash.connect(self.show_pending_flash)
    
    def show_pending_download(self, download_request):
        self.header.setText("Resume Download")
        self.description.setText("You have a partially downloaded update:")
        self.request_type_label.setText("Request Type: Download")
        
        # Format date
        date_str = download_request.timestamp.strftime("%Y-%m-%d %H:%M")
        self.request_date_label.setText(f"Date: {date_str}")
        
        # Show progress if available
        if hasattr(download_request, 'downloaded_size') and hasattr(download_request, 'total_size'):
            if download_request.total_size > 0:
                progress = int((download_request.downloaded_size / download_request.total_size) * 100)
                self.request_progress_label.setText(f"Progress: {progress}%")
        
        # Update download info
        self.pending_request = download_request
        self.is_download = True
    
    def show_pending_flash(self, download_request):
        self.header.setText("Resume Flashing")
        self.description.setText("You have downloaded updates ready to install:")
        self.request_type_label.setText("Request Type: Install Updates")
        
        # Format date
        date_str = download_request.timestamp.strftime("%Y-%m-%d %H:%M")
        self.request_date_label.setText(f"Date: {date_str}")
        
        # Show progress if available
        if hasattr(download_request, 'completed_ecus') and hasattr(download_request, 'total_ecus'):
            if download_request.total_ecus > 0:
                progress = int((download_request.completed_ecus / download_request.total_ecus) * 100)
                self.request_progress_label.setText(f"Progress: {progress}%")
        
        # Update flash info
        self.pending_request = download_request
        self.is_download = False

class CarUpdateGUI(QMainWindow):
    """Main window for the Car Update GUI application"""
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupClient()
    
    def initUI(self):
        """Initialize the user interface"""
        self.setWindowTitle("Car Software Update System")
        self.setMinimumSize(700, 500)
        
        # Create signal handler
        self.signal_handler = SignalHandler()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create stacked widget to manage screens
        self.stacked_widget = QStackedWidget()
        
        # Create screens
        self.welcome_screen = WelcomeScreen(self.signal_handler)
        self.notification_screen = UpdateNotificationScreen(self.signal_handler)
        self.download_screen = DownloadScreen(self.signal_handler)
        self.flash_consent_screen = FlashConsentScreen(self.signal_handler)
        self.flashing_screen = FlashingScreen(self.signal_handler)
        self.completion_screen = CompletionScreen()
        self.pending_requests_screen = PendingRequestsScreen(self.signal_handler)
        
        # Add screens to stacked widget
        self.stacked_widget.addWidget(self.welcome_screen)
        self.stacked_widget.addWidget(self.notification_screen)
        self.stacked_widget.addWidget(self.download_screen)
        self.stacked_widget.addWidget(self.flash_consent_screen)
        self.stacked_widget.addWidget(self.flashing_screen)
        self.stacked_widget.addWidget(self.completion_screen)
        self.stacked_widget.addWidget(self.pending_requests_screen)
        
        # Add stacked widget to main layout
        main_layout.addWidget(self.stacked_widget)
        
        # Apply some styling to the main window
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: white;
                font-family: Arial;
            }
        """)
        
        # Connect signals
        self.setup_signal_connections()
        
        # Show welcome screen initially
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
    
    def setup_signal_connections(self):
        """Connect signals to slots"""
        # Signal handler connections
        self.signal_handler.update_available.connect(self.handle_update_available)
        self.signal_handler.download_completed.connect(self.handle_download_completed)
        self.signal_handler.flash_completed.connect(self.handle_flash_completed)
        self.signal_handler.connection_failed.connect(self.handle_connection_failed)
        self.signal_handler.pending_download.connect(self.handle_pending_download)
        self.signal_handler.pending_flash.connect(self.handle_pending_flash)
        
        # Button connections
        self.notification_screen.download_button.clicked.connect(self.start_download)
        self.notification_screen.skip_button.clicked.connect(self.skip_updates)
        
        self.download_screen.cancel_button.clicked.connect(self.cancel_download)
        
        self.flash_consent_screen.flash_button.clicked.connect(self.start_flashing)
        self.flash_consent_screen.later_button.clicked.connect(self.flash_later)
        
        self.completion_screen.done_button.clicked.connect(self.reset_to_welcome)
        
        self.pending_requests_screen.resume_button.clicked.connect(self.resume_pending_request)
        self.pending_requests_screen.cancel_button.clicked.connect(self.cancel_pending_request)
    
    def setupClient(self):
        """Setup the ECU update client"""
        # Initialize the client (replace with actual parameters)
        self.client = ECUUpdateClient(
            server_host="localhost", 
            server_port=5000,
            data_directory="../client_data"
        )
        
        # Start client in a separate thread
        self.client_thread = threading.Thread(target=self.monitor_client)
        self.client_thread.daemon = True
        self.client_thread.start()
        
        # Start client
        self.client.start()
    
    def monitor_client(self):
        """Monitor client status and emit signals accordingly"""
        last_status = None
        last_download_size = 0
        last_flash_progress = 0
        
        while True:
            try:
                # Check if status changed
                if self.client.status != last_status:
                    last_status = self.client.status
                    self.signal_handler.status_changed.emit(f"Status: {self.client.status.name}")
                    
                    # Handle specific status changes
                    if self.client.status == ClientStatus.AUTHENTICATED:
                        pass  # Will proceed to check for updates automatically
                    
                    elif self.client.status == ClientStatus.VERSIONS_UP_TO_DATE:
                        # If we just completed a flashing operation
                        if hasattr(self, 'just_flashed') and self.just_flashed:
                            self.signal_handler.flash_completed.emit()
                            self.just_flashed = False
                
                # Check for pending download requests on startup
                if hasattr(self.client, 'current_download') and self.client.current_download:
                    download = self.client.current_download
                    
                    # Check download status
                    if download.status == ClientDownloadStatus.DOWNLOADING:
                        if not hasattr(self, 'pending_download_handled') or not self.pending_download_handled:
                            self.signal_handler.pending_download.emit(download)
                            self.pending_download_handled = True
                    
                    # Check flashing status
                    elif download.status == ClientDownloadStatus.IN_FLASHING:
                        if not hasattr(self, 'pending_flash_handled') or not self.pending_flash_handled:
                            self.signal_handler.pending_flash.emit(download)
                            self.pending_flash_handled = True
                    
                    # Monitor download progress
                    if download.status == ClientDownloadStatus.DOWNLOADING:
                        if hasattr(download, 'downloaded_size') and hasattr(download, 'total_size'):
                            if download.downloaded_size != last_download_size:
                                last_download_size = download.downloaded_size
                                self.signal_handler.download_progress.emit(
                                    download.downloaded_size, 
                                    download.total_size
                                )
                    
                    # Monitor flashing progress
                    elif download.status == ClientDownloadStatus.IN_FLASHING:
                        if hasattr(download, 'completed_ecus') and hasattr(download, 'total_ecus'):
                            if download.completed_ecus != last_flash_progress:
                                last_flash_progress = download.completed_ecus
                                self.signal_handler.flash_progress.emit(
                                    download.completed_ecus, 
                                    download.total_ecus
                                )
                    
                    # Check for download completion
                    if (download.status == ClientDownloadStatus.COMPLETED and 
                        not hasattr(self, 'download_completed_handled')):
                        self.signal_handler.download_completed.emit()
                        self.download_completed_handled = True
                
                # Check for updates if authenticated
                if self.client.status == ClientStatus.DOWNLOAD_NEEDED:
                    if hasattr(self.client, 'car_info') and self.client.car_info:
                        # Convert required updates to old_version -> new_version format
                        if hasattr(self.client.current_download, 'required_updates'):
                            updates = {}
                            for ecu_name, new_version in self.client.current_download.required_updates.items():
                                old_version = self.client.car_info.ecu_versions.get(ecu_name, "Unknown")
                                updates[ecu_name] = (old_version, new_version)
                            
                            # Emit signal with updates
                            if updates and not hasattr(self, 'updates_displayed'):
                                self.signal_handler.update_available.emit(updates)
                                self.updates_displayed = True
                
                # Check connection status
                if self.client.status == ClientStatus.OFFLINE:
                    if not hasattr(self, 'connection_failed_handled'):
                        self.signal_handler.connection_failed.emit()
                        self.connection_failed_handled = True
                
                time.sleep(0.1)  # Prevent high CPU usage
            
            except Exception as e:
                print(f"Error monitoring client: {str(e)}")
                time.sleep(1)  # Wait before retrying
    
    def handle_update_available(self, updates):
        """Handle when updates are available"""
        # Switch to notification screen
        self.stacked_widget.setCurrentWidget(self.notification_screen)
    
    def handle_download_completed(self):
        """Handle download completion"""
        # Switch to flash consent screen
        self.stacked_widget.setCurrentWidget(self.flash_consent_screen)
    
    def handle_flash_completed(self):
        """Handle flashing completion"""
        # Switch to completion screen
        self.stacked_widget.setCurrentWidget(self.completion_screen)
    
    def handle_connection_failed(self):
        """Handle connection failure"""
        QMessageBox.critical(
            self,
            "Connection Error",
            "Failed to connect to the update server. Please ensure you have internet connectivity and try again.",
            QMessageBox.Ok
        )
    
    def handle_pending_download(self, download_request):
        """Handle pending download request"""
        # Show pending download screen
        self.stacked_widget.setCurrentWidget(self.pending_requests_screen)
        # The pending_requests_screen will handle displaying the download details
    
    def handle_pending_flash(self, download_request):
        """Handle pending flash request"""
        # Show pending flash screen
        self.stacked_widget.setCurrentWidget(self.pending_requests_screen)
        # The pending_requests_screen will handle displaying the flash details
    
    def start_download(self):
        """Start downloading updates"""
        # Switch to download screen
        self.stacked_widget.setCurrentWidget(self.download_screen)
        
        # The client should already be in the process of downloading
        # since it detected updates needed and created a download request
        
        # Reset handled flags
        if hasattr(self, 'download_completed_handled'):
            delattr(self, 'download_completed_handled')
    
    def skip_updates(self):
        """Skip updates for now"""
        result = QMessageBox.question(
            self,
            "Skip Updates",
            "Are you sure you want to skip these updates? They may contain important security or performance improvements.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # Reset client and return to welcome screen
            self.reset_to_welcome()
    
    def cancel_download(self):
        """Cancel download in progress"""
        result = QMessageBox.question(
            self,
            "Cancel Download",
            "Are you sure you want to cancel the download? Progress will be saved and you can resume later.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # The download state should be preserved by the client
            self.reset_to_welcome()
    
    def start_flashing(self):
        """Start flashing ECUs"""
        # Switch to flashing screen
        self.stacked_widget.setCurrentWidget(self.flashing_screen)
        
        # Set flag to detect when flashing completes
        self.just_flashed = True
        
        # Client should already be prepared to flash
        # Trigger flash_updates if needed
        if self.client.current_download.status == ClientDownloadStatus.DOWNLOADING:
            # Change status to start flashing
            self.client.current_download.status = ClientDownloadStatus.IN_FLASHING
            # Reset flash handling flag
            if hasattr(self, 'pending_flash_handled'):
                delattr(self, 'pending_flash_handled')
    
    def flash_later(self):
        """Postpone flashing for later"""
        QMessageBox.information(
            self,
            "Updates Postponed",
            "Updates have been downloaded and will be available to install later.",
            QMessageBox.Ok
        )
        self.reset_to_welcome()
    
    def resume_pending_request(self):
        """Resume a pending download or flash request"""
        if hasattr(self.pending_requests_screen, 'is_download') and self.pending_requests_screen.is_download:
            # Resume download
            self.stacked_widget.setCurrentWidget(self.download_screen)
            
            # Client should automatically resume download
            # Reset download handling flag
            if hasattr(self, 'download_completed_handled'):
                delattr(self, 'download_completed_handled')
        else:
            # Resume flashing
            self.stacked_widget.setCurrentWidget(self.flashing_screen)
            
            # Set flag to detect when flashing completes
            self.just_flashed = True
            
            # Client should continue flashing
            # Reset flash handling flag
            if hasattr(self, 'pending_flash_handled'):
                delattr(self, 'pending_flash_handled')
    
    def cancel_pending_request(self):
        """Cancel a pending request"""
        result = QMessageBox.question(
            self,
            "Cancel Request",
            "Are you sure you want to cancel this operation? You may need to restart it from the beginning later.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # Mark the download as failed
            if self.client.current_download:
                self.client.current_download.status = ClientDownloadStatus.FAILED
                self.client.db.save_download_request(self.client.current_download)
            
            self.reset_to_welcome()
    
    def reset_to_welcome(self):
        """Reset the GUI to welcome screen"""
        # Reset handled flags
        if hasattr(self, 'updates_displayed'):
            delattr(self, 'updates_displayed')
        if hasattr(self, 'pending_download_handled'):
            delattr(self, 'pending_download_handled')
        if hasattr(self, 'pending_flash_handled'):
            delattr(self, 'pending_flash_handled')
        if hasattr(self, 'download_completed_handled'):
            delattr(self, 'download_completed_handled')
        if hasattr(self, 'connection_failed_handled'):
            delattr(self, 'connection_failed_handled')
        
        # Return to welcome screen
        self.stacked_widget.setCurrentWidget(self.welcome_screen)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = CarUpdateGUI()
    gui.show()
    sys.exit(app.exec_())
