"""
Heartbeat sending logic.
"""

from pymavlink import mavutil
from ..common.modules.logger import logger


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
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Fallible create (instantiation) method to create a HeartbeatSender object.
        """
        if connection is None:
            local_logger.error("Failed to create HeartbeatSender: connection is None", True)
            return False, None

        instance = cls(cls.__private_key, connection, local_logger)
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
        Attempt to send a heartbeat message. Returns True on success, False on error.
        """
        try:
            self.__connection.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                0,
                0,
                0,
            )
            return True
        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            # Log the error using the logger class
            self.__logger.error(f"Failed to send MAVLink heartbeat: {e}", True)
            return False
