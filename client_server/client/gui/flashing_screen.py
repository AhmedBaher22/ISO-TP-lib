"""
Simplified Flashing Screen for the ECU Update System.
Shows a loading animation while ECUs are being flashed.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QApplication, 
                            QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

class LoadingCircle(QWidget):
    """A custom widget that shows an animated loading circle"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setMaximumSize(150, 150)
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
        painter.setPen(QPen(QColor("#3498db"), 5))
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

class FlashingScreen(QWidget):
    """Simplified screen to show flashing progress"""
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        self.current_ecu_index = 0
        self.ecu_names = []
        self.ecu_versions = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        self.header = QLabel("Installing Updates")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setFont(QFont("Arial", 24, QFont.Bold))
        self.header.setStyleSheet("color: #2c3e50;")
        
        # Warning message
        warning = QLabel("DO NOT TURN OFF THE VEHICLE")
        warning.setAlignment(Qt.AlignCenter)
        warning.setFont(QFont("Arial", 14, QFont.Bold))
        warning.setStyleSheet("color: #e74c3c;")
        
        # Loading circle
        self.loading_circle = LoadingCircle()
        
        # Current ECU label
        self.current_ecu_label = QLabel("updating...")
        self.current_ecu_label.setAlignment(Qt.AlignCenter)
        self.current_ecu_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.current_ecu_label.setStyleSheet("color: #2c3e50; margin-top: 20px;")
        
        # Add widgets to layout with proper spacing
        layout.addWidget(self.header)
        layout.addWidget(warning)
        layout.addStretch(1)
        layout.addWidget(self.loading_circle, alignment=Qt.AlignCenter)
        layout.addWidget(self.current_ecu_label)
        layout.addStretch(1)
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.flash_progress.connect(self.update_flash_progress)
    
    def set_ecu_list(self, ecu_names):
        """Set the list of ECUs to be flashed"""
        self.ecu_names = list(ecu_names)
        self.current_ecu_index = 0
        
        if len(self.ecu_names) > 0:
            self.update_current_ecu_label(0)
    
    def set_ecu_versions(self, ecu_versions):
        """Set the versions for each ECU"""
        self.ecu_versions = ecu_versions
        
    def update_flash_progress(self, completed_ecus, total_ecus):
        """Update the flashing progress indicators"""
        if total_ecus <= 0:
            return
            
        # Update current ECU if needed
        current_ecu_index = min(completed_ecus, len(self.ecu_names) - 1)
        
        # If we've moved to a new ECU
        if current_ecu_index > self.current_ecu_index:
            self.update_current_ecu_label(current_ecu_index)
    
    def update_current_ecu_label(self, index):
        """Update the label showing the current ECU being flashed"""
        self.current_ecu_index = index
        
        if 0 <= index < len(self.ecu_names):
            ecu_name = self.ecu_names[index]
            
            # Check if we have version info
            if ecu_name in self.ecu_versions:
                version = self.ecu_versions[ecu_name]
                self.current_ecu_label.setText(f"Updating {ecu_name} to version {version}")
            else:
                self.current_ecu_label.setText(f"Updating {ecu_name}")

# For testing the screen individually
if __name__ == "__main__":
    class DummySignalHandler:
        def __init__(self):
            self.flash_progress = None
        
        def connect(self, slot):
            self.flash_progress = slot
    
    app = QApplication(sys.argv)
    
    handler = DummySignalHandler()
    screen = FlashingScreen(handler)
    
    # Set sample ECU list
    screen.set_ecu_list([
        "Engine Control Module",
        "Brake Control Module",
        "Airbag Control Unit"
    ])
    
    # Set sample versions
    screen.set_ecu_versions({
        "Engine Control Module": "1.3.0",
        "Brake Control Module": "2.0.0",
        "Airbag Control Unit": "2.1.2"
    })
    
    screen.show()
    
    # Simulate progress updates
    def update_progress():
        for i in range(4):  # 0, 1, 2, 3
            if i < 3:
                handler.flash_progress(i, 3)
            QTimer.singleShot(i * 2000, lambda idx=i: handler.flash_progress(idx, 3))
    
    QTimer.singleShot(1000, update_progress)
    
    sys.exit(app.exec_())