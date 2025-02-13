import os
from typing import Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QComboBox, QCheckBox, QProgressBar
)
from PyQt5.QtCore import Qt
from uds_layer.uds_client import UdsClient
from uds_layer.transfer_enums import EncryptionMethod, CompressionMethod


class FlashPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self.firmware_data: Optional[bytearray] = None
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
        self.address_input.setPlaceholderText(
            "Enter Memory Address (hex), e.g. 0x1000")
        layout.addWidget(QLabel("Memory Address:"))
        layout.addWidget(self.address_input)

        # Encryption method combo
        self.encryption_combo = QComboBox()
        for method in EncryptionMethod:
            self.encryption_combo.addItem(method.name, method)
        layout.addWidget(QLabel("Encryption Method:"))
        layout.addWidget(self.encryption_combo)

        # Compression method combo
        self.compression_combo = QComboBox()
        for method in CompressionMethod:
            self.compression_combo.addItem(method.name, method)
        layout.addWidget(QLabel("Compression Method:"))
        layout.addWidget(self.compression_combo)

        # Checksum required?
        self.checksum_checkbox = QCheckBox("Checksum Required")
        layout.addWidget(self.checksum_checkbox)

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
            self, "Select Firmware File", "", "SREC Files (*.srec);;All Files (*)", options=options
        )
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

        # Retrieve selected server
        selected_row = self.server_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, "Warning", "Please select a server from the server table.")
            return

        try:
            server_text = self.server_table.item(selected_row, 0).text()
            recv_DA = int(server_text.split()[1], 16)
        except Exception:
            QMessageBox.critical(
                self, "Error", "Failed to parse server ID from the table.")
            return

        # Parse memory address
        address_str = self.address_input.text().strip()
        if not address_str.startswith("0x"):
            QMessageBox.critical(
                self, "Error", "Memory Address must be in hexadecimal format (e.g., 0x1000)."
            )
            return
        try:
            memory_address = bytearray.fromhex(address_str[2:])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid Memory Address: {e}")
            return

        encryption_method = self.encryption_combo.currentData()
        compression_method = self.compression_combo.currentData()
        checksum_required = self.checksum_checkbox.isChecked()

        # Attempt to flash
        try:
            self.progress_bar.setValue(0)
            self.client.transfer_NEW_data_to_ecu(
                recv_DA=recv_DA,
                data=self.firmware_data,
                encryption_method=encryption_method,
                compression_method=compression_method,
                memory_address=memory_address,
                checksum_required=checksum_required
            )
            self.progress_bar.setValue(100)
            QMessageBox.information(
                self, "Flash Completed", "Firmware flash operation completed successfully."
            )
        except Exception as e:
            QMessageBox.critical(self, "Flash Error",
                                 f"An error occurred: {e}")
