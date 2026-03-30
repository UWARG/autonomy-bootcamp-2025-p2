"""
Heartbeat sending logic.
"""

from pymavlink import mavutil
from ..common.modules.logger.logger import Logger


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
        cls, connection: mavutil.mavfile, logger: Logger  # Put your own arguments here
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        try:
            instance = cls(cls.__private_key, connection, logger)  # add args here

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to create HeartbeatSender instance: " + str(e))
            return False, None
        logger.debug("HeartbeatSender instance created", True)
        return True, instance

        # Create a HeartbeatSender object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        logger: Logger,  # Put your own arguments here
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        self.connection = connection
        self.logger = logger

        # Do any intializiation here

    def run(self) -> None:  # Put your own arguments here
        """
        Attempt to send a heartbeat message.
        """

        self.connection.mav.heartbeat_send(
            type=mavutil.mavlink.MAV_TYPE_GCS,
            autopilot=mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            base_mode=mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            custom_mode=0,
            system_status=mavutil.mavlink.MAV_STATE_ACTIVE,
            mavlink_version=3,
        )

        self.logger.debug("MAVLink Heartbeat Sent", True)

        # Send a heartbeat message


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
