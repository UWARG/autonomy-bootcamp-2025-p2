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
    ) -> "tuple[bool, Command | None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        if connection is None:
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

        self.__connection = connection
        self.__target = target
        self.__local_logger = local_logger
        self.__total_vx = 0.0
        self.__total_vy = 0.0
        self.__total_vz = 0.0
        self.__num_reports = 0

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,
    ) -> "tuple[bool, list[str] | None]":
        """
        Make a decision based on received telemetry data.
        """
        if telemetry_data is None:
            return False, None

        # Log average velocity for this trip so far
        self.__num_reports += 1
        self.__total_vx += telemetry_data.x_velocity
        self.__total_vy += telemetry_data.y_velocity
        self.__total_vz += telemetry_data.z_velocity
        avg_vx = self.__total_vx / self.__num_reports
        avg_vy = self.__total_vy / self.__num_reports
        avg_vz = self.__total_vz / self.__num_reports
        self.__local_logger.info(f"Average velocity: ({avg_vx}, {avg_vy}, {avg_vz})", True)

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system
        outputs = []
        delta_z = self.__target.z - telemetry_data.z
        if abs(delta_z) > 0.5:
            self.__connection.mav.command_long_send(
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
                self.__target.z,
            )
            outputs.append(f"CHANGE ALTITUDE: {delta_z}")
        else:
            target_yaw = math.atan2(
                self.__target.y - telemetry_data.y,
                self.__target.x - telemetry_data.x,
            )
            yaw_delta_rad = target_yaw - telemetry_data.yaw
            yaw_delta_rad = (yaw_delta_rad + math.pi) % (2 * math.pi) - math.pi
            yaw_delta_degrees = math.degrees(yaw_delta_rad)

            if abs(yaw_delta_degrees) > 5:
                direction = -1 if yaw_delta_degrees > 0 else 1
                self.__connection.mav.command_long_send(
                    1,
                    0,
                    mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                    0,
                    abs(yaw_delta_degrees),
                    5,
                    direction,
                    1,
                    0,
                    0,
                    0,
                )
                outputs.append(f"CHANGE YAW: {yaw_delta_degrees}")

        return True, outputs


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
