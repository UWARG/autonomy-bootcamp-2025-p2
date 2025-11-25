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
        heartbeat_period_s: float,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> "tuple[bool, HeartbeatReceiver | None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        try:
            return True, HeartbeatReceiver(
                HeartbeatReceiver.__private_key,
                connection,
                heartbeat_period_s,
                disconnect_threshold,
            )
        except:  # pylint: disable=bare-except
            local_logger.error("Failed to create HeartbeatReceiver", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        heartbeat_period_s: float,
        disconnect_threshold: int,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__period_s = heartbeat_period_s
        self.__missed_in_row = 0
        self.__disconnect_threshold = disconnect_threshold

    def run(
        self,
        local_logger: logger.Logger,
    ) -> "tuple[bool, str]":
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        try:
            msg = self.__connection.recv_match(
                type="HEARTBEAT", blocking=True, timeout=self.__period_s
            )
        except Exception as e:  # pylint: disable=broad-except
            local_logger.error(f"Exception while receiving heartbeat: {e}", True)
            msg = None

        if not msg or msg.get_type() != "HEARTBEAT":
            self.__missed_in_row += 1
            local_logger.warning("Missed heartbeat", True)
        else:
            self.__missed_in_row = 0

        state = (
            "Connected" if self.__missed_in_row < self.__disconnect_threshold else "Disconnected"
        )
        local_logger.info(f"State: {state}", True)
        return True, state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
