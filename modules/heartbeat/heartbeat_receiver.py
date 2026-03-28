"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil

from ..common.modules.logger import logger


DISCONNECT_THRESHOLD = 5


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
        return True, HeartbeatReceiver(cls.__private_key, connection, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.connection = connection
        self.local_logger = local_logger
        self.missed_count = 0
        self.connected = False

    def run(self) -> "tuple[bool, str]":
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = self.connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1.0)

        if msg and msg.get_type() == "HEARTBEAT":
            self.missed_count = 0
            self.connected = True
            self.local_logger.info("Received heartbeat")
        else:
            self.missed_count += 1
            self.local_logger.warning(f"Missed heartbeat ({self.missed_count})")
            if self.missed_count >= DISCONNECT_THRESHOLD:
                self.connected = False

        state = "Connected" if self.connected else "Disconnected"
        return True, state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
