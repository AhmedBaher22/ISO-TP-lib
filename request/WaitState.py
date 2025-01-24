from RequestState import RequestState
from frames.FrameType import FrameType
from datetime import datetime, timedelta


class WaitState(RequestState):
    def __init__(self, separationTime: int):
        """
        Initialize WaitState with a wait duration.

        :param separationTime: The amount of time to wait in milliseconds.
        """
        self.start_time = datetime.now()  # Record the start time
        self.separationTime = timedelta(milliseconds=separationTime)  # Wait duration

    def has_time_passed(self) -> bool:
        """
        Check if the wait duration has passed.

        :return: True if the wait time has elapsed, otherwise False.
        """
        return datetime.now() >= self.start_time + self.separationTime

    def handle(self, request, message):
        """
        Handle the request. Only proceed if the wait time has passed.

        :param request: The Request object.
        :param message: The message to process.
        """
        if not self.has_time_passed():
            print("Wait time has not elapsed yet. Waiting...")
            return

        print("Wait time elapsed. Proceeding with handling the message.")
        # Handle the message and update the request as needed
        # Example:
        # request.message.append(message)
