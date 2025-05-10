"""
Flash Consent Screen for the ECU Update System.
Asks for user permission before flashing ECUs.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSpacerItem, QSizePolicy, QFrame, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

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
                border: 1px solid #dddddd;
            }
        """)

class StyledButton(QPushButton):
    """Custom styled button with hover effects"""
    def __init__(self, text, button_type="primary", parent=None):
        super().__init__(text, parent)
        # CLAUDE CHANGE: Changed font to Segoe UI
        self.setFont(QFont("Segoe UI", 12))
        self.setCursor(Qt.PointingHandCursor)
        
        # Set minimum size for better touch targets
        self.setMinimumHeight(45)
        self.setMinimumWidth(120)
        
        # Set style based on button type
        if button_type == "primary":
            # CLAUDE CHANGE: Added 3D effect with border, gradient, and shadow
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
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #ecf0f1;
                    border-bottom: 3px solid #6d7b7c;
                }
            """)
        elif button_type == "success":
            # CLAUDE CHANGE: Added 3D effect with border, gradient, and shadow
            self.setStyleSheet("""
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #40d47e, stop:1 #2ecc71);
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
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #ecf0f1;
                    border-bottom: 3px solid #6d7b7c;
                }
            """)
        elif button_type == "danger":
            # CLAUDE CHANGE: Added 3D effect with border, gradient, and shadow
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
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #ecf0f1;
                    border-bottom: 3px solid #6d7b7c;
                }
            """)
        elif button_type == "secondary":
            # CLAUDE CHANGE: Added 3D effect with border, gradient, and shadow
            self.setStyleSheet("""
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #f5f5f5, stop:1 #ecf0f1);
                    color: #2c3e50;
                    border: 1px solid #bdc3c7;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    border-bottom: 3px solid #95a5a6;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #ecf0f1, stop:1 #bdc3c7);
                }
                QPushButton:pressed {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                      stop:0 #bdc3c7, stop:1 #a1a6a9);
                    border-bottom: 1px solid #95a5a6;
                    padding-top: 12px;
                }
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #ecf0f1;
                    border-bottom: 3px solid #6d7b7c;
                }
            """)

class WarningBox(QFrame):
    """A styled warning box with icon"""
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        # CLAUDE CHANGE: Enhanced styling for better contrast against grey background
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
        # CLAUDE CHANGE: Changed font to Segoe UI
        icon_label.setFont(QFont("Segoe UI", 24))
        icon_label.setStyleSheet("background-color: transparent;")
        
        # Warning message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        # CLAUDE CHANGE: Changed font to Segoe UI
        message_label.setFont(QFont("Segoe UI", 12))
        message_label.setStyleSheet("color: #856404; background-color: transparent;")
        
        layout.addWidget(icon_label)
        layout.addWidget(message_label, 1)  # 1 is the stretch factor

class StyledCheckBox(QCheckBox):
    """A styled checkbox with custom styling"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        # CLAUDE CHANGE: Changed font to Segoe UI
        self.setFont(QFont("Segoe UI", 12))
        # CLAUDE CHANGE: Enhanced checkbox styling
        self.setStyleSheet("""
            QCheckBox {
                spacing: 10px;
                color: #2c3e50;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #7f8c8d;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #3498db;
            }
            QCheckBox::indicator:unchecked {
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #3498db;
                border: 2px solid #3498db;
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
        header = QLabel("Ready to Install Updates")
        header.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; background-color: transparent;")
        
        # CLAUDE CHANGE: Added subtitle for better user experience
        # description = QLabel(
        #     "All updates have been downloaded successfully. "
        #     "Your vehicle is now ready to install the new software. "
        #     "Would you like to install the updates now?"
        # )
        # description.setAlignment(Qt.AlignCenter)
        # description.setWordWrap(True)
        # # CLAUDE CHANGE: Changed font to Segoe UI
        # description.setFont(QFont("Segoe UI", 14))
        # description.setStyleSheet("color: #34495e; margin-bottom: 20px; background-color: transparent;")
        
        # Warning box
        warning_box = WarningBox(
            "IMPORTANT: During the update installation, your vehicle must remain turned on with the engine running. "
            "Do not attempt to drive or turn off the vehicle until the installation is complete."
        )
        
        # Duration information
        # duration_label = QLabel("This process will take approximately 5-10 minutes to complete.")
        # duration_label.setAlignment(Qt.AlignCenter)
        # # CLAUDE CHANGE: Changed font to Segoe UI
        # duration_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        # duration_label.setStyleSheet("color: #2c3e50; margin: 10px 0; background-color: transparent;")
        
        # Consent checkbox
        self.consent_checkbox = StyledCheckBox(
            "I understand that I must keep the vehicle turned on during the update process."
        )
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.later_button = StyledButton("Install Later", "secondary")
        self.flash_button = StyledButton("Install Now", "success")
        self.flash_button.setEnabled(False)  # Disabled until checkbox is checked
        
        # Add buttons to layout
        button_layout.addStretch()
        button_layout.addWidget(self.later_button)
        button_layout.addWidget(self.flash_button)
        
        # CLAUDE CHANGE: Add all components to panel layout
        panel_layout.addWidget(header)
        # panel_layout.addWidget(description)
        panel_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum))
        panel_layout.addWidget(warning_box)
        # panel_layout.addWidget(duration_label)
        panel_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        panel_layout.addWidget(self.consent_checkbox)
        panel_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Minimum))
        panel_layout.addLayout(button_layout)
        
        # CLAUDE CHANGE: Add the content panel to the main layout
        self.content_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.content_panel)
        
        # CLAUDE CHANGE: Set overall dark background for main widget
        self.setStyleSheet("""
            QWidget#FlashConsentScreen {
                background-color: #2c3e50;
            }
        """)
        # Set object name for the style to work
        self.setObjectName("FlashConsentScreen")
        
        # Connect signals
        self.consent_checkbox.stateChanged.connect(self.update_button_state)
        self.flash_button.clicked.connect(self.flash_approved.emit)
        self.later_button.clicked.connect(self.flash_postponed.emit)
    
    def update_button_state(self, state):
        """Enable or disable the flash button based on checkbox state"""
        self.flash_button.setEnabled(state == Qt.Checked)
        
    def resizeEvent(self, event):
        """Handle resize events to keep the content panel full size"""
        super().resizeEvent(event)
        # Force the content panel to update its geometry
        if hasattr(self, 'content_panel'):
            self.content_panel.setGeometry(10, 10, self.width() - 20, self.height() - 20)

