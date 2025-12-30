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
        _connection: mavutil.mavfile,
        disconnect_threshold: int,
        local_logger: logger.Logger,
        # Put your own arguments here
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        if _connection is None:
            return False, None

        if disconnect_threshold <= 0:
            if local_logger is not None:
                local_logger.error("disconnect_threshold must be > 0", True)
            return False, None

        try:
            # Create an instance using the private key
            instance = cls(cls.__private_key, _connection, disconnect_threshold)
            return True, instance
        except Exception:
            # fail safely
            return False, None

    def __init__(
        self,
        key: object,
        _connection: mavutil.mavfile,
        disconnect_threshold: int,
        # Put your own arguments here
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"
        self._connection = _connection
        self.disconnect_threshold = disconnect_threshold
        self.missed_periods = 0
        self.is_connected = True

    def run(
        self,
        timeout_s: float,  # Put your own arguments here
    ) -> tuple[bool, bool]:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        try:
            # Send the heartbeat message over the connection
            msg = self._connection.recv_match(
                type="HEARTBEAT",
                blocking=True,
                timeout=timeout_s,
            )

        except Exception:
            msg = None

        if msg is not None and msg.get_type() == "HEARTBEAT":
            self.missed_periods = 0
            self.is_connected = True
            return True, True

        self.missed_periods += 1

        if self.missed_periods >= self.disconnect_threshold:
            self.is_connected = False

        return False, self.is_connected


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
