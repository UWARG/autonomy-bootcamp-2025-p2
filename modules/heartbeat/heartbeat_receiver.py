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
            instance = HeartbeatReceiver(
                cls.__private_key,
                connection,
                heartbeat_period_s,
                disconnect_threshold,
                local_logger,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Failed to create HeartbeatReceiver: {exc}", True)
            return False, None
        return True, instance

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        heartbeat_period_s: float,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        self.__connection = connection
        self.__heartbeat_period_s = heartbeat_period_s
        self.__disconnect_threshold = disconnect_threshold
        self.__missed_count = 0
        self.__connected = False
        self.__logger = local_logger

    def run(
        self,
    ) -> str:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        msg = None
        try:
            msg = self.__connection.recv_match(
                type="HEARTBEAT",
                blocking=True,
                timeout=self.__heartbeat_period_s,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.__logger.error(f"Heartbeat receive failed: {exc}", True)

        if msg and msg.get_type() == "HEARTBEAT":
            if not self.__connected:
                self.__logger.info("Heartbeat connection established", True)
            self.__connected = True
            self.__missed_count = 0
        else:
            self.__missed_count += 1
            self.__logger.warning(
                f"Missed heartbeat {self.__missed_count}/{self.__disconnect_threshold}",
                True,
            )
            if self.__missed_count >= self.__disconnect_threshold:
                if self.__connected:
                    self.__logger.warning("Heartbeat connection lost", True)
                self.__connected = False

        return "Connected" if self.__connected else "Disconnected"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
