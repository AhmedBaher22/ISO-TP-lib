"""
Completion Screen for the ECU Update System.
Shows a success message after all ECUs have been updated.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSpacerItem, QSizePolicy, QFrame,
                            QApplication, QStyleFactory)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush

class SuccessIcon(QWidget):
    """A custom widget that draws an animated success checkmark"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setMaximumSize(150, 150)
        self.animation_progress = 0.0
        
        # Create animation
        self.animation = QPropertyAnimation(self, b"progress")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Auto-start animation when widget is shown
        self.shown = False
    
    def get_progress(self):
        return self.animation_progress
    
    def set_progress(self, value):
        self.animation_progress = value
        self.update()
    
    progress = pyqtSignal(float)
    progress = property(get_progress, set_progress)
    
    def showEvent(self, event):
        """Start animation when widget is shown"""
        if not self.shown:
            QTimer.singleShot(200, self.animation.start)
            self.shown = True
        super().showEvent(event)
    
    def paintEvent(self, event):
        """Paint the success checkmark"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate sizes
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 10
        
        # Draw circle
        circle_pen = QPen(QColor("#2ecc71"), 5)
        painter.setPen(circle_pen)
        
        # Draw partial circle based on animation progress
        if self.animation_progress > 0:
            span_angle = int(min(self.animation_progress * 1.2, 1.0) * 360 * 16)  # In 1/16th of a degree
            start_angle = 90 * 16  # Start at top (90 degrees in Qt's system)
            
            # Convert to integers as required by drawArc
            x = int(center_x - radius)
            y = int(center_y - radius)
            w = int(radius * 2)
            h = int(radius * 2)
            
            painter.drawArc(x, y, w, h, start_angle, span_angle)
        
        # Draw checkmark
        if self.animation_progress > 0.5:
            check_progress = min((self.animation_progress - 0.5) * 2, 1.0)
            
            painter.setPen(QPen(QColor("#2ecc71"), 8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            
            # Calculate checkmark points
            left_point = (center_x - radius/2, center_y)
            middle_point = (center_x - radius/5, center_y + radius/2)
            right_point = (center_x + radius/2, center_y - radius/3)
            
            # Draw first line of checkmark
            if check_progress < 0.5:
                # Scale for first half of check animation
                scaled_progress = check_progress * 2
                end_x = left_point[0] + (middle_point[0] - left_point[0]) * scaled_progress
                end_y = left_point[1] + (middle_point[1] - left_point[1]) * scaled_progress
                
                # Convert to integers for the line drawing
                painter.drawLine(
                    int(left_point[0]), int(left_point[1]), 
                    int(end_x), int(end_y)
                )
            else:
                # First line complete
                painter.drawLine(
                    int(left_point[0]), int(left_point[1]), 
                    int(middle_point[0]), int(middle_point[1])
                )
                
                # Second line based on remaining progress
                scaled_progress = (check_progress - 0.5) * 2
                end_x = middle_point[0] + (right_point[0] - middle_point[0]) * scaled_progress
                end_y = middle_point[1] + (right_point[1] - middle_point[1]) * scaled_progress
                
                # Convert to integers for the line drawing
                painter.drawLine(
                    int(middle_point[0]), int(middle_point[1]), 
                    int(end_x), int(end_y)
                )

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

class CompletionScreen(QWidget):
    """Screen to show completion of the update process"""
    
    # Define custom signals
    done_clicked = pyqtSignal()
    
    def __init__(self, signal_handler=None):
        super().__init__()
        self.signal_handler = signal_handler
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Success icon
        self.success_icon = SuccessIcon()
        
        # Header
        header = QLabel("Updates Installed Successfully")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50;")
        
        # Message
        message = QLabel(
            "All Electronic Control Units have been updated to the latest version. "
            "Your vehicle software is now up to date with the latest improvements and fixes."
        )
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setFont(QFont("Arial", 14))
        message.setStyleSheet("color: #34495e; margin-bottom: 20px;")
        
        # Details Frame
        details_frame = QFrame()
        details_frame.setFrameShape(QFrame.StyledPanel)
        details_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border: 1px solid #c8e6c9;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        details_layout = QVBoxLayout(details_frame)
        
        details_header = QLabel("Update Summary")
        details_header.setFont(QFont("Arial", 14, QFont.Bold))
        details_header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        
        self.details_content = QLabel(
            "• All ECUs have been successfully updated\n"
            "• Your vehicle has the latest security patches\n"
            "• New features are now available\n"
            "• Performance and stability improvements applied"
        )
        self.details_content.setFont(QFont("Arial", 12))
        self.details_content.setStyleSheet("color: #2c3e50;")
        
        details_layout.addWidget(details_header)
        details_layout.addWidget(self.details_content)
        
        # Done button
        self.done_button = StyledButton("Done", "success")
        
        # Add all components to main layout with proper spacing
        layout.addWidget(self.success_icon, 0, Qt.AlignCenter)
        layout.addWidget(header)
        layout.addWidget(message)
        layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum))
        layout.addWidget(details_frame)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(self.done_button, 0, Qt.AlignCenter)
        
        self.setLayout(layout)
        
        # Connect signals
        self.done_button.clicked.connect(self.done_clicked.emit)
    
    def set_update_details(self, details):
        """Set detailed information about the updates"""
        if isinstance(details, list):
            # Format as bullet points
            details_text = "\n".join([f"• {detail}" for detail in details])
            self.details_content.setText(details_text)
        else:
            self.details_content.setText(details)
