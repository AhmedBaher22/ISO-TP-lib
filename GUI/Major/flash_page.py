import os
from typing import Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QComboBox, QProgressBar, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from uds_layer.uds_client import UdsClient
from uds_layer.transfer_enums import EncryptionMethod, CompressionMethod, CheckSumMethod
from hex_parser.SRecordParser import SRecordParser, DataRecord


def parse_srec_file(filename: str) -> List[DataRecord]:
    parser = SRecordParser()
    parser.parse_file(filename)
    return parser._merged_records


class FlashPage(QWidget):
    # Signal to safely update progress on the main thread.
    progressUpdated = pyqtSignal(int)

    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self.firmware_segments: Optional[List[DataRecord]] = None
        self._init_ui()
        self.default_on_success_send = self.client.on_success_send
        self.progressUpdated.connect(self.handle_progress_updated)

    def _init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Flash (Firmware Update)")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # File selection layout.
        file_layout = QHBoxLayout()
        self.file_line_edit = QLineEdit()
        self.file_line_edit.setPlaceholderText("Select firmware file...")
        self.file_select_btn = QPushButton("Select File")
        self.file_select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_line_edit)
        file_layout.addWidget(self.file_select_btn)
        layout.addLayout(file_layout)

        # Encryption method combo.
        self.encryption_combo = QComboBox()
        for method in EncryptionMethod:
            self.encryption_combo.addItem(method.name, method)
        layout.addWidget(QLabel("Encryption Method:"))
        layout.addWidget(self.encryption_combo)

        # Compression method combo.
        self.compression_combo = QComboBox()
        for method in CompressionMethod:
            self.compression_combo.addItem(method.name, method)
        layout.addWidget(QLabel("Compression Method:"))
        layout.addWidget(self.compression_combo)

        # Checksum method combo from the CheckSumMethod enum.
        self.checksum_combo = QComboBox()
        for method in CheckSumMethod:
            self.checksum_combo.addItem(method.name, method)
        layout.addWidget(QLabel("Checksum Method:"))
        layout.addWidget(self.checksum_combo)

        # Flash button.
        self.flash_btn = QPushButton("Start Flash")
        self.flash_btn.clicked.connect(self.start_flash)
        layout.addWidget(self.flash_btn)

        # Progress bar.
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
            self.progress_bar.setValue(0)
            try:
                self.firmware_segments = parse_srec_file(filename)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to parse firmware file: {e}")
                self.firmware_segments = None

    def update_progress(self, progress: float):
        # Called from a background thread: emit a signal with the progress percentage.
        progress_value = int(progress * 100)
        self.progressUpdated.emit(progress_value)

    def handle_progress_updated(self, progress_value: int):
        self.progress_bar.setValue(progress_value)
        if progress_value >= 100:
            QMessageBox.information(
                self, "Flash Completed", "Firmware flash operation completed successfully.")
            self.client.on_success_send = self.default_on_success_send

    def start_flash(self):
        # Reset progress bar and force UI update.
        self.progress_bar.setValue(0)
        QApplication.processEvents()

        if not self.firmware_segments:
            QMessageBox.critical(
                self, "Error", "No firmware file selected or parsing failed.")
            return

        selected_row = self.server_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(
                self, "Warning", "Please select a server from the server table.")
            return

        try:
            server_text = self.server_table.item(selected_row, 0).text()
            recv_DA = int(server_text.split()[1], 16)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to parse server ID from the table: {e}")
            return

        # Optional: read memory address from a field (assuming you have self.address_input).
        address_str = getattr(self, "address_input",
                              QLineEdit()).text().strip()
        if address_str and address_str.startswith("0x"):
            try:
                memory_address = bytearray.fromhex(address_str[2:].strip())
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Invalid Memory Address: {e}")
                return
        else:
            memory_address = bytearray()

        encryption_method = self.encryption_combo.currentData()
        compression_method = self.compression_combo.currentData()
        # Get the checksum method from the combo box.
        checksum_method = self.checksum_combo.currentData()

        # Pre-convert each firmware segment's address from str to bytearray.
        converted_segments = []
        for seg in self.firmware_segments:
            try:
                conv_addr = bytearray.fromhex(seg.address)
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Invalid segment address '{seg.address}': {e}")
                return
            new_seg = DataRecord(record_type=seg.record_type, address=conv_addr,
                                 data=seg.data, data_length=seg.data_length)
            converted_segments.append(new_seg)

        self.client.on_success_send = self.update_progress
        try:
            self.client.Flash_ECU(
                segments=converted_segments,
                recv_DA=recv_DA,
                encryption_method=encryption_method,
                compression_method=compression_method,
                checksum_required=checksum_method
            )
        except Exception as e:
            QMessageBox.critical(self, "Flash Error",
                                 f"An error occurred: {e}")
            self.client.on_success_send = self.default_on_success_send
