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
            return True, cls(cls.__private_key, connection, local_logger)
        except (OSError, TypeError, AttributeError) as e:
            local_logger.error(f"Error when creating heartbeat reciever: {e}", True)
            return (False, None)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,  # Put your own arguments here
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"
        self._connection = connection
        self._logger = local_logger
        self._missed_count = 0
        self._status = False
        # Do any intializiation here

    def run(
        self,
    ) -> bool:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        try:
            msg = self._connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1)
        except (OSError, TypeError, AttributeError) as e:
            self._logger.error(f"Error receiving heartbeat: {e}", True)
            self._missed_count += 1
            if self._missed_count >= 5:
                self._status = False
            return self._status

        if msg:
            self._missed_count = 0
            self._status = True
        else:
            self._missed_count += 1
            self._logger.warning("Missed a heartbeat", True)
            if self._missed_count >= 5:
                self._status = False

        return self._status


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
