import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt
from uds_layer.uds_client import UdsClient, Address
from uds_layer.uds_enums import SessionType
from app_initialization import init_uds_client


class ServersManagementPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = init_uds_client()  # Properly initialize the UDS client
        self.servers = {}  # Dictionary to store servers by RXID
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Group Box for adding/connecting servers
        group_box = QGroupBox("Servers Management")
        grid = QGridLayout()

        txid_label = QLabel("TXID:")
        self.txid_input = QLineEdit("0x33")
        rxid_label = QLabel("RXID:")
        self.rxid_input = QLineEdit("0x33")
        session_label = QLabel("Session:")
        self.session_combo = QComboBox()
        self.session_combo.addItem("DEFAULT", SessionType.DEFAULT)
        self.session_combo.addItem("EXTENDED", SessionType.EXTENDED)
        self.session_combo.addItem("PROGRAMMING", SessionType.PROGRAMMING)

        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self.connect_server)
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.remove_server)

        grid.addWidget(txid_label, 0, 0)
        grid.addWidget(self.txid_input, 0, 1)
        grid.addWidget(rxid_label, 1, 0)
        grid.addWidget(self.rxid_input, 1, 1)
        grid.addWidget(session_label, 2, 0)
        grid.addWidget(self.session_combo, 2, 1)
        grid.addWidget(connect_button, 3, 0, 1, 2)
        grid.addWidget(remove_button, 4, 0, 1, 2)

        group_box.setLayout(grid)
        layout.addWidget(group_box)

        # Table to display connected servers
        self.server_table = QTableWidget()
        self.server_table.setColumnCount(1)
        self.server_table.setHorizontalHeaderLabels(["Connected Servers"])
        self.server_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.server_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.server_table.setFixedHeight(220)
        layout.addWidget(self.server_table)

        self.setLayout(layout)

    def connect_server(self):
        """Establish a UDS session with the specified TXID, RXID, and session type."""
        if self.client._isotp_send is None:
            QMessageBox.critical(
                self, "Error", "ISO-TP send function is not set. Initialization issue detected."
            )
            return

        try:
            txid = int(self.txid_input.text().strip(), 16)
            rxid = int(self.rxid_input.text().strip(), 16)
            session = self.session_combo.currentData()

            if rxid in self.servers:
                QMessageBox.warning(self, "Warning", f"Server {
                                    hex(rxid)} is already connected.")
                return

            address = Address(txid=txid, rxid=rxid)
            self.client.add_server(address, session)
            time.sleep(1)
            servers = self.client.get_servers()
            if servers:
                server = servers[-1]
                self.servers[rxid] = server
                self._update_server_table(session)
                QMessageBox.information(
                    self, "Connected", f"Connected to Server {
                        hex(rxid)} in {session.name} session."
                )
            else:
                QMessageBox.warning(
                    self, "Warning", f"Failed to establish session with Server {
                        hex(rxid)}."
                )

        except ValueError:
            QMessageBox.critical(
                self, "Error", "Invalid TXID or RXID format. Use hexadecimal values like 0x7E0."
            )

    def remove_server(self):
        """Remove a selected server from the list and terminate session."""
        row = self.server_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Warning", "Please select a server to remove."
            )
            return

        server_id = list(self.servers.keys())[row]
        del self.servers[server_id]  # Remove the server from the dictionary

        self._update_server_table(session="null")
        QMessageBox.information(
            self, "Removed", f"Disconnected from Server {hex(server_id)}."
        )

    def _update_server_table(self, session):
        """Update the table with the list of connected servers."""
        self.server_table.setRowCount(len(self.servers))
        for i, (rxid, server) in enumerate(self.servers.items()):
            item = QTableWidgetItem(f"Server {hex(rxid)} ({session})")
            self.server_table.setItem(i, 0, item)
