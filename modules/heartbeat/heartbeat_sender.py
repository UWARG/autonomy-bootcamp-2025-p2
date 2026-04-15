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
        cls, connection: mavutil.mavfile, local_logger: logger.Logger
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        try:
            return (True, cls(cls.__private_key, connection, local_logger))
        except (OSError, TypeError, AttributeError) as e:
            local_logger.error(f"Error when creating heartbeat sender: {e}", True)
            return (False, None)
        # Create a HeartbeatSender object

    def __init__(
        self, key: object, connection: mavutil.mavfile, local_logger: logger.Logger
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        self._connection = connection
        self._logger = local_logger

    def run(self) -> bool:
        """
        Attempt to send a heartbeat message.
        """
        try:
            self._connection.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0
            )
            return True
        except (OSError, TypeError, AttributeError) as e:
            self._logger.error(f"Error while sending a heartbeat: {e}", True)
            return False
        # Send a heartbeat message


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
