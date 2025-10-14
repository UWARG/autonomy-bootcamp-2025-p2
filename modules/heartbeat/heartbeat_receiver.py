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
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        try:
            # Create a HeartbeatSender object
            return (True, HeartbeatReceiver(cls.__private_key, connection, local_logger))

        except (AssertionError, TypeError, AttributeError):
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
        self.last_5_heartbeats = [False, False, False, False, False]

    def run_receive_heartbeat(
        self,
    ) -> "tuple[True, str] | tuple[False, None]":
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """

        try:
            msg = self.connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1.1)

            # remove last heartbeat
            self.last_5_heartbeats.pop(0)

            # if no heartbeat received in 1.1 second
            if not msg:
                self.last_5_heartbeats.append(False)
                self.local_logger.warning("Did not receive heartbeat from drone")

                # check if there is no record of the drone being connected in last 5 checks
                if True not in self.last_5_heartbeats:
                    return (True, "Disconnected")

                return (True, "Connected")

            # if heartbeat received
            self.last_5_heartbeats.append(True)
            self.local_logger.info("Received heartbeat from drone")
            return (True, "Connected")

        except (AssertionError, TypeError, AttributeError):
            self.local_logger.error("heartbeat_receiver.py failed to receive heartbeat status")
            return (False, None)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
