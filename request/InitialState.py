from RequestState import RequestState
from frames.FrameType import FrameType
from request.FinalState import FinalState
from request.FirstFrameState import FirstFrameState
from request.ErrorState import ErrorState


class InitialState(RequestState):
    def handle(self, request, message):
        if message.frameType == FrameType.SingleFrame:
            request.append_bits(message.data)
            request.set_state(FinalState())
        elif message.frameType == FrameType.FirstFrame:
            request.append_bits(message.data)

            # SEND ACK

            request.set_state(FirstFrameState())
        else:
            request.set_state(ErrorState())
        print("request is in the initial state.")
