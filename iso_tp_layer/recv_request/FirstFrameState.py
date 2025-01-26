from RequestState import RequestState
from iso_tp_layer.frames.FrameType import FrameType
from iso_tp_layer.recv_request.ConsecutiveFrameState import ConsecutiveFrameState
from iso_tp_layer.recv_request.ErrorState import ErrorState

from iso_tp_layer.Exceptions import ConsecutiveFrameOutOfSequenceException, UnexpectedFrameTypeException


class FirstFrameState(RequestState):
    def handle(self, request, message):
        try:
            if message.frameType == FrameType.ConsecutiveFrame:
                if not request.check_stmin():
                    return
                if message.sequenceNumber == request.get_expected_sequence_number():
                    request.set_expected_sequence_number((message.sequenceNumber + 1) % 16)
                    request.append_bits(message._data)
                    request.set_state(ConsecutiveFrameState())
                else:
                    raise ConsecutiveFrameOutOfSequenceException(request.get_expected_sequence_number(),
                                                                 message.sequenceNumber)

            else:
                raise UnexpectedFrameTypeException("FrameType.ConsecutiveFrame", message.frameType)


        except Exception as e:
            request.set_state(ErrorState())
            request.send_error_frame()
            request._on_error(e)
