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
    ) -> "tuple[bool, HeartbeatReceiver] | tuple[bool, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        if connection is None:
            return False, None
        return True, HeartbeatReceiver(cls.__private_key, connection, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__local_logger = local_logger
        self.__missed_count = 0
        self.__is_connected = False

    def run(
        self,
    ) -> "tuple[bool, str]":
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = self.__connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1)

        if msg is not None:
            self.__missed_count = 0
            self.__is_connected = True
            self.__local_logger.info("Heartbeat received", True)
        else:
            self.__missed_count += 1
            self.__local_logger.warning(f"Missed heartbeat ({self.__missed_count})", True)
            if self.__missed_count >= 5:
                self.__is_connected = False

        state = "Connected" if self.__is_connected else "Disconnected"
        return True, state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
