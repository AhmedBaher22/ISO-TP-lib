from FrameType import FrameType
from Exceptions import InvalidFirstFrameException
from FinalState import FinalState
from FirstFrameState import FirstFrameState
from ErrorState import ErrorState
from RequestState import RequestState


class InitialState(RequestState):
    def handle(self, request, message):
        try:
            if message.frameType == FrameType.SingleFrame:
                request.set_data_length(message.dataLength)
                request.append_bits(message.data)
                request.set_state(FinalState())
                request.on_success(request.get_message(),request.get_address())
            elif message.frameType == FrameType.FirstFrame:
                request.set_data_length(message.dataLength)
                request.append_bits(message.data)

                request.send_flow_control_frame()

                request.update_last_received_time()
                request.set_state(FirstFrameState())
            else:
                # f"The first frame can't be {frame_type}"
                raise InvalidFirstFrameException(message.frameType)
        except Exception as e:
            request.set_state(ErrorState())
            request.send_error_frame()
            request.on_error(e)
