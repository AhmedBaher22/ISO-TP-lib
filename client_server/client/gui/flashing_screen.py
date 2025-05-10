"""
Simplified Flashing Screen for the ECU Update System.
Shows a loading animation while ECUs are being flashed.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

# CLAUDE CHANGE: Added ContentPanel class for consistent styling with other screens
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

class LoadingCircle(QWidget):
    """A custom widget that shows an animated loading circle"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # CLAUDE CHANGE: Increased size of loading circle
        self.setMinimumSize(250, 250)
        self.setMaximumSize(250, 250)
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
        radius = min(self.width(), self.height()) / 2 - 15
        
        # Draw a complete light gray circle as background
        # CLAUDE CHANGE: Increased line width for more prominence
        painter.setPen(QPen(QColor("#e0e0e0"), 10))
        painter.drawEllipse(center, radius, radius)
        
        # Draw the blue arc that rotates
        # CLAUDE CHANGE: Increased line width and updated color for better appearance
        painter.setPen(QPen(QColor("#3498db"), 10))
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
        # CLAUDE CHANGE: Create main layout with minimal margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        
        # CLAUDE CHANGE: Create the content panel to contain all widgets
        self.content_panel = ContentPanel()
        
        # CLAUDE CHANGE: Create panel layout
        panel_layout = QVBoxLayout(self.content_panel)
        panel_layout.setContentsMargins(30, 30, 30, 30)
        panel_layout.setSpacing(20)
        
        # Header
        self.header = QLabel("Installing Updates")
        self.header.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI
        self.header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.header.setStyleSheet("color: #2c3e50; background-color: transparent;")
        
        # Warning message
        warning = QLabel("DO NOT TURN OFF THE VEHICLE")
        warning.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI
        warning.setFont(QFont("Segoe UI", 14, QFont.Bold))
        warning.setStyleSheet("color: #e74c3c; background-color: transparent;")
        
        # # CLAUDE CHANGE: Added subtitle for better user experience
        # subtitle = QLabel("Please wait while we install the latest software for your vehicle.")
        # subtitle.setAlignment(Qt.AlignCenter)
        # subtitle.setFont(QFont("Segoe UI", 12))
        # subtitle.setStyleSheet("color: #34495e; background-color: transparent; margin-bottom: 20px;")
        
        # Loading circle
        self.loading_circle = LoadingCircle()
        
        # Current ECU label
        self.current_ecu_label = QLabel("installing...")
        self.current_ecu_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI
        self.current_ecu_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.current_ecu_label.setStyleSheet("color: #2c3e50; margin-top: 20px; background-color: transparent;")
        
        # CLAUDE CHANGE: Added progress info label
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setFont(QFont("Segoe UI", 12))
        self.progress_label.setStyleSheet("color: #34495e; background-color: transparent;")
        
        # CLAUDE CHANGE: Add widgets to panel layout with proper spacing
        panel_layout.addWidget(self.header)
        panel_layout.addWidget(warning)
        # panel_layout.addWidget(subtitle)
        panel_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))
        panel_layout.addWidget(self.loading_circle, alignment=Qt.AlignCenter)
        panel_layout.addWidget(self.current_ecu_label)
        panel_layout.addWidget(self.progress_label)
        panel_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # CLAUDE CHANGE: Add the content panel to the main layout
        self.content_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.content_panel)
        
        # CLAUDE CHANGE: Set overall dark background for main widget
        self.setStyleSheet("""
            QWidget#FlashingScreen {
                background-color: #2c3e50;
            }
        """)
        # Set object name for the style to work
        self.setObjectName("FlashingScreen")
        
        # Connect signals
        self.signal_handler.flash_progress.connect(self.update_flash_progress)
    
    def set_ecu_list(self, ecu_names):
        """Set the list of ECUs to be flashed"""
        self.ecu_names = list(ecu_names)
        self.current_ecu_index = 0
        
        if len(self.ecu_names) > 0:
            self.update_current_ecu_label(0)
            # CLAUDE CHANGE: Update progress information
            self.progress_label.setText(f"ECU 1 of {len(self.ecu_names)}")
    
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
        if current_ecu_index != self.current_ecu_index:
            self.update_current_ecu_label(current_ecu_index)
            
        # CLAUDE CHANGE: Update progress information
        self.progress_label.setText(f"ECU {completed_ecus + 1} of {total_ecus}")
    
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
                
    def resizeEvent(self, event):
        """Handle resize events to keep the content panel full size"""
        super().resizeEvent(event)
        # Force the content panel to update its geometry
        if hasattr(self, 'content_panel'):
            self.content_panel.setGeometry(10, 10, self.width() - 20, self.height() - 20)
