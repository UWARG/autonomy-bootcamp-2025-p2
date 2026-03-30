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
        # Put your own arguments here
        local_logger: logger.Logger,
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """

        try:
            instance = cls(cls.__private_key, connection, local_logger)
        except (ValueError, TypeError, AttributeError) as e:
            local_logger.error("Failed to create HeartbeatReceiver instance: " + str(e))
            return False, None
        local_logger.debug("HeartbeatReceiver instance created", True)
        return True, instance

        # Create a HeartbeatReceiver object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
        missed: int = 0,
        state: str = "Disconnected",  # Put your own arguments here
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.connection = connection
        self.local_logger = local_logger
        self.missed = missed
        self.state = state
        # Do any intializiation here

    def run(
        self, period: float, error: float, threshold: int
    ) -> str:  # Put your own arguments here
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """

        msg = self.connection.recv_match(type="HEARTBEAT", blocking=True, timeout=period + error)

        if msg:
            self.missed = 0
            self.state = "Connected"
            self.local_logger.debug("Connected")
        else:
            self.missed += 1
            self.local_logger.warning("Missed Heartbeats: " + str(self.missed))

        if self.missed >= threshold:
            self.state = "Disconnected"
            self.local_logger.warning("Disconnected")

        return self.state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
