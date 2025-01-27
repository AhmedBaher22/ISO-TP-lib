import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(package_dir)
from uds_layer.uds_enums import OperationType, OperationStatus
from typing import List


class Operation:
    def __init__(self, operation_type: OperationType, message: List[int]):
        self._operation_type = operation_type
        self._status = OperationStatus.PENDING
        self._message = message

    @property
    def operation_type(self) -> OperationType:
        return self._operation_type

    @property
    def status(self) -> OperationStatus:
        return self._status

    @status.setter
    def status(self, value: OperationStatus):
        self._status = value

    @property
    def message(self) -> List[int]:
        return self._message