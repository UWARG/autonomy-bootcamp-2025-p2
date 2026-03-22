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
    HeartbeatReceiver class to receive heartbeats and report connection state.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        args: tuple,  # Put your own arguments here (disconnect_threshold,)
        local_logger: logger.Logger,
    ) -> "tuple[bool, HeartbeatReceiver | None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        return True, cls(cls.__private_key, connection, args, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        args: tuple,  # Put your own arguments here (disconnect_threshold,)
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"
        self._connection = connection
        self._logger = local_logger
        self._disconnect_threshold = args[0] if args else 5
        self._state = "Disconnected"
        self._missed_count = 0

    def run(
        self,
        _args: tuple,  # Put your own arguments here (unused)
    ) -> str:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        try:
            msg = self._connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.error(f"Heartbeat receive error: {e}", True)
            self._missed_count += 1
            if self._missed_count >= 1:
                self._logger.warning("Missed heartbeat", True)
            if self._missed_count >= self._disconnect_threshold:
                self._state = "Disconnected"
            return self._state

        if msg is not None and msg.get_type() == "HEARTBEAT":
            self._state = "Connected"
            self._missed_count = 0
        else:
            self._missed_count += 1
            if self._missed_count >= 1:
                self._logger.warning("Missed heartbeat", True)
            if self._missed_count >= self._disconnect_threshold:
                self._state = "Disconnected"

        return self._state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
