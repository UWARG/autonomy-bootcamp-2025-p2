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
        turn_speed: float,
        local_logger: logger.Logger,
    ) -> "tuple[True, Command] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        return True, Command(
            cls.__private_key,
            connection,
            target,
            height_tolerance,
            z_speed,
            angle_tolerance,
            turn_speed,
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
        turn_speed: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__target = target
        self.__h_tolerance = height_tolerance
        self.__z_speed = z_speed
        self.__a_tolerance = angle_tolerance
        self.__turn_speed = turn_speed
        self.__logger = local_logger
        self.__vx = 0.0
        self.__vy = 0.0
        self.__vz = 0.0
        self.__total_time = 0.0

    def run(self, tel_data: telemetry.TelemetryData) -> "tuple[bool, str ]":
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far
        self.__vx += tel_data.x_velocity
        self.__vy += tel_data.y_velocity
        self.__vz += tel_data.z_velocity
        self.__total_time += 1.0

        avg_v_x = self.__vx / self.__total_time
        avg_v_y = self.__vy / self.__total_time
        avg_v_z = self.__vz / self.__total_time

        self.__logger.info(f"Average velocity: {avg_v_x:.3f}, {avg_v_y:.3f}, {avg_v_z:.3f}", True)

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below
        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)

        # difference in height b/w drone & target
        delta_z = self.__target.z - tel_data.z

        if abs(delta_z) > self.__h_tolerance:
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
            # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

            message = str(f"CHANGE_ALTITUDE: {delta_z:.3f} meters")
            self.__logger.info(message, True)
            return True, message

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        delta_x = self.__target.x - tel_data.x
        delta_y = self.__target.y - tel_data.y

        target_yaw = math.atan2(delta_y, delta_x)  # target yaw between [-pi,pi]
        delta_yaw = math.degrees(target_yaw - tel_data.yaw)
        delta_yaw = (delta_yaw + 180) % 360 - 180

        if abs(delta_yaw) > self.__a_tolerance:
            self.__connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                abs(delta_yaw),
                self.__turn_speed,
                1 if delta_yaw > 0 else -1,
                1,
                0,
                0,
                0,
            )
            # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
            message = str(f"CHANGING_YAW: {delta_yaw:.3f} degrees")
            self.__logger.info(message, True)
            return True, message
        # Positive angle is counter-clockwise as in a right handed system
        return True, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
