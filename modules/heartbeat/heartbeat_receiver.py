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
        Fallible create (instantiation) method to create a HeartbeatReceiver object.
        """
        if connection is None:
            local_logger.error("Failed to create HeartbeatReceiver: connection is None", True)
            return False, None

        instance = cls(cls.__private_key, connection, local_logger)
        return True, instance

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"
        self.__connection = connection
        self.__logger = local_logger
        self.__is_connected = False
        self.__missed_count = 0

    def run(self) -> "tuple[bool, str]":
        """
        Attempt to receive a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        try:
            # Block for up to 1.0 second waiting for a HEARTBEAT
            msg = self.__connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1.0)

            if msg is not None and msg.get_type() == "HEARTBEAT":
                self.__is_connected = True
                self.__missed_count = 0
            else:
                self.__missed_count += 1
                self.__logger.warning(
                    f"Missed heartbeat! Consecutive missed: {self.__missed_count}", True
                )
                if self.__missed_count >= 5:
                    if self.__is_connected:
                        self.__logger.warning(
                            "Disconnected from drone after 5 missed heartbeats", True
                        )
                    self.__is_connected = False

            state = "Connected" if self.__is_connected else "Disconnected"
            return True, state

        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            self.__logger.error(f"Error receiving heartbeat: {e}", True)
            return False, "Disconnected"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
