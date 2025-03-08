from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox
from uds_layer.uds_client import UdsClient


class ECUResetPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Select ECU Reset Type:")
        self.reset_combo = QComboBox()
        self.reset_combo.addItem("Hard Reset", 0x01)
        self.reset_combo.addItem("Key Off/On Reset", 0x02)
        self.reset_combo.addItem("Soft Reset", 0x03)
        self.reset_combo.addItem("Enable Rapid Power Shutdown", 0x04)
        self.reset_combo.addItem("Disable Rapid Power Shutdown", 0x05)

        self.reset_button = QPushButton("Send ECU Reset")
        self.reset_button.clicked.connect(self.send_ecu_reset)

        layout.addWidget(self.label)
        layout.addWidget(self.reset_combo)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)

    def send_ecu_reset(self):
        """Sends an ECU Reset (0x11) request to the selected server."""
        selected_row = self.server_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, "Warning", "Please select a server from the list.")
            return

        server_id = int(self.server_table.item(
            selected_row, 0).text().split()[1], 16)
        servers = self.client.get_servers()
        server = next((s for s in servers if s.can_id == server_id), None)

        if server:
            reset_type = self.reset_combo.currentData()
            message = server.ecu_reset(reset_type)
            self.client.send_message(server.can_id, message)
            QMessageBox.information(
                self,
                "Request Sent",
                f"ECU Reset request sent with type {self.reset_combo.currentText()} to Server {hex(server_id)}"
            )
        else:
            QMessageBox.warning(self, "Warning", "Selected server not found.")
