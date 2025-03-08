import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont
from PyQt5.QtCore import Qt
from .servers_management_page import ServersManagementPage
from ..Minor.minor_services_page import MinorServicesPage
from ..Major.major_services_page import MajorServicesPage
from ..Logs.exception_handling_page import ExceptionHandlingPage
from ..Logs.per_server_log_page import PerServerLogPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-page UDS Client GUI")
        self.setGeometry(100, 100, 1200, 800)
        self._create_pages()
        self._set_emoji_icon("🖥")
        self._create_navigation()
        self._apply_styles()

    def _set_emoji_icon(self, emoji):
        """Creates a QIcon from an emoji and sets it as the window icon."""
        # Create a pixmap with transparent background
        size = 64  # Adjust the size as needed
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        # Draw the emoji on the pixmap
        painter = QPainter(pixmap)
        font = QFont("Segoe UI Emoji", int(size * 0.5))
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
        painter.end()

        self.setWindowIcon(QIcon(pixmap))

    def _create_pages(self):
        self.servers_management_page = ServersManagementPage()
        self.pages = {
            "Servers Management": self.servers_management_page,
            "Minor Services": MinorServicesPage(
                self.servers_management_page.client,
                self.servers_management_page.server_table
            ),
            "Major Services": MajorServicesPage(
                self.servers_management_page.client,
                self.servers_management_page.server_table
            ),
            # "Error Log": ExceptionHandlingPage(),
            # "Communication Log": PerServerLogPage()
        }

        self.stacked_widget = QStackedWidget()
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

    def _create_navigation(self):
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
