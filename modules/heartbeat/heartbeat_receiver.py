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
        local_logger: logger.Logger,
    ) -> "tuple[True, 'HeartbeatReceiver'] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        try:
            return (True, HeartbeatReceiver(cls.__private_key, connection, local_logger))

        except (Exception):
            return (False, None)

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
        self.is_connected = False

    def run(
        self,
        args=None,  # Put your own arguments here
    ) -> str:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """

        # Add blocking to check once per second
        msg = self.connection.recv_match(type='HEARTBEAT', blocking=True, timeout=1.5)

        if msg is not None:
            self.missed_count = 0
            self.is_connected = True
        else:
            self.missed_count += 1
            self.local_logger.warning("Missed " + str(self.missed_count) + " heartbeat(s)", True)

            if self.missed_count >= 5:
                self.is_connected = False

        if self.is_connected:
            return "Connected"
        else:
            return "Disconnected"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
