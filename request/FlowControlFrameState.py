from RequestState import RequestState
from frames.FrameType import FrameType
from request.ErrorState import ErrorState
from frames.FlowStatus import FlowStatus
from request.WaitState import WaitState
from request.ConsecutiveFrameState import ConsecutiveFrameState


class FlowControlFrameState(RequestState):
    def handle(self, request, message):
        if message.frameType == FrameType.ConsecutiveFrame:
            if message.sequenceNumber == request.get_expected_sequence_number():
                request.set_expected_sequence_number((message.sequenceNumber + 1) % 16)
                request.append_bits(message.data)
                request.set_state(ConsecutiveFrameState())
            else:
                request.set_state(ErrorState())
        elif message.frameType == FrameType.FlowControlFrame:
            if message.flowStatus == FlowStatus.Wait:
                request.set_state(WaitState(separationTime=message.separationTime))
            elif message.flowStatus == FlowStatus.Continue:
                pass
            else:
                request.set_state(ErrorState())
        else:
            request.set_state(ErrorState())
