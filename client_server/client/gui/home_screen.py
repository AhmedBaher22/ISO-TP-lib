"""
Home Screen for the Car Infotainment System.
Shows the main dashboard with various app icons including the software update option.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QGridLayout, QSpacerItem, QSizePolicy,
                            QFrame, QApplication, QStyleFactory)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPainter, QPen, QPixmap

class AppButton(QPushButton):
    """Custom button for app icons on the home screen"""
    def __init__(self, icon_name, text, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setFont(QFont("Segoe UI", 10))
        self.setCursor(Qt.PointingHandCursor)
        
        # Set fixed size for all app buttons
        self.setMinimumSize(120, 120)
        self.setMaximumSize(120, 120)
        
        # Set icon - using a basic icon display for this example
        self.icon_name = icon_name
        
        # Set button to be flat and styled
        self.setFlat(True)
        self.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: rgba(52, 73, 94, 0.7);
                border-radius: 10px;
                border: 2px solid rgba(255, 255, 255, 0.2);
                padding-top: 65px;
                text-align: bottom;
            }
            QPushButton:hover {
                background-color: rgba(41, 128, 185, 0.8);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(41, 128, 185, 1.0);
                border: 2px solid rgba(255, 255, 255, 0.7);
            }
        """)
    
    def paintEvent(self, event):
        """Custom paint event to draw the icon above the text"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the icon placeholder based on icon_name
        if self.icon_name == "update":
            self.drawUpdateIcon(painter)
        elif self.icon_name == "navigation":
            self.drawNavigationIcon(painter)
        elif self.icon_name == "music":
            self.drawMusicIcon(painter)
        elif self.icon_name == "phone":
            self.drawPhoneIcon(painter)
        elif self.icon_name == "settings":
            self.drawSettingsIcon(painter)
        elif self.icon_name == "climate":
            self.drawClimateIcon(painter)
        else:
            # Default app icon
            self.drawDefaultIcon(painter)
    
    def drawUpdateIcon(self, painter):
        """Draw a software update icon"""
        painter.setPen(QPen(QColor("white"), 2))
        
        # Draw circular arrow
        center_x = self.width() / 2
        center_y = self.height() / 2 - 15  # Move up to make room for text
        radius = min(center_x, center_y) / 2
        
        # Draw download arrow
        arrow_width = radius
        arrow_height = radius
        arrow_x = center_x - arrow_width / 2
        arrow_y = center_y - arrow_height / 2
        
        # CLAUDE CHANGE: Convert all float coordinates to integers
        # Download arrow (rectangle with arrow pointing down)
        painter.drawRect(
            int(arrow_x), 
            int(arrow_y), 
            int(arrow_width), 
            int(arrow_height / 2)
        )
        
        # Arrow head - convert all coordinates to integers
        painter.drawLine(
            int(center_x), 
            int(center_y + arrow_height / 2), 
            int(center_x - arrow_width / 3), 
            int(center_y)
        )
        painter.drawLine(
            int(center_x), 
            int(center_y + arrow_height / 2), 
            int(center_x + arrow_width / 3), 
            int(center_y)
        )
        
        # Draw circular progress - convert all coordinates to integers
        painter.drawArc(
            int(center_x - radius), 
            int(center_y - radius), 
            int(radius * 2), 
            int(radius * 2), 
            0, 
            270 * 16
        )
    
    def drawNavigationIcon(self, painter):
        """Draw a navigation/map icon"""
        painter.setPen(QPen(QColor("white"), 2))
        
        center_x = self.width() / 2
        center_y = self.height() / 2 - 15
        size = min(center_x, center_y)
        
        # Draw map pin
        pin_width = size / 2
        pin_height = size
        
        # CLAUDE CHANGE: Convert all coordinates to integers
        # Draw pin (upside down teardrop)
        painter.drawEllipse(
            int(center_x - pin_width / 2), 
            int(center_y - pin_height / 2), 
            int(pin_width), 
            int(pin_width)
        )
        
        # Draw pin pointer with integer coordinates
        painter.drawLine(
            int(center_x), 
            int(center_y), 
            int(center_x), 
            int(center_y + pin_height / 2)
        )
    
    def drawMusicIcon(self, painter):
        """Draw a music note icon"""
        painter.setPen(QPen(QColor("white"), 2))
        
        center_x = self.width() / 2
        center_y = self.height() / 2 - 15
        size = min(center_x, center_y)
        
        # Draw music note
        note_x = center_x - size / 3
        note_y = center_y - size / 2
        note_width = size / 2
        note_height = size / 4
        
        # CLAUDE CHANGE: Convert all coordinates to integers
        # Draw note head
        painter.drawEllipse(
            int(note_x), 
            int(note_y + size / 2), 
            int(note_width / 2), 
            int(note_height)
        )
        
        # Draw note stem with integer coordinates
        painter.drawLine(
            int(note_x + note_width / 2), 
            int(note_y), 
            int(note_x + note_width / 2), 
            int(note_y + size / 2 + note_height / 2)
        )
    
    def drawPhoneIcon(self, painter):
        """Draw a phone icon"""
        painter.setPen(QPen(QColor("white"), 2))
        
        center_x = self.width() / 2
        center_y = self.height() / 2 - 15
        size = min(center_x, center_y)
        
        # Draw phone outline
        phone_width = size / 1.5
        phone_height = size
        phone_x = center_x - phone_width / 2
        phone_y = center_y - phone_height / 2
        
        # CLAUDE CHANGE: Convert all coordinates to integers
        painter.drawRoundedRect(
            int(phone_x), 
            int(phone_y), 
            int(phone_width), 
            int(phone_height), 
            5, 5
        )
        
        # Draw receiver with integer coordinates
        painter.drawRoundedRect(
            int(phone_x + phone_width / 4), 
            int(phone_y + phone_height / 5), 
            int(phone_width / 2), 
            int(phone_height / 10), 
            2, 2
        )
    
    def drawSettingsIcon(self, painter):
        """Draw a settings/gear icon"""
        painter.setPen(QPen(QColor("white"), 2))
        
        center_x = self.width() / 2
        center_y = self.height() / 2 - 15
        radius = min(center_x, center_y) / 2
        
        # CLAUDE CHANGE: Convert all coordinates to integers
        # Draw gear circle
        painter.drawEllipse(
            int(center_x - radius / 2), 
            int(center_y - radius / 2), 
            int(radius), 
            int(radius)
        )
        
        # Draw gear teeth (8 spokes)
        for i in range(8):
            angle = i * 45 * 3.14159 / 180
            x1 = center_x + radius / 2 * 0.9 * (1.5 if i % 2 == 0 else 1) * (1 if i < 4 else -1)
            y1 = center_y + radius / 2 * 0.9 * (1.5 if i % 2 == 1 else 1) * (1 if i < 2 or i > 5 else -1)
            
            # Convert line coordinates to integers
            painter.drawLine(
                int(center_x), 
                int(center_y), 
                int(x1), 
                int(y1)
            )
    
    def drawClimateIcon(self, painter):
        """Draw a climate control icon"""
        painter.setPen(QPen(QColor("white"), 2))
        
        center_x = self.width() / 2
        center_y = self.height() / 2 - 15
        size = min(center_x, center_y)
        
        # Draw temperature symbol (thermometer)
        therm_x = center_x - size / 8
        therm_y = center_y - size / 2
        therm_width = size / 4
        therm_height = size
        
        # CLAUDE CHANGE: Convert all coordinates to integers
        # Draw thermometer tube
        painter.drawLine(
            int(therm_x + therm_width / 2), 
            int(therm_y + therm_height / 4), 
            int(therm_x + therm_width / 2), 
            int(therm_y + therm_height * 3 / 4)
        )
        
        # Draw thermometer bulb
        painter.drawEllipse(
            int(therm_x), 
            int(therm_y + therm_height * 3 / 4 - therm_width / 2), 
            int(therm_width), 
            int(therm_width)
        )
        
        # Draw snowflake (simple)
        snow_x = center_x + size / 3
        snow_y = center_y
        snow_size = size / 3
        
        # Draw snowflake arms with integer coordinates
        for i in range(3):
            angle = i * 60 * 3.14159 / 180
            dx = snow_size / 2 * (1 if i < 4 else -1)
            dy = snow_size / 2 * (1 if i < 2 or i > 5 else -1)
            
            painter.drawLine(
                int(snow_x), 
                int(snow_y), 
                int(snow_x + dx), 
                int(snow_y + dy)
            )
    
    def drawDefaultIcon(self, painter):
        """Draw a default app icon"""
        painter.setPen(QPen(QColor("white"), 2))
        
        center_x = self.width() / 2
        center_y = self.height() / 2 - 15
        size = min(center_x, center_y) / 2
        
        # CLAUDE CHANGE: Convert coordinates to integers
        # Draw app icon (simple square with rounded corners)
        painter.drawRoundedRect(
            int(center_x - size), 
            int(center_y - size), 
            int(size * 2), 
            int(size * 2), 
            5, 5
        )

class StatusBar(QFrame):
    """Status bar widget shown at the top of the screen"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # Time display
        self.time_label = QLabel("10:30 AM")
        self.time_label.setFont(QFont("Segoe UI", 12))
        self.time_label.setStyleSheet("color: white;")
        
        # Center spacer
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        # Status icons
        self.status_icons = QLabel("🔋 100%  |  📶  |  🔊  |  ⚙️")
        self.status_icons.setFont(QFont("Segoe UI", 12))
        self.status_icons.setStyleSheet("color: white;")
        
        layout.addWidget(self.time_label)
        layout.addItem(spacer)
        layout.addWidget(self.status_icons)

class HomeScreen(QWidget):
    """Main home screen for the car infotainment system"""
    
    # Define custom signal for opening the update screen
    check_for_updates_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()        

    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add status bar at the top
        self.status_bar = StatusBar()
        main_layout.addWidget(self.status_bar)
        
        # Content area with semi-transparent background
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #121212;  /* Dark background */
                color: white;
            }
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Car Infotainment System")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; margin-bottom: 20px;")
        
        # App grid layout
        app_grid = QGridLayout()
        app_grid.setSpacing(20)
        
        # Create app buttons
        # Row 1
        self.update_button = AppButton("update", "Software\nUpdate")
        self.navigation_button = AppButton("navigation", "Navigation")
        self.music_button = AppButton("music", "Music")
        
        # Row 2
        self.phone_button = AppButton("phone", "Phone")
        self.climate_button = AppButton("climate", "Climate")
        self.settings_button = AppButton("settings", "Settings")
        
        # Add buttons to grid
        app_grid.addWidget(self.update_button, 0, 0, Qt.AlignCenter)
        app_grid.addWidget(self.navigation_button, 0, 1, Qt.AlignCenter)
        app_grid.addWidget(self.music_button, 0, 2, Qt.AlignCenter)
        app_grid.addWidget(self.phone_button, 1, 0, Qt.AlignCenter)
        app_grid.addWidget(self.climate_button, 1, 1, Qt.AlignCenter)
        app_grid.addWidget(self.settings_button, 1, 2, Qt.AlignCenter)
        
        # Center the grid in the layout
        grid_container = QWidget()
        grid_container.setLayout(app_grid)
        
        # Add title and grid to content layout
        content_layout.addWidget(title)
        content_layout.addWidget(grid_container, 1, Qt.AlignCenter)
        
        # Add content widget to main layout
        main_layout.addWidget(content_widget)
        
        # Set window properties
        self.setWindowTitle("Car Infotainment System")
        
        # Connect signals
        self.update_button.clicked.connect(self.check_for_updates_clicked.emit)
        
        # Disable other buttons for this demo (they don't do anything)
        self.navigation_button.setEnabled(True)  # Set to False to disable
        self.music_button.setEnabled(True)      # Set to False to disable
        self.phone_button.setEnabled(True)      # Set to False to disable
        self.climate_button.setEnabled(True)    # Set to False to disable  
        self.settings_button.setEnabled(True)   # Set to False to disable

# For testing the screen individually
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    screen = HomeScreen()
    screen.show()
    
    sys.exit(app.exec_())