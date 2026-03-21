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
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        if disconnect_threshold < 1:
            local_logger.error("disconnect_threshold must be at least 1", True)
            return False, None

        return True, HeartbeatReceiver(
            cls.__private_key,
            connection,
            disconnect_threshold,
            local_logger,
        )

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> None:

        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.__connection = connection
        self.__local_logger = local_logger
        self.__disconnect_threshold = disconnect_threshold
        self.__missed_heartbeats = 0
        self.__connected = False

    def run(
        self,
    ) -> str:
        """
        Attempt to receive a heartbeat and return the current connection state.
        """

        heartbeat_msg = self.__connection.recv_match(
            type="HEARTBEAT",
            blocking=True,
            timeout=1.0,
        )

        # we check if the heart_msg is still recieving data
        if heartbeat_msg is not None:
            self.__missed_heartbeats = 0
            self.__connected = True
            return "Connected"

        # we asume data was not received this cycle
        self.__missed_heartbeats += 1
        self.__local_logger.warning(
            f"A heartbeat was missed, so far {self.__missed_heartbeats} times in a row",
            True,
        )

        if self.__missed_heartbeats >= self.__disconnect_threshold:
            self.__connected = False

        if self.__connected:
            return "Connected"
        return "Disconnected"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
