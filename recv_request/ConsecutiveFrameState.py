from RequestState import RequestState
from frames.FrameType import FrameType
from recv_request.ErrorState import ErrorState
from frames.FlowStatus import FlowStatus
from recv_request.WaitState import WaitState


class ConsecutiveFrameState(RequestState):
    def handle(self, request, message):
        if message.frameType == FrameType.ConsecutiveFrame:
            if message.sequenceNumber == request.get_expected_sequence_number():
                max_block_size = request.get_max_block_size()
                if max_block_size > 0:
                    current_block_size = request.get_current_block_size()
                    current_block_size += 1
                    request.set_current_block_size(current_block_size)

                    if current_block_size == max_block_size:

                        # Call send control frame Here

                        request.set_current_block_size(0)

                request.set_expected_sequence_number((message.sequenceNumber + 1) % 16)
                request.append_bits(message.data)
            else:
                request.set_state(ErrorState())
        elif message.frameType == FrameType.FlowControlFrame:
            if message.flowStatus == FlowStatus.Wait:
                request.set_state(WaitState(separationTime=message.separationTime))
            elif message.flowStatus == FlowStatus.Continue:
                request.set_state(request.FlowControlFrameState())
            else:
                request.set_state(ErrorState())
        else:
            request.set_state(ErrorState())
