from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from uds_layer.uds_client import UdsClient


class ReadByIdentifierPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Enter VIN in the format: vin=[0x01, 0x90]")
        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("vin=[0x01, 0x90]")

        self.read_button = QPushButton("Read Data")
        self.read_button.clicked.connect(self.read_data_by_identifier)

        layout.addWidget(self.label)
        layout.addWidget(self.identifier_input)
        layout.addWidget(self.read_button)

        self.setLayout(layout)

    def read_data_by_identifier(self):
        """
        Sends a Read Data by Identifier request using VIN input in the format:
            vin=[0x01, 0x90]
        """
        try:
            vin_input = self.identifier_input.text().strip()
            if not (vin_input.lower().startswith("vin=[") and vin_input.endswith("]")):
                raise ValueError(
                    "VIN input must be in the format vin=[0x01, 0x90]")
            # Remove prefix "vin=[" and trailing "]"
            inner = vin_input[5:-1]
            parts = inner.split(",")
            if len(parts) != 2:
                raise ValueError(
                    "VIN input must contain exactly two hexadecimal values.")
            vin = [int(p.strip(), 16) for p in parts]
        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Invalid VIN input: {e}")
            return

        selected_row = self.server_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, "Warning", "Please select a server from the list.")
            return

        try:
            # Parse server ID from table text, e.g. "Server 0x33 (SESSION)"
            server_text = self.server_table.item(selected_row, 0).text()
            server_id = int(server_text.split()[1], 16)
        except Exception:
            QMessageBox.critical(
                self, "Error", "Failed to parse server ID from the table.")
            return

        servers = self.client.get_servers()
        server = next((s for s in servers if s.can_id == server_id), None)
        if server:
            message = server.read_data_by_identifier(vin=vin)
            self.client.send_message(server.can_id, message)
            QMessageBox.information(
                self, "Request Sent",
                f"Read request sent for VIN: {vin} to Server {hex(server_id)}"
            )
        else:
            QMessageBox.warning(self, "Warning", "Selected server not found.")
