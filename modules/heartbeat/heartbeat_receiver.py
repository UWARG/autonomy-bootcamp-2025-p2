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
        self._connection = connection
        self._local_logger = local_logger
        self._missed_count = 0
        self._is_connected = False

    def run(
        self,
    ) -> "tuple[bool, str]":
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = self._connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1)

        if msg is not None:
            self._missed_count = 0
            self._is_connected = True
            self._local_logger.info("Heartbeat received", True)
        else:
            self._missed_count += 1
            self._local_logger.warning(f"Missed heartbeat ({self._missed_count})", True)
            if self._missed_count >= 5:
                self._is_connected = False

        state = "Connected" if self._is_connected else "Disconnected"
        return True, state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
