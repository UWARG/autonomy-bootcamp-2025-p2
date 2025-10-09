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

    def __init__(self: "Position", x: float, y: float, z: float) -> None:
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
        cls: "type[Command]",
        connection: mavutil.mavfile,
        target: Position,
        height_tolerance: float,
        z_speed: float,
        angle_tolerance: float,
        turning_speed: float,
        local_logger: logger.Logger,
    ) -> "tuple[bool, Command | None]":
        """create command processor"""
        if connection is None or local_logger is None:
            return False, None

        return True, Command(
            cls.__private_key,
            connection,
            target,
            height_tolerance,
            z_speed,
            angle_tolerance,
            turning_speed,
            local_logger,
        )

    def __init__(
        self: "Command",
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        height_tolerance: float,
        z_speed: float,
        angle_tolerance: float,
        turning_speed: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"
        self.__connection = connection
        self.__target = target
        self.__height_tolerance = height_tolerance
        self.__z_speed = z_speed
        self.__angle_tolerance = angle_tolerance
        self.__turning_speed = turning_speed
        self.__logger = local_logger
        self.__velocity_sum_x = 0.0
        self.__velocity_sum_y = 0.0
        self.__velocity_sum_z = 0.0
        self.__data_count = 0

    def run(
        self: "Command",
        telemetry_data: telemetry.TelemetryData,
    ) -> "tuple[bool, str | None]":
        """process telemetry and send commands"""
        self.__velocity_sum_x += telemetry_data.x_velocity
        self.__velocity_sum_y += telemetry_data.y_velocity
        self.__velocity_sum_z += telemetry_data.z_velocity
        self.__data_count += 1

        avg_vel_x = self.__velocity_sum_x / self.__data_count
        avg_vel_y = self.__velocity_sum_y / self.__data_count
        avg_vel_z = self.__velocity_sum_z / self.__data_count

        self.__logger.info(
            f"Average velocity: ({avg_vel_x:.2f}, {avg_vel_y:.2f}, " f"{avg_vel_z:.2f})",
            True,
        )

        altitude_diff = self.__target.z - telemetry_data.z
        if abs(altitude_diff) > self.__height_tolerance:
            self.__connection.mav.command_long_send(
                target_system=1,
                target_component=0,
                command=mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                confirmation=0,
                param1=self.__z_speed,  # Ascent/descent speed
                param2=0,
                param3=0,
                param4=0,
                param5=0,
                param6=0,
                param7=self.__target.z,  # Target altitude
            )
            return True, f"CHANGE ALTITUDE: {altitude_diff}"

        dx = self.__target.x - telemetry_data.x
        dy = self.__target.y - telemetry_data.y
        target_yaw = math.atan2(dy, dx)

        yaw_diff = target_yaw - telemetry_data.yaw
        while yaw_diff > math.pi:
            yaw_diff -= 2 * math.pi
        while yaw_diff < -math.pi:
            yaw_diff += 2 * math.pi

        yaw_diff_deg = math.degrees(yaw_diff)

        if abs(yaw_diff_deg) > self.__angle_tolerance:
            self.__connection.mav.command_long_send(
                target_system=1,
                target_component=0,
                command=mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                confirmation=0,
                param1=yaw_diff_deg,
                param2=self.__turning_speed,
                param3=1,
                param4=1,
                param5=0,
                param6=0,
                param7=0,
            )
            return True, f"CHANGE YAW: {yaw_diff_deg}"

        return True, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
