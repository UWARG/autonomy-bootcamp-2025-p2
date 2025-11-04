"""
Decision-making logic.
"""

import math

from pymavlink import mavutil

from ..common.modules.logger import logger
from ..telemetry import telemetry


class Position:
    """
    3D vector struct.
    """

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Command:  # pylint: disable=too-many-instance-attributes
    """
    Command class to make a decision based on recieved telemetry,
    and send out commands based upon the data.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> tuple:
        """
        Falliable create (instantiation) method to create a Command object.
        """
        return True, Command(cls.__private_key, connection, target, local_logger)

        #  Create a Command object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.key = key
        self.connection = connection
        self.target = target
        self.local_logger = local_logger
        self.last_telemetry = None
        self.counter = 0

    def run(
        self,
        current_telemetry: telemetry.TelemetryData,
    ) -> str:
        """
        Make a decision based on received telemetry data.
        """

        if current_telemetry is None:
            self.local_logger.warning("No telemetry data receieved!")
            return "No telemetry data received"

        # Log average velocity for this trip so far
        self.counter += 1
        if self.last_telemetry is not None:
            dx = current_telemetry.x  # - self.last_telemetry.x
            dy = current_telemetry.y  # - self.last_telemetry.y
            dz = current_telemetry.z  # - self.last_telemetry.z
            # dt = (current_telemetry.time_since_boot - self.last_telemetry.time_since_boot) / 1000
            dt = self.counter
            avg_vel = (dx / dt, dy / dt, dz / dt)

            self.local_logger.info(f"Average velocity vector: {avg_vel} m/s")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system

        dx = self.target.x - current_telemetry.x
        dy = self.target.y - current_telemetry.y
        target_yaw = math.atan2(dy, dx)
        current_yaw = current_telemetry.yaw

        # Compute delta yaw in radians
        delta_yaw_rad = target_yaw - current_yaw
        delta_yaw_rad = math.atan2(math.sin(delta_yaw_rad), math.cos(delta_yaw_rad))
        delta_yaw_deg = math.degrees(delta_yaw_rad)

        if delta_yaw_deg >= 0:
            direction = -1
        else:
            direction = 1

        delta_height = self.target.z - current_telemetry.z

        if abs(delta_height) > 0.5:
            self.connection.mav.command_long_send(
                target_system=1,
                target_component=0,
                command=mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                confirmation=0,
                param1=1,
                param2=0,
                param3=0,
                param4=0,
                param5=0,
                param6=0,
                param7=self.target.z,
            )
            # self.local_logger.info(f"CHANGE ALTITUDE: {delta_height:.2f}")
            return f"CHANGE ALTITUDE: {delta_height:.2f}"

        if abs(delta_yaw_deg) > 5:
            self.connection.mav.command_long_send(
                target_system=1,
                target_component=0,
                command=mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                confirmation=0,
                param1=abs(delta_yaw_deg),
                param2=5,
                param3=direction,
                param4=1,
                param5=0,
                param6=0,
                param7=0,
            )

            # self.local_logger.info(f"CHANGE YAW: {delta_yaw_deg:.2f}")
            return f"CHANGE YAW: {delta_yaw_deg:.2f}"

        self.last_telemetry = current_telemetry

        return "Nothing Done"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
