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
        local_logger: object,  # Put your own arguments here
    ) -> tuple[bool, "HeartbeatSender | None"]:
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """
        if connection is not None:
            return True, cls(cls.__private_key, connection, local_logger)

        return False, None  # Create a HeartbeatSender object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: object,  # Put your own arguments here
    ) -> None:
        assert key is HeartbeatSender.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.logger = local_logger

    def run(self) -> bool:  # Put your own arguments here
        """
        Attempt to send a heartbeat message.
        """
        try:  # Send a heartbeat message
            self.connection.mav.heartbeat_send(6, 8, 0, 0, 0)

            self.logger.info("Heartbeat Sender: Sent heartbeat message.")

            return True
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Log the specific error if the connection fails
            self.logger.error(f"Heartbeat Sender: Failed to send heartbeat. Error: {e}")
            return False


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
