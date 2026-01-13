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
        height_tolerance: float,
        yaw_tolerance_deg: float,
        z_speed: float,
        turning_speed: float,
        local_logger: logger.Logger,
    ):
        """
        Falliable create (instantiation) method to create a Command object.
        """
        try:
            instance = Command(
                cls.__private_key,
                connection,
                target,
                height_tolerance,
                yaw_tolerance_deg,
                z_speed,
                turning_speed,
                local_logger,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Failed to create Command: {exc}", True)
            return False, None
        return True, instance

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        height_tolerance: float,
        yaw_tolerance_deg: float,
        z_speed: float,
        turning_speed: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        self.__connection = connection
        self.__target = target
        self.__height_tolerance = height_tolerance
        self.__yaw_tolerance_deg = yaw_tolerance_deg
        self.__z_speed = z_speed
        self.__turning_speed = turning_speed
        self.__logger = local_logger
        self.__velocity_sum = [0.0, 0.0, 0.0]
        self.__velocity_count = 0

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,
    ) -> "tuple[bool, str | None]":
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system
        if (
            telemetry_data.x_velocity is None
            or telemetry_data.y_velocity is None
            or telemetry_data.z_velocity is None
        ):
            self.__logger.error("Telemetry missing velocity data", True)
            return False, None

        self.__velocity_sum[0] += telemetry_data.x_velocity
        self.__velocity_sum[1] += telemetry_data.y_velocity
        self.__velocity_sum[2] += telemetry_data.z_velocity
        self.__velocity_count += 1

        avg_velocity = (
            self.__velocity_sum[0] / self.__velocity_count,
            self.__velocity_sum[1] / self.__velocity_count,
            self.__velocity_sum[2] / self.__velocity_count,
        )
        self.__logger.info(f"Average velocity: {avg_velocity}", True)

        if telemetry_data.z is None:
            self.__logger.error("Telemetry missing altitude data", True)
            return False, None

        delta_z = self.__target.z - telemetry_data.z
        if abs(delta_z) > self.__height_tolerance:
            try:
                self.__connection.mav.command_long_send(
                    1,
                    0,
                    mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                    0,
                    self.__z_speed,
                    0,
                    0,
                    0,
                    0,
                    0,
                    self.__target.z,
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self.__logger.error(f"Failed to send altitude command: {exc}", True)
                return False, None

            return True, f"CHANGE ALTITUDE: {delta_z}"

        if telemetry_data.x is None or telemetry_data.y is None or telemetry_data.yaw is None:
            self.__logger.error("Telemetry missing position or yaw data", True)
            return False, None

        desired_yaw = math.atan2(
            self.__target.y - telemetry_data.y, self.__target.x - telemetry_data.x
        )
        yaw_error = math.atan2(
            math.sin(desired_yaw - telemetry_data.yaw),
            math.cos(desired_yaw - telemetry_data.yaw),
        )
        yaw_error_deg = math.degrees(yaw_error)

        if abs(yaw_error_deg) > self.__yaw_tolerance_deg:
            try:
                self.__connection.mav.command_long_send(
                    1,
                    0,
                    mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                    0,
                    yaw_error_deg,
                    self.__turning_speed,
                    0,
                    1,
                    0,
                    0,
                    0,
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self.__logger.error(f"Failed to send yaw command: {exc}", True)
                return False, None

            return True, f"CHANGE YAW: {yaw_error_deg}"

        return True, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
