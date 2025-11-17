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
        local_logger: logger.Logger
    ) -> "tuple [True, HeartbeatReceiver] | tuple [False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        return cls.__init__(cls.__private_key, connection, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.local_logger = local_logger
        self.status = "Connected"
        self.missed = 0



    def run(
        self
    ) -> "tuple[bool, str]":
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        message = self.connection.recv_match(
            type = 'HEARTBEAT',
            blocking = True,
            timeout = 2
        )

        if message == 'HEARTBEAT':
            self.status = "Connected"
            self.missed = 0
            self.local_logger.info("Heartbeat message received")

        else:
            ++self.missed
            self.local_logger.warning(f"{self.missed} heartbeat(s) missed")
            if self.missed == 5:
                self.status = "Disconnected"
                self.local_logger.warning("Drone Disconnected")

        return True, self.status


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
