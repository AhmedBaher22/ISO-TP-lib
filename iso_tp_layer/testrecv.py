import time

from bitarray import bitarray
from RecvRequest import RecvRequest
from Address import Address
from FrameMessage import FrameMessage
from SingleFrameMessage import SingleFrameMessage
from FirstFrameMessage import FirstFrameMessage
from ConsecutiveFrameMessage import ConsecutiveFrameMessage


# Success and error callbacks
def on_success():
    print("✅ Transmission successful!")


def on_error(error):
    print(f"❌ Transmission failed: {error}")


def send_frame(address: Address, frame: FrameMessage):
    print(frame)


def main():
    address = Address(addressing_mode=0x00, txid=0x123, rxid=0x456)  # Replace 0x00 with the appropriate mode
    # Create an address object (assuming Address takes an address string as input)
    # address = Address("0x1234")

    # Initialize the Request object with the address
    request1 = RecvRequest(address, 0, 0, 0, on_success, on_error, send_frame)

    # Test InitialState with a SingleFrame
    print("\n--- Testing InitialState with SingleFrame ---")
    single_frame = SingleFrameMessage(data=bitarray("1010"), dataLength=4)
    request1.process(single_frame)
    print(request1.get_state())

    request1.process(single_frame)
    print(request1.get_state())


    # Initialize the Request object with the address
    request11 = RecvRequest(address, 0, 0, 0, on_success, on_error, send_frame)

    # Test InitialState with a SingleFrame
    print("\n--- Testing InitialState with Wrong ---")
    consecutive_frame = ConsecutiveFrameMessage(data=bitarray("1010"), sequenceNumber=1)
    request11.process(consecutive_frame)
    print(request11.get_state())

    # Test InitialState with First and Consecutive Frames
    request2 = RecvRequest(address=address, block_size=0, timeout=50, stmin=3, on_success=on_success, on_error=on_error, send_frame=send_frame)
    print("\n--- Testing InitialState with First and Consecutive Frames ---")
    first_frame = FirstFrameMessage(data=bitarray("1010"), dataLength=4)
    request2.process(first_frame)
    print(request2.get_state())
    consecutive_frame_1 = ConsecutiveFrameMessage(data=bitarray("1010"), sequenceNumber=1)
    request2.process(consecutive_frame_1)
    time.sleep(0.01)
    request2.process(consecutive_frame_1)
    print(request2.get_state())
    consecutive_frame_2 = ConsecutiveFrameMessage(data=bitarray("1111"), sequenceNumber=2)
    request2.process(consecutive_frame_2)
    print(request2.get_state())


    # # Initialize the Request object with the address
    # request3 = Request(address, 0, 0, 0)
    #
    # # Test InitialState with a SingleFrame
    # print("\n--- Testing InitialState with SingleFrame ---")
    # consecutive_frame_3 = ConsecutiveFrameMessage(data=bitarray("1010"), sequenceNumber=0)
    # request3.process(consecutive_frame_3)
    # print(request3.get_state())


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
