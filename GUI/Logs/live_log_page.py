import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QStackedWidget, QTextEdit, QHBoxLayout, QComboBox
)
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor
from PyQt5.QtCore import QTimer, QFileSystemWatcher, Qt


class LiveLogPage(QWidget):
    def __init__(self, title: str, log_file: str, placeholder_text: str, parent=None, update_interval=1000):
        super().__init__(parent)
        self.log_file = log_file
        self.current_match_index = -1  # Track current match index
        self.match_positions = []      # Store all match positions
        self.full_log_content = []     # Will store all lines read from file

        layout = QVBoxLayout()
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # Row for search bar, navigation buttons, and filters.
        search_layout = QHBoxLayout()

        # Search bar for highlighting (e.g., showing matches)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search logs for highlighting...")
        self.search_bar.textChanged.connect(self.filter_logs)
        search_layout.addWidget(self.search_bar)

        # Navigation buttons for cycling through search matches.
        self.prev_button = QPushButton("◀")
        self.prev_button.clicked.connect(self.jump_to_previous_match)
        search_layout.addWidget(self.prev_button)

        self.match_label = QLabel("")  # Label to show "Match X/Y"
        search_layout.addWidget(self.match_label)

        self.next_button = QPushButton("▶")
        self.next_button.clicked.connect(self.jump_to_next_match)
        search_layout.addWidget(self.next_button)

        # Dropdown filter (e.g., to filter on predefined types)
        self.filter_dropdown = QComboBox()
        self.filter_dropdown.addItems(["All", "CAN", "ISO-TP", "UDS"])
        self.filter_dropdown.currentTextChanged.connect(self.filter_logs)
        search_layout.addWidget(self.filter_dropdown)

        # New custom filter field for filtering by any word.
        self.custom_filter_bar = QLineEdit()
        self.custom_filter_bar.setPlaceholderText(
            "Enter custom filter word...")
        self.custom_filter_bar.textChanged.connect(self.filter_logs)
        search_layout.addWidget(self.custom_filter_bar)

        layout.addLayout(search_layout)

        # Log display widget.
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText(placeholder_text)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

        # File watcher for live updates
        self.watcher = QFileSystemWatcher(self)
        if os.path.exists(self.log_file):
            self.watcher.addPath(self.log_file)
        self.watcher.fileChanged.connect(self.update_log)

        # Timer to periodically check for file changes
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_file_existence)
        self.timer.start(update_interval)

        # Initial update
        self.update_log()

    def update_log(self, path=None):
        """Reads the log file and updates the text widget, then applies filtering."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    self.full_log_content = f.readlines()  # Store full log content
                self.filter_logs()  # Apply filtering with both dropdown and custom filter
            except Exception as e:
                self.log_text.setPlainText(f"Error reading log file:\n{e}")
        else:
            self.log_text.setPlainText("Log file not found.")

    def filter_logs(self):
        """
        Applies filtering based on both the dropdown selection and the custom filter word.
        Also applies search term highlighting.
        """
        if not self.full_log_content:
            return

        # Retrieve filter values.
        dropdown_filter = self.filter_dropdown.currentText()
        custom_filter = self.custom_filter_bar.text().strip().lower()

        # Filter lines by combining both dropdown criteria and custom filter.
        def line_matches(line: str) -> bool:
            lower_line = line.lower()
            # Exception: if the dropdown is "CAN", exclude lines with "can's" or "can bus".
            if dropdown_filter.upper() == "CAN" and "iso-tp" in lower_line:
                return False

            # Exception: if dropdown is "ISO-TP", exclude lines containing "parsing"
            if dropdown_filter.upper() == "ISO-TP" and "parsing" in lower_line:
                return False

            # Exception: if dropdown is "UDS", exclude lines containing "parsing"
            if dropdown_filter.upper() == "UDS" and "iso-tp" in lower_line:
                return False

            matches_dropdown = (dropdown_filter == "All") or (
                dropdown_filter.lower() in lower_line)
            matches_custom = (custom_filter == "") or (
                custom_filter in lower_line)
            return matches_dropdown and matches_custom

        filtered_lines = [
            line for line in self.full_log_content if line_matches(line)]
        self.log_text.setPlainText("".join(filtered_lines))

        # Reset search highlighting and match positions.
        self.reset_highlighting()
        self.match_positions = []
        self.current_match_index = -1

        # Retrieve the search term from the search bar.
        search_term = self.search_bar.text().strip()
        if search_term:
            self.highlight_search_term(search_term)
            self.find_all_matches(search_term)
            if self.match_positions:
                self.current_match_index = 0
                self.jump_to_match(self.current_match_index)
        self.update_match_label()

    def jump_to_next_match(self):
        """Moves the cursor to the next match (loops back if at the end)."""
        if not self.match_positions:
            return
        self.current_match_index = (
            self.current_match_index + 1) % len(self.match_positions)
        self.jump_to_match(self.current_match_index)

    def jump_to_previous_match(self):
        """Moves the cursor to the previous match (loops back if at the beginning)."""
        if not self.match_positions:
            return
        self.current_match_index = (
            self.current_match_index - 1) % len(self.match_positions)
        self.jump_to_match(self.current_match_index)

    def jump_to_match(self, index):
        """Moves the cursor to the specified match position."""
        if not self.match_positions or index < 0 or index >= len(self.match_positions):
            return
        cursor = self.log_text.textCursor()
        cursor.setPosition(self.match_positions[index])
        self.log_text.setTextCursor(cursor)
        self.update_match_label()

    def update_match_label(self):
        """Updates the match label to show 'Match X/Y' or 'No matches'."""
        if not self.match_positions:
            self.match_label.setText("No matches")
        else:
            self.match_label.setText(
                f"{self.current_match_index + 1}/{len(self.match_positions)}")

    def find_all_matches(self, term):
        """Finds all occurrences of the search term and stores their positions."""
        self.match_positions = []
        if not term:
            return
        doc = self.log_text.document()
        highlight_cursor = QTextCursor(doc)
        while not highlight_cursor.isNull() and not highlight_cursor.atEnd():
            highlight_cursor = doc.find(term, highlight_cursor)
            if not highlight_cursor.isNull():
                self.match_positions.append(highlight_cursor.position())

    def highlight_search_term(self, term):
        """Highlights occurrences of the search term in the QTextEdit."""
        doc = self.log_text.document()
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.Document)
        default_format = QTextCharFormat()
        cursor.setCharFormat(default_format)

        if not term:
            return
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("orange"))
        highlight_format.setForeground(QColor("black"))
        highlight_cursor = QTextCursor(doc)
        highlight_cursor.movePosition(QTextCursor.Start)
        while True:
            highlight_cursor = doc.find(term, highlight_cursor)
            if highlight_cursor.isNull():
                break
            highlight_cursor.mergeCharFormat(highlight_format)

    def reset_highlighting(self):
        """Clears all highlighting in the QTextEdit."""
        doc = self.log_text.document()
        cursor = QTextCursor(doc)
        cursor.select(QTextCursor.Document)
        default_format = QTextCharFormat()
        cursor.setCharFormat(default_format)

    def check_file_existence(self):
        """Adds the log file to the watcher if it exists and isn’t already watched."""
        if os.path.exists(self.log_file) and self.log_file not in self.watcher.files():
            self.watcher.addPath(self.log_file)
            self.update_log()
