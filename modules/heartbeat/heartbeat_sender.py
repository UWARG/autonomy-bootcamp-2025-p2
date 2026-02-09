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
        cls, connection: mavutil.mavfile, period: float
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        if period <= 0:
            return (False, None)
        return (True, cls(cls.__private_key, connection, period))

    def __init__(self, key: object, connection: mavutil.mavfile, period: float) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        self.period = period
        self.connection = connection

    def run(self) -> None:
        """
        Attempt to send a heartbeat message.
        """
        self.connection.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS,
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            0,
            0,
            mavutil.mavlink.MAV_STATE_ACTIVE,
            3,
        )


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
