"""
Welcome screen for the ECU Update System.
Shows loading animation until connection is established.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication, 
                            QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
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

class WelcomeScreen(QWidget):
    """Welcome screen with loading animation"""
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
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
        
        # Add widgets to layout with proper spacing
        layout.addStretch(1)
        layout.addWidget(welcome_label)
        layout.addWidget(subtitle_label)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(self.loading_circle, alignment=Qt.AlignCenter)
        layout.addWidget(self.status_label)
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
    
    def update_status(self, status):
        """Update the status message"""
        self.status_label.setText(status)
        
    def show_connection_success(self):
        """Update UI for successful connection"""
        self.loading_circle.timer.stop()
        self.loading_circle.hide()
        
        success_label = QLabel("✓")
        success_label.setAlignment(Qt.AlignCenter)
        success_label.setFont(QFont("Arial", 48))
        success_label.setStyleSheet("color: #2ecc71;")
        
        # Replace loading circle with success icon
        layout = self.layout()
        layout.insertWidget(4, success_label, alignment=Qt.AlignCenter)
        
        self.status_label.setText("Connected successfully!")
        self.status_label.setStyleSheet("color: #2ecc71; margin-top: 20px;")
        
    def show_connection_failure(self):
        """Update UI for connection failure"""
        self.loading_circle.timer.stop()
        self.loading_circle.hide()
        
        failure_label = QLabel("✗")
        failure_label.setAlignment(Qt.AlignCenter)
        failure_label.setFont(QFont("Arial", 48))
        failure_label.setStyleSheet("color: #e74c3c;")
        
        # Replace loading circle with failure icon
        layout = self.layout()
        layout.insertWidget(4, failure_label, alignment=Qt.AlignCenter)
        
        self.status_label.setText("Connection failed. Please try again.")
        self.status_label.setStyleSheet("color: #e74c3c; margin-top: 20px;")

# For testing the screen individually
if __name__ == "__main__":
    class DummySignalHandler:
        def __init__(self):
            pass
        
        def status_changed(self, status):
            pass
    
    app = QApplication(sys.argv)
    screen = WelcomeScreen(DummySignalHandler())
    screen.show()
    
    # Simulate status updates
    def update_status():
        screen.update_status("Connected to server...")
    
    def show_success():
        screen.show_connection_success()
    
    QTimer.singleShot(2000, update_status)
    QTimer.singleShot(4000, show_success)
    
    sys.exit(app.exec_())