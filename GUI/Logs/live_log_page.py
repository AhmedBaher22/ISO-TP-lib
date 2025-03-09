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
        self.last_cleared_position = 0  # Keeps track of last cleared log position
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

    def get_position_marker_filename(self):
        """Return the filename where the last cleared position is stored."""
        return self.log_file + ".pos"

    def load_last_cleared_position(self):
        """Load the last cleared file position from a persistent file (if it exists)."""
        pos_filename = self.get_position_marker_filename()
        if os.path.exists(pos_filename):
            try:
                with open(pos_filename, "r") as pos_file:
                    self.last_cleared_position = int(pos_file.read().strip())
            except (ValueError, IOError):
                self.last_cleared_position = 0
        else:
            self.last_cleared_position = 0

    def save_last_cleared_position(self):
        """Save the current last_cleared_position to a persistent file."""
        pos_filename = self.get_position_marker_filename()
        try:
            with open(pos_filename, "w") as pos_file:
                pos_file.write(str(self.last_cleared_position))
        except IOError as e:
            print(f"Error saving last cleared position: {e}")

    def update_log(self, path=None):
        """
        Reads the log file from last_cleared_position and appends only new lines.
        Ensures new logs are not fully highlighted unless they contain the search term.
        """
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    f.seek(self.last_cleared_position)
                    new_logs = f.readlines()
                    if new_logs:
                        self.last_cleared_position = f.tell()  # Update last read position
                        self.save_last_cleared_position()      # Persist the new position

                        # Preserve old logs and append only new ones
                        old_text = self.log_text.toPlainText()
                        updated_text = old_text + "".join(new_logs)
                        self.log_text.setPlainText(updated_text)

                        # Update full log storage
                        self.full_log_content.extend(new_logs)

                        # Retrieve the search term
                        search_term = self.search_bar.text().strip()

                        # Apply search highlights ONLY if a term exists
                        if search_term:
                            self.highlight_search_term(search_term)
                            self.find_all_matches(search_term)
                        else:
                            # Reset highlighting if no search term is present
                            self.reset_highlighting()

            except Exception as e:
                self.log_text.setPlainText(f"Error reading log file:\n{e}")

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

    def filter_lines_by_dropdown(self, lines):
        """
        Returns only the lines that match the dropdown filter.
        If the selected option is 'All', returns all lines.
        Otherwise, returns only lines that contain the dropdown text.
        """
        filter_option = self.filter_dropdown.currentText()
        if filter_option == "All":
            return lines
        else:
            return [line for line in lines if filter_option in line]

    def find_all_matches(self, term):
        """Finds all occurrences of the search term and stores their positions."""
        self.match_positions = []  # Clear previous matches
        if not term:
            return

        doc = self.log_text.document()
        highlight_cursor = QTextCursor(doc)

        # Keep searching until we reach the end of the document
        while not highlight_cursor.isNull() and not highlight_cursor.atEnd():
            highlight_cursor = doc.find(term, highlight_cursor)
            if not highlight_cursor.isNull():
                self.match_positions.append(highlight_cursor.position())

    def jump_to_next_match(self):
        """Moves the cursor to the next match (loops back if at the end)."""
        if not self.match_positions:
            return
        self.current_match_index += 1
        if self.current_match_index >= len(self.match_positions):
            self.current_match_index = 0  # Loop back to the first match
        self.jump_to_match(self.current_match_index)

    def jump_to_previous_match(self):
        """Moves the cursor to the previous match (loops back if at the beginning)."""
        if not self.match_positions:
            return
        self.current_match_index -= 1
        if self.current_match_index < 0:
            self.current_match_index = len(self.match_positions) - 1
        self.jump_to_match(self.current_match_index)

    def jump_to_match(self, index):
        """Moves the cursor to the specified match position."""
        if not self.match_positions or index < 0 or index >= len(self.match_positions):
            return

        cursor = self.log_text.textCursor()
        cursor.setPosition(self.match_positions[index])
        # Move the cursor to highlight the match
        self.log_text.setTextCursor(cursor)

        # Update match label (e.g., "Match 2/5")
        self.update_match_label()

    def update_match_label(self):
        """Updates the match label to show 'Match X/Y' or 'No matches'."""
        if not self.match_positions:
            self.match_label.setText("No matches")
        else:
            self.match_label.setText(
                f"{self.current_match_index + 1}/{len(self.match_positions)}")

    def highlight_search_term(self, term):
        """Highlights occurrences of the search term in the QTextEdit."""
        # Reset all existing highlights first
        self.reset_highlighting()

        if not term:
            return  # Do nothing if no search term is provided

        doc = self.log_text.document()
        highlight_cursor = QTextCursor(doc)
        highlight_cursor.movePosition(QTextCursor.Start)

        # Define the highlight format
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("orange"))
        highlight_format.setForeground(QColor("black"))

        # Search and highlight all occurrences of the term
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
        """
        If the file now exists and is not being watched,
        add it to the watcher and update the log.
        """
        if os.path.exists(self.log_file) and self.log_file not in self.watcher.files():
            self.watcher.addPath(self.log_file)
            self.update_log()
