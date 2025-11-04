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
        main_logger: logger.Logger,
    ) -> tuple:
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """

        return True, HeartbeatReceiver(cls.__private_key, connection, main_logger)

        # Create a HeartbeatReceiver object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        main_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.connection = connection
        self.main_logger = main_logger
        self.missed_heartbeats = 0
        self.state = "Disconnected"
        # Do any intializiation here

    def run(
        self,
    ) -> tuple:
        "Runs Code"

        msg = self.connection.recv_match(type="HEARTBEAT", blocking=False)

        if msg is not None:
            self.missed_heartbeats = 0
            self.state = "Connected"
            self.main_logger.info("Heartbeat Received")

        else:
            self.missed_heartbeats += 1
            self.main_logger.warning("Missed Heartbeat")

        if self.missed_heartbeats >= 5:
            self.state = "Disconnected"

        return self.state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
