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
        cls,
        connection: mavutil.mavfile,
        period_s: float,
    ) -> "tuple[bool, HeartbeatSender | None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        try:
            return True, HeartbeatSender(
                HeartbeatSender.__private_key,
                connection,
                period_s,
            )
        except:  # pylint: disable=bare-except
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        period_s: float,
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        self.__connection = connection
        self.__period_s = period_s

    def run(
        self,
        _unused: None | object = None,
    ) -> "tuple[bool, float]":
        """
        Attempt to send a heartbeat message.
        """
        # Send heartbeat from GCS once
        self.__connection.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_GCS,
            mavutil.mavlink.MAV_AUTOPILOT_INVALID,
            0,
            0,
            0,
        )
        return True, self.__period_s


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
