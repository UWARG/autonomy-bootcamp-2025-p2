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

    MISSED_THRESHOLD = 5

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        # Put your own arguments here
        local_logger: logger.Logger,
    ) -> tuple[bool, "Command | None"]:
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        return True, cls(
            cls.__private_key, connection, local_logger
        )  # Create a HeartbeatReceiver object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,  # Put your own arguments here
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.logger = local_logger

        self.consecutive_missed = 0
        self.is_connected = False

    def run(self) -> None:  # Put your own arguments here
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = self.connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1.1)

        if msg is not None:
            self.consecutive_missed = 0
            self.is_connected = True
        else:
            self.consecutive_missed += 1
            self.logger.warning(f"Missed heartbeat. Consecutive missed: {self.consecutive_missed}")

            if self.consecutive_missed >= self.MISSED_THRESHOLD:
                if self.is_connected:
                    self.logger.error("Drone communication lost: Disconnected")
                self.is_connected = False

        return "Connected" if self.is_connected else "Disconnected"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
