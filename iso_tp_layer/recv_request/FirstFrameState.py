from math import ceil
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
package_dir = os.path.abspath(os.path.join(package_dir, ".."))
sys.path.append(package_dir)
from iso_tp_layer.recv_request.RequestState import RequestState
from iso_tp_layer.recv_request.FinalState import FinalState
from iso_tp_layer.recv_request.ErrorState import ErrorState
from iso_tp_layer.recv_request.ConsecutiveFrameState import ConsecutiveFrameState
from iso_tp_layer.frames.FrameType import FrameType
from iso_tp_layer.Exceptions import (
    MessageSizeExceededException,
    ConsecutiveFrameOutOfSequenceException,
    UnexpectedFrameTypeException,
)
from logger import LogType


class FirstFrameState(RequestState):
    def handle(self, request, message):
        try:
            if message.frameType == FrameType.ConsecutiveFrame:
                request.logger.log_message(
                    log_type=LogType.RECEIVE,
                    message=f"[RecvRequest-{request._id}] Received {message}"
                )
                if message.sequenceNumber == request.get_expected_sequence_number():
                    request.reset_timeout_timer()
                    request.start_timeout_timer()
                    request.set_expected_sequence_number((message.sequenceNumber + 1) % 16)
                    message_length = ceil(len(message.data) / 8)
                    if (request.get_current_data_length() + message_length) > request.get_data_length():
                        #  f"Message received larger than expected! Expected size is {expected_size}, received {received_size}"
                        # raise MessageSizeExceededException(request.get_data_length(),
                        #                                    request.get_current_data_length() + message_length)
                        request.append_bits(message.data[
                                            :request.get_current_data_length() + message_length - request.get_data_length() + 1])
                        # request.set_data_length(message.dataLength)
                    else:
                        request.append_bits(message.data)
                        # request.set_data_length(message.dataLength)
                    if request.get_current_data_length() >= request.get_data_length():
                        request.set_state(FinalState())
                        try:
                            request.on_success(request.get_message(), request.get_address())
                        except Exception as e:
                            pass
                    else:
                        request.set_state(ConsecutiveFrameState())

                    # request.set_expected_sequence_number((message.sequenceNumber + 1) % 16)
                    # request.append_bits(message.data)
                    # request.set_state(ConsecutiveFrameState())
                    # request.reset_timeout_timer()
                    # request.start_timeout_timer()
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
