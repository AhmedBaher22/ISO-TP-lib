from iso_tp_layer.frames.FirstFrameMessage import FirstFrameMessage
from iso_tp_layer.frames.ConsecutiveFrameMessage import ConsecutiveFrameMessage
from iso_tp_layer.frames.FlowStatus import FlowStatus
from iso_tp_layer.frames.SingleFrameMessage import SingleFrameMessage
from iso_tp_layer.frames.FlowControlFrameMessage import FlowControlFrameMessage
from iso_tp_layer.frames.ErrorFrameMessage import ErrorFrameMessage
from bitarray import bitarray


# FirstFrameMessage test
first_frame = FirstFrameMessage(dataLength=5, data=bitarray('101010'))
print(f"FirstFrameMessage: {first_frame}")
print(f"FirstFrameMessage: {first_frame.frameType}")

# ConsecutiveFrameMessage test
consecutive_frame = ConsecutiveFrameMessage(sequenceNumber=10, data=bitarray('101101'))
print(f"ConsecutiveFrameMessage: {consecutive_frame}")
print(f"ConsecutiveFrameMessage: {consecutive_frame.frameType}")

# SingleFrameMessage test
single_frame = SingleFrameMessage(dataLength=8, data=bitarray('110110'))
print(f"SingleFrameMessage: {single_frame}")
print(f"SingleFrameMessage: {single_frame.frameType}")

# FlowControlFrameMessage test
flow_control_frame = FlowControlFrameMessage(flowStatus=FlowStatus.Continue, blockSize=5, separationTime=2)
print(f"FlowControlFrameMessage: {flow_control_frame}")
print(f"FlowControlFrameMessage: {flow_control_frame.frameType}")

# ErrorFrameMessage test
error_frame = ErrorFrameMessage(serviceId=15, errorCode=3)
print(f"ErrorFrameMessage: {error_frame}")
print(f"ErrorFrameMessage: {error_frame.frameType}")

# FirstFrameMessage test
first_frame = FirstFrameMessage(dataLength=5, data=bitarray('101010'))
print(f"FirstFrameMessage: {first_frame}")
print(f"FirstFrameMessage: {first_frame.frameType}")

# ConsecutiveFrameMessage test
consecutive_frame = ConsecutiveFrameMessage(sequenceNumber=10, data=bitarray('101101'))
print(f"ConsecutiveFrameMessage: {consecutive_frame}")
print(f"ConsecutiveFrameMessage: {consecutive_frame.frameType}")

# SingleFrameMessage test
single_frame = SingleFrameMessage(dataLength=8, data=bitarray('110110'))
print(f"SingleFrameMessage: {single_frame}")
print(f"SingleFrameMessage: {single_frame.frameType}")

# FlowControlFrameMessage test
flow_control_frame = FlowControlFrameMessage(flowStatus=1, blockSize=5, separationTime=2)
print(f"FlowControlFrameMessage: {flow_control_frame}")
print(f"FlowControlFrameMessage: {flow_control_frame.frameType}")

# ErrorFrameMessage test
error_frame = ErrorFrameMessage(serviceId=15, errorCode=3)
print(f"ErrorFrameMessage: {error_frame}")
print(f"ErrorFrameMessage: {error_frame.frameType}")
