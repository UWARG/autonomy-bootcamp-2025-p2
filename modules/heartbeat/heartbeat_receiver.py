"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil

from ..common.modules.logger import logger  # pylint: disable=unused-import


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatReceiver:
    """
    HeartbeatReceiver class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls, connection: mavutil.mavfile
    ) -> tuple[bool, HeartbeatReceiver]:  # pylint: disable=undefined-variable
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        return True, cls(cls.__private_key, connection)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,  # Put your own arguments here
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection

    def run(self) -> str:  # Put your own arguments here
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        message = self.connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1)
        return message


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
