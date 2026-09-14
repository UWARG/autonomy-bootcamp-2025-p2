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
        return True, Command(
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
        self.__logger = local_logger

        self.velocity_sum_x = 0.0
        self.velocity_sum_y = 0.0
        self.velocity_sum_z = 0.0
        self.num_readings = 0

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,  # Put your own arguments here
    ) -> "tuple[bool, str | None]":
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far
        self.velocity_sum_x += telemetry_data.x_velocity
        self.velocity_sum_y += telemetry_data.y_velocity
        self.velocity_sum_z += telemetry_data.z_velocity
        self.num_readings += 1

        avg_velocity_x = self.velocity_sum_x / self.num_readings
        avg_velocity_y = self.velocity_sum_y / self.num_readings
        avg_velocity_z = self.velocity_sum_z / self.num_readings

        self.__logger.info(
            f"Average velocity: ({avg_velocity_x}, {avg_velocity_y}, {avg_velocity_z})", True
        )

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        altitude_difference = self.target.z - telemetry_data.z

        if abs(altitude_difference) > 0.5:
            self.connection.mav.command_long_send(
                1,  # target_system
                0,  # target_component
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,  # confirmation
                1,  # param1: ascent/descent rate
                0,  # param2: unused
                0,  # param3: unused
                0,  # param4: unused
                0,  # param5: unused
                0,  # param6: unused
                self.target.z,  # param7: target altitude
            )
            return True, f"CHANGE_ALTITUDE: {altitude_difference}"

        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        desired_yaw = math.atan2(self.target.y - telemetry_data.y, self.target.x - telemetry_data.x)
        yaw_difference = math.degrees(desired_yaw - telemetry_data.yaw)

        # Normalizing to -180, 180
        yaw_difference = (yaw_difference + 180) % 360 - 180

        if abs(yaw_difference) > 5:
            direction = -1 if yaw_difference > 0 else 1

            self.connection.mav.command_long_send(
                1,  # target_system
                0,  # target_component
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,  # confirmation
                abs(yaw_difference),  # target angle magnitude
                5,  # param2: yaw speed
                direction,
                1,  # param4: relative
                0,
                0,
                0,  # param5-7: unused
            )
            return True, f"CHANGING_YAW: {yaw_difference}"
        return True, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
