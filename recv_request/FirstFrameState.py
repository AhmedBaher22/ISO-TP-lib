from RequestState import RequestState
from frames.FrameType import FrameType
from recv_request.ConsecutiveFrameState import ConsecutiveFrameState
from recv_request.ErrorState import ErrorState


class FirstFrameState(RequestState):
    def handle(self, request, message):
        if message.frameType == FrameType.ConsecutiveFrame:
            if message.sequenceNumber == request.get_expected_sequence_number():
                request.set_expected_sequence_number((message.sequenceNumber + 1) % 16)
                request.append_bits(message.data)
                request.set_state(ConsecutiveFrameState())
            else:
                request.set_state(ErrorState())
        else:
            request.set_state(ErrorState())
