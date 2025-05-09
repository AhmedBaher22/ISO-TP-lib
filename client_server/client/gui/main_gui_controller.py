"""
Main GUI Controller for the ECU Update System.
Manages all screens and handles navigation between them.
"""

import sys
import os
import time
import logging
import threading
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QStackedWidget, QMessageBox, QStyleFactory)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer

# Import all screens
from welcome_screen import WelcomeScreen
from update_notification_screen import UpdateNotificationScreen
from download_screen import DownloadScreen
from flash_consent_screen import FlashConsentScreen
from flashing_screen import FlashingScreen
from completion_screen import CompletionScreen
from pending_requests_screen import PendingRequestsScreen

# Import backend related modules
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
    connection_success = pyqtSignal()
    pending_download = pyqtSignal(object)  # ClientDownloadRequest object
    pending_flash = pyqtSignal(object)  # ClientDownloadRequest object

class CarUpdateGUI(QMainWindow):
    """Main window for the Car Update GUI application"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Software Update System")
        self.setMinimumSize(800, 600)
        
        # Create signal handler
        self.signal_handler = SignalHandler()
        
        # Initialize the UI
        self.init_ui()
        
        # Setup client
        self.client = None
        self.client_thread = None
        self.setup_client()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create stacked widget to manage screens
        self.stacked_widget = QStackedWidget()
        
        # Create all screens
        self.welcome_screen = WelcomeScreen(self.signal_handler)
        self.notification_screen = UpdateNotificationScreen(self.signal_handler)
        self.download_screen = DownloadScreen(self.signal_handler)
        self.flash_consent_screen = FlashConsentScreen(self.signal_handler)
        self.flashing_screen = FlashingScreen(self.signal_handler)
        self.completion_screen = CompletionScreen(self.signal_handler)
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
        
        # Set welcome screen as initial screen
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
        
        # Connect all signals
        self.connect_signals()
    
    def connect_signals(self):
        """Connect all signals to slots"""
        # SignalHandler connections
        self.signal_handler.connection_success.connect(self.on_connection_success)
        self.signal_handler.connection_failed.connect(self.on_connection_failed)
        self.signal_handler.update_available.connect(self.on_update_available)
        self.signal_handler.download_completed.connect(self.on_download_completed)
        self.signal_handler.flash_completed.connect(self.on_flash_completed)
        self.signal_handler.pending_download.connect(self.on_pending_download)
        self.signal_handler.pending_flash.connect(self.on_pending_flash)
        
        # Screen-specific connections
        self.notification_screen.download_approved.connect(self.start_download)
        self.notification_screen.download_declined.connect(self.skip_updates)
        
        self.download_screen.download_cancelled.connect(self.cancel_download)
        
        self.flash_consent_screen.flash_approved.connect(self.start_flashing)
        self.flash_consent_screen.flash_postponed.connect(self.postpone_flashing)
        
        self.completion_screen.done_clicked.connect(self.reset_to_welcome)
        
        self.pending_requests_screen.resume_clicked.connect(self.resume_pending_request)
        self.pending_requests_screen.cancel_clicked.connect(self.cancel_pending_request)
    
    def setup_client(self):
        """Set up the ECU update client"""
        try:
            # Initialize client
            self.client = ECUUpdateClient(
                server_host="localhost",
                server_port=5000,
                data_directory="../client_data"
            )
            
            # Start client monitoring thread
            self.client_thread = threading.Thread(target=self.monitor_client)
            self.client_thread.daemon = True
            self.client_thread.start()
            
            # Start client
            self.client.start()
            
        except Exception as e:
            logging.error(f"Failed to initialize client: {str(e)}")
            QMessageBox.critical(
                self,
                "Client Initialization Error",
                f"Failed to initialize update client: {str(e)}",
                QMessageBox.Ok
            )
    
    def monitor_client(self):
        """Monitor client status and emit signals accordingly"""
        last_status = None
        last_download_size = 0
        last_flash_progress = 0
        connection_timeout_counter = 0
        connection_timeout_limit = 10  # Wait 10 seconds max for initial connection
        
        while True:
            try:
                # Check if client is available
                if not self.client:
                    time.sleep(1)
                    continue
                
                # Check for initial connection timeout
                if self.client.status == ClientStatus.OFFLINE:
                    connection_timeout_counter += 1
                    if connection_timeout_counter >= connection_timeout_limit:
                        self.signal_handler.connection_failed.emit()
                        connection_timeout_counter = 0  # Reset counter
                
                # Handle status changes
                if self.client.status != last_status:
                    last_status = self.client.status
                    self.signal_handler.status_changed.emit(f"Status: {self.client.status.name}")
                    
                    # Handle specific status changes
                    if self.client.status == ClientStatus.AUTHENTICATED:
                        self.signal_handler.connection_success.emit()
                    
                    elif self.client.status == ClientStatus.VERSIONS_UP_TO_DATE:
                        # If we just completed a flashing operation
                        if hasattr(self, 'just_flashed') and self.just_flashed:
                            self.signal_handler.flash_completed.emit()
                            self.just_flashed = False
                
                # Check for pending download/flash requests
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
                        if hasattr(download, 'number_of_flashed_ecus') and hasattr(download, 'flashed_ecus'):
                            completed_ecus = download.number_of_flashed_ecus
                            total_ecus = len(download.flashed_ecus)
                            
                            if completed_ecus != last_flash_progress:
                                last_flash_progress = completed_ecus
                                self.signal_handler.flash_progress.emit(
                                    completed_ecus, 
                                    total_ecus
                                )
                    
                    # Check for download completion
                    if download.status == ClientDownloadStatus.COMPLETED:
                        if not hasattr(self, 'download_completed_handled'):
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
                
                time.sleep(0.5)  # Prevent high CPU usage
            
            except Exception as e:
                logging.error(f"Error monitoring client: {str(e)}")
                time.sleep(1)  # Wait before retrying
    
    # Signal handlers
    def on_connection_success(self):
        """Handle successful connection to server"""
        self.welcome_screen.show_connection_success()
        
        # Wait a moment to show the success message before proceeding
        QTimer.singleShot(1500, self.check_for_pending_requests)
    
    def on_connection_failed(self):
        """Handle failed connection to server"""
        self.welcome_screen.show_connection_failure()
        
        # Show error message
        QMessageBox.warning(
            self,
            "Connection Failed",
            "Failed to connect to the update server. Please check your network connection and try again.",
            QMessageBox.Ok
        )
    
    def check_for_pending_requests(self):
        """Check if there are pending download or flashing requests"""
        # This will be handled by the monitor_client thread which emits signals
        # for pending_download and pending_flash
        pass
    
    def on_update_available(self, updates):
        """Handle when updates are available"""
        # Show notification screen
        self.stacked_widget.setCurrentWidget(self.notification_screen)
    
    def on_download_completed(self):
        """Handle download completion"""
        # Show flash consent screen
        self.stacked_widget.setCurrentWidget(self.flash_consent_screen)
    
    def on_flash_completed(self):
        """Handle flashing completion"""
        # Set update details if available
        if hasattr(self.client, 'current_download') and self.client.current_download:
            download = self.client.current_download
            if hasattr(download, 'downloaded_versions'):
                details = []
                for ecu_name, new_version in download.downloaded_versions.items():
                    old_version = self.client.car_info.ecu_versions.get(ecu_name, "Unknown")
                    details.append(f"{ecu_name} updated from v{old_version} to v{new_version}")
                
                if details:
                    self.completion_screen.set_update_details(details)
        
        # Show completion screen
        self.stacked_widget.setCurrentWidget(self.completion_screen)
    
    def on_pending_download(self, download_request):
        """Handle pending download request"""
        # Show pending requests screen
        self.stacked_widget.setCurrentWidget(self.pending_requests_screen)
    
    def on_pending_flash(self, download_request):
        """Handle pending flash request"""
        # Show pending requests screen
        self.stacked_widget.setCurrentWidget(self.pending_requests_screen)
    
    # User action handlers
    def start_download(self):
        """Start downloading updates"""
        # Switch to download screen
        self.stacked_widget.setCurrentWidget(self.download_screen)
        
        # Set ECU info in download screen
        if hasattr(self.client, 'current_download') and self.client.current_download:
            if hasattr(self.client.current_download, 'required_updates'):
                self.download_screen.set_ecu_info(self.client.current_download.required_updates.keys())
        
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
            # Reset to welcome screen
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
            # Reset to welcome screen
            self.reset_to_welcome()
    
    def start_flashing(self):
        """Start flashing ECUs"""
        # Switch to flashing screen
        self.stacked_widget.setCurrentWidget(self.flashing_screen)
        
        # Set ECU list in flashing screen
        if hasattr(self.client, 'current_download') and self.client.current_download:
            if hasattr(self.client.current_download, 'flashed_ecus'):
                ecu_names = [ecu.ecu_name for ecu in self.client.current_download.flashed_ecus]
                self.flashing_screen.set_ecu_list(ecu_names)
            elif hasattr(self.client.current_download, 'required_updates'):
                self.flashing_screen.set_ecu_list(self.client.current_download.required_updates.keys())
        
        # Set flag to detect when flashing completes
        self.just_flashed = True
        
        # Trigger flashing if needed
        if self.client.current_download.status == ClientDownloadStatus.DOWNLOADING:
            # Change status to start flashing
            self.client.current_download.status = ClientDownloadStatus.IN_FLASHING
            # Reset flash handling flag
            if hasattr(self, 'pending_flash_handled'):
                delattr(self, 'pending_flash_handled')
    
    def postpone_flashing(self):
        """Postpone flashing for later"""
        QMessageBox.information(
            self,
            "Installation Postponed",
            "Updates have been downloaded and will be available to install later.",
            QMessageBox.Ok
        )
        self.reset_to_welcome()
    
    def resume_pending_request(self):
        """Resume a pending download or flash request"""
        if self.pending_requests_screen.is_download:
            # Resume download
            self.stacked_widget.setCurrentWidget(self.download_screen)
            
            # Set ECU info
            if hasattr(self.client, 'current_download') and self.client.current_download:
                if hasattr(self.client.current_download, 'required_updates'):
                    self.download_screen.set_ecu_info(self.client.current_download.required_updates.keys())
            
            # Reset download flags
            if hasattr(self, 'download_completed_handled'):
                delattr(self, 'download_completed_handled')
        else:
            # Resume flashing
            self.stacked_widget.setCurrentWidget(self.flashing_screen)
            
            # Set ECU list
            if hasattr(self.client, 'current_download') and self.client.current_download:
                if hasattr(self.client.current_download, 'flashed_ecus'):
                    ecu_names = [ecu.ecu_name for ecu in self.client.current_download.flashed_ecus]
                    self.flashing_screen.set_ecu_list(ecu_names)
            
            # Set flash flags
            self.just_flashed = True
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
            
            # Reset to welcome screen
            self.reset_to_welcome()
    
    def reset_to_welcome(self):
        """Reset the GUI to welcome screen"""
        # Reset all handled flags
        if hasattr(self, 'updates_displayed'):
            delattr(self, 'updates_displayed')
        if hasattr(self, 'pending_download_handled'):
            delattr(self, 'pending_download_handled')
        if hasattr(self, 'pending_flash_handled'):
            delattr(self, 'pending_flash_handled')
        if hasattr(self, 'download_completed_handled'):
            delattr(self, 'download_completed_handled')
        
        # Return to welcome screen
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
    
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self.client, 'current_download') and self.client.current_download:
            if self.client.current_download.status in [ClientDownloadStatus.DOWNLOADING, ClientDownloadStatus.IN_FLASHING]:
                result = QMessageBox.question(
                    self,
                    "Exit Confirmation",
                    "An update operation is in progress. If you exit now, it will be paused and can be resumed later. Are you sure you want to exit?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if result == QMessageBox.No:
                    event.ignore()
                    return
        
        # Shut down client
        if self.client:
            self.client.shutdown()
        
        event.accept()

def main():
    """Main function to run the application"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("updater.log"),
            logging.StreamHandler()
        ]
    )
    
    # Ensure data directory exists
    # data_directory="../client_data"
    # data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    data_dir = os.path.join(".", "client_data")

    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Create QApplication instance
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Create and show the GUI
    gui = CarUpdateGUI()
    gui.show()
    
    # Run application event loop
    return app.exec_()

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)