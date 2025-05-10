"""
Download Screen for the ECU Update System.
Shows download progress with a visual progress bar.
"""

import sys
import time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                            QPushButton, QSpacerItem, QSizePolicy,
                            QFrame, QApplication, QStyleFactory)
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
                border-radius: 15px;
                border: 1px solid #dddddd;
            }
        """)

class CircularProgressBar(QWidget):
    """A circular progress bar for visual feedback"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # CLAUDE CHANGE: Increased size of the progress circle
        self.setMinimumSize(250, 250)
        self.setMaximumSize(250, 250)
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
        margin = 15
        # CLAUDE CHANGE: Increased line width for more prominence
        line_width = 15
        
        # Draw background circle
        painter.setPen(QPen(QColor("#e0e0e0"), line_width))
        painter.drawEllipse(margin, margin, width - 2*margin, height - 2*margin)
        
        # Draw progress arc
        if self.value > 0:
            # CLAUDE CHANGE: Improved color of the progress arc
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
        # CLAUDE CHANGE: Changed font to Segoe UI and increased size
        painter.setFont(QFont("Segoe UI", 32, QFont.Bold))
        
        percent_text = f"{int(self.value)}%"
        text_rect = QRectF(0, 0, width, height)
        painter.drawText(text_rect, Qt.AlignCenter, percent_text)

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
        header = QLabel("Downloading Updates")
        header.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; background-color: transparent;")
        
        # CLAUDE CHANGE: Add subtitle
        subtitle = QLabel("Please wait while we download the latest software for your vehicle.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #34495e; background-color: transparent; margin-bottom: 20px;")
        
        # CLAUDE CHANGE: Simplified layout with just the circular progress in the center
        # Circular progress indicator - now centered
        self.circular_progress = CircularProgressBar()
        
        # CLAUDE CHANGE: Create a vertical layout for text below the circular progress
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)
        info_layout.setSpacing(10)
        
        # CLAUDE CHANGE: Progress percentage is already in the circle, but we'll add download info and estimated time
        self.details_label = QLabel("Starting download...")
        self.details_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI
        self.details_label.setFont(QFont("Segoe UI", 12))
        self.details_label.setStyleSheet("color: #34495e; background-color: transparent;")
        
        # CLAUDE CHANGE: Add estimated time label
        self.time_label = QLabel("Calculating time remaining...")
        self.time_label.setAlignment(Qt.AlignCenter)
        # CLAUDE CHANGE: Changed font to Segoe UI
        self.time_label.setFont(QFont("Segoe UI", 12))
        self.time_label.setStyleSheet("color: #34495e; background-color: transparent;")
        
        # Add labels to info layout
        info_layout.addWidget(self.details_label)
        info_layout.addWidget(self.time_label)
        
        # Cancel button
        self.cancel_button = StyledButton("Cancel", "danger")
        
        # CLAUDE CHANGE: Add all components to panel layout
        panel_layout.addWidget(header)
        panel_layout.addWidget(subtitle)
        panel_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))
        panel_layout.addWidget(self.circular_progress, alignment=Qt.AlignCenter)
        panel_layout.addLayout(info_layout)
        panel_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))
        panel_layout.addWidget(self.cancel_button, alignment=Qt.AlignCenter)
        
        # CLAUDE CHANGE: Add the content panel to the main layout
        self.content_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.content_panel)
        
        # CLAUDE CHANGE: Set overall dark background for main widget
        self.setStyleSheet("""
            QWidget#DownloadScreen {
                background-color: #2c3e50;
            }
        """)
        # Set object name for the style to work
        self.setObjectName("DownloadScreen")
        
        # Connect signals
        self.signal_handler.download_progress.connect(self.update_progress)
        self.cancel_button.clicked.connect(self.download_cancelled.emit)
    
    def update_progress(self, downloaded_size, total_size):
        """Update the progress indicators with current download status"""
        if total_size > 0:
            percent = int((downloaded_size / total_size) * 100)
            # CLAUDE CHANGE: Just update the circular progress and labels
            self.circular_progress.set_value(percent)
            
            # Update details
            self.details_label.setText(
                f"Downloaded {self.format_size(downloaded_size)} of {self.format_size(total_size)}"
            )
            
            # Update estimated time (simple calculation)
            if downloaded_size > 0:
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
                            time_str = f"About {int(remaining_time)} seconds remaining"
                        elif remaining_time < 3600:
                            time_str = f"About {int(remaining_time / 60)} minutes remaining"
                        else:
                            time_str = f"About {int(remaining_time / 3600)} hours {int((remaining_time % 3600) / 60)} minutes remaining"
                        
                        self.time_label.setText(time_str)
                
                # Store current values for next calculation
                self.last_update_time = time.time()
                self.last_downloaded_size = downloaded_size
                
    def set_ecu_info(self, ecu_names):
        """
        This method is kept for backwards compatibility but doesn't display anything now
        """
        pass
    
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
            
    def resizeEvent(self, event):
        """Handle resize events to keep the content panel full size"""
        super().resizeEvent(event)
        # Force the content panel to update its geometry
        if hasattr(self, 'content_panel'):
            self.content_panel.setGeometry(10, 10, self.width() - 20, self.height() - 20)

# For testing the screen individually
if __name__ == "__main__":
    import time
    
    class DummySignalHandler:
        def __init__(self):
            self.download_progress = None
        
        def connect(self, slot):
            self.slot = slot
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    dummy_handler = DummySignalHandler()
    screen = DownloadScreen(dummy_handler)
    screen.show()
    screen.showMaximized()  # Show maximized for better testing
    
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