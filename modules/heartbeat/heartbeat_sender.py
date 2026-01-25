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
        # Put your own arguments here
    ) -> "tuple[True, HeartbeatSender] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        if connection is None:
            return False, None

        try:
            # Create an instance using the private key
            instance = cls(cls.__private_key, connection)
            return True, instance
        except Exception:  # pylint: disable=broad-exception-caught
            # fail safely
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        # Put your own arguments here
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        self._connection = connection

        # 5 required fields
        self._mav_type = mavutil.mavlink.MAV_TYPE_GCS
        self._autopilot = mavutil.mavlink.MAV_AUTOPILOT_INVALID
        self._base_mode = 0
        self._custom_mode = 0
        self._system_status = 0

    def run(
        self,
        # Put your own arguments here
    ) -> bool:
        """
        Attempt to send a heartbeat message.
        """
        try:
            # Send the heartbeat message over the connection
            self._connection.mav.heartbeat_send(
                self._mav_type,
                self._autopilot,
                self._base_mode,
                self._custom_mode,
                self._system_status,
            )
            return True
        except Exception:  # pylint: disable=broad-exception-caught
            return False


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
