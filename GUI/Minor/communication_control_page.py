from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox
from uds_layer.uds_enums import CommunicationControlSubFunction, CommunicationControlType
from uds_layer.uds_client import UdsClient


class CommunicationControlPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select Communication Control Parameters"))

        # Sub-function combo
        self.sub_function_combo = QComboBox()
        for sub in CommunicationControlSubFunction:
            self.sub_function_combo.addItem(sub.name, sub)
        layout.addWidget(QLabel("Sub Function:"))
        layout.addWidget(self.sub_function_combo)

        # Control type combo
        self.control_type_combo = QComboBox()
        for ct in CommunicationControlType:
            self.control_type_combo.addItem(ct.name, ct)
        layout.addWidget(QLabel("Control Type:"))
        layout.addWidget(self.control_type_combo)

        self.send_button = QPushButton("Send Communication Control")
        self.send_button.clicked.connect(self.send_communication_control)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

    def send_communication_control(self):
        sub_function = self.sub_function_combo.currentData()
        control_type = self.control_type_combo.currentData()

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
            message = self.client.communication_control(
                sub_function, control_type)
            self.client.send_message(server.can_id, message)
            QMessageBox.information(
                self, "Request Sent",
                f"Communication Control request sent with SubFunction: {
                    sub_function.name}, "
                f"ControlType: {control_type.name} to Server {hex(server_id)}"
            )
        else:
            QMessageBox.warning(self, "Warning", "Selected server not found.")
