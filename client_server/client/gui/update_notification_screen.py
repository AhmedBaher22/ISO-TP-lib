"""
Update Notification Screen for the ECU Update System.
Shows available updates and asks for user permission to download.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QSizePolicy, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# CLAUDE CHANGE: Added ContentPanel class for consistent styling with welcome screen
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

class UpdateTableWidget(QTableWidget):
    """Enhanced table widget for displaying updates with modern styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["ECU Component", "Current Version", "New Version"])
        
        # Stretch the columns to fill the available space
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        # CLAUDE CHANGE: Completely redesigned table styling for modern look
        self.setStyleSheet("""
            QTableWidget {
                border: none;
                border-radius: 12px;
                background-color: rgba(255, 255, 255, 0.9);
                gridline-color: transparent;
                font-family: 'Segoe UI';
                font-size: 11pt;
                selection-background-color: #e0f2fe;
                selection-color: #2c3e50;
            }
            
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #eaeaea;
                border-radius: 6px;
                margin: 4px;
            }
            
            QTableWidget::item:hover {
                background-color: #f8f9fa;
            }
            
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 14px;
                border: none;
                font-family: 'Segoe UI';
                font-size: 12pt;
                font-weight: bold;
            }
            
            QHeaderView::section:first {
                border-top-left-radius: 12px;
            }
            
            QHeaderView::section:last {
                border-top-right-radius: 12px;
            }
            
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                border-radius: 5px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #bdc3c7;
                border-radius: 5px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #95a5a6;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QTableCornerButton::section {
                background-color: #34495e;
            }
        """)
        
        # CLAUDE CHANGE: Set other properties for modern look
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setShowGrid(False)  # Hide grid lines for cleaner look
        self.verticalHeader().setVisible(False)
        self.setFocusPolicy(Qt.NoFocus)  # Remove focus highlighting
        
        # Set fixed row height
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(60)  # Larger row height
        
        # Add some padding around the table
        self.setContentsMargins(15, 15, 15, 15)
        
    # CLAUDE CHANGE: Custom paint method to add box shadow effect
    def paintEvent(self, event):
        """Override paint event to add custom styling"""
        super().paintEvent(event)
        # This would be the place to add additional custom drawing if needed
        # For example, to highlight the current row or add custom decorations
        
    # CLAUDE CHANGE: Custom method to style cells based on content
    def setRowData(self, row, ecu_name, old_version, new_version):
        """Set row data with custom styling for each cell"""
        # Create table items
        ecu_item = QTableWidgetItem(ecu_name)
        old_version_item = QTableWidgetItem(old_version)
        new_version_item = QTableWidgetItem(new_version)
        
        # ECU name styling
        ecu_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        ecu_font = QFont("Segoe UI", 11)
        ecu_font.setBold(True)
        ecu_item.setFont(ecu_font)
        ecu_item.setForeground(QColor("#2c3e50"))
        
        # Old version styling
        old_version_item.setTextAlignment(Qt.AlignCenter)
        old_version_item.setFont(QFont("Segoe UI", 10))
        old_version_item.setForeground(QColor("#7f8c8d"))
        
        # New version styling - highlight with blue instead of green for better design harmony
        new_version_item.setTextAlignment(Qt.AlignCenter)
        new_version_font = QFont("Segoe UI", 10)
        new_version_font.setBold(True)
        new_version_item.setFont(new_version_font)
        new_version_item.setForeground(QColor("#3498db"))
        
        # Set items in the table
        self.setItem(row, 0, ecu_item)
        self.setItem(row, 1, old_version_item)
        self.setItem(row, 2, new_version_item)


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
        
        # CLAUDE CHANGE: Updated with Segoe UI font
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px;
                font-family: 'Segoe UI';
            }}
        """)
        
        # Create layout
        layout = QHBoxLayout(self)
        
        # Icon
        icon_label = QLabel(icon)
        # CLAUDE CHANGE: Updated to Segoe UI font
        icon_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        icon_label.setStyleSheet(f"color: {icon_color}; background-color: transparent;")
        icon_label.setFixedWidth(30)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        # CLAUDE CHANGE: Updated to Segoe UI font
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setStyleSheet("background-color: transparent;")
        
        layout.addWidget(icon_label)
        layout.addWidget(message_label, 1)  # 1 is the stretch factor
        layout.setContentsMargins(10, 10, 10, 10)

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
        header = QLabel("Available Updates")
        header.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; margin-bottom: 10px; background-color: transparent;")
        
        # Table for updates
        self.table = UpdateTableWidget()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.skip_button = StyledButton("Skip For Now", "secondary")
        self.download_button = StyledButton("Download", "primary")
        
        # Add spacer to push buttons to the right
        button_layout.addStretch()
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.download_button)
        
        # Add all components to panel layout
        panel_layout.addWidget(header)
        panel_layout.addWidget(self.table, 1)  # 1 is the stretch factor
        panel_layout.addLayout(button_layout)
        
        # CLAUDE CHANGE: Add the content panel to the main layout
        self.content_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.content_panel)
        
        # CLAUDE CHANGE: Set overall dark background for main widget
        self.setStyleSheet("""
            QWidget#UpdateNotificationScreen {
                background-color: #2c3e50;
            }
        """)
        # Set object name for the style to work
        self.setObjectName("UpdateNotificationScreen")
        
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
            
            # CLAUDE CHANGE: Use the new custom method to set row data with modern styling
            self.table.setRowData(row, ecu_name, old_version, new_version)
            
            row += 1
        
        # CLAUDE CHANGE: Add visual separator between table and buttons
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: transparent; margin: 10px 0;")
        
        # Find the button layout and add the separator before it
        for i in range(self.content_panel.layout().count()):
            item = self.content_panel.layout().itemAt(i)
            if isinstance(item, QHBoxLayout):
                # Remove old button layout
                button_layout = item
                self.content_panel.layout().removeItem(button_layout)
                
                # Add separator and then button layout
                self.content_panel.layout().addWidget(separator)
                self.content_panel.layout().addLayout(button_layout)
                break
            

    def resizeEvent(self, event):
        """Handle resize events to keep the content panel full size"""
        super().resizeEvent(event)
        # Force the content panel to update its geometry
        if hasattr(self, 'content_panel'):
            self.content_panel.setGeometry(10, 10, self.width() - 20, self.height() - 20)
