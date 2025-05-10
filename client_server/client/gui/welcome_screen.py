"""
Welcome screen for the ECU Update System.
Shows loading animation until connection is established.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication, 
                            QSpacerItem, QSizePolicy, QPushButton)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QFontMetrics

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
        self.setFont(QFont("Arial", 12))
        self.setCursor(Qt.PointingHandCursor)
        
        # Set minimum size for better touch targets
        self.setMinimumHeight(45)
        self.setMinimumWidth(200)
        
        # Set style based on button type
        if button_type == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #1f6dad;
                }
            """)
        elif button_type == "success":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
                QPushButton:pressed {
                    background-color: #1f8c4d;
                }
            """)
        elif button_type == "danger":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
                QPushButton:pressed {
                    background-color: #a5281d;
                }
            """)

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
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Welcome Text
        welcome_label = QLabel("Welcome")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setFont(QFont("Arial", 32, QFont.Bold))
        welcome_label.setStyleSheet("color: #2c3e50;")
        
        # Subtitle
        subtitle_label = QLabel("Car Software Update System")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 18))
        subtitle_label.setStyleSheet("color: #34495e; margin-bottom: 30px;")
        
        # Loading circle
        self.loading_circle = LoadingCircle()
        
        # Status message
        self.status_label = QLabel("Connecting to update server...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setStyleSheet("color: #7f8c8d; margin-top: 20px;")
        
        # Success icon (hidden initially)
        self.success_label = QLabel("✓")
        self.success_label.setAlignment(Qt.AlignCenter)
        self.success_label.setFont(QFont("Arial", 48))
        self.success_label.setStyleSheet("color: #2ecc71;")
        self.success_label.hide()
        
        # Failure icon (hidden initially)
        self.failure_label = QLabel("✗")
        self.failure_label.setAlignment(Qt.AlignCenter)
        self.failure_label.setFont(QFont("Arial", 48))
        self.failure_label.setStyleSheet("color: #e74c3c;")
        self.failure_label.hide()
        
        # Up to date icon (hidden initially)
        self.up_to_date_label = QLabel("✓")
        self.up_to_date_label.setAlignment(Qt.AlignCenter)
        self.up_to_date_label.setFont(QFont("Arial", 48))
        self.up_to_date_label.setStyleSheet("color: #2ecc71;")
        self.up_to_date_label.hide()
        
        # Updates available icon (hidden initially)
        self.updates_available_label = QLabel("!")
        self.updates_available_label.setAlignment(Qt.AlignCenter)
        self.updates_available_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.updates_available_label.setStyleSheet("color: #f39c12;")
        self.updates_available_label.hide()
        
        # Updates downloaded icon (hidden initially)
        self.updates_downloaded_label = QLabel("↓")
        self.updates_downloaded_label.setAlignment(Qt.AlignCenter)
        self.updates_downloaded_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.updates_downloaded_label.setStyleSheet("color: #3498db;")
        self.updates_downloaded_label.hide()
        
        # View Updates button (hidden initially)
        self.view_updates_button = StyledButton("View Available Updates", "primary")
        self.view_updates_button.hide()
        
        # Install Downloaded Updates button (hidden initially)
        self.install_downloaded_button = StyledButton("Install Downloaded Updates", "success")
        self.install_downloaded_button.hide()
        
        # Add widgets to layout with proper spacing
        layout.addStretch(1)
        layout.addWidget(welcome_label)
        layout.addWidget(subtitle_label)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(self.loading_circle, alignment=Qt.AlignCenter)
        layout.addWidget(self.success_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.failure_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.up_to_date_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.updates_available_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.updates_downloaded_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum))
        layout.addWidget(self.view_updates_button, alignment=Qt.AlignCenter)
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum))
        layout.addWidget(self.install_downloaded_button, alignment=Qt.AlignCenter)
        layout.addStretch(1)
        
        self.setLayout(layout)
        
        # Set overall styling
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        
        # Connect signals
        self.signal_handler.status_changed.connect(self.update_status)
        self.signal_handler.connection_success.connect(self.show_connection_success)
        self.signal_handler.connection_failed.connect(self.show_connection_failure)
        self.view_updates_button.clicked.connect(self.view_updates_clicked.emit)
        self.install_downloaded_button.clicked.connect(self.install_downloaded_clicked.emit)
    
    def update_status(self, status):
        """Update the status message"""
        self.status_label.setText(status)

        # Check for specific status updates
        if "up_to_date" in status.lower():
            self.show_up_to_date()
        elif "download_needed" in status.lower() or "updates_available" in status.lower():
            self.show_updates_available()
        elif "updates_downloaded" in status.lower() or "ready_to_flash" in status.lower():
            self.show_updates_downloaded()
        
    def show_connection_success(self):
        """Update UI for successful connection"""
        if self.connection_status in ["up_to_date", "updates_available", "updates_downloaded"]:
            return
            
        self.connection_status = "success"
        self.loading_circle.stop()
        self.loading_circle.hide()
        self.success_label.show()
        self.status_label.setText("Connected successfully!")
        self.status_label.setStyleSheet("color: #2ecc71; margin-top: 20px;")
    
    def show_connection_failure(self):
        """Update UI for connection failure"""
        self.connection_status = "failed"
        self.loading_circle.stop()
        self.loading_circle.hide()
        self.failure_label.show()
        self.status_label.setText("Connection failed. Please try again.")
        self.status_label.setStyleSheet("color: #e74c3c; margin-top: 20px;")
    
    def show_up_to_date(self):
        """Update UI to show system is up to date"""
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
        self.status_label.setStyleSheet("color: #2ecc71; margin-top: 20px;")
    
    def show_updates_available(self):
        """Update UI to show updates are available"""
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
        self.status_label.setStyleSheet("color: #f39c12; margin-top: 20px;")
    
    def show_updates_downloaded(self):
        """Update UI to show updates are downloaded and ready to install"""
        self.connection_status = "updates_downloaded"
        self.loading_circle.stop()
        self.loading_circle.hide()
        self.success_label.hide()
        self.failure_label.hide()
        self.up_to_date_label.hide()
        self.updates_available_label.hide()
        self.updates_downloaded_label.show()
        self.view_updates_button.hide()
        self.install_downloaded_button.show()
        self.status_label.setText("Updates downloaded and ready to install!")
        self.status_label.setStyleSheet("color: #3498db; margin-top: 20px;")
        
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
        self.status_label.setStyleSheet("color: #7f8c8d; margin-top: 20px;")

# For testing the screen individually
if __name__ == "__main__":
    class DummySignalHandler:
        def __init__(self):
            self.status_changed = None
            self.connection_success = None
            self.connection_failed = None
        
        def connect(self, func):
            if func.__name__ == "update_status":
                self.status_changed = func
            elif func.__name__ == "show_connection_success":
                self.connection_success = func
            elif func.__name__ == "show_connection_failure":
                self.connection_failed = func
    
    app = QApplication(sys.argv)
    
    handler = DummySignalHandler()
    screen = WelcomeScreen(handler)
    screen.show()
    
    # Simulate status updates
    def update_status():
        handler.status_changed("Connected to server...")
    
    def show_success():
        handler.connection_success()
    
    def show_updates_available():
        handler.status_changed("Updates available - download needed")
    
    def show_updates_downloaded():
        handler.status_changed("Updates downloaded - ready to flash")
        
    QTimer.singleShot(1000, update_status)
    QTimer.singleShot(2000, show_success)
    QTimer.singleShot(3000, show_updates_available)
    QTimer.singleShot(5000, show_updates_downloaded)
    
    sys.exit(app.exec_())