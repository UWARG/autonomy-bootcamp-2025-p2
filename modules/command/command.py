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
        z_speed: float,
        height_tolerance: float,
        angle_tolerance: float,
        turning_speed: float,
        local_logger: logger.Logger,
    ) -> "tuple[True, Command] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """

        if z_speed <= 0:
            local_logger.error("z_speed must be positive", True)
            return False, None
        if height_tolerance < 0:
            local_logger.error("height_tolerence must be non-negative", True)
            return False, None
        if angle_tolerance < 0:
            local_logger.error("angle_tolerance must be non-negative", True)
            return False, None
        if turning_speed <= 0:
            local_logger.error("angle_tolerance must be positive", True)
            return False, None

        return True, Command(
            cls.__private_key,
            connection,
            target,
            z_speed,
            height_tolerance,
            angle_tolerance,
            turning_speed,
            local_logger,
        )

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        z_speed: float,
        height_tolerance: float,
        angle_tolerance: float,
        turning_speed: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        self.connection = connection
        self.target = target
        self.z_speed = z_speed
        self.height_tolerance = height_tolerance
        self.angle_tolerance = angle_tolerance
        self.turning_speed = turning_speed
        self.local_logger = local_logger

        self.x_velocity_total = 0.0
        self.y_velocity_total = 0.0
        self.z_velocity_total = 0.0
        self.velocity_count = 0

    # Helper function to normalize degree angle between -180 to 180
    @staticmethod
    def normalize_angle_deg(angle_deg: float) -> float:
        normalized = (angle_deg + 180.0) % 360.0 - 180
        if normalized == -180.0 and angle_deg > 0:
            return 180.0
        return normalized

    def run(
        self,
        telematry_data: telemetry.TelemetryData,  # Put your own arguments here
    ) -> "tuple[bool, str | None]":
        """
        Make a decision based on received telemetry data.
        """
        self.x_velocity_total += telematry_data.x_velocity
        self.y_velocity_total += telematry_data.y_velocity
        self.z_velocity_total += telematry_data.z_velocity
        self.velocity_count += 1

        avg_x_velocity = self.x_velocity_total / self.velocity_count
        avg_y_velocity = self.y_velocity_total / self.velocity_count
        avg_z_velocity = self.z_velocity_total / self.velocity_count

        # Log average velocity for this trip so far
        self.local_logger.info(
            f"The average velocity so far is (xyz) : {avg_x_velocity}, {avg_y_velocity}, {avg_z_velocity}",
            True,
        )

        delta_z = self.target.z - telematry_data.z
        delta_x = self.target.x - telematry_data.x
        delta_y = self.target.y - telematry_data.y

        if abs(delta_z) > self.height_tolerance:
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,
                self.z_speed,
                0,
                0,
                0,
                0,
                0,
                self.target.z,
            )
            return True, f"CHANGE_ALTITUDE: {delta_z}"

        desired_yaw_deg = math.degrees(math.atan2(delta_y, delta_x))
        current_yaw_deg = math.degrees(telematry_data.yaw)
        yaw_change_deg = Command.normalize_angle_deg(desired_yaw_deg - current_yaw_deg)

        if abs(yaw_change_deg) > self.angle_tolerance:
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                yaw_change_deg,
                self.turning_speed,
                1,
                1,
                0,
                0,
                0,
            )
            return True, f"CHANGING_YAW: {yaw_change_deg}"

        return True, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
