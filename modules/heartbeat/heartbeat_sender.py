"""
Heartbeat sending logic.
"""

from pymavlink import mavutil


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls: "type[HeartbeatSender]",
        connection: mavutil.mavfile,
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a
        HeartbeatSender object.

        connection: MAVLink connection to send heartbeats through
        """
        # Validate connection
        if connection is None:
            return False, None

        # Create and return HeartbeatSender object
        return True, HeartbeatSender(cls.__private_key, connection)

    def __init__(
        self: "HeartbeatSender",
        key: object,
        connection: mavutil.mavfile,
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        # Store the connection
        self.__connection = connection

    def run(
        self: "HeartbeatSender",
    ) -> "tuple[bool, None]":
        """
        Attempt to send a heartbeat message.

        Returns tuple of (success, None)
        """
        try:
            # Send heartbeat with MAV_TYPE_GCS and MAV_AUTOPILOT_INVALID
            # as expected by the test drone
            self.__connection.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_GCS,
                mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                0,  # base_mode
                0,  # custom_mode
                0,  # system_status
            )
            return True, None
        except Exception:  # pylint: disable=broad-except
            return False, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
