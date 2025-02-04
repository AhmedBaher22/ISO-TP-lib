# Adjust import as needed
# Global variable to store uploaded file bytes
from global_data import global_uploaded_bytes
from uds_layer.uds_enums import CommunicationControlSubFunction, CommunicationControlType
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QTimer, QFileSystemWatcher, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox, QTableWidget
from uds_layer.uds_client import UdsClient
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTableWidget
from PyQt5.QtCore import QTimer
import os
import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QGroupBox, QGridLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QTextEdit, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, QFileSystemWatcher
from PyQt5.QtGui import QTextCursor
from typing import Optional


# ---------------------------
# Page Implementations
# ---------------------------
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import Qt
from uds_layer.transfer_enums import EncryptionMethod, CompressionMethod, TransferStatus
from uds_layer.transfer_request import TransferRequest
from uds_layer.uds_client import UdsClient, Address
from uds_layer.uds_enums import SessionType
from app_initialization import init_uds_client
from global_data import global_uploaded_bytes


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
        """ Establish a UDS session with the specified TXID, RXID, and session type """
        if self.client._isotp_send is None:
            QMessageBox.critical(
                self, "Error", "ISO-TP send function is not set. Initialization issue detected.")
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
                self._update_server_table()
                QMessageBox.information(self, "Connected", f"Connected to Server {
                                        hex(rxid)} in {session.name} session.")
            else:
                QMessageBox.warning(
                    self, "Warning", f"Failed to establish session with Server {hex(rxid)}.")

        except ValueError:
            QMessageBox.critical(
                self, "Error", "Invalid TXID or RXID format. Use hexadecimal values like 0x7E0.")

    def remove_server(self):
        """ Remove a selected server from the list and terminate session """
        row = self.server_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Warning", "Please select a server to remove.")
            return

        server_id = list(self.servers.keys())[row]
        del self.servers[server_id]  # Remove the server from the dictionary

        self._update_server_table()
        QMessageBox.information(
            self, "Removed", f"Disconnected from Server {hex(server_id)}.")

    def _update_server_table(self):
        """ Update the table with the list of connected servers """
        self.server_table.setRowCount(len(self.servers))
        for i, (rxid, server) in enumerate(self.servers.items()):
            item = QTableWidgetItem(
                f"Server {hex(rxid)} ({server.session.name})")
            self.server_table.setItem(i, 0, item)


# Ensure the global variable is imported from your global_data module


class ReadByIdentifierPage(QWidget):
    def __init__(self, client: UdsClient, server_table: QTableWidget, parent=None):
        super().__init__(parent)
        self.client = client          # Reference to UDS client
        self.server_table = server_table  # Server selection table
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
            # Validate input format.
            if not (vin_input.lower().startswith("vin=[") and vin_input.endswith("]")):
                raise ValueError(
                    "VIN input must be in the format vin=[0x01, 0x90]")
            # Remove the prefix and trailing bracket.
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
            # Assume server table text is like: "Server 0x33 (SESSION_NAME)"
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


class WriteByIdentifierPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client          # Reference to UDS client
        self.server_table = server_table  # Server selection table
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # --- File upload section ---
        file_layout = QHBoxLayout()
        self.file_line_edit = QLineEdit()
        self.file_line_edit.setPlaceholderText("Select data file (hex)...")
        self.upload_btn = QPushButton("Upload File Data")
        self.upload_btn.clicked.connect(self.upload_file_data)
        file_layout.addWidget(self.file_line_edit)
        file_layout.addWidget(self.upload_btn)
        layout.addLayout(file_layout)

        # --- VIN input section ---
        self.label_id = QLabel("Enter VIN in the format: vin=[0x01, 0x90]")
        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("vin=[0x01, 0x90]")
        layout.addWidget(self.label_id)
        layout.addWidget(self.identifier_input)

        # --- Info label ---
        self.info_label = QLabel("Uploaded file data will be used as payload.")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        # --- Write Data button ---
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
                    # Remove extra characters such as quotes, spaces, newlines, and colons.
                    clean_token = token.strip(" '\"\n")
                    if clean_token.startswith(":"):
                        clean_token = clean_token[1:]
                    if clean_token:
                        # Process two characters at a time into a byte.
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
        """
        Sends a Write Data by Identifier request using VIN input in the format:
            vin=[0x01, 0x90]
        and uses the uploaded file data (from global_uploaded_bytes) as the payload.
        """
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

        # Retrieve the uploaded file data.
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


class ECUResetPage(QWidget):
    def __init__(self, client: UdsClient, server_table: QTableWidget, parent=None):
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
        """ Sends an ECU Reset (0x11) request to the selected server. """
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
            QMessageBox.information(self, "Request Sent", f"ECU Reset request sent with type {
                                    self.reset_combo.currentText()} to Server {hex(server_id)}")

# =========================
# global_data.py
# =========================
# Create a file named global_data.py with the following content:


global_uploaded_bytes = []


# =========================
# New Minor Services Pages
# =========================


# --- Communication Control Page ---

class CommunicationControlPage(QWidget):
    def __init__(self, client, server_table, parent=None):
        """
        Page to send a Communication Control request.
        """
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Select Communication Control Parameters"))

        # Combo box for sub-function
        self.sub_function_combo = QComboBox()
        for sub in CommunicationControlSubFunction:
            self.sub_function_combo.addItem(sub.name, sub)
        layout.addWidget(QLabel("Sub Function:"))
        layout.addWidget(self.sub_function_combo)

        # Combo box for control type
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

        # Get selected server from the server table.
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
            # Call the client's communication_control method
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


# --- Erase Memory Page ---
class EraseMemoryPage(QWidget):
    def __init__(self, client, server_table, parent=None):
        """
        Page to send an Erase Memory request.
        """
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


class MinorServicesPage(QWidget):
    def __init__(self, client: UdsClient, server_table: QTableWidget, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self._create_sub_pages()
        self._create_sub_navigation()

    def _create_sub_pages(self):
        self.sub_pages = {
            "Read by Identifier": ReadByIdentifierPage(self.client, self.server_table),
            "Write by Identifier": WriteByIdentifierPage(self.client, self.server_table),
            "ECU Reset": ECUResetPage(self.client, self.server_table),
            "Communication Control": CommunicationControlPage(self.client, self.server_table),
            "Erase Memory": EraseMemoryPage(self.client, self.server_table)
        }
        self.sub_stacked_widget = QStackedWidget()
        for page in self.sub_pages.values():
            self.sub_stacked_widget.addWidget(page)

    def _create_sub_navigation(self):
        self.sub_nav_list = QListWidget()
        for page_name in self.sub_pages.keys():
            self.sub_nav_list.addItem(page_name)
        self.sub_nav_list.currentRowChanged.connect(
            self.sub_stacked_widget.setCurrentIndex)
        self.sub_nav_list.setFixedWidth(230)

        layout = QHBoxLayout()
        layout.addWidget(self.sub_nav_list)
        layout.addWidget(self.sub_stacked_widget)
        self.setLayout(layout)

# ==============================
# Flash Page (Firmware Update)
# ==============================


class FlashPage(QWidget):
    def __init__(self, client, server_table, parent=None):
        """
        FlashPage now receives a reference to the server table so that the selected
        server's ID is used for the flash operation.
        """
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self.firmware_data: Optional[bytearray] = None
        self.transfer_request: Optional[TransferRequest] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Flash (Firmware Update)")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # File selection layout
        file_layout = QHBoxLayout()
        self.file_line_edit = QLineEdit()
        self.file_line_edit.setPlaceholderText("Select firmware file...")
        self.file_select_btn = QPushButton("Select File")
        self.file_select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_line_edit)
        file_layout.addWidget(self.file_select_btn)
        layout.addLayout(file_layout)

        # Memory address input
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Enter Memory Address (hex)")
        layout.addWidget(QLabel("Memory Address:"))
        layout.addWidget(self.address_input)

        # Encryption method combo box
        self.encryption_combo = QComboBox()
        for method in EncryptionMethod:
            self.encryption_combo.addItem(method.name, method)
        layout.addWidget(QLabel("Encryption Method:"))
        layout.addWidget(self.encryption_combo)

        # Compression method combo box
        self.compression_combo = QComboBox()
        for method in CompressionMethod:
            self.compression_combo.addItem(method.name, method)
        layout.addWidget(QLabel("Compression Method:"))
        layout.addWidget(self.compression_combo)

        # Checksum required checkbox
        self.checksum_checkbox = QCheckBox("Checksum Required")
        layout.addWidget(self.checksum_checkbox)

        # Max Block Length input (user-specified instead of hard-coded)
        self.block_length_input = QLineEdit()
        self.block_length_input.setPlaceholderText(
            "Enter Max Block Length (decimal)")
        layout.addWidget(QLabel("Max Block Length:"))
        layout.addWidget(self.block_length_input)

        # Flash button
        self.flash_btn = QPushButton("Start Flash")
        self.flash_btn.clicked.connect(self.start_flash)
        layout.addWidget(self.flash_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def select_file(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Firmware File", "", "Hex Files (*.hex);;All Files (*)", options=options)
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
                self.firmware_data = bytearray(parsed_bytes)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to parse firmware file: {e}")
                self.firmware_data = None

    def start_flash(self):
        if not self.firmware_data:
            QMessageBox.critical(
                self, "Error", "No firmware file selected or parsing failed.")
            return

        # Retrieve the selected server from the server table.
        selected_row = self.server_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, "Warning", "Please select a server from the server table.")
            return
        try:
            server_text = self.server_table.item(selected_row, 0).text()
            # Assume server text format: "Server 0x33 (SESSION_NAME)"
            server_id = int(server_text.split()[1], 16)
        except Exception:
            QMessageBox.critical(
                self, "Error", "Failed to parse server ID from table.")
            return

        # Get Memory Address input
        address_str = self.address_input.text().strip()
        if not address_str.startswith("0x"):
            QMessageBox.critical(
                self, "Error", "Memory Address must be in hexadecimal format.")
            return
        try:
            memory_address = bytearray.fromhex(address_str[2:])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid Memory Address: {e}")
            return

        encryption_method = self.encryption_combo.currentData()
        compression_method = self.compression_combo.currentData()
        checksum_required = self.checksum_checkbox.isChecked()

        # Retrieve max block length from user input.
        try:
            block_length_str = self.block_length_input.text().strip()
            if not block_length_str:
                raise ValueError("Max Block Length is required.")
            max_block_length = int(block_length_str)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Invalid Max Block Length: {e}")
            return

        # Use the selected server's CAN ID as the receiver DA.
        recv_DA = server_id

        # Create the transfer request with user-specified parameters.
        self.transfer_request = TransferRequest(
            recv_DA=recv_DA,
            data=self.firmware_data,
            encryption_method=encryption_method,
            compression_method=compression_method,
            memory_address=memory_address,
            checksum_required=checksum_required
        )
        self.transfer_request.max_number_of_block_length = max_block_length
        self.transfer_request.calculate_steps_number()

        self.current_step = 0
        self.total_steps = self.transfer_request.steps_number
        self.progress_bar.setValue(0)
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self._update_flash_progress)
        self.flash_timer.start(200)  # Update every 200 milliseconds

    def _update_flash_progress(self):
        self.current_step += 1
        progress_percent = int((self.current_step / self.total_steps) * 100)
        self.progress_bar.setValue(progress_percent)
        if self.current_step >= self.total_steps:
            self.flash_timer.stop()
            self.transfer_request.status = TransferStatus.COMPLETED
            QMessageBox.information(
                self, "Flash Completed", "Firmware flash operation completed successfully.")


# ==============================
# Major Services Page
# ==============================

class MajorServicesPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Major Services - Flash")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        # Pass the server table to FlashPage.
        self.flash_page = FlashPage(self.client, self.server_table)
        layout.addWidget(self.flash_page)
        self.setLayout(layout)

# ---------------------------
# Live Log Pages using QFileSystemWatcher
# ---------------------------


class LiveLogPage(QWidget):
    def __init__(self, title: str, log_file: str, placeholder_text: str, parent=None, update_interval=1000):
        """
        :param title: Title to display at the top of the page.
        :param log_file: Path to the text file that contains log data.
        :param placeholder_text: Placeholder text when no log data is available.
        :param update_interval: Interval (in milliseconds) to check the file (fallback timer).
        """
        super().__init__(parent)
        self.log_file = log_file

        # Set up the layout and label.
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # Log display widget.
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText(placeholder_text)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

        # Set up QFileSystemWatcher to monitor the log file.
        self.watcher = QFileSystemWatcher(self)
        if os.path.exists(self.log_file):
            self.watcher.addPath(self.log_file)
        self.watcher.fileChanged.connect(self.update_log)

        # Fallback: a timer to periodically check for file existence.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_file_existence)
        self.timer.start(update_interval)

        # Initial update.
        self.update_log()

    def check_file_existence(self):
        """If the file now exists and is not being watched, add it to the watcher."""
        if os.path.exists(self.log_file) and self.log_file not in self.watcher.files():
            self.watcher.addPath(self.log_file)
            self.update_log()

    def update_log(self, path=None):
        """Reads the log file and updates the text widget, then scrolls to the bottom."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    content = f.read()
                self.log_text.setPlainText(content)
                # Scroll to the bottom:
                self.log_text.moveCursor(QTextCursor.End)
            except Exception as e:
                self.log_text.setPlainText(f"Error reading log file:\n{e}")
        else:
            self.log_text.setPlainText("Log file not found.")


class ExceptionHandlingPage(LiveLogPage):
    def __init__(self, service_name="Service", log_file="logs/uds/error.log", parent=None, update_interval=1000):
        title = f"Exception Handling for {service_name}"
        placeholder_text = "Errors details will appear here..."
        super().__init__(title, log_file, placeholder_text, parent, update_interval)


class PerServerLogPage(LiveLogPage):
    def __init__(self, log_file="logs/uds/communication.log", parent=None, update_interval=1000):
        title = "Server Communication Log"
        placeholder_text = "Communication Logs will appear here..."
        super().__init__(title, log_file, placeholder_text, parent, update_interval)


class GlobalLogPage(LiveLogPage):
    def __init__(self, log_file="logs/uds/success.log", parent=None, update_interval=1000):
        title = "Global Log for All Servers"
        placeholder_text = "Global logs will appear here..."
        super().__init__(title, log_file, placeholder_text, parent, update_interval)


# ===============================
# Main Window and Navigation
# ===============================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-page UDS Client GUI")
        self.setGeometry(100, 100, 1200, 800)
        self._create_pages()
        self._create_navigation()
        self._apply_styles()

    def _create_pages(self):
        # Initialize server management
        self.servers_management_page = ServersManagementPage()
        self.pages = {
            "Servers Management": self.servers_management_page,
            "Minor Services": MinorServicesPage(self.servers_management_page.client, self.servers_management_page.server_table),
            "Major Services": MajorServicesPage(self.servers_management_page.client, self.servers_management_page.server_table),
            "Global Log": GlobalLogPage(),
            "Error Log": ExceptionHandlingPage(),
            "Communication Log": PerServerLogPage()
        }

        self.stacked_widget = QStackedWidget()
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

    def _create_navigation(self):
        from PyQt5.QtWidgets import QListWidget
        self.nav_list = QListWidget()
        for page_name in self.pages.keys():
            self.nav_list.addItem(page_name)
        self.nav_list.currentRowChanged.connect(
            self.stacked_widget.setCurrentIndex)
        self.nav_list.setFixedWidth(200)

        container = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.nav_list)
        layout.addWidget(self.stacked_widget)
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.nav_list.setCurrentRow(0)

    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 16px;
            }
            QGroupBox {
                border: 1px solid #666;
                border-radius: 8px;
                margin-top: 10px;
                font-weight: bold;
                color: #ffffff;
                padding: 10px;
                font-size: 18px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
            QLabel {
                font-size: 16px;
                color: #ffffff;
            }
            QLineEdit, QComboBox, QTableWidget {
                font-size: 16px;
                color: #ffffff;
                background-color: #2d2d30;
                padding: 8px;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QPushButton {
                font-size: 16px;
                background-color: #007acc;
                color: #ffffff;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #005f9e;
            }
            QTextEdit {
                font-size: 16px;
                background-color: #2d2d30;
                color: #ffffff;
                border: 1px solid #444;
                padding: 8px;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #444;
                color: #ffffff;
                padding: 8px;
                font-size: 16px;
            }
            QListWidget {
                font-size: 16px;
                background-color: #2d2d30;
                border: none;
                color: #ffffff;
                padding: 4px;
            }
            QListWidget::item {
                padding: 12px;
                margin: 4px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #005f9e;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #007acc;
            }
            QMessageBox {
                background-color: #2d2d30;
                border: 1px solid #444;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 16px;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QMessageBox QPushButton {
                background-color: #007acc;
                color: #ffffff;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QMessageBox QPushButton:hover {
                background-color: #005f9e;
            }
            QProgressBar {
                border: 2px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d30;
                color: #ffffff;
                font-size: 16px;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                width: 20px;
                margin: 0.5px;
            }
            QCheckBox{
                font-size: 16px;
                color: #ffffff;
                border: 1px solid #444;
                padding: 8px;
                border-radius: 4px;
            }
        """)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
