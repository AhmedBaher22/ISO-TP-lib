from RequestState import RequestState
from frames.FrameType import FrameType
from recv_request.ErrorState import ErrorState
from recv_request.FinalState import FinalState
from frames.FlowStatus import FlowStatus
from recv_request.WaitState import WaitState


class ConsecutiveFrameState(RequestState):
    def handle(self, request, message):
        if message.frameType == FrameType.ConsecutiveFrame:
            if message.sequenceNumber == request.get_expected_sequence_number():
                max_block_size = request.get_max_block_size()
                current_block_size = request.get_current_block_size()
                if max_block_size > 0:
                    if current_block_size < max_block_size:
                        current_block_size = request.get_current_block_size()
                        current_block_size += 1
                        request.set_current_block_size(current_block_size)
                        
                        if current_block_size == max_block_size:

                            # Call send control frame Here

                            request.set_current_block_size(0)
                    else:
                        request.set_state(ErrorState())
                        return

                request.set_expected_sequence_number((message.sequenceNumber + 1) % 16)
                if (request.get_current_data_length()+len(message.data)) > request.get_data_length():
                    request.set_state(ErrorState())
                    return
                request.append_bits(message.data)
                request.set_current_data_length()
                if request.get_current_data_length() == request.get_data_length():
                    request.set_state(FinalState())
            else:
                request.set_state(ErrorState())
        else:
            request.set_state(ErrorState())
