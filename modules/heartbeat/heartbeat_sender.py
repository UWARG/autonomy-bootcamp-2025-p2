"""
Heartbeat sending logic.
"""

from pymavlink import mavutil
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,  # Put your own arguments here
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """

        return True, cls(
            cls.__private_key, connection, local_logger
        )  # Create a HeartbeatSender object

    def __init__(
        self, key: object, connection: mavutil.mavfile, local_logger: logger.Logger
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        # Do any intializiation here
        self.local_logger = local_logger
        self.connection = connection

    def run(self) -> "tuple[bool, None]":
        """
        Attempt to send a heartbeat message.
        """
        self.connection.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0
        )

        return True, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
