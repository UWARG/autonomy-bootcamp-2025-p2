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
        local_logger: logger.Logger,
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        if connection is None:
            local_logger.error("Connection is None", True)
            return False, None

        return True, HeartbeatReceiver(cls.__private_key, connection, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,  # Put your own arguments here
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.__connection = connection
        self.__logger = local_logger

        self.__is_connected = False
        self.__missed_heartbeats = 0
        self.__disconnect_threshold = 5

    def run(self) -> "tuple[bool, str]":
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = self.__connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1)

        if msg is not None:
            self.__logger.debug("Heartbeat Received", True)

            self.__missed_heartbeats = 0

            if not self.__is_connected:
                self.__is_connected = True
                self.__logger.info("Connected to Drone", True)
        else:
            self.__missed_heartbeats += 1
            self.__logger.warning(f"Missed Heartbeat ({self.__missed_heartbeats})", True)

            if self.__missed_heartbeats >= self.__disconnect_threshold:
                self.__is_connected = False
                self.__logger.error("Disconnected from Drone", True)

        if self.__is_connected:
            status = "Connected"
        else:
            status = "Disconnected"

        return True, status


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
