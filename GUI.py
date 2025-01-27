import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QGroupBox, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# For demonstration, we'll define minimal stubs rather than import real classes:


class SessionTypeStub:
    NONE = 0
    DEFAULT = 1
    EXTENDED = 2
    PROGRAMMING = 3


class Address:
    def __init__(self, addressing_mode=0, txid=None, rxid=None):
        self.addressing_mode = addressing_mode
        self._txid = txid
        self._rxid = rxid


class UdsClient:
    def __init__(self, client_id):
        self._client_id = client_id
        self._servers = []
        self._isotp_send = None

    def set_isotp_send(self, e):
        self._isotp_send = e

    def add_server(self, address: Address, session_type: int):
        """Simulate adding a server."""
        print(f"Adding Server: TXID={address._txid}, RXID={
              address._rxid}, SessionType={session_type}")
        # For demonstration, store a placeholder string
        self._servers.append(f"Server_{address._rxid}_Session_{session_type}")

    def remove_server(self, server_idx: int):
        """Remove server from the list if index is valid."""
        if 0 <= server_idx < len(self._servers):
            removed = self._servers.pop(server_idx)
            print(f"Removed server: {removed}")

    def get_servers(self):
        return self._servers

    def read_vin(self, server_idx: int):
        """Placeholder read VIN function."""
        return "WAUZZZ8V6JA123456"

    def write_vin(self, server_idx: int, new_vin: str):
        """Placeholder write VIN function."""
        pass

    def ecu_reset(self, server_idx: int, reset_type: int):
        """Placeholder ECU reset function."""
        pass

    def on_fail_receive(self, e: Exception):
        print(e)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("UDS Client GUI")
        self.setGeometry(100, 100, 900, 600)

        # Create our UDS Client
        self.uds_client = UdsClient(client_id=0x123)  # Example client ID

        # Main container widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main vertical layout
        self.main_layout = QVBoxLayout()
        main_widget.setLayout(self.main_layout)

        # Create a UI
        self._create_server_group()
        self._create_server_table()
        self._create_vin_operations_group()
        self._create_ecu_reset_group()
        self._create_log_box()

        # Apply some basic styling
        self._apply_styles()

    def _create_server_group(self):
        """Group box to connect or create new server sessions."""
        group_box = QGroupBox("Create/Connect to Server")
        layout = QGridLayout()

        # Labels and inputs
        txid_label = QLabel("TXID:")
        self.txid_input = QLineEdit("0x7E0")
        rxid_label = QLabel("RXID:")
        self.rxid_input = QLineEdit("0x7E8")

        session_label = QLabel("Session:")
        self.session_combo = QComboBox()
        self.session_combo.addItem("DEFAULT", SessionTypeStub.DEFAULT)
        self.session_combo.addItem("EXTENDED", SessionTypeStub.EXTENDED)
        self.session_combo.addItem("PROGRAMMING", SessionTypeStub.PROGRAMMING)

        connect_button = QPushButton("Connect")
        connect_button.clicked.connect(self._on_connect_server)

        # ** New Remove button **
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self._on_remove_server)

        layout.addWidget(txid_label, 0, 0)
        layout.addWidget(self.txid_input, 0, 1)
        layout.addWidget(rxid_label, 1, 0)
        layout.addWidget(self.rxid_input, 1, 1)
        layout.addWidget(session_label, 2, 0)
        layout.addWidget(self.session_combo, 2, 1)
        layout.addWidget(connect_button, 3, 0, 1, 2)
        layout.addWidget(remove_button, 4, 0, 1, 2)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

    def _create_server_table(self):
        """Table to display servers that are connected."""
        self.server_table = QTableWidget()
        self.server_table.setColumnCount(1)
        self.server_table.setHorizontalHeaderLabels(["Connected Servers"])
        self.server_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.server_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.server_table.setFixedHeight(120)
        self.main_layout.addWidget(self.server_table)

    def _create_vin_operations_group(self):
        """Group box to perform VIN read/write."""
        group_box = QGroupBox("VIN Operations")
        layout = QHBoxLayout()

        # Read VIN
        self.read_vin_btn = QPushButton("Read VIN")
        self.read_vin_btn.clicked.connect(self._on_read_vin)

        # Write VIN
        self.write_vin_input = QLineEdit()
        self.write_vin_input.setPlaceholderText("Enter new VIN...")
        self.write_vin_btn = QPushButton("Write VIN")
        self.write_vin_btn.clicked.connect(self._on_write_vin)

        layout.addWidget(self.read_vin_btn)
        layout.addWidget(self.write_vin_input)
        layout.addWidget(self.write_vin_btn)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

    def _create_ecu_reset_group(self):
        """Group box to trigger different types of ECU reset."""
        group_box = QGroupBox("ECU Reset")
        layout = QHBoxLayout()

        self.ecu_reset_combo = QComboBox()
        self.ecu_reset_combo.addItem("Hard Reset (0x01)", 0x01)
        self.ecu_reset_combo.addItem("Key Off/On Reset (0x02)", 0x02)
        self.ecu_reset_combo.addItem("Soft Reset (0x03)", 0x03)
        self.ecu_reset_combo.addItem(
            "Enable Rapid Power Shutdown (0x04)", 0x04)
        self.ecu_reset_combo.addItem(
            "Disable Rapid Power Shutdown (0x05)", 0x05)

        self.ecu_reset_btn = QPushButton("Send ECU Reset")
        self.ecu_reset_btn.clicked.connect(self._on_ecu_reset)

        layout.addWidget(self.ecu_reset_combo)
        layout.addWidget(self.ecu_reset_btn)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

    def _create_log_box(self):
        """Text box to display log messages and responses."""
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Logs & Responses will appear here...")
        self.main_layout.addWidget(self.log_box)

    def _on_connect_server(self):
        """Called when user clicks the Connect button to create a new server."""
        txid_text = self.txid_input.text().strip()
        rxid_text = self.rxid_input.text().strip()

        # Convert from hex string if needed
        try:
            txid = int(txid_text, 16)
        except ValueError:
            txid = 0x7E0  # fallback
        try:
            rxid = int(rxid_text, 16)
        except ValueError:
            rxid = 0x7E8  # fallback

        session_type = self.session_combo.currentData()

        # Add server via UdsClient
        addr = Address(addressing_mode=0, txid=txid, rxid=rxid)
        self.uds_client.add_server(addr, session_type)

        self._update_server_table()
        self._log(f"Server added. TXID={hex(txid)}, RXID={
                  hex(rxid)}, SessionType={session_type}")

    def _on_remove_server(self):
        """Called when user clicks the Remove button to delete a selected server."""
        row = self.server_table.currentRow()
        if row < 0:
            self._alert(
                "Please select a server to remove from the table first.")
            return

        self.uds_client.remove_server(row)
        self._update_server_table()
        self._log(f"Removed server at index {row}")

    def _update_server_table(self):
        """Refresh the server table with the current server list."""
        servers = self.uds_client.get_servers()
        self.server_table.setRowCount(len(servers))

        for i, srv in enumerate(servers):
            item = QTableWidgetItem(str(srv))
            self.server_table.setItem(i, 0, item)

    def _on_read_vin(self):
        """Handle reading VIN from a selected server."""
        row = self.server_table.currentRow()
        if row < 0:
            self._alert("Please select a server from the table first.")
            return

        # Call read function from UdsClient
        vin = self.uds_client.read_vin(row)
        self._log(f"Read VIN: {vin}")

    def _on_write_vin(self):
        """Handle writing VIN to a selected server."""
        row = self.server_table.currentRow()
        if row < 0:
            self._alert("Please select a server from the table first.")
            return

        new_vin = self.write_vin_input.text().strip()
        if not new_vin:
            self._alert("Please enter a VIN to write.")
            return

        # Call write function from UdsClient
        self.uds_client.write_vin(row, new_vin)
        self._log(f"Requested to write VIN: {new_vin}")

    def _on_ecu_reset(self):
        """Handle sending an ECU reset request to a selected server."""
        row = self.server_table.currentRow()
        if row < 0:
            self._alert("Please select a server from the table first.")
            return

        reset_type = self.ecu_reset_combo.currentData()
        self.uds_client.ecu_reset(row, reset_type)
        self._log(f"Requested ECU Reset: Type={hex(reset_type)}")

    def _log(self, msg: str):
        """Convenience method to append log messages to the text box."""
        self.log_box.append(msg)

    def _alert(self, msg: str):
        """Show a simple alert dialog."""
        QMessageBox.warning(self, "Warning", msg)

    def _apply_styles(self):
        """Optional function to set some minimal styling for a sleek look."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QGroupBox {
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 6px;
                font-weight: bold;
                color: #dddddd;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
            QLabel, QLineEdit, QComboBox, QTableWidget {
                font-size: 14px;d
                color: #000000;
            }
            QLineEdit {
                background-color: #3c3f41;
                border: 1px solid #555;
                padding: 4px;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #505357;
                color: #eeeeee;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #696969;
            }
            QTextEdit {
                background-color: #3c3f41;
                color: #eeeeee;
                border: 1px solid #555;
            }
            QHeaderView::section {
                background-color: #444;
                color: #fff;
            }
        """)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
