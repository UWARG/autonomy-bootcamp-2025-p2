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
    HeartbeatReceiver class to receive heartbeats and track connection state
    """

    __private_key = object()

    @classmethod
    def create(
        cls: "type[HeartbeatReceiver]",
        connection: mavutil.mavfile,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a
        HeartbeatReceiver object.

        connection: MAVLink connection to receive heartbeats from
        disconnect_threshold: Number of missed heartbeats before disconnect
        local_logger: Logger instance for logging
        """
        # Validate inputs
        if connection is None or local_logger is None:
            return False, None

        # Create and return HeartbeatReceiver object
        return True, HeartbeatReceiver(
            cls.__private_key, connection, disconnect_threshold, local_logger
        )

    def __init__(
        self: "HeartbeatReceiver",
        key: object,
        connection: mavutil.mavfile,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Store connection and logger
        self.__connection = connection
        self.__logger = local_logger
        self.__disconnect_threshold = disconnect_threshold

        # Track connection state
        self.__is_connected = True
        self.__missed_heartbeats = 0

    def run(
        self: "HeartbeatReceiver",
        timeout: float,
    ) -> "tuple[bool, str]":
        """
        Attempt to receive a heartbeat message.
        If disconnected for over threshold number of periods,
        the connection is considered disconnected.

        timeout: Time to wait for heartbeat message
        Returns: (success, connection_status_string)
        """
        # Try to receive a heartbeat
        msg = self.__connection.recv_match(
            type="HEARTBEAT", blocking=True, timeout=timeout
        )

        # Check if we received a heartbeat
        if msg and msg.get_type() == "HEARTBEAT":
            # Received heartbeat
            if not self.__is_connected:
                # Was disconnected, now reconnected
                self.__logger.info("Reconnected to drone")
                self.__is_connected = True

            self.__missed_heartbeats = 0
            return True, "Connected"

        # No heartbeat received
        self.__missed_heartbeats += 1

        # Check if we've exceeded disconnect threshold
        if self.__missed_heartbeats >= self.__disconnect_threshold:
            if self.__is_connected:
                # Just disconnected
                self.__logger.warning(
                    f"Disconnected: missed {self.__missed_heartbeats} "
                    f"heartbeats"
                )
                self.__is_connected = False
            return True, "Disconnected"

        # Still connected but missing heartbeats
        self.__logger.warning(
            f"Warning: missed {self.__missed_heartbeats} heartbeat(s)"
        )
        return True, "Connected"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
