from .live_log_page import LiveLogPage


class PerServerLogPage(LiveLogPage):
    def __init__(self, log_file="logs/uds/communication.log", parent=None, update_interval=1000):
        title = "Server Communication Log"
        placeholder_text = "Communication Logs will appear here..."
        super().__init__(title, log_file, placeholder_text, parent, update_interval)
