import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.Exceptions import InvalidFirstFrameException
from iso_tp_layer.frames.FrameType import FrameType
from iso_tp_layer.recv_request.FinalState import FinalState
from iso_tp_layer.recv_request.FirstFrameState import FirstFrameState
from iso_tp_layer.recv_request.ErrorState import ErrorState
from iso_tp_layer.recv_request.RequestState import RequestState


class InitialState(RequestState):
    def handle(self, request, message):
        try:
            if message.frameType == FrameType.SingleFrame:
                request.set_data_length(message.dataLength)
                request.append_bits(message.data)
                request.set_state(FinalState())
                try:
                    request.on_success(request.get_message(), request.get_address())
                except Exception as e:
                    pass
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
            request.send_error_frame(e)
            request.on_error(e)
