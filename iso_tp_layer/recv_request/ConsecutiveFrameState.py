from math import ceil
from RequestState import RequestState
from iso_tp_layer.frames.FrameType import FrameType
from iso_tp_layer.recv_request.ErrorState import ErrorState
from iso_tp_layer.Exceptions import ConsecutiveFrameBeforeFlowControlException, MessageSizeExceededException, \
    ConsecutiveFrameOutOfSequenceException, UnexpectedFrameTypeException
from iso_tp_layer.recv_request.FinalState import FinalState


class ConsecutiveFrameState(RequestState):
    def handle(self, request, message):
        try:
            if message.frameType == FrameType.ConsecutiveFrame:
                if not request.check_stmin():
                    return
                if message.sequenceNumber == request.get_expected_sequence_number():
                    max_block_size = request.get_max_block_size()
                    current_block_size = request.get_current_block_size()
                    if max_block_size > 0:
                        if current_block_size < max_block_size:
                            current_block_size = request.get_current_block_size()
                            current_block_size += 1
                            request.set_current_block_size(current_block_size)

                            if current_block_size == max_block_size:
                                request.send_flow_control_frame()

                                request.set_current_block_size(0)
                            request.update_last_received_time()
                        else:
                            raise ConsecutiveFrameBeforeFlowControlException()

                    request.set_expected_sequence_number((message.sequenceNumber + 1) % 16)
                    message_length = ceil(len(message._data) / 8)
                    if (request.get_current_data_length() + message_length) > request.get_data_length():
                        raise MessageSizeExceededException(request.get_data_length(),
                                                           request.get_current_data_length() + message_length)

                    request.append_bits(message._data)
                    if request.get_current_data_length() == request.get_data_length():
                        request.set_state(FinalState())
                        request._on_success()
                else:
                    raise ConsecutiveFrameOutOfSequenceException(request.get_expected_sequence_number(),
                                                                 message.sequenceNumber)
            else:
                raise UnexpectedFrameTypeException("FrameType.ConsecutiveFrame", message.frameType)

        except Exception as e:
            request.set_state(ErrorState())
            request.send_error_frame()
            request._on_error(e)
