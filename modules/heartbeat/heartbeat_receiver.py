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
        # args  Put your own arguments here
        local_logger: logger.Logger,
    )-> tuple :
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """

        return True, HeartbeatReceiver(cls, connection, local_logger)

        # Create a HeartbeatReceiver object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger,
        # args Put your own arguments here
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.connection = connection
        self.local_logger = local_logger
        self.missed_heartbeats = 0
        # Do any intializiation here

    def run(
        self,
        # args Put your own arguments here
    ) -> None:

        msg = self.connection.recv_match(type="HEARTBEAT", blocking=False)

        if msg is not None:
            self.missed_heartbeats = 0
            self.logger.info("Heartbeat received")
            return True

        else:
            self.missed_heartbeats += 1

            if self.missed_heartbeats == 5:
                self.logger.error("Connection Lost: Missed 5 Heartbeats")
                return False

        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
