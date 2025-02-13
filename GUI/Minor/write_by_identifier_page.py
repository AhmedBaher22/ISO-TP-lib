import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from uds_layer.uds_client import UdsClient
from global_data import global_uploaded_bytes


class WriteByIdentifierPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # File upload section
        file_layout = QHBoxLayout()
        self.file_line_edit = QLineEdit()
        self.file_line_edit.setPlaceholderText("Select data file (hex)...")
        self.upload_btn = QPushButton("Upload File Data")
        self.upload_btn.clicked.connect(self.upload_file_data)
        file_layout.addWidget(self.file_line_edit)
        file_layout.addWidget(self.upload_btn)
        layout.addLayout(file_layout)

        # VIN input section
        self.label_id = QLabel("Enter VIN in the format: vin=[0x01, 0x90]")
        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("vin=[0x01, 0x90]")
        layout.addWidget(self.label_id)
        layout.addWidget(self.identifier_input)

        # Info label
        self.info_label = QLabel("Uploaded file data will be used as payload.")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        # Write Data button
        self.write_button = QPushButton("Write Data")
        self.write_button.clicked.connect(self.write_data_by_identifier)
        layout.addWidget(self.write_button)

        self.setLayout(layout)

    def upload_file_data(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "", "Hex Files (*.hex);;All Files (*)", options=options)
        if filename:
            self.file_line_edit.setText(filename)
            try:
                with open(filename, 'r') as f:
                    content = f.read().strip()
                tokens = content.split()
                parsed_bytes = []
                for token in tokens:
                    clean_token = token.strip(" '\"\n")
                    if clean_token.startswith(":"):
                        clean_token = clean_token[1:]
                    if clean_token:
                        for i in range(0, len(clean_token), 2):
                            byte_val = int(clean_token[i:i+2], 16)
                            parsed_bytes.append(byte_val)
                global global_uploaded_bytes
                global_uploaded_bytes = parsed_bytes
                QMessageBox.information(
                    self, "Upload Complete",
                    f"File '{filename}' uploaded successfully! Parsed {
                        len(parsed_bytes)} bytes."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to parse file: {e}")

    def write_data_by_identifier(self):
        """Sends a Write Data by Identifier request using the uploaded file data."""
        try:
            vin_input = self.identifier_input.text().strip()
            if not (vin_input.lower().startswith("vin=[") and vin_input.endswith("]")):
                raise ValueError(
                    "VIN input must be in the format vin=[0x01, 0x90]")
            inner = vin_input[5:-1]
            parts = inner.split(",")
            if len(parts) != 2:
                raise ValueError(
                    "VIN input must contain exactly two hexadecimal values.")
            vin = [int(p.strip(), 16) for p in parts]
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Invalid VIN input: {e}")
            return

        try:
            data = global_uploaded_bytes
            if not data:
                raise ValueError(
                    "No uploaded file data available. Please upload a file first.")
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to retrieve uploaded file data: {e}")
            return

        selected_row = self.server_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, "Warning", "Please select a server from the list.")
            return

        try:
            server_text = self.server_table.item(selected_row, 0).text()
            server_id = int(server_text.split()[1], 16)
        except Exception:
            QMessageBox.critical(
                self, "Error", "Failed to parse server ID from the table.")
            return

        servers = self.client.get_servers()
        server = next((s for s in servers if s.can_id == server_id), None)
        if server:
            message = server.write_data_by_identifier(vin=vin, data=data)
            self.client.send_message(server.can_id, message)
            QMessageBox.information(
                self, "Request Sent",
                f"Write request sent for VIN: {vin} with data {
                    data} to Server {hex(server_id)}"
            )
        else:
            QMessageBox.warning(self, "Warning", "Selected server not found.")
