from .live_log_page import LiveLogPage


class ExceptionHandlingPage(LiveLogPage):
    def __init__(self, service_name="Service", log_file="logs/uds/error.log", parent=None, update_interval=1000):
        title = f"Exception Handling for {service_name}"
        placeholder_text = "Errors details will appear here..."
        super().__init__(title, log_file, placeholder_text, parent, update_interval)
