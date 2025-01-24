from bitarray import bitarray

from Request import Request
from frames.FrameType import FrameType
from frames.FlowStatus import FlowStatus
from Address import Address
from frames.FrameMessage import FrameMessage
from frames.SingleFrameMessage import SingleFrameMessage
from frames.FirstFrameMessage import FirstFrameMessage
from frames.ConsecutiveFrameMessage import ConsecutiveFrameMessage
from recv_request.InitialState import InitialState


def main():
    address = Address(addressing_mode=0x00, txid=0x123, rxid=0x456)  # Replace 0x00 with the appropriate mode
    # Create an address object (assuming Address takes an address string as input)
    address = Address("0x1234")

    # Initialize the Request object with the address
    request1 = Request(address,0,0)

    # Test InitialState with a SingleFrame
    print("\n--- Testing InitialState with SingleFrame ---")
    single_frame = SingleFrameMessage(data=bitarray("1010"), dataLength=4)
    request1.process(single_frame)
    print(request1.get_state())

    request1.process(single_frame)
    print(request1.get_state())



    # Initialize the Request object with the address
    request2 = Request(address,0,0)

    # Test InitialState with a SingleFrame
    print("\n--- Testing InitialState with SingleFrame ---")
    first_frame = FirstFrameMessage(data=bitarray("1010"), dataLength=4)
    request2.process(first_frame)
    print(request2.get_state())
    consicative_frame1 = ConsecutiveFrameMessage(data=bitarray("1010"), sequenceNumber=1)
    request2.process(consicative_frame1)
    print(request2.get_state())
    consicative_frame2 = ConsecutiveFrameMessage(data=bitarray("1111"), sequenceNumber=2)
    request2.process(consicative_frame2)
    print(request2.get_state())
    # Initialize the Request object with the address
    request3 = Request(address,0,0)

    # Test InitialState with a SingleFrame
    print("\n--- Testing InitialState with SingleFrame ---")
    consicative_frame = ConsecutiveFrameMessage(data=bitarray("1010"), sequenceNumber=0)
    request3.process(consicative_frame)
    print(request3.get_state())
    # # Test InitialState with a FirstFrame
    # print("\n--- Testing InitialState with FirstFrame ---")
    # recv_request.set_state(InitialState())
    # first_frame = FrameMessage(frameType=FrameType.FirstFrame, data="1100")
    # recv_request.process(first_frame)
    #
    # # Test FirstFrameState with a ConsecutiveFrame
    # print("\n--- Testing FirstFrameState with ConsecutiveFrame ---")
    # consecutive_frame = FrameMessage(frameType=FrameType.ConsecutiveFrame, data="1110", sequenceNumber=0)
    # recv_request.process(consecutive_frame)
    #
    # # Test ConsecutiveFrameState with correct sequence number
    # print("\n--- Testing ConsecutiveFrameState with correct sequence number ---")
    # consecutive_frame_correct = FrameMessage(frameType=FrameType.ConsecutiveFrame, data="1111", sequenceNumber=1)
    # recv_request.process(consecutive_frame_correct)
    #
    # # Test ConsecutiveFrameState with incorrect sequence number
    # print("\n--- Testing ConsecutiveFrameState with incorrect sequence number ---")
    # consecutive_frame_incorrect = FrameMessage(frameType=FrameType.ConsecutiveFrame, data="0001", sequenceNumber=3)
    # recv_request.process(consecutive_frame_incorrect)
    #
    # # Test FlowControlFrameState with FlowControlFrame (Wait)
    # print("\n--- Testing FlowControlFrameState with FlowControlFrame (Wait) ---")
    # flow_control_wait = FrameMessage(frameType=FrameType.FlowControlFrame, flowStatus=FlowStatus.Wait, separationTime=1000)
    # recv_request.process(flow_control_wait)
    #
    # # Test WaitState handling (before time elapsed)
    # print("\n--- Testing WaitState (before time elapsed) ---")
    # recv_request.process(flow_control_wait)
    #
    # # Simulate time passage (manually for demonstration purposes)
    # import time
    # time.sleep(1.1)  # Wait for 1.1 seconds to allow time to elapse
    #
    # # Test WaitState handling (after time elapsed)
    # print("\n--- Testing WaitState (after time elapsed) ---")
    # recv_request.process(flow_control_wait)


if __name__ == "__main__":
    main()
