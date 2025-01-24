from RequestState import RequestState
from frames.FrameType import FrameType
from recv_request.FinalState import FinalState
from recv_request.FirstFrameState import FirstFrameState
from recv_request.ErrorState import ErrorState


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
        print("recv_request is in the initial state.")
