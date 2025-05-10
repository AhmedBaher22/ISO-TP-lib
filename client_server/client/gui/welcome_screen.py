"""
Welcome screen for the ECU Update System.
Shows loading animation until connection is established.
"""

import sys
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication, 
                            QSpacerItem, QSizePolicy, QPushButton, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

class LoadingCircle(QWidget):
    """A custom widget that shows an animated loading circle"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self.setMaximumSize(100, 100)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(50)  # Update every 50ms
        
        # Set styling
        self.setStyleSheet("background-color: transparent;")
    
    def rotate(self):
        """Rotate the circle by updating the angle"""
        self.angle = (self.angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        """Paint the loading circle with a gradient effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        radius = min(self.width(), self.height()) / 2 - 10
        
        # Draw a complete light gray circle as background
        painter.setPen(QPen(QColor("#e0e0e0"), 5))
        painter.drawEllipse(center, radius, radius)
        
        # Draw the blue arc that rotates
        painter.setPen(QPen(QColor("#2980b9"), 5))
        span_angle = 120 * 16  # 120 degrees, in 1/16th of a degree units (Qt convention)
        
        # Convert our angle to Qt's angle system (counterclockwise, starting at 3 o'clock)
        qt_angle = (90 - self.angle) % 360
        start_angle = qt_angle * 16
        
        # Convert to integers as required by drawArc
        x = int(center.x() - radius)
        y = int(center.y() - radius)
        w = int(radius * 2)
        h = int(radius * 2)
        
        painter.drawArc(x, y, w, h, start_angle, span_angle)
    
    def stop(self):
        """Stop the animation"""
        self.timer.stop()
    
    def start(self):
        """Start the animation"""
        self.timer.start()

class StyledButton(QPushButton):
    """Custom styled button with hover effects"""
    def __init__(self, text, button_type="primary", parent=None):
        super().__init__(text, parent)
        # CLAUDE CHANGE: Changed font to Segoe UI which is more modern and better for displays
        self.setFont(QFont("Segoe UI", 12, QFont.Medium))  
        self.setCursor(Qt.PointingHandCursor)
        
        # Set minimum size for better touch targets
        self.setMinimumHeight(45)
        self.setMinimumWidth(200)
        
        # Set style based on button type
        if button_type == "primary":
            # CLAUDE CHANGE: Added 3D effect with border, gradient, and box-shadow
            self.setStyleSheet("""
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #3da7f5, stop:1 #3498db);
                    color: white;
                    border: 1px solid #2980b9;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    border-bottom: 3px solid #2475ab;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #45aef7, stop:1 #2980b9);
                }
                QPushButton:pressed {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #2980b9, stop:1 #2475ab);
                    border-bottom: 1px solid #2475ab;
                    padding-top: 12px;
                }
            """)
        elif button_type == "success":
            # CLAUDE CHANGE: Added 3D effect with border, gradient, and box-shadow
            self.setStyleSheet("""
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #40d47e, stop:1 #32CD32);
                    color: white;
                    border: 1px solid #27ae60;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    border-bottom: 3px solid #229954;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #4adc88, stop:1 #27ae60);
                }
                QPushButton:pressed {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #27ae60, stop:1 #1f8c4d);
                    border-bottom: 1px solid #1f8c4d;
                    padding-top: 12px;
                }
            """)
        elif button_type == "danger":
            # CLAUDE CHANGE: Added 3D effect with border, gradient, and box-shadow
            self.setStyleSheet("""
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #f05a4b, stop:1 #e74c3c);
                    color: white;
                    border: 1px solid #c0392b;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    border-bottom: 3px solid #a5281d;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #f16f61, stop:1 #c0392b);
                }
                QPushButton:pressed {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #c0392b, stop:1 #a5281d);
                    border-bottom: 1px solid #a5281d;
                    padding-top: 12px;
                }
            """)

# CLAUDE CHANGE: Added new container widget class for the grey background panel
class ContentPanel(QFrame):
    """A styled panel to contain all content with rounded corners and shadow"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set frame style
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        
        # Set styling with rounded corners and soft shadow
        self.setStyleSheet("""
            ContentPanel {
                background-color: #C0C0C0;
                border-radius: 15px;
                border: 1px solid #dddddd;
            }
        """)
        
        # Set minimum size
        # self.setMinimumSize(600, 500)

class WelcomeScreen(QWidget):
    """Welcome screen with loading animation"""
    
    # Define custom signals for the buttons
    view_updates_clicked = pyqtSignal()
    install_downloaded_clicked = pyqtSignal()  # New signal for installing downloaded updates
    
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        self.connection_status = "connecting"  # "connecting", "success", "failed", "up_to_date", "updates_available", "updates_downloaded"
        self.init_ui()
        

    def init_ui(self):
        """Initialize the user interface"""
        # CLAUDE CHANGE: Create main layout with minimal margins to maximize screen usage
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)  # Reduce spacing to maximize content area
        
        # CLAUDE CHANGE: Create the content panel to contain all widgets
        self.content_panel = ContentPanel()
        
        # CLAUDE CHANGE: Create panel layout
        panel_layout = QVBoxLayout(self.content_panel)
        panel_layout.setContentsMargins(30, 30, 30, 30)
        
        # Welcome Text
        # welcome_label = QLabel("Welcome")
        # welcome_label.setAlignment(Qt.AlignCenter)
        # # CLAUDE CHANGE: Changed font to Segoe UI for a more modern look
        # welcome_label.setFont(QFont("Segoe UI", 32, QFont.Bold))  
        # # CLAUDE CHANGE: Changed text color to dark blue
        # welcome_label.setStyleSheet("color: #2c3e50; background-color: transparent;")  
        
        # Subtitle
        subtitle_label = QLabel("Software Update")
        subtitle_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI for a more modern look        
        font = QFont("Segoe UI", 32)
        font.setBold(True)  # <-- Make it bold
        subtitle_label.setFont(font)
        # subtitle_label.setFont(QFont("Segoe UI", 32))  
        # CLAUDE CHANGE: Changed text color to dark blue
        subtitle_label.setStyleSheet("color: #34495e; background-color: transparent; margin-bottom: 30px;")  
        
        # Loading circle
        self.loading_circle = LoadingCircle()
        
        # Status message
        self.status_label = QLabel("Connecting to update server...")
        self.status_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI for a more modern look
        self.status_label.setFont(QFont("Segoe UI", 14))  
        # CLAUDE CHANGE: Changed default text color to dark blue (status-specific colors are set in their methods)
        self.status_label.setStyleSheet("color: #34495e; background-color: transparent; margin-top: 20px;")  
        
        # Success icon (hidden initially)
        self.success_label = QLabel("✓")
        self.success_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI for a more modern look
        self.success_label.setFont(QFont("Segoe UI", 48))  
        # CLAUDE CHANGE: Keep green color but transparent background
        self.success_label.setStyleSheet("color: #32CD32; background-color: transparent;")  
        self.success_label.hide()
        
        # Failure icon (hidden initially)
        self.failure_label = QLabel("✗")
        self.failure_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI for a more modern look
        self.failure_label.setFont(QFont("Segoe UI", 48))  
        # CLAUDE CHANGE: Keep red color but transparent background
        self.failure_label.setStyleSheet("color: #e74c3c; background-color: transparent;")  
        self.failure_label.hide()
        
        # Up to date icon (hidden initially)
        self.up_to_date_label = QLabel("✓")
        self.up_to_date_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI for a more modern look
        self.up_to_date_label.setFont(QFont("Segoe UI", 48))  
        # CLAUDE CHANGE: Keep green color but transparent background
        self.up_to_date_label.setStyleSheet("color: #32CD32; background-color: transparent;")  
        self.up_to_date_label.hide()
        
        # Updates available icon (hidden initially)
        self.updates_available_label = QLabel("!")
        self.updates_available_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI for a more modern look
        self.updates_available_label.setFont(QFont("Segoe UI", 48, QFont.Bold))  
        # CLAUDE CHANGE: Keep orange color but transparent background
        self.updates_available_label.setStyleSheet("color: #f39c12; background-color: transparent;")  
        self.updates_available_label.hide()
        
        # Updates downloaded icon (hidden initially)
        self.updates_downloaded_label = QLabel("↓")
        self.updates_downloaded_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI for a more modern look
        self.updates_downloaded_label.setFont(QFont("Segoe UI", 48, QFont.Bold))  
        # CLAUDE CHANGE: Keep blue color but transparent background
        self.updates_downloaded_label.setStyleSheet("color: #3498db; background-color: transparent;")  
        self.updates_downloaded_label.hide()
        
        # View Updates button (hidden initially)
        self.view_updates_button = StyledButton("View Available Updates", "primary")
        self.view_updates_button.hide()
        
        # Install Downloaded Updates button (hidden initially)
        self.install_downloaded_button = StyledButton("Install Updates", "success")
        self.install_downloaded_button.hide()
        
        # Add widgets to panel layout with proper spacing
        panel_layout.addStretch(1)
        # panel_layout.addWidget(welcome_label)
        panel_layout.addWidget(subtitle_label)
        panel_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        panel_layout.addWidget(self.loading_circle, alignment=Qt.AlignCenter)
        panel_layout.addWidget(self.success_label, alignment=Qt.AlignCenter)
        panel_layout.addWidget(self.failure_label, alignment=Qt.AlignCenter)
        panel_layout.addWidget(self.up_to_date_label, alignment=Qt.AlignCenter)
        panel_layout.addWidget(self.updates_available_label, alignment=Qt.AlignCenter)
        panel_layout.addWidget(self.updates_downloaded_label, alignment=Qt.AlignCenter)
        panel_layout.addWidget(self.status_label)
        panel_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum))
        panel_layout.addWidget(self.view_updates_button, alignment=Qt.AlignCenter)
        panel_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum))
        panel_layout.addWidget(self.install_downloaded_button, alignment=Qt.AlignCenter)
        panel_layout.addStretch(1)
        
        # CLAUDE CHANGE: Add the content panel to the main layout with full size policy
        self.content_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.content_panel)
        
        # CLAUDE CHANGE: Set dark background for the main widget (will only show at margins if any)
        self.setStyleSheet("""
            QWidget#WelcomeScreen {
                background-color: #2c3e50;
            }
        """)
        # CLAUDE CHANGE: Need to set object name for the style to work
        self.setObjectName("WelcomeScreen")
        
        # Connect signals
        self.signal_handler.status_changed.connect(self.update_status)
        self.signal_handler.connection_success.connect(self.show_connection_success)
        self.signal_handler.connection_failed.connect(self.show_connection_failure)
        self.view_updates_button.clicked.connect(self.view_updates_clicked.emit)
        self.install_downloaded_button.clicked.connect(self.install_downloaded_clicked.emit)
        


    def resizeEvent(self, event):
        """Handle resize events to keep the content panel full size"""
        super().resizeEvent(event)
        # Force the content panel to update its geometry
        if hasattr(self, 'content_panel'):
            self.content_panel.setGeometry(10, 10, self.width() - 20, self.height() - 20)


    def update_status(self, status):
        """Update the status message"""
        self.status_label.setText(status)
        logging.info(f"Welcome screen status updated to: '{status}'")

        # Check for specific status updates with more explicit, case-insensitive checks
        status_lower = status.lower()
        
        if "up to date" in status_lower or "up_to_date" in status_lower:
            logging.info("Detected 'up to date' status - showing up to date UI")
            self.show_up_to_date()
            
        elif any(phrase in status_lower for phrase in ["download needed", "updates available", "download_needed", "updates_available"]):
            logging.info("Detected 'updates available' status - showing updates available UI")
            self.show_updates_available()
            
        elif any(phrase in status_lower for phrase in ["downloaded", "ready to flash", "ready to install", "ready_to_flash"]):
            logging.info("Detected 'updates downloaded' status - showing updates downloaded UI")
            self.show_updates_downloaded()
            # Force update of button visibility with a short delay
            QTimer.singleShot(100, self.ensure_downloaded_button_visible)
        
    def ensure_downloaded_button_visible(self):
        """Make sure the Install Downloaded Updates button is visible when it should be"""
        if self.connection_status == "updates_downloaded":
            logging.info("Ensuring install button is visible")
            self.install_downloaded_button.show()
            
            # Debugging: Check if button is in layout and visible
            logging.info(f"Install button isVisible: {self.install_downloaded_button.isVisible()}")
            logging.info(f"Install button geometry: {self.install_downloaded_button.geometry()}")
            
            # Force layout update
            self.layout().activate()
            self.update()
        
    def show_connection_success(self):
        """Update UI for successful connection"""
        if self.connection_status in ["up_to_date", "updates_available", "updates_downloaded"]:
            return
            
        self.connection_status = "success"
        self.loading_circle.stop()
        self.loading_circle.hide()
        self.success_label.show()
        self.status_label.setText("Connected successfully!")
        # CLAUDE CHANGE: Keep green text color for success
        self.status_label.setStyleSheet("color: #32CD32; margin-top: 20px; background-color: transparent;")  
    
    def show_connection_failure(self):
        """Update UI for connection failure"""
        self.connection_status = "failed"
        self.loading_circle.stop()
        self.loading_circle.hide()
        self.failure_label.show()
        self.status_label.setText("Connection failed. Please try again.")
        # CLAUDE CHANGE: Keep red text color for failure
        self.status_label.setStyleSheet("color: #e74c3c; margin-top: 20px; background-color: transparent;")  
    
    def show_up_to_date(self):
        """Update UI to show system is up to date"""
        logging.info("Showing up to date UI state")
        self.connection_status = "up_to_date"
        self.loading_circle.stop()
        self.loading_circle.hide()
        self.success_label.hide()
        self.failure_label.hide()
        self.updates_available_label.hide()
        self.updates_downloaded_label.hide()
        self.view_updates_button.hide()
        self.install_downloaded_button.hide()
        self.up_to_date_label.show()
        self.status_label.setText("Your vehicle software is up to date!")
        self.status_label.setFont(QFont("Segoe UI", 18)) 
        # CLAUDE CHANGE: Keep green text color for up to date
        self.status_label.setStyleSheet("color: #32CD32; margin-top: 20px; background-color: transparent;")  
    
    def show_updates_available(self):
        """Update UI to show updates are available"""
        logging.info("Showing updates available UI state")
        self.connection_status = "updates_available"
        self.loading_circle.stop()
        self.loading_circle.hide()
        self.success_label.hide()
        self.failure_label.hide()
        self.up_to_date_label.hide()
        self.updates_downloaded_label.hide()
        self.updates_available_label.show()
        self.view_updates_button.show()
        self.install_downloaded_button.hide()
        self.status_label.setText("Software updates are available for your vehicle!")
        # CLAUDE CHANGE: Keep orange text color for updates available
        self.status_label.setStyleSheet("color: #f39c12; margin-top: 20px; background-color: transparent;")  
        
        # Debug check visibility
        logging.info(f"View updates button visible: {self.view_updates_button.isVisible()}")
    
    def show_updates_downloaded(self):
        """Update UI to show updates are downloaded and ready to install"""
        logging.info("Showing updates downloaded UI state")
        self.connection_status = "updates_downloaded"
        self.loading_circle.stop()
        self.loading_circle.hide()
        self.success_label.hide()
        self.failure_label.hide()
        self.up_to_date_label.hide()
        self.updates_available_label.hide()
        self.updates_downloaded_label.show()
        self.view_updates_button.hide()
        
        # Make sure install button is shown and visible
        self.install_downloaded_button.show()
        logging.info(f"Install button visible after show() call: {self.install_downloaded_button.isVisible()}")
        
        self.status_label.setText("Updates downloaded and ready to install!")
        # CLAUDE CHANGE: Keep blue text color for updates downloaded
        self.status_label.setStyleSheet("color: #3498db; margin-top: 20px; background-color: transparent;")  
        
        # Force layout update
        self.layout().activate()
        self.update()
        
        # Debug: Log UI state
        logging.info(f"UI state after update: updates_downloaded_label visible={self.updates_downloaded_label.isVisible()}, "
                     f"install_button visible={self.install_downloaded_button.isVisible()}")
        
    def reset_to_connecting(self):
        """Reset UI to connecting state"""
        self.connection_status = "connecting"
        self.loading_circle.show()
        self.loading_circle.start()
        self.success_label.hide()
        self.failure_label.hide()
        self.up_to_date_label.hide()
        self.updates_available_label.hide()
        self.updates_downloaded_label.hide()
        self.view_updates_button.hide()
        self.install_downloaded_button.hide()
        self.status_label.setText("Connecting to update server...")
        # CLAUDE CHANGE: Dark blue text color for connecting state
        self.status_label.setStyleSheet("color: #34495e; margin-top: 20px; background-color: transparent;")