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
    ) -> "tuple[True, Command] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        if None in (connection, target, local_logger):
            return False, None

        return True, Command(cls.__private_key, connection, target, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__target = target
        self.__logger = local_logger

        self.__elapsed_intervals = 0
        self.__cum_vx = 0
        self.__cum_vy = 0
        self.__cum_vz = 0

    def run(self, telemetry_point: telemetry.TelemetryData) -> tuple[float | None, float | None]:
        """
        Make a decision based on received telemetry data.
        """
        # Update velocity calculations
        self.__cum_vx += telemetry_point.x_velocity
        self.__cum_vy += telemetry_point.y_velocity
        self.__cum_vz += telemetry_point.z_velocity
        self.__elapsed_intervals += 1

        # Log average velocity for this trip so far
        vx = self.__cum_vx / self.__elapsed_intervals
        vy = self.__cum_vy / self.__elapsed_intervals
        vz = self.__cum_vz / self.__elapsed_intervals

        self.__logger.info(f"Average velocity: {vx}, {vy}, {vz}")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
        altitude_delta = self.__target.z - telemetry_point.z
        if abs(altitude_delta) > 0.5:
            self.__connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                self.__target.z,
            )

            return altitude_delta, None

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system

        dx = self.__target.x - telemetry_point.x
        dy = self.__target.y - telemetry_point.y

        target_yaw = math.atan2(dy, dx)

        yaw_delta = (target_yaw - telemetry_point.yaw + math.pi) % (2 * math.pi) - math.pi

        yaw_degrees = math.degrees(abs(yaw_delta))
        yaw_direction = 1 if yaw_delta >= 0 else -1

        if yaw_degrees > 5:
            self.__connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                yaw_degrees,
                5,
                yaw_direction,
                1,
                0,
                0,
                0,
            )

            return None, yaw_degrees * yaw_direction

        return None, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
