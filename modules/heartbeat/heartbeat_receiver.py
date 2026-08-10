"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil

from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
# The two states reported to the main process
CONNECTED = "Connected"
DISCONNECTED = "Disconnected"


class HeartbeatReceiver:
    """
    HeartbeatReceiver class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        period: float,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.

        connection: MAVLink connection to the drone.
        period: How long to wait for a heartbeat before counting it as missed, in seconds.
        disconnect_threshold: Consecutive missed heartbeats before declaring a disconnect.
        local_logger: Existing logger from the worker process.

        Returns whether the object was created and the object itself.
        """
        # A receiver without a connection has nothing to receive heartbeats from
        if connection is None:
            local_logger.error("No connection was provided", True)
            return False, None

        # Waiting a non-positive amount of time means a heartbeat can never arrive in time
        if period <= 0:
            local_logger.error(f"Period must be positive, got {period}", True)
            return False, None

        # A non-positive threshold would report a disconnect before missing anything
        if disconnect_threshold <= 0:
            local_logger.error(
                f"Disconnect threshold must be positive, got {disconnect_threshold}", True
            )
            return False, None

        return True, HeartbeatReceiver(
            cls.__private_key,
            connection,
            period,
            disconnect_threshold,
            local_logger,
        )

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        period: float,
        disconnect_threshold: int,
        local_logger: logger.Logger,
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__period = period
        self.__disconnect_threshold = disconnect_threshold
        self.__logger = local_logger

        # Nothing has been received yet, so the drone is not considered connected
        self.__missed_heartbeats = 0
        self.__state = DISCONNECTED

    def run(
        self,
    ) -> "tuple[bool, str | None]":
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.

        Returns whether the state could be determined and the current state.
        """
        # A heartbeat is expected once per period, so waiting longer means it was missed
        try:
            message = self.__connection.recv_match(
                type="HEARTBEAT",
                blocking=True,
                timeout=self.__period,
            )
        # Catching all exceptions for library call
        # pylint: disable-next=broad-exception-caught
        except Exception as e:
            self.__logger.error(f"Could not receive a heartbeat: {e}", True)
            return False, None

        if message is not None:
            self.__missed_heartbeats = 0
            self.__state = CONNECTED
            return True, self.__state

        self.__missed_heartbeats += 1
        self.__logger.warning(
            f"Missed a heartbeat ({self.__missed_heartbeats} in a row)",
            True,
        )

        # Enough heartbeats in a row have been missed for the drone to count as gone
        if self.__missed_heartbeats >= self.__disconnect_threshold:
            self.__state = DISCONNECTED

        return True, self.__state


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
