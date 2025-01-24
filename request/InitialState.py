from RequestState import RequestState


class InitialState(RequestState):
    def handle(self, request):
        request.append_bits("111")
        print("request is in the initial state.")
