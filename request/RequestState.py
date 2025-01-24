from abc import ABC, abstractmethod


class RequestState(ABC):
    @abstractmethod
    def handle(self, request, message):
        pass
