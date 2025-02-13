from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from uds_layer.uds_client import UdsClient


class EraseMemoryPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(
            QLabel("Enter Memory Address and Size for Erase Operation"))

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("e.g., 0x12 0x34")
        layout.addWidget(QLabel("Memory Address (space-separated hex):"))
        layout.addWidget(self.address_input)

        self.size_input = QLineEdit()
        self.size_input.setPlaceholderText("e.g., 0x10")
        layout.addWidget(QLabel("Memory Size (space-separated hex):"))
        layout.addWidget(self.size_input)

        self.erase_button = QPushButton("Erase Memory")
        self.erase_button.clicked.connect(self.erase_memory)
        layout.addWidget(self.erase_button)

        self.setLayout(layout)

    def erase_memory(self):
        # Parse memory address
        try:
            address_tokens = self.address_input.text().strip().split()
            memory_address = bytearray([int(token, 16)
                                       for token in address_tokens])
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Invalid memory address input: {e}")
            return

        # Parse memory size
        try:
            size_tokens = self.size_input.text().strip().split()
            memory_size = bytearray([int(token, 16) for token in size_tokens])
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Invalid memory size input: {e}")
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
                self, "Error", "Failed to parse server ID from table.")
            return

        servers = self.client.get_servers()
        server = next((s for s in servers if s.can_id == server_id), None)
        if server:
            message = server.erase_memory(memory_address, memory_size)
            self.client.send_message(server.can_id, message)
            QMessageBox.information(
                self, "Request Sent",
                f"Erase Memory request sent to Server {hex(server_id)}"
            )
        else:
            QMessageBox.warning(self, "Warning", "Selected server not found.")
