"""
Completion Screen for the ECU Update System.
Shows a success message after all ECUs have been updated.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                            QPushButton, QSpacerItem, QSizePolicy, QFrame, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient

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

class SuccessIcon(QWidget):
    """A custom widget that draws an animated success checkmark"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # CLAUDE CHANGE: Made icon larger
        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)
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
        # CLAUDE CHANGE: Increased line width for better visibility
        circle_pen = QPen(QColor("#2ecc71"), 8)
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
            
            # CLAUDE CHANGE: Increased line width for better visibility
            painter.setPen(QPen(QColor("#2ecc71"), 12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            
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
        # Create main layout with minimal margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        
        # Create the content panel to contain all widgets
        self.content_panel = ContentPanel()
        
        # Create panel layout
        panel_layout = QVBoxLayout(self.content_panel)
        panel_layout.setContentsMargins(30, 30, 30, 30)
        # CLAUDE CHANGE: Reduced overall spacing between elements
        panel_layout.setSpacing(10)
        
        # Create a container for the header with minimal margins
        header_container = QWidget()
        header_container.setStyleSheet("background-color: transparent;")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("Updated Successfully")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50; background-color: transparent;")
        
        # Add header to its container
        header_layout.addWidget(header)
        
        # Add a divider line below the header
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: rgba(189, 195, 199, 0.5); margin: 0 100px 10px 100px;")
        divider.setMaximumHeight(1)
        
        # CLAUDE CHANGE: Made success icon optional or smaller
        # Success icon - comment out to remove or use a smaller size
        self.success_icon = SuccessIcon()
        # CLAUDE CHANGE: Reduced size of success icon (optional)
        self.success_icon.setMinimumSize(150, 150)
        self.success_icon.setMaximumSize(150, 150)
        
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
        # CLAUDE CHANGE: Reduced internal spacing in details frame
        details_layout.setSpacing(5)
        
        details_header = QLabel("Update Summary")
        details_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        details_header.setStyleSheet("color: #2c3e50; margin-bottom: 5px; background-color: transparent;")
        
        self.details_content = QLabel(
            "• All ECUs have been successfully updated\n"
            "• Your vehicle has the latest security patches\n"
            "• New features are now available\n"
            "• Performance and stability improvements applied"
        )
        self.details_content.setFont(QFont("Segoe UI", 12))
        self.details_content.setStyleSheet("color: #2c3e50; background-color: transparent;")
        
        details_layout.addWidget(details_header)
        details_layout.addWidget(self.details_content)
        
        # Done button
        self.done_button = StyledButton("Done", "success")
        
        # CLAUDE CHANGE: Use layout to position elements with less space between them
        panel_layout.addWidget(header_container)
        panel_layout.addWidget(divider)
        
        # CLAUDE CHANGE: Calculate available space and use a fixed portion for top and bottom spacing
        # This creates a more balanced layout with less empty space in the middle
        panel_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        panel_layout.addWidget(self.success_icon, 0, Qt.AlignCenter)
        # CLAUDE CHANGE: Minimal spacing between icon and details
        panel_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        panel_layout.addWidget(details_frame)
        # CLAUDE CHANGE: Minimal space after details frame
        panel_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        panel_layout.addWidget(self.done_button, 0, Qt.AlignCenter)
        panel_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Add the content panel to the main layout
        self.content_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.content_panel)
        
        # Set overall dark background for main widget
        self.setStyleSheet("""
            QWidget#CompletionScreen {
                background-color: #2c3e50;
            }
        """)
        # Set object name for the style to work
        self.setObjectName("CompletionScreen")
        
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
            
    def resizeEvent(self, event):
        """Handle resize events to keep the content panel full size"""
        super().resizeEvent(event)
        # Force the content panel to update its geometry
        if hasattr(self, 'content_panel'):
            self.content_panel.setGeometry(10, 10, self.width() - 20, self.height() - 20)
