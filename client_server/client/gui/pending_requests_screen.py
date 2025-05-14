"""
Pending Requests Screen for the ECU Update System.
Shows pending download or flashing requests and options to resume or cancel.
"""

import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSpacerItem, QSizePolicy, QFrame,
                            QApplication, QStyleFactory)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

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

class InfoRow(QWidget):
    """A row displaying a label and value"""
    def __init__(self, label, value="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Arial", 12))
        label_widget.setStyleSheet("color: #7f8c8d;")
        label_widget.setMinimumWidth(150)
        
        self.value_widget = QLabel(value)
        self.value_widget.setFont(QFont("Arial", 12, QFont.Bold))
        self.value_widget.setStyleSheet("color: #2c3e50;")
        self.value_widget.setWordWrap(True)
        
        layout.addWidget(label_widget)
        layout.addWidget(self.value_widget, 1)  # 1 is the stretch factor
    
    def set_value(self, value):
        """Set the value text"""
        self.value_widget.setText(value)

class ProgressIndicator(QWidget):
    """A visual progress indicator showing percentage complete"""
    def __init__(self, value=0, parent=None):
        super().__init__(parent)
        self.value = value
        self.setMinimumHeight(30)
        
    def set_value(self, value):
        """Set the progress value (0-100)"""
        self.value = max(0, min(100, value))
        self.update()
    
    def paintEvent(self, event):
        """Paint the progress indicator"""
        from PyQt5.QtGui import QPainter, QColor, QBrush, QPen
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Draw background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#ecf0f1")))
        painter.drawRoundedRect(0, 0, width, height, height/2, height/2)
        
        # Draw progress
        if self.value > 0:
            progress_width = int(width * (self.value / 100))
            painter.setBrush(QBrush(QColor("#3498db")))
            painter.drawRoundedRect(0, 0, progress_width, height, height/2, height/2)
        
        # Draw text
        painter.setPen(QPen(QColor("#2c3e50")))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(0, 0, width, height, Qt.AlignCenter, f"{self.value}%")

class PendingRequestsScreen(QWidget):
    """Screen to show pending download or flashing requests"""
    
    # Define custom signals
    resume_clicked = pyqtSignal()
    cancel_clicked = pyqtSignal()
    
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        self.is_download = False  # Flag to indicate if pending request is download or flash
        self.pending_request = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        self.header = QLabel("Pending Update Request")
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setFont(QFont("Arial", 24, QFont.Bold))
        self.header.setStyleSheet("color: #2c3e50;")
        
        # Description
        self.description = QLabel(
            "We found a pending update operation that was interrupted. "
            "Would you like to resume or cancel it?"
        )
        self.description.setAlignment(Qt.AlignCenter)
        self.description.setWordWrap(True)
        self.description.setFont(QFont("Arial", 14))
        self.description.setStyleSheet("color: #34495e;")
        
        # Request details card
        details_card = QFrame()
        details_card.setFrameShape(QFrame.StyledPanel)
        details_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        details_layout = QVBoxLayout(details_card)
        
        # Card title
        self.request_type_label = QLabel("Download Request")
        self.request_type_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.request_type_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        # Info rows
        self.date_row = InfoRow("Date:")
        self.ecus_row = InfoRow("ECUs:")
        self.size_row = InfoRow("Size:")
        
        # Progress
        progress_layout = QVBoxLayout()
        
        progress_label = QLabel("Progress:")
        progress_label.setFont(QFont("Arial", 12))
        progress_label.setStyleSheet("color: #7f8c8d; margin-top: 10px;")
        
        self.progress_indicator = ProgressIndicator()
        
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_indicator)
        
        # Add all rows to details layout
        details_layout.addWidget(self.request_type_label)
        details_layout.addWidget(self.date_row)
        details_layout.addWidget(self.ecus_row)
        details_layout.addWidget(self.size_row)
        details_layout.addLayout(progress_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.cancel_button = StyledButton("Cancel Request", "danger")
        self.resume_button = StyledButton("Resume", "success")
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.resume_button)
        
        # Add all components to main layout
        layout.addWidget(self.header)
        layout.addWidget(self.description)
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum))
        layout.addWidget(details_card)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.pending_download.connect(self.show_pending_download)
        self.signal_handler.pending_flash.connect(self.show_pending_flash)
        self.resume_button.clicked.connect(self.resume_clicked.emit)
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
    
    def show_pending_download(self, download_request):
        """Display pending download request details"""
        self.pending_request = download_request
        self.is_download = True
        
        # Update header and description
        self.header.setText("Resume Download")
        self.description.setText(
            "We found a partially downloaded update that was interrupted. "
            "Would you like to resume downloading or cancel it?"
        )
        
        # Update request type
        self.request_type_label.setText("Download Request")
        self.request_type_label.setStyleSheet("color: #3498db; margin-bottom: 10px;")
        
        # Format date
        if hasattr(download_request, 'timestamp'):
            date_str = download_request.timestamp.strftime("%Y-%m-%d %H:%M")
            self.date_row.set_value(date_str)
        
        # Set ECUs info
        if hasattr(download_request, 'required_updates'):
            ecu_names = list(download_request.required_updates.keys())
            ecu_text = ", ".join(ecu_names)
            self.ecus_row.set_value(ecu_text)
        
        # Set size info
        if hasattr(download_request, 'downloaded_size') and hasattr(download_request, 'total_size'):
            if download_request.total_size > 0:
                downloaded = self.format_size(download_request.downloaded_size)
                total = self.format_size(download_request.total_size)
                self.size_row.set_value(f"{downloaded} of {total}")
                
                # Set progress
                progress = int((download_request.downloaded_size / download_request.total_size) * 100)
                self.progress_indicator.set_value(progress)
        
        # Update button text
        self.resume_button.setText("Resume Download")
    
    def show_pending_flash(self, download_request):
        """Display pending flash request details"""
        self.pending_request = download_request
        self.is_download = False
        
        # Update header and description
        self.header.setText("Resume Installation")
        self.description.setText(
            "We found updates ready to be installed that were interrupted. "
            "Would you like to resume installation or cancel it?"
        )
        
        # Update request type
        self.request_type_label.setText("Installation Request")
        self.request_type_label.setStyleSheet("color: #2ecc71; margin-bottom: 10px;")
        
        # Format date
        if hasattr(download_request, 'timestamp'):
            date_str = download_request.timestamp.strftime("%Y-%m-%d %H:%M")
            self.date_row.set_value(date_str)
        
        # Set ECUs info
        if hasattr(download_request, 'downloaded_versions'):
            ecu_names = list(download_request.downloaded_versions.keys())
            ecu_text = ", ".join(ecu_names)
            self.ecus_row.set_value(ecu_text)
        elif hasattr(download_request, 'required_updates'):
            ecu_names = list(download_request.required_updates.keys())
            ecu_text = ", ".join(ecu_names)
            self.ecus_row.set_value(ecu_text)
        
        # Set size info (not relevant for flashing)
        self.size_row.set_value("Download Complete")
        
        # Set progress
        if hasattr(download_request, 'completed_ecus') and hasattr(download_request, 'total_ecus'):
            if download_request.total_ecus > 0:
                progress = int((download_request.completed_ecus / download_request.total_ecus) * 100)
                self.progress_indicator.set_value(progress)
        
        # Update button text
        self.resume_button.setText("Resume Installation")
    
    def format_size(self, size_bytes):
        """Format bytes into human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.1f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f} GB"

# For testing the screen individually
if __name__ == "__main__":
    class DummySignalHandler:
        def __init__(self):
            self.pending_download = pyqtSignal(object)
            self.pending_flash = pyqtSignal(object)
        
        def connect(self, slot):
            self.slot = slot
    
    class DummyDownloadRequest:
        def __init__(self):
            self.timestamp = datetime.now()
            self.required_updates = {
                "Engine Control Module": "1.3.0",
                "Brake Control Module": "2.0.0",
                "Airbag Control Unit": "2.1.2"
            }
            self.downloaded_size = 25 * 1024 * 1024  # 25 MB
            self.total_size = 50 * 1024 * 1024  # 50 MB
            self.status = "DOWNLOADING"
    
    class DummyFlashRequest:
        def __init__(self):
            self.timestamp = datetime.now()
            self.downloaded_versions = {
                "Engine Control Module": "1.3.0",
                "Brake Control Module": "2.0.0",
                "Airbag Control Unit": "2.1.2"
            }
            self.completed_ecus = 1
            self.total_ecus = 3
            self.status = "IN_FLASHING"
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    dummy_handler = DummySignalHandler()
    screen = PendingRequestsScreen(dummy_handler)
    
    # Simulate a pending download
    dummy_download = DummyDownloadRequest()
    screen.show_pending_download(dummy_download)
    
    # Uncomment to test flashing instead
    # dummy_flash = DummyFlashRequest()
    # screen.show_pending_flash(dummy_flash)
    
    screen.show()
    
    sys.exit(app.exec_())