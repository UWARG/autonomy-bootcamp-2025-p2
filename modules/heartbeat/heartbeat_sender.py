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
        local_logger: logger.Logger,
    ) -> "tuple[bool, HeartbeatSender | None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        try:
            instance = HeartbeatSender(cls.__private_key, connection, local_logger)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Failed to create HeartbeatSender: {exc}", True)
            return False, None
        return True, instance

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        self.__connection = connection
        self.__logger = local_logger

    def run(self) -> bool:
        """
        Attempt to send a heartbeat message.
        """
        try:
            self.__connection.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                0,
                0,
                0,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.__logger.error(f"Failed to send heartbeat: {exc}", True)
            return False

        self.__logger.info("Sent heartbeat", True)
        return True


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
