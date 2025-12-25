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
        z_speed: float,
        angle_tolerance: float,
        turning_speed: float,
        local_logger: logger.Logger,
    ) -> "tuple[bool, Command | None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        if connection is None:
            local_logger.error("Connection is None", True)
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
        self,
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

        # For tracking average velocity
        self.__velocity_samples = []

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,
    ) -> "tuple[bool, str]":
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far
        self.__velocity_samples.append(
            (telemetry_data.x_velocity, telemetry_data.y_velocity, telemetry_data.z_velocity)
        )

        sum_x = 0
        sum_y = 0
        sum_z = 0
        velocity_len = len(self.__velocity_samples)

        for velocity in self.__velocity_samples:
            sum_x += velocity[0]
            sum_y += velocity[1]
            sum_z += velocity[2]

        avg_x = sum_x / velocity_len
        avg_y = sum_y / velocity_len
        avg_z = sum_z / velocity_len

        self.__logger.info(f"Average velocity: ({avg_x}, {avg_y}, {avg_z}) m/s", True)

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        altitude_delta = self.__target.z - telemetry_data.z

        if abs(altitude_delta) > self.__height_tolerance:
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
            return True, f"CHANGE_ALTITUDE: {altitude_delta}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system

        dx = self.__target.x - telemetry_data.x
        dy = self.__target.y - telemetry_data.y
        angle_to_target = math.atan2(dy, dx)

        angle_delta = angle_to_target - telemetry_data.yaw

        while angle_delta > math.pi:
            angle_delta -= 2 * math.pi

        while angle_delta < -math.pi:
            angle_delta += 2 * math.pi

        angle_delta_deg = math.degrees(angle_delta)

        direction = 1
        if angle_delta_deg >= 0:
            direction = -1

        if abs(angle_delta_deg) > self.__angle_tolerance:
            self.__connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                angle_delta_deg,
                self.__turning_speed,
                direction,
                1,
                0,
                0,
                0,
            )
            return True, f"CHANGING_YAW: {angle_delta_deg}"
        return True, "ON_TARGET"


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
