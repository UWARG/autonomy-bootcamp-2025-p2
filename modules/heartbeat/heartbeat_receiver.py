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
        disconnect: int,
        local_logger: logger.Logger,
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        return True, HeartbeatReceiver(cls.__private_key, connection, disconnect, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        disconnect: int,
        local_logger: logger.Logger,  # Put your own arguments here
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__disconnect = disconnect
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
            type="HEARTBEAT", blocking=False, timeout=self.__disconnect
        )

        connected = message is not None

        if not connected:
            self.__logger.warning("Drone is disconnected", True)
        else:
            self.__logger.info("Heartbeat received", True)

        return True, connected


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
