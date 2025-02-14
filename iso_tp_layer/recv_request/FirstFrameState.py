import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.recv_request.RequestState import RequestState
from iso_tp_layer.recv_request.ConsecutiveFrameState import ConsecutiveFrameState
from iso_tp_layer.recv_request.ErrorState import ErrorState
from iso_tp_layer.Exceptions import ConsecutiveFrameOutOfSequenceException, UnexpectedFrameTypeException
from iso_tp_layer.frames.FrameType import FrameType



class FirstFrameState(RequestState):
    def handle(self, request, message):
        try:
            if message.frameType == FrameType.ConsecutiveFrame:
                if message.sequenceNumber == request.get_expected_sequence_number():
                    request.set_expected_sequence_number((message.sequenceNumber + 1) % 16)
                    request.append_bits(message.data)
                    request.set_state(ConsecutiveFrameState())
                    request.reset_timeout_timer()
                    request.start_timeout_timer()
                else:
                    raise ConsecutiveFrameOutOfSequenceException(request.get_expected_sequence_number(),
                                                                 message.sequenceNumber)

            else:
                # f"Was expecting {expected_type} and received {received_type}"
                raise UnexpectedFrameTypeException("FrameType.ConsecutiveFrame", message.frameType)


        except Exception as e:
            request.set_state(ErrorState())
            request.send_error_frame(e)
            request.on_error(e)
