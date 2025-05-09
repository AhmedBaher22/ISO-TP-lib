"""
Download Screen for the ECU Update System.
Shows download progress with a visual progress bar.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QProgressBar, QSpacerItem, QSizePolicy,
                            QFrame, QApplication, QStyleFactory)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap

class CircularProgressBar(QWidget):
    """A circular progress bar for visual feedback"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setMaximumSize(150, 150)
        self.value = 0
        self.max_value = 100
        
    def set_value(self, value):
        """Set the current progress value"""
        self.value = value
        self.update()  # Trigger a repaint
        
    def paintEvent(self, event):
        """Paint the circular progress bar"""
        from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath
        from PyQt5.QtCore import QRectF, Qt
        import math
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate sizes
        width = self.width()
        height = self.height()
        margin = 10
        line_width = 10
        
        # Draw background circle
        painter.setPen(QPen(QColor("#e0e0e0"), line_width))
        painter.drawEllipse(margin, margin, width - 2*margin, height - 2*margin)
        
        # Draw progress arc
        if self.value > 0:
            pen = QPen(QColor("#3498db"), line_width)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            
            # Calculate the angle span
            span_angle = int(-360 * (self.value / self.max_value) * 16)  # In 1/16th of a degree
            
            painter.drawArc(
                margin, margin, 
                width - 2*margin, height - 2*margin, 
                90 * 16, span_angle
            )
        
        # Draw text in center
        painter.setPen(QColor("#2c3e50"))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        
        percent_text = f"{int(self.value)}%"
        text_rect = QRectF(0, 0, width, height)
        painter.drawText(text_rect, Qt.AlignCenter, percent_text)

class StyledProgressBar(QProgressBar):
    """An enhanced progress bar with better styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setMinimumHeight(12)
        self.setMaximumHeight(12)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #ecf0f1;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 6px;
            }
        """)

class InfoCard(QFrame):
    """A card widget to display download information"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50; padding-bottom: 5px; border-bottom: 1px solid #ecf0f1;")
        
        # Content widget (will be set externally)
        self.content_widget = QLabel()
        self.content_widget.setFont(QFont("Arial", 12))
        self.content_widget.setStyleSheet("color: #34495e; margin-top: 10px;")
        self.content_widget.setWordWrap(True)
        
        layout.addWidget(title_label)
        layout.addWidget(self.content_widget)
        
    def set_content(self, content):
        """Set the content text"""
        self.content_widget.setText(content)

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

class DownloadScreen(QWidget):
    """Screen to show download progress"""
    
    # Define custom signals
    download_cancelled = pyqtSignal()
    
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
        header = QLabel("Downloading Updates")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50;")
        
        # Description
        description = QLabel("Please wait while updates are being downloaded.")
        description.setAlignment(Qt.AlignCenter)
        description.setFont(QFont("Arial", 14))
        description.setStyleSheet("color: #34495e; margin-bottom: 20px;")
        
        # Progress visualization section
        progress_layout = QHBoxLayout()
        
        # Circular progress indicator
        self.circular_progress = CircularProgressBar()
        
        # Vertical progress information
        progress_info_layout = QVBoxLayout()
        
        self.progress_label = QLabel("0%")
        self.progress_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.progress_label.setStyleSheet("color: #2c3e50;")
        
        self.progress_bar = StyledProgressBar()
        
        self.details_label = QLabel("Starting download...")
        self.details_label.setFont(QFont("Arial", 12))
        self.details_label.setWordWrap(True)
        
        progress_info_layout.addWidget(self.progress_label)
        progress_info_layout.addWidget(self.progress_bar)
        progress_info_layout.addWidget(self.details_label)
        
        progress_layout.addWidget(self.circular_progress, alignment=Qt.AlignCenter)
        progress_layout.addLayout(progress_info_layout)
        
        # Information cards section
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        # ECUs card
        self.ecus_card = InfoCard("ECUs Being Updated")
        self.ecus_card.set_content("Preparing...")
        
        # Size card
        self.size_card = InfoCard("Download Size")
        self.size_card.set_content("Calculating...")
        
        # Estimated time card
        self.time_card = InfoCard("Estimated Time")
        self.time_card.set_content("Calculating...")
        
        cards_layout.addWidget(self.ecus_card)
        cards_layout.addWidget(self.size_card)
        cards_layout.addWidget(self.time_card)
        
        # Cancel button
        self.cancel_button = StyledButton("Cancel", "danger")
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(description)
        layout.addLayout(progress_layout)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addLayout(cards_layout)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(self.cancel_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.download_progress.connect(self.update_progress)
        self.cancel_button.clicked.connect(self.download_cancelled.emit)
    
    def update_progress(self, downloaded_size, total_size):
        """Update the progress indicators with current download status"""
        if total_size > 0:
            percent = int((downloaded_size / total_size) * 100)
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f"{percent}%")
            self.circular_progress.set_value(percent)
            
            # Update details
            self.details_label.setText(
                f"Downloaded {self.format_size(downloaded_size)} of {self.format_size(total_size)}"
            )
            
            # Update size card
            self.size_card.set_content(f"{self.format_size(downloaded_size)} / {self.format_size(total_size)}")
            
            # Update estimated time (simple calculation)
            if downloaded_size > 0:
                import time
                current_time = time.time()
                # Calculate rate and estimated time remaining
                if hasattr(self, 'last_update_time') and hasattr(self, 'last_downloaded_size'):
                    time_diff = current_time - self.last_update_time
                    size_diff = downloaded_size - self.last_downloaded_size
                    
                    if time_diff > 0 and size_diff > 0:
                        download_rate = size_diff / time_diff  # bytes per second
                        remaining_size = total_size - downloaded_size
                        remaining_time = remaining_size / download_rate if download_rate > 0 else 0
                        
                        if remaining_time < 60:
                            time_str = f"About {int(remaining_time)} seconds"
                        elif remaining_time < 3600:
                            time_str = f"About {int(remaining_time / 60)} minutes"
                        else:
                            time_str = f"About {int(remaining_time / 3600)} hours {int((remaining_time % 3600) / 60)} minutes"
                        
                        self.time_card.set_content(time_str)
                
                # Store current values for next calculation
                self.last_update_time = time.time()
                self.last_downloaded_size = downloaded_size
                
    def set_ecu_info(self, ecu_names):
        """Set information about the ECUs being updated"""
        if ecu_names:
            ecu_text = "\n".join([f"• {name}" for name in ecu_names])
            self.ecus_card.set_content(ecu_text)
    
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
    import time
    
    class DummySignalHandler:
        def __init__(self):
            self.download_progress = pyqtSignal(int, int)
        
        def connect(self, slot):
            self.slot = slot
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    dummy_handler = DummySignalHandler()
    screen = DownloadScreen(dummy_handler)
    screen.show()
    
    # Set ECU info
    screen.set_ecu_info(["Engine Control Module", "Brake Control Module", "Airbag Control Unit"])
    
    # Simulate download progress
    def simulate_progress():
        total_size = 50 * 1024 * 1024  # 50 MB
        for progress in range(0, 101, 5):
            downloaded_size = int(total_size * (progress / 100))
            dummy_handler.slot(downloaded_size, total_size)
            time.sleep(0.5)
    
    # Start progress simulation in a separate thread
    import threading
    threading.Thread(target=simulate_progress).start()
    
    sys.exit(app.exec_())