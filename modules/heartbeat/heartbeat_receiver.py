"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil

from ..common.modules.logger import logger


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
        cls,
        connection: mavutil.mavfile,
        heartbeat_period: float,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        return True, HeartbeatReceiver(
            cls.__private_key, connection, heartbeat_period, disconnect_threshold, local_logger
        )

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        heartbeat_period: float,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.__connection = connection
        self.__heartbeat_period = heartbeat_period
        self.__disconnect_threshold = disconnect_threshold
        self.__missed = 0
        self.__logger = local_logger

    def run(
        self,
    ) -> "tuple[bool, bool]":
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        message = self.__connection.recv_match(
            type="HEARTBEAT", blocking=True, timeout=self.__heartbeat_period
        )

        if message is not None:
            self.__missed = 0
            self.__logger.info("Heartbeat received", True)
            return True, True

        self.__missed += 1
        is_connected = self.__missed < self.__disconnect_threshold

        if not is_connected:
            self.__logger.warning("Drone is disconnected", True)

        return True, is_connected


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
