from PyQt5.QtWidgets import QPushButton
from .live_log_page import LiveLogPage
import os


class GlobalLogPage(LiveLogPage):
    def __init__(self, log_file="logs/uds/success.log", parent=None, update_interval=1000):
        title = "Global Log for All Servers"
        placeholder_text = "Global logs will appear here..."
        super().__init__(title, log_file, placeholder_text, parent, update_interval)

        # Add Clear Log button
        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(self.clear_log)
        self.layout().addWidget(self.clear_button)

    def clear_log(self):
        """
        Clear the displayed log in the GUI (without modifying the file)
        and update the last_cleared_position.
        """
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                f.seek(0, os.SEEK_END)  # Move to the end of the file
                self.last_cleared_position = f.tell()  # Save the current file position
                self.save_last_cleared_position()       # Persist the marker
        self.log_text.clear()
