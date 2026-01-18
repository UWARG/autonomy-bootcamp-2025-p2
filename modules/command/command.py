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
    ) -> tuple[bool, "Command | None"]:
        """
        Falliable create (instantiation) method to create a Command object.
        """
        return True, cls(
            cls.__private_key, connection, target, local_logger
        )  #  Create a Command object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.target = target
        self.logger = local_logger

        self.count = 0
        self.sum_x_vel = 0.0
        self.sum_y_vel = 0.0
        self.sum_z_vel = 0.0

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,  # Put your own arguments here
    ) -> str | None:
        """
        Make a decision based on received telemetry data.
        """
        if telemetry_data is None:
            return None
        # Log average velocity for this trip so far
        self.count += 1
        self.sum_x_vel += telemetry_data.x_velocity
        self.sum_y_vel += telemetry_data.y_velocity
        self.sum_z_vel += telemetry_data.z_velocity

        avg_x = self.sum_x_vel / self.count
        avg_y = self.sum_y_vel / self.count
        avg_z = self.sum_z_vel / self.count

        self.logger.info(f"Average Velocity: x={avg_x:.2f}, y={avg_y:.2f}, z={avg_z:.2f}")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        delta_z = self.target.z - telemetry_data.z
        if abs(delta_z) > 0.5:
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,
                1.0,
                0,
                0,
                0,
                0,
                0,
                float(self.target.z),
            )
            # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
            return f"CHANGE ALTITUDE: {delta_z}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        target_angle_rad = math.atan2(
            self.target.y - telemetry_data.y, self.target.x - telemetry_data.x
        )

        angle_diff_rad = target_angle_rad - telemetry_data.yaw
        while angle_diff_rad > math.pi:
            angle_diff_rad -= 2 * math.pi
        while angle_diff_rad < -math.pi:
            angle_diff_rad += 2 * math.pi

        angle_diff_deg = math.degrees(angle_diff_rad)

        if abs(angle_diff_deg) > 5.0:
            direction = -1 if angle_diff_deg > 0 else 1
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                abs(angle_diff_deg),
                5.0,
                direction,
                1,
                0,
                0,
                0,
            )
            # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
            return f"CHANGE YAW: {angle_diff_deg}"

        return None
        # Positive angle is counter-clockwise as in a right handed system


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
