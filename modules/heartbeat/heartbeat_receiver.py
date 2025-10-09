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
    HeartbeatReceiver class to receive heartbeats and track connection state
    """

    __private_key = object()

    @classmethod
    def create(
        cls: "type[HeartbeatReceiver]",
        connection: mavutil.mavfile,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """create heartbeat receiver"""
        if connection is None or local_logger is None:
            return False, None

        return True, HeartbeatReceiver(
            cls.__private_key, connection, disconnect_threshold, local_logger
        )

    def __init__(
        self: "HeartbeatReceiver",
        key: object,
        connection: mavutil.mavfile,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"
        self.__connection = connection
        self.__logger = local_logger
        self.__disconnect_threshold = disconnect_threshold
        self.__is_connected = True
        self.__missed_heartbeats = 0

    def run(
        self: "HeartbeatReceiver",
        timeout: float,
    ) -> "tuple[bool, str]":
        """receive heartbeat and track connection"""
        msg = self.__connection.recv_match(type="HEARTBEAT", blocking=True, timeout=timeout)

        if msg and msg.get_type() == "HEARTBEAT":
            if not self.__is_connected:
                self.__logger.info("Reconnected to drone")
                self.__is_connected = True

            self.__missed_heartbeats = 0
            return True, "Connected"

        self.__missed_heartbeats += 1

        if self.__missed_heartbeats >= self.__disconnect_threshold:
            if self.__is_connected:
                self.__logger.warning(
                    f"Disconnected: missed {self.__missed_heartbeats} " f"heartbeats"
                )
                self.__is_connected = False
            return True, "Disconnected"

        self.__logger.warning(f"Warning: missed {self.__missed_heartbeats} heartbeat(s)")
        return True, "Connected"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
