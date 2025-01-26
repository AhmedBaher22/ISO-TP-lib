from RequestState import RequestState
from iso_tp_layer.frames.FrameType import FrameType
from iso_tp_layer.Exceptions import InvalidFirstFrameException
from iso_tp_layer.recv_request.FinalState import FinalState
from iso_tp_layer.recv_request.FirstFrameState import FirstFrameState
from iso_tp_layer.recv_request.ErrorState import ErrorState


class InitialState(RequestState):
    def handle(self, request, message):
        try:
            if message.frameType == FrameType.SingleFrame:
                request.set_data_length(message.dataLength)
                request.append_bits(message._data)
                request.set_state(FinalState())
                request._on_success()
            elif message.frameType == FrameType.FirstFrame:
                request.set_data_length(message.dataLength)
                request.append_bits(message._data)

                request.send_flow_control_frame()

                request.update_last_received_time()
                request.set_state(FirstFrameState())
            else:
                raise InvalidFirstFrameException(message.frameType)
        except Exception as e:
            request.set_state(ErrorState())
            request.send_error_frame()
            request._on_error(e)
