import time


class CANStatistics:
    def __init__(self):
        self.tx_count = 0
        self.rx_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.last_error_time = None
        self.bus_load = 0.0
        self.peak_bus_load = 0.0
        self.error_frames = 0
        self.last_message_timestamp = None
        self.total_bytes_transferred = 0

    def update_bus_load(self, load: float):
        self.bus_load = load
        self.peak_bus_load = max(self.peak_bus_load, load)

    def get_statistics_dict(self):
        return {
            'tx_count': self.tx_count,
            'rx_count': self.rx_count,
            'error_count': self.error_count,
            'uptime': time.time() - self.start_time,
            'bus_load': self.bus_load,
            'peak_bus_load': self.peak_bus_load,
            'error_frames': self.error_frames,
            'total_bytes': self.total_bytes_transferred
        }
