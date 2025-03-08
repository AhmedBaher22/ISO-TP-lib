from PyQt5.QtWidgets import QWidget, QVBoxLayout
from uds_layer.uds_client import UdsClient
from .flash_page import FlashPage
from ..Logs.global_log_page import GlobalLogPage


class MajorServicesPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
        super().__init__(parent)
        self.client = client
        self.server_table = server_table
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout()

        # Flash Page
        self.flash_page = FlashPage(self.client, self.server_table)
        layout.addWidget(self.flash_page)

        # Add Global Log Page
        self.global_log = GlobalLogPage()
        layout.addWidget(self.global_log)

        self.setLayout(layout)
