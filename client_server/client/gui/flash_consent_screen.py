"""
Flash Consent Screen for the ECU Update System.
Asks for user permission before flashing ECUs.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSpacerItem, QSizePolicy, QFrame,
                            QApplication, QStyleFactory, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap

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
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #ecf0f1;
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
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #ecf0f1;
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
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #ecf0f1;
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
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #ecf0f1;
                }
            """)

class WarningBox(QFrame):
    """A styled warning box with icon"""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(self)
        
        # Warning icon
        icon_label = QLabel("⚠️")
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setStyleSheet("background-color: transparent;")
        
        # Warning message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 12))
        message_label.setStyleSheet("color: #856404; background-color: transparent;")
        
        layout.addWidget(icon_label)
        layout.addWidget(message_label, 1)  # 1 is the stretch factor

class StyledCheckBox(QCheckBox):
    """A styled checkbox with custom styling"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Arial", 12))
        self.setStyleSheet("""
            QCheckBox {
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
            }
            QCheckBox::indicator:unchecked {
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 2px solid #3498db;
                image: url('check.png');
            }
            QCheckBox::indicator:checked:hover {
                background-color: #2980b9;
                border: 2px solid #2980b9;
            }
        """)

class FlashConsentScreen(QWidget):
    """Screen to ask for user consent to flash the ECUs"""
    
    # Define custom signals
    flash_approved = pyqtSignal()
    flash_postponed = pyqtSignal()
    
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Ready to Install Updates")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50;")
        
        # Description
        description = QLabel(
            "All updates have been downloaded successfully. "
            "Your vehicle is now ready to install the new software. "
            "Would you like to install the updates now?"
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setFont(QFont("Arial", 14))
        description.setStyleSheet("color: #34495e; margin-bottom: 20px;")
        
        # Warning box
        warning_box = WarningBox(
            "IMPORTANT: During the update installation, your vehicle must remain turned on with the engine running. "
            "Do not attempt to drive or turn off the vehicle until the installation is complete."
        )
        
        # Duration information
        duration_label = QLabel("This process will take approximately 5-10 minutes to complete.")
        duration_label.setAlignment(Qt.AlignCenter)
        duration_label.setFont(QFont("Arial", 12, QFont.Bold))
        duration_label.setStyleSheet("color: #2c3e50; margin: 10px 0;")
        
        # Consent checkbox
        self.consent_checkbox = StyledCheckBox(
            "I understand that I must keep the vehicle turned on during the update process."
        )
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.later_button = StyledButton("Install Later", "secondary")
        self.flash_button = StyledButton("Install Updates", "success")
        self.flash_button.setEnabled(False)  # Disabled until checkbox is checked
        
        # Add buttons to layout
        button_layout.addStretch()
        button_layout.addWidget(self.later_button)
        button_layout.addWidget(self.flash_button)
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(description)
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum))
        layout.addWidget(warning_box)
        layout.addWidget(duration_label)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(self.consent_checkbox)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum))
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.consent_checkbox.stateChanged.connect(self.update_button_state)
        self.flash_button.clicked.connect(self.flash_approved.emit)
        self.later_button.clicked.connect(self.flash_postponed.emit)
    
    def update_button_state(self, state):
        """Enable or disable the flash button based on checkbox state"""
        self.flash_button.setEnabled(state == Qt.Checked)

# For testing the screen individually
if __name__ == "__main__":
    class DummySignalHandler:
        def __init__(self):
            pass
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    screen = FlashConsentScreen(DummySignalHandler())
    screen.show()
    
    sys.exit(app.exec_())