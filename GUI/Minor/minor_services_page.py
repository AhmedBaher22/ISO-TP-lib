from PyQt5.QtWidgets import QWidget, QStackedWidget, QListWidget, QHBoxLayout
from uds_layer.uds_client import UdsClient
from .read_by_identifier_page import ReadByIdentifierPage
from .write_by_identifier_page import WriteByIdentifierPage
from .ecu_reset_page import ECUResetPage
from .communication_control_page import CommunicationControlPage
from .erase_memory_page import EraseMemoryPage


class MinorServicesPage(QWidget):
    def __init__(self, client: UdsClient, server_table, parent=None):
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
