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
        args: object,  # Put your own arguments here
        local_logger: logger.Logger,
    ) -> "tuple[bool, HeartbeatReceiver | None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        try:
            instance = HeartbeatReceiver(HeartbeatReceiver.__private_key, connection, args)
            return True, instance
        except Exception:  # pylint: disable=broad-except
            local_logger.error("Failed to create HeartbeatReceiver")
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        args: object,  # Put your own arguments here  # pylint: disable=unused-argument
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self._connection = connection
        self._missed = 0
        self._is_connected = False

    def run(
        self,
        period_seconds: float,
        disconnect_threshold: int,
    ) -> str:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = self._connection.recv_match(type="HEARTBEAT", blocking=True, timeout=period_seconds)
        if msg and msg.get_type() == "HEARTBEAT":
            self._missed = 0
            self._is_connected = True
        else:
            self._missed += 1
            if self._missed >= disconnect_threshold:
                self._is_connected = False
        return "Connected" if self._is_connected else "Disconnected"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
