"""
Main GUI Controller for the ECU Update System.
Manages all screens and handles navigation between them.
"""

import sys
import os
import time
import logging
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QStackedWidget, QMessageBox, QStyleFactory)
from PyQt5.QtCore import pyqtSignal, QObject, QTimer

# Import all screens
from home_screen import HomeScreen  # CLAUDE CHANGE: Added import for new home screen
from welcome_screen import WelcomeScreen
from update_notification_screen import UpdateNotificationScreen
from download_screen import DownloadScreen
from flash_consent_screen import FlashConsentScreen
from flashing_screen import FlashingScreen
from completion_screen import CompletionScreen
from pending_requests_screen import PendingRequestsScreen
from client_for_gui import ECUUpdateClient

# Import backend related modules
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from client_server.client.enums import ClientStatus, ClientDownloadStatus
from client_server.client.shared_models import CarInfo

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
        
        # Initialize tracking flags
        self.download_completed_handled = False
        self.updates_displayed = False
        self.pending_download_handled = False
        self.pending_flash_handled = False
        self.just_flashed = False
        self.download_just_started = False
        self.updates_downloaded = False
        self.updates = {}
        
        # Initialize the UI
        self.init_ui()
        
        # Setup client
        self.client = None
        self.client_thread = None
        self.setup_client()
        
        # CLAUDE CHANGE: Make the app full screen or maximized
        self.showMaximized()  # Use this for maximized window with decorations
        # self.showFullScreen()  # Use this for completely full screen (no window frame)
    
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
        # CLAUDE CHANGE: Added home screen
        self.home_screen = HomeScreen()
        self.welcome_screen = WelcomeScreen(self.signal_handler)
        self.notification_screen = UpdateNotificationScreen(self.signal_handler)
        self.download_screen = DownloadScreen(self.signal_handler)
        self.flash_consent_screen = FlashConsentScreen(self.signal_handler)
        self.flashing_screen = FlashingScreen(self.signal_handler)
        self.completion_screen = CompletionScreen(self.signal_handler)
        self.pending_requests_screen = PendingRequestsScreen(self.signal_handler)
        
        # Add screens to stacked widget
        # CLAUDE CHANGE: Added home screen as first screen
        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.welcome_screen)
        self.stacked_widget.addWidget(self.notification_screen)
        self.stacked_widget.addWidget(self.download_screen)
        self.stacked_widget.addWidget(self.flash_consent_screen)
        self.stacked_widget.addWidget(self.flashing_screen)
        self.stacked_widget.addWidget(self.completion_screen)
        self.stacked_widget.addWidget(self.pending_requests_screen)
        
        # Add stacked widget to main layout
        main_layout.addWidget(self.stacked_widget)
        
        # CLAUDE CHANGE: Set home screen as initial screen
        self.stacked_widget.setCurrentWidget(self.home_screen)
        
        # Connect all signals
        self.connect_signals()

    
    
    def return_to_home_screen(self):
        """Return to the home screen when the back button is clicked"""
        logging.info("Back button clicked, returning to home screen")
        self.stacked_widget.setCurrentWidget(self.home_screen)


    def show_welcome_screen(self):
        """Show welcome screen from home screen"""
        logging.info("Showing welcome screen from home screen")
        self.stacked_widget.setCurrentWidget(self.welcome_screen)
        
        # CLAUDE CHANGE: Start connecting to the server when entering welcome screen
        # This will trigger the connection sequence
        self.signal_handler.status_changed.emit("Connecting to update server...")

    def show_flash_consent(self):
        """Show flash consent screen directly when Install Downloaded Updates button is clicked"""
        logging.info("Showing flash consent screen directly")
        self.stacked_widget.setCurrentWidget(self.flash_consent_screen)
    
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
        
        # CLAUDE CHANGE: Connect home screen check for updates button
        self.home_screen.check_for_updates_clicked.connect(self.show_welcome_screen)
        
        # Welcome screen connections
        self.welcome_screen.view_updates_clicked.connect(self.show_update_notification)
        self.welcome_screen.install_downloaded_clicked.connect(self.show_flash_consent)
        
        # Screen-specific connections
        self.notification_screen.download_approved.connect(self.start_download)
        self.notification_screen.download_declined.connect(self.skip_updates)
        
        self.download_screen.download_cancelled.connect(self.cancel_download)
        
        self.flash_consent_screen.flash_approved.connect(self.start_flashing)
        self.flash_consent_screen.flash_postponed.connect(self.postpone_flashing)
        
        self.completion_screen.done_clicked.connect(self.handle_completion_done)
        
        self.pending_requests_screen.resume_clicked.connect(self.resume_pending_request)
        self.pending_requests_screen.cancel_clicked.connect(self.cancel_pending_request)

        self.welcome_screen.back_button_clicked.connect(self.return_to_home_screen)

    
    def setup_client(self):
        """Set up the ECU update client"""
        try:
            # Initialize client with your specific parameters
            self.client = ECUUpdateClient(
                server_host="localhost",
                server_port=5000,
                data_directory="../client_data"
            )
            
            # Start client monitoring thread
            self.client_thread = threading.Thread(target=self.monitor_client)
            self.client_thread.daemon = True
            self.client_thread.start()
            
            # Start client without automatic background processing
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
                
                # Debug logging
                if self.client.status != last_status:
                    logging.info(f"Client status changed: {last_status} -> {self.client.status}")
                
                # Check for initial connection timeout
                if self.client.status == ClientStatus.OFFLINE:
                    connection_timeout_counter += 1
                    if connection_timeout_counter >= connection_timeout_limit:
                        logging.info("Connection timeout reached, emitting connection_failed signal")
                        self.signal_handler.connection_failed.emit()
                        connection_timeout_counter = 0  # Reset counter
                
                # Handle status changes
                if self.client.status != last_status:
                    last_status = self.client.status
                    status_msg = f"Status: {self.client.status.name}"
                    logging.info(f"Emitting status_changed signal: {status_msg}")
                    self.signal_handler.status_changed.emit(status_msg)
                    
                    # Handle specific status changes
                    if self.client.status == ClientStatus.AUTHENTICATED:
                        logging.info("Emitting connection_success signal")
                        self.signal_handler.connection_success.emit()
                    
                    elif self.client.status == ClientStatus.VERSIONS_UP_TO_DATE:
                        # System is up to date - update welcome screen
                        logging.info("System is up to date, updating welcome screen")
                        self.signal_handler.status_changed.emit("System is up to date")
                        
                        # If we just completed a flashing operation
                        if self.just_flashed:
                            logging.info("Flashing just completed (just_flashed=True), emitting flash_completed signal")
                            self.signal_handler.flash_completed.emit()
                            self.just_flashed = False
                            logging.info("Reset just_flashed to False")
                        else:
                            logging.info("System is up to date but just_flashed=False, not showing completion screen")
                    
                    elif self.client.status == ClientStatus.DOWNLOAD_NEEDED:
                        # Updates are available - update welcome screen
                        logging.info("Updates available, emitting status for welcome screen")
                        self.signal_handler.status_changed.emit("Updates available - download needed")
                        self.signal_handler.status_changed.emit(f"Status: {self.client.status.name}")
                
                # Check for pending download/flash requests
                if hasattr(self.client, 'current_download') and self.client.current_download:
                    download = self.client.current_download
                    
                    # Check if update has been downloaded and is ready to flash
                    if download.status == ClientDownloadStatus.DOWNLOAD_COMPLETED:
                        if not self.updates_downloaded:
                            logging.info("Updates downloaded detected, setting updates_downloaded flag")
                            self.updates_downloaded = True
                            self.signal_handler.status_changed.emit("Updates downloaded - ready to flash")

                    # Check download status - only treat as pending if we didn't just start it
                    if download.status == ClientDownloadStatus.DOWNLOADING:
                        # Only treat as pending if we didn't just start the download ourselves
                        if not self.pending_download_handled and not self.download_just_started:
                            logging.info("Pending download found, emitting pending_download signal")
                            self.signal_handler.pending_download.emit(download)
                            self.pending_download_handled = True
                    
                    # Check flashing status - only treat as pending if we didn't just start it
                    elif download.status == ClientDownloadStatus.IN_FLASHING:
                        if not self.pending_flash_handled and not self.just_flashed:
                            logging.info("Pending flashing found, emitting pending_flash signal")
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
                    # Try to check both possible download completed status values
                    download_completed_status = False
                    try:
                        if download.status == ClientDownloadStatus.DOWNLOAD_COMPLETED:
                            logging.info("Download completed detected (DOWNLOAD_COMPLETED status)")
                            download_completed_status = True
                    except (AttributeError, ValueError):
                        try:
                            if download.status == ClientDownloadStatus.COMPLETED:
                                logging.info("Download completed detected (COMPLETED status)")
                                download_completed_status = True
                        except (AttributeError, ValueError):
                            pass
                    
                    if download_completed_status:
                        logging.info(f"Download completed status: handled={self.download_completed_handled}")
                        if not self.download_completed_handled:
                            logging.info("Emitting download_completed signal")
                            self.signal_handler.download_completed.emit()
                            self.download_completed_handled = True
                            self.updates_downloaded = True  # Set updates downloaded flag
                            logging.info("download_completed_handled set to True")
                
                # Check for updates if authenticated and notify UI
                if self.client.status == ClientStatus.DOWNLOAD_NEEDED:
                    logging.info("Client status is DOWNLOAD_NEEDED, checking for update details")
                    if hasattr(self.client, 'car_info') and self.client.car_info:
                        logging.info(f"Car info found: {self.client.car_info}")
                        # Convert required updates to old_version -> new_version format
                        if hasattr(self.client, 'current_download') and self.client.current_download:
                            logging.info(f"Current download: {self.client.current_download}")
                            if hasattr(self.client.current_download, 'required_updates'):
                                logging.info(f"Required updates: {self.client.current_download.required_updates}")
                                updates = {}
                                for ecu_name, new_version in self.client.current_download.required_updates.items():
                                    old_version = self.client.car_info.ecu_versions.get(ecu_name, "Unknown")
                                    updates[ecu_name] = (old_version, new_version)
                                
                                # Emit signal with updates
                                if updates and not self.updates_displayed:
                                    logging.info(f"Emitting update_available signal with updates: {updates}")
                                    self.signal_handler.update_available.emit(updates)
                                    self.updates_displayed = True
                                else:
                                    logging.info("Updates already displayed, not emitting signal again")
                
                time.sleep(0.5)  # Prevent high CPU usage
            
            except Exception as e:
                logging.error(f"Error monitoring client: {str(e)}")
                time.sleep(1)  # Wait before retrying
    
    def show_update_notification(self):
        """Show update notification screen when user clicks the View Updates button"""
        logging.info("Showing update notification screen")
        
        # Use stored updates if available
        if self.updates:
            logging.info(f"Using stored updates: {self.updates}")
            self.notification_screen.show_updates(self.updates)
        # Otherwise try to get them from the client
        elif hasattr(self.client, 'current_download') and self.client.current_download:
            if hasattr(self.client.current_download, 'required_updates'):
                updates = {}
                for ecu_name, new_version in self.client.current_download.required_updates.items():
                    old_version = self.client.car_info.ecu_versions.get(ecu_name, "Unknown")
                    updates[ecu_name] = (old_version, new_version)
                
                if updates:
                    logging.info(f"Using updates from client: {updates}")
                    self.notification_screen.show_updates(updates)
        
        # Switch to notification screen
        self.stacked_widget.setCurrentWidget(self.notification_screen)
    
    # Signal handlers
    def on_connection_success(self):
        """Handle successful connection to server"""
        logging.info("Connection successful")
        self.welcome_screen.show_connection_success()
        
        # Wait a moment to show the success message before proceeding
        QTimer.singleShot(1500, self.check_for_pending_requests)
    
    def on_connection_failed(self):
        """Handle failed connection to server"""
        logging.info("Connection failed")
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
        logging.info(f"Updates available: {updates}")
        # Store the updates for when the user clicks the View Updates button
        self.updates = updates
        
        # Don't automatically switch to notification screen
        # Just set the flag so we know updates are displayed on welcome screen
        self.updates_displayed = True
        
        # Explicitly force the welcome screen to show updates are available
        # This helps ensure the UI updates correctly
        logging.info("Forcing welcome screen to show updates available")
        self.welcome_screen.show_updates_available()
    
    def on_download_completed(self):
        """Handle download completion"""
        logging.info("Download completed, showing flash consent screen")
        self.updates_downloaded = True

        # Show flash consent screen
        self.stacked_widget.setCurrentWidget(self.flash_consent_screen)
    
    def on_flash_completed(self):
        """Handle flashing completion"""
        logging.info("Flashing completion handler called")
        self.updates_downloaded = False
        
        # Set update details if available
        if hasattr(self.client, 'current_download') and self.client.current_download:
            download = self.client.current_download
            logging.info(f"Current download: {download}")
            
            if hasattr(download, 'downloaded_versions'):
                logging.info(f"Downloaded versions: {download.downloaded_versions}")
                details = []
                for ecu_name, new_version in download.downloaded_versions.items():
                    details.append(f"{ecu_name} updated to version: {new_version}")
                
                if details:
                    logging.info(f"Setting update details: {details}")
                    self.completion_screen.set_update_details(details)
            else:
                logging.info("No downloaded_versions attribute found")
                
                # Try to get info from flashed_ecus instead
                if hasattr(download, 'flashed_ecus'):
                    logging.info(f"Found flashed_ecus: {download.flashed_ecus}")
                    details = []
                    for ecu in download.flashed_ecus:
                        if hasattr(ecu, 'flashing_done') and ecu.flashing_done:
                            details.append(f"{ecu.ecu_name} updated from v{ecu.old_version} to v{ecu.new_version}")
                    
                    if details:
                        logging.info(f"Setting update details from flashed_ecus: {details}")
                        self.completion_screen.set_update_details(details)
        
        # Show completion screen
        self.stacked_widget.setCurrentWidget(self.completion_screen)
    
    def on_pending_download(self, download_request):
        """Handle pending download request"""
        logging.info("Pending download found, showing pending requests screen")
        # Show pending requests screen
        self.stacked_widget.setCurrentWidget(self.pending_requests_screen)
    
    def on_pending_flash(self, download_request):
        """Handle pending flash request"""
        logging.info("Pending flashing found, showing pending requests screen")
        # Show pending requests screen
        self.stacked_widget.setCurrentWidget(self.pending_requests_screen)
    
    # User action handlers
    def start_download(self):
        """Start downloading updates"""
        logging.info("Starting download")
        # Switch to download screen
        self.stacked_widget.setCurrentWidget(self.download_screen)
        
        # Set ECU info in download screen
        if hasattr(self.client, 'current_download') and self.client.current_download:
            if hasattr(self.client.current_download, 'required_updates'):
                logging.info("Setting ECU info in download screen")
                self.download_screen.set_ecu_info(self.client.current_download.required_updates.keys())
        
        # Reset handled flags
        self.download_completed_handled = False
        logging.info("Reset download_completed_handled to False")
        
        # Set flag to indicate we just started a download (to prevent resume dialog)
        self.download_just_started = True
        logging.info("Set download_just_started flag")
        
        # Clear the flag after 5 seconds
        def clear_download_started_flag():
            self.download_just_started = False
            logging.info("Cleared download_just_started flag")
        
        QTimer.singleShot(5000, clear_download_started_flag)
        
        # Initiate download using the client state pattern
        logging.info("Calling client.initiate_download()")
        self.client.initiate_download()
    
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
            logging.info("Skipping updates - returning to welcome screen without canceling")
            # DO NOT cancel the operation, just return to welcome screen
            # so the updates remain available
            
            # Reset UI-related flags but preserve update status
            self.pending_download_handled = False
            self.pending_flash_handled = False
            self.download_completed_handled = False
            self.just_flashed = False
            self.download_just_started = False
            
            # CLAUDE CHANGE: Return to home screen instead of welcome screen
            self.stacked_widget.setCurrentWidget(self.home_screen)
    
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
            logging.info("Cancelling download")
            # Cancel operation through the client
            self.client.cancel_operation()
            
            # Reset to welcome screen
            self.reset_to_welcome()
    
    def start_flashing(self):
        """Start flashing ECUs"""
        logging.info("Starting flashing")
        # Switch to flashing screen
        self.stacked_widget.setCurrentWidget(self.flashing_screen)
        
        # Set ECU list in flashing screen
        if hasattr(self.client, 'current_download') and self.client.current_download:
            # Set ECU names
            ecu_names = []
            ecu_versions = {}
            
            if hasattr(self.client.current_download, 'flashed_ecus'):
                logging.info("Setting ECU list from flashed_ecus")
                for ecu in self.client.current_download.flashed_ecus:
                    ecu_names.append(ecu.ecu_name)
                    ecu_versions[ecu.ecu_name] = ecu.new_version
            elif hasattr(self.client.current_download, 'required_updates'):
                logging.info("Setting ECU list from required_updates")
                for ecu_name, version in self.client.current_download.required_updates.items():
                    ecu_names.append(ecu_name)
                    ecu_versions[ecu_name] = version
            
            self.flashing_screen.set_ecu_list(ecu_names)
            self.flashing_screen.set_ecu_versions(ecu_versions)
        
        # Set flag to detect when flashing completes
        self.just_flashed = True
        logging.info("Set just_flashed to True")
        
        # Start flashing through the client
        logging.info("Calling client.flash_updates()")
        self.client.flash_updates()
    
    def postpone_flashing(self):
        """Postpone flashing for later"""
        logging.info("Postponing flashing - keeping download status")
        QMessageBox.information(
            self,
            "Installation Postponed",
            "Updates have been downloaded and will be available to install later.",
            QMessageBox.Ok
        )
        
        # Reset UI-related flags but preserve download status
        self.pending_download_handled = False
        self.pending_flash_handled = False 
        self.just_flashed = False
        self.download_just_started = False
        
        # Update welcome screen to show "Updates downloaded" status
        self.signal_handler.status_changed.emit("Updates downloaded - ready to flash")
        
        # CLAUDE CHANGE: Return to home screen instead of welcome screen
        self.stacked_widget.setCurrentWidget(self.home_screen)
    
    def resume_pending_request(self):
        """Resume a pending download or flash request"""
        if self.pending_requests_screen.is_download:
            # Resume download
            logging.info("Resuming download")
            self.stacked_widget.setCurrentWidget(self.download_screen)
            
            # Set ECU info
            if hasattr(self.client, 'current_download') and self.client.current_download:
                if hasattr(self.client.current_download, 'required_updates'):
                    logging.info("Setting ECU info in download screen")
                    self.download_screen.set_ecu_info(self.client.current_download.required_updates.keys())
            
            # Reset download flags
            self.download_completed_handled = False
            self.pending_download_handled = False
            self.download_just_started = True
            logging.info("Reset download flags")
            
            # Clear the flag after 5 seconds
            def clear_download_started_flag():
                self.download_just_started = False
                logging.info("Cleared download_just_started flag")
            
            QTimer.singleShot(5000, clear_download_started_flag)
                
            # Resume the download through the client
            logging.info("Calling client.resume_download()")
            self.client.resume_download()
        else:
            # Resume flashing
            logging.info("Resuming flashing")
            self.stacked_widget.setCurrentWidget(self.flashing_screen)
            
            # Set ECU list with versions
            if hasattr(self.client, 'current_download') and self.client.current_download:
                # Set ECU names
                ecu_names = []
                ecu_versions = {}
                
                if hasattr(self.client.current_download, 'flashed_ecus'):
                    logging.info("Setting ECU list from flashed_ecus")
                    for ecu in self.client.current_download.flashed_ecus:
                        ecu_names.append(ecu.ecu_name)
                        ecu_versions[ecu.ecu_name] = ecu.new_version
                elif hasattr(self.client.current_download, 'required_updates'):
                    logging.info("Setting ECU list from required_updates")
                    for ecu_name, version in self.client.current_download.required_updates.items():
                        ecu_names.append(ecu_name)
                        ecu_versions[ecu_name] = version
                
                self.flashing_screen.set_ecu_list(ecu_names)
                self.flashing_screen.set_ecu_versions(ecu_versions)
            
            # Set flash flags
            self.just_flashed = True
            self.pending_flash_handled = False
            logging.info("Reset flash flags")
                
            # Resume flashing through the client
            logging.info("Calling client.resume_flashing()")
            self.client.resume_flashing()
    
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
            logging.info("Cancelling pending request")
            # Cancel the operation through the client
            self.client.cancel_operation()
            
            # Reset to welcome screen
            self.reset_to_welcome()
    
    def reset_to_welcome(self):
        """Reset the GUI to welcome screen"""
        logging.info("Resetting to welcome screen")
        # Reset all handled flags
        self.updates_displayed = False
        self.pending_download_handled = False
        self.pending_flash_handled = False
        self.download_completed_handled = False
        self.just_flashed = False
        self.download_just_started = False
        logging.info("Reset all flags")

        # Check if we still have downloaded updates and update welcome screen accordingly
        if self.updates_downloaded:
            logging.info("Updates are downloaded, showing the appropriate status")
            self.signal_handler.status_changed.emit("Updates downloaded - ready to install")
        else:
            logging.info("No pending updates, showing up to date status")
            self.signal_handler.status_changed.emit("System is up to date")

        # CLAUDE CHANGE: Return to home screen instead of welcome screen
        self.stacked_widget.setCurrentWidget(self.home_screen)
    
    def handle_completion_done(self):
        """Handle when the user clicks Done on the completion screen"""
        logging.info("User clicked Done on completion screen")

        # Reset all flags related to the update process
        self.updates_displayed = False
        self.pending_download_handled = False
        self.pending_flash_handled = False
        self.download_completed_handled = False
        self.just_flashed = False
        self.download_just_started = False
        self.updates_downloaded = False  # Ensure this flag is reset

        # Force the welcome screen to show "System is up to date"
        self.signal_handler.status_changed.emit("System is up to date")

        # CLAUDE CHANGE: Switch to home screen instead of welcome screen
        self.stacked_widget.setCurrentWidget(self.home_screen)

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
            logging.info("Shutting down client")
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
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../client_data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        logging.info(f"Created data directory: {data_dir}")
    
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