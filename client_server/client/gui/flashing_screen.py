"""
Flashing Screen for the ECU Update System.
Shows flashing progress and warns user not to turn off the vehicle.
"""

import sys
import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar, QSpacerItem, QSizePolicy, QFrame,
                           QApplication, QStyleFactory)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath

class PulsatingWarningLabel(QLabel):
    """A warning label with attention-grabbing pulsating effect"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Arial", 14, QFont.Bold))
        self.setStyleSheet("color: #e74c3c; background-color: transparent;")
        
        # Setup animation
        self.animation = QPropertyAnimation(self, b"pulse")
        self.animation.setDuration(1500)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setLoopCount(-1)  # Infinite
        self.animation.setEasingCurve(QEasingCurve.SineCurve)
        self.animation.start()
        
        self._pulse = 0.0
    
    def get_pulse(self):
        return self._pulse
    
    def set_pulse(self, value):
        self._pulse = value
        
        # Calculate color based on pulse value
        intensity = int(200 + 55 * math.sin(value * math.pi))
        self.setStyleSheet(f"color: rgb(231, {intensity}, {intensity}); background-color: transparent;")
        
        # Update the widget
        self.update()
    
    pulse = pyqtSignal(float)
    pulse = property(get_pulse, set_pulse)

class ECUProgressWidget(QWidget):
    """Widget showing the progress of individual ECU flashing"""
    def __init__(self, ecu_name, parent=None):
        super().__init__(parent)
        self.ecu_name = ecu_name
        self.status = "Waiting"  # "Waiting", "In Progress", "Completed", "Failed"
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # ECU name label
        self.name_label = QLabel(self.ecu_name)
        self.name_label.setFont(QFont("Arial", 12))
        self.name_label.setMinimumWidth(200)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #ecf0f1;
                text-align: center;
                height: 12px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        
        # Status label
        self.status_label = QLabel(self.status)
        self.status_label.setFont(QFont("Arial", 11))
        self.status_label.setMinimumWidth(100)
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.update_status(self.status)
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.progress_bar, 1)  # 1 is the stretch factor
        layout.addWidget(self.status_label)
    
    def update_progress(self, value):
        """Update the progress bar value"""
        self.progress_bar.setValue(value)
    
    def update_status(self, status):
        """Update the status of this ECU"""
        self.status = status
        self.status_label.setText(status)
        
        # Update styling based on status
        if status == "Waiting":
            self.status_label.setStyleSheet("color: #7f8c8d;")
        elif status == "In Progress":
            self.status_label.setStyleSheet("color: #3498db;")
            # Apply a pulsating effect to the progress bar
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 4px;
                    background-color: #ecf0f1;
                    text-align: center;
                    height: 12px;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                    border-radius: 4px;
                }
            """)
        elif status == "Completed":
            self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
            self.progress_bar.setValue(100)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 4px;
                    background-color: #ecf0f1;
                    text-align: center;
                    height: 12px;
                }
                QProgressBar::chunk {
                    background-color: #2ecc71;
                    border-radius: 4px;
                }
            """)
        elif status == "Failed":
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 4px;
                    background-color: #ecf0f1;
                    text-align: center;
                    height: 12px;
                }
                QProgressBar::chunk {
                    background-color: #e74c3c;
                    border-radius: 4px;
                }
            """)

class StepProgressIndicator(QWidget):
    """A progress indicator showing multiple steps"""
    def __init__(self, steps=None, parent=None):
        super().__init__(parent)
        self.steps = steps or ["Preparing", "Erasing", "Writing", "Verifying", "Finalizing"]
        self.current_step = -1  # No step active initially
        self.setMinimumHeight(80)
        
    def set_current_step(self, step_index):
        """Set the current active step"""
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            self.update()
    
    def paintEvent(self, event):
        """Paint the step indicator"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Calculate step width
        step_width = width / len(self.steps)
        
        # Draw the steps
        for i, step_text in enumerate(self.steps):
            x = i * step_width
            
            # Determine colors based on step status
            if i < self.current_step:
                # Completed step
                circle_color = QColor("#2ecc71")
                text_color = QColor("#27ae60")
            elif i == self.current_step:
                # Current step
                circle_color = QColor("#3498db")
                text_color = QColor("#2980b9")
            else:
                # Future step
                circle_color = QColor("#bdc3c7")
                text_color = QColor("#7f8c8d")
            
            # Draw circle
            circle_x = x + step_width / 2
            circle_y = 20
            circle_radius = 10
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(circle_color))
            
            # Convert to integers for the ellipse
            ellipse_x = int(circle_x - circle_radius)
            ellipse_y = int(circle_y - circle_radius)
            ellipse_width = int(circle_radius * 2)
            ellipse_height = int(circle_radius * 2)
            
            painter.drawEllipse(
                ellipse_x, ellipse_y,
                ellipse_width, ellipse_height
            )
            
            # Draw connecting line (if not last step)
            if i < len(self.steps) - 1:
                line_pen = QPen(QColor("#bdc3c7"), 2)
                painter.setPen(line_pen)
                
                # Convert to integers for the line
                x1 = int(circle_x + circle_radius)
                y1 = int(circle_y)
                x2 = int(circle_x + step_width - circle_radius)
                y2 = int(circle_y)
                
                painter.drawLine(x1, y1, x2, y2)
            
            # Draw step text
            text_rect = QRectF(x, circle_y + circle_radius + 5, step_width, 30)
            painter.setPen(text_color)
            painter.setFont(QFont("Arial", 9))
            painter.drawText(text_rect, Qt.AlignCenter, step_text)

class TotalProgressBar(QProgressBar):
    """An enhanced progress bar with better styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setMinimumHeight(20)
        self.setFormat("%p%")
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #ecf0f1;
                text-align: center;
                color: #2c3e50;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 10px;
            }
        """)

class FlashingScreen(QWidget):
    """Screen to show flashing progress"""
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        self.current_ecu_index = 0
        self.ecu_widgets = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("Installing Updates")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setStyleSheet("color: #2c3e50;")
        
        # Warning message at the top
        self.warning_label = PulsatingWarningLabel("DO NOT TURN OFF THE VEHICLE")
        
        # Step progress indicator
        self.step_indicator = StepProgressIndicator()
        
        # Current ECU frame
        current_ecu_frame = QFrame()
        current_ecu_frame.setFrameShape(QFrame.StyledPanel)
        current_ecu_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        current_ecu_layout = QVBoxLayout(current_ecu_frame)
        
        self.current_ecu_label = QLabel("Preparing...")
        self.current_ecu_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.current_ecu_label.setStyleSheet("color: #2c3e50;")
        
        self.current_ecu_status = QLabel("Initializing update process")
        self.current_ecu_status.setFont(QFont("Arial", 12))
        
        current_ecu_layout.addWidget(self.current_ecu_label)
        current_ecu_layout.addWidget(self.current_ecu_status)
        
        # Total progress bar
        progress_layout = QVBoxLayout()
        
        progress_header = QLabel("Overall Progress")
        progress_header.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.total_progress_bar = TotalProgressBar()
        
        progress_layout.addWidget(progress_header)
        progress_layout.addWidget(self.total_progress_bar)
        
        # ECU list container
        ecu_list_container = QFrame()
        ecu_list_container.setFrameShape(QFrame.StyledPanel)
        ecu_list_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        
        self.ecu_list_layout = QVBoxLayout(ecu_list_container)
        self.ecu_list_layout.setContentsMargins(10, 10, 10, 10)
        self.ecu_list_layout.setSpacing(10)
        
        # Add all components to main layout
        layout.addWidget(header)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.step_indicator)
        layout.addWidget(current_ecu_frame)
        layout.addLayout(progress_layout)
        layout.addWidget(ecu_list_container, 1)  # 1 is the stretch factor
        
        self.setLayout(layout)
        
        # Connect signals
        self.signal_handler.flash_progress.connect(self.update_flash_progress)
    
    def set_ecu_list(self, ecu_names):
        """Initialize the list of ECUs to be flashed"""
        # Clear existing widgets
        for i in reversed(range(self.ecu_list_layout.count())): 
            widget = self.ecu_list_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
        self.ecu_widgets = []
        
        # Add new ECU widgets
        for ecu_name in ecu_names:
            ecu_widget = ECUProgressWidget(ecu_name)
            self.ecu_list_layout.addWidget(ecu_widget)
            self.ecu_widgets.append(ecu_widget)
        
        # Reset current ECU index
        self.current_ecu_index = 0
        self.total_progress_bar.setValue(0)
        
        # Start with the first ECU if available
        if self.ecu_widgets:
            self.set_current_ecu(0)
    
    def set_current_ecu(self, index):
        """Set the currently active ECU"""
        if 0 <= index < len(self.ecu_widgets):
            # Update previous ECU status if applicable
            if self.current_ecu_index < len(self.ecu_widgets) and self.current_ecu_index != index:
                self.ecu_widgets[self.current_ecu_index].update_status("Completed")
            
            # Update current ECU
            self.current_ecu_index = index
            self.ecu_widgets[index].update_status("In Progress")
            self.current_ecu_label.setText(f"Updating: {self.ecu_widgets[index].ecu_name}")
            
            # Reset step indicator
            self.step_indicator.set_current_step(0)
    
    def update_flash_progress(self, completed_ecus, total_ecus):
        """Update the flashing progress indicators"""
        if total_ecus <= 0:
            return
            
        # Calculate overall progress percentage
        overall_progress = int((completed_ecus / total_ecus) * 100)
        self.total_progress_bar.setValue(overall_progress)
        
        # Update current ECU if needed
        current_ecu_index = min(completed_ecus, len(self.ecu_widgets) - 1)
        
        # If we've moved to a new ECU
        if current_ecu_index > self.current_ecu_index:
            # Mark previous ECUs as completed
            for i in range(self.current_ecu_index, current_ecu_index):
                if i < len(self.ecu_widgets):
                    self.ecu_widgets[i].update_status("Completed")
                    self.ecu_widgets[i].update_progress(100)
            
            # Set new current ECU
            self.set_current_ecu(current_ecu_index)
        
        # Update step for current ECU (simulate progress through steps)
        if completed_ecus < total_ecus:  # Still in progress
            # Calculate which step we're in for the current ECU (simplified)
            current_ecu_progress = int((completed_ecus - current_ecu_index) * 100)
            if current_ecu_progress < 20:
                step = 0  # Preparing
                self.current_ecu_status.setText("Preparing ECU for update...")
            elif current_ecu_progress < 40:
                step = 1  # Erasing
                self.current_ecu_status.setText("Erasing old firmware...")
            elif current_ecu_progress < 70:
                step = 2  # Writing
                self.current_ecu_status.setText("Writing new firmware...")
            elif current_ecu_progress < 90:
                step = 3  # Verifying
                self.current_ecu_status.setText("Verifying installation...")
            else:
                step = 4  # Finalizing
                self.current_ecu_status.setText("Finalizing installation...")
            
            self.step_indicator.set_current_step(step)
            
            # Update progress of current ECU
            self.ecu_widgets[current_ecu_index].update_progress(min(current_ecu_progress, 99))
        else:
            # All ECUs completed
            for widget in self.ecu_widgets:
                widget.update_status("Completed")
                widget.update_progress(100)
            
            self.current_ecu_label.setText("All updates completed!")
            self.current_ecu_status.setText("Your vehicle is now up to date.")
            self.step_indicator.set_current_step(4)  # Final step

# For testing the screen individually
if __name__ == "__main__":
    import time
    import threading
    
    class DummySignalHandler:
        def __init__(self):
            self.flash_progress = pyqtSignal(int, int)
        
        def connect(self, slot):
            self.slot = slot
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    dummy_handler = DummySignalHandler()
    screen = FlashingScreen(dummy_handler)
    
    # Set some sample ECUs
    ecu_names = [
        "Engine Control Module", 
        "Brake Control Module", 
        "Airbag Control Unit",
        "Transmission Control Unit",
        "Body Control Module"
    ]
    screen.set_ecu_list(ecu_names)
    
    screen.show()
    
    # Simulate flashing progress
    def simulate_progress():
        total_ecus = len(ecu_names)
        for progress in range(total_ecus + 1):
            dummy_handler.slot(progress, total_ecus)
            time.sleep(2)  # Slower to see the transitions
    
    # Start progress simulation in a separate thread
    threading.Thread(target=simulate_progress).start()
    
    sys.exit(app.exec_())