"""
Heartbeat sending logic.
"""

from pymavlink import mavutil


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
# The ground station identifies itself as a GCS without an autopilot
MAV_TYPE = mavutil.mavlink.MAV_TYPE_GCS
MAV_AUTOPILOT = mavutil.mavlink.MAV_AUTOPILOT_INVALID

# Remaining HEARTBEAT fields are unused by a ground station
BASE_MODE = 0
CUSTOM_MODE = 0
SYSTEM_STATUS = 0


class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.

        connection: MAVLink connection to the drone.

        Returns whether the object was created and the object itself.
        """
        # A sender without a connection has nothing to send heartbeats over
        if connection is None:
            return False, None

        return True, HeartbeatSender(cls.__private_key, connection)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection

    def run(
        self,
    ) -> bool:
        """
        Attempt to send a heartbeat message.

        Returns whether the heartbeat was sent successfully.
        """
        # Send a heartbeat message
        try:
            self.__connection.mav.heartbeat_send(
                MAV_TYPE,
                MAV_AUTOPILOT,
                BASE_MODE,
                CUSTOM_MODE,
                SYSTEM_STATUS,
            )
        # Catching all exceptions for library call
        # pylint: disable-next=broad-exception-caught
        except Exception:
            return False

        return True


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
