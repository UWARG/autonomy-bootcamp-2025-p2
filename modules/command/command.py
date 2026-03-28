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


HEIGHT_TOLERANCE = 0.5  # meters
ANGLE_TOLERANCE = 5.0  # degrees
Z_SPEED = 1.0  # m/s
TURNING_SPEED = 5.0  # deg/s


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
    ) -> "tuple[True, Command] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        return True, Command(cls.__private_key, connection, target, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        self.connection = connection
        self.target = target
        self.local_logger = local_logger
        self.velocity_sum_x = 0.0
        self.velocity_sum_y = 0.0
        self.velocity_sum_z = 0.0
        self.count = 0

    def run(
        self,
        data: telemetry.TelemetryData,
    ) -> "list[str]":
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far
        self.velocity_sum_x += data.x_velocity
        self.velocity_sum_y += data.y_velocity
        self.velocity_sum_z += data.z_velocity
        self.count += 1
        avg_vx = self.velocity_sum_x / self.count
        avg_vy = self.velocity_sum_y / self.count
        avg_vz = self.velocity_sum_z / self.count
        self.local_logger.info(f"Average velocity: ({avg_vx}, {avg_vy}, {avg_vz})")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        results = []

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
        delta_z = self.target.z - data.z
        if abs(delta_z) > HEIGHT_TOLERANCE:
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,
                Z_SPEED,
                0,
                0,
                0,
                0,
                0,
                self.target.z,
            )
            results.append(f"CHANGE_ALTITUDE: {delta_z}")
            return results

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system
        yaw_target = math.atan2(self.target.y - data.y, self.target.x - data.x)
        yaw_diff = yaw_target - data.yaw
        while yaw_diff > math.pi:
            yaw_diff -= 2 * math.pi
        while yaw_diff < -math.pi:
            yaw_diff += 2 * math.pi

        yaw_diff_deg = math.degrees(yaw_diff)
        if abs(yaw_diff_deg) > ANGLE_TOLERANCE:
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                yaw_diff_deg,
                TURNING_SPEED,
                0,
                1,
                0,
                0,
                0,
            )
            results.append(f"CHANGING_YAW: {yaw_diff_deg}")

        return results


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
