from iso_tp_layer.recv_request.RequestState import RequestState


class ErrorState(RequestState):
    def handle(self, request, message):
        pass
