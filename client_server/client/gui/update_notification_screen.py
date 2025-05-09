"""
Update Notification Screen for the ECU Update System.
Shows available updates and asks for user permission to download.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QSpacerItem, QSizePolicy, QFrame,
                            QApplication, QStyleFactory)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap

class UpdateTableWidget(QTableWidget):
    """Enhanced table widget for displaying updates with better styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["ECU Component", "Current Version", "New Version"])
        
        # Stretch the columns to fill the available space
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Set table styling
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        
        # Set other properties
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.verticalHeader().setVisible(False)

class InfoBox(QFrame):
    """A styled info box to display important information"""
    def __init__(self, message, icon_type="info", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        
        # Set style based on icon type
        if icon_type == "info":
            bg_color = "#e1f5fe"
            border_color = "#81d4fa"
            icon_color = "#03a9f4"
            icon = "ℹ"
        elif icon_type == "warning":
            bg_color = "#fff8e1"
            border_color = "#ffe082"
            icon_color = "#ffa000"
            icon = "⚠"
        elif icon_type == "error":
            bg_color = "#ffebee"
            border_color = "#ef9a9a"
            icon_color = "#f44336"
            icon = "✗"
        elif icon_type == "success":
            bg_color = "#e8f5e9"
            border_color = "#a5d6a7"
            icon_color = "#4caf50"
            icon = "✓"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        # Create layout
        layout = QHBoxLayout(self)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 16, QFont.Bold))
        icon_label.setStyleSheet(f"color: {icon_color}; background-color: transparent;")
        icon_label.setFixedWidth(30)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("background-color: transparent;")
        
        layout.addWidget(icon_label)
        layout.addWidget(message_label, 1)  # 1 is the stretch factor
        layout.setContentsMargins(10, 10, 10, 10)

class StyledButton(QPushButton):
    """Custom styled button with hover effects"""
    def __init__(self, text, button_type="primary", parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Arial", 12))
        self.setCursor(Qt.PointingHandCursor)
        
        # Set minimum size for better touch targets
        self.setMinimumHeight(45)
        self.setMinimumWidth(120)
        
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
        elif button_type == "secondary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    border: 1px solid #bdc3c7;
                    border-radius: 8px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #bdc3c7;
                }
                QPushButton:pressed {
                    background-color: #a1a6a9;
                }
            """)

class UpdateNotificationScreen(QWidget):
    """Screen to notify user about available updates and ask for permission to download"""
    
    # Define custom signals
    download_approved = pyqtSignal()
    download_declined = pyqtSignal()
    
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        self.updates = {}  # Will store ecu_name -> (old_version, new_version)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Software Updates Available")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        # Description
        description = QLabel("The following Electronic Control Units (ECUs) have updates available. "
                            "Would you like to download these updates?")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setFont(QFont("Arial", 14))
        description.setStyleSheet("color: #34495e; margin-bottom: 15px;")
        
        # Info box
        self.info_box = InfoBox(
            "Downloading updates will prepare your vehicle for the latest features and improvements. "
            "Your vehicle will remain operational during this process.",
            "info"
        )
        
        # Table for updates
        self.table = UpdateTableWidget()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.skip_button = StyledButton("Skip For Now", "secondary")
        self.download_button = StyledButton("Download Updates", "primary")
        
        # Add spacer to push buttons to the right
        button_layout.addStretch()
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.download_button)
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(description)
        layout.addWidget(self.info_box)
        layout.addWidget(self.table, 1)  # 1 is the stretch factor
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.update_available.connect(self.show_updates)
        self.download_button.clicked.connect(self.download_approved.emit)
        self.skip_button.clicked.connect(self.download_declined.emit)
    
    def show_updates(self, updates):
        """Display the available updates in the table"""
        self.updates = updates
        self.table.setRowCount(len(updates))
        
        row = 0
        for ecu_name, versions in updates.items():
            old_version, new_version = versions
            
            # Create table items
            ecu_item = QTableWidgetItem(ecu_name)
            old_version_item = QTableWidgetItem(old_version)
            new_version_item = QTableWidgetItem(new_version)
            
            # Center align the version numbers
            old_version_item.setTextAlignment(Qt.AlignCenter)
            new_version_item.setTextAlignment(Qt.AlignCenter)
            
            # Highlight new version with green color
            new_version_item.setForeground(QColor("#27ae60"))
            new_version_item.setFont(QFont("Arial", 9, QFont.Bold))
            
            # Set items in the table
            self.table.setItem(row, 0, ecu_item)
            self.table.setItem(row, 1, old_version_item)
            self.table.setItem(row, 2, new_version_item)
            
            row += 1
        
        # Resize row heights for better spacing
        for i in range(self.table.rowCount()):
            self.table.setRowHeight(i, 40)

# For testing the screen individually
if __name__ == "__main__":
    class DummySignalHandler:
        def __init__(self):
            self.update_available = pyqtSignal(dict)
        
        def connect(self, slot):
            pass
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    dummy_handler = DummySignalHandler()
    screen = UpdateNotificationScreen(dummy_handler)
    screen.show()
    
    # Add some sample data
    sample_updates = {
        "Engine Control Module": ("1.2.3", "1.3.0"),
        "Brake Control Module": ("1.5.2", "2.0.0"),
        "Airbag Control Unit": ("2.1.0", "2.1.2"),
        "Transmission Control Unit": ("2.2.4", "2.3.1")
    }
    screen.show_updates(sample_updates)
    
    sys.exit(app.exec_())
    