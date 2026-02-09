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
        period: float,
        local_logger: logger.Logger,
    ) -> tuple[bool, "HeartbeatReceiver | None"]:
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        if period <= 0:
            return (False, None)

        return (True, cls(cls.__private_key, connection, period, local_logger))

    def __init__(
        self, key: object, connection: mavutil.mavfile, period: float, local_logger: logger.Logger
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.period = period
        self.local_logger = local_logger

        self.state = "Disconnected"
        self.missed_count = 0
        self.miss_threshold = 5

    def run(self) -> str:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = self.connection.recv_match(type="HEARTBEAT", blocking=True, timeout=self.period)

        if msg:
            # Successfully received heartbeat
            self.missed_count = 0
            self.state = "Connected"
            self.local_logger.info("Received heartbeat")
        else:
            # Missed heartbeat (timeout)
            self.missed_count += 1
            self.local_logger.warning(f"Missed heartbeat (count: {self.missed_count})")

            if self.missed_count >= self.miss_threshold:
                self.state = "Disconnected"
                self.local_logger.error(f"Disconnected after {self.missed_count} missed heartbeats")

        return self.state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
