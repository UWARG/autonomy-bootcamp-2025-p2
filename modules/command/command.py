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
        if target is None:
            local_logger.error("Not a valid target")
            return (False, None)
        return (True, cls(cls.__private_key, connection, target, local_logger))

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
        self.local_logger = local_logger
        self.initial_x = None
        self.initial_y = None
        self.initial_z = None
        self.initial_time = None

    def run(self, telemetry_data: telemetry.TelemetryData) -> str | None:
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

        if self.initial_time is None and telemetry_data.time_since_boot is not None:
            self.initial_x = telemetry_data.x
            self.initial_y = telemetry_data.y
            self.initial_z = telemetry_data.z
            self.initial_time = telemetry_data.time_since_boot
        elif self.initial_time is not None and telemetry_data.time_since_boot is not None:
            elapsed = (telemetry_data.time_since_boot - self.initial_time) / 1000.0

            avg_vx = (telemetry_data.x - self.initial_x) / elapsed
            avg_vy = (telemetry_data.y - self.initial_y) / elapsed
            avg_vz = (telemetry_data.z - self.initial_z) / elapsed
            self.local_logger.info(f"Average velocity: ({avg_vx}, {avg_vy}, {avg_vz}) m/s")

        altitude_error = self.target.z - telemetry_data.z

        if abs(altitude_error) > 0.5:
            self.connection.mav.command_long_send(
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
                self.target.z,
            )
            return f"CHANGE ALTITUDE: {altitude_error}"

        angle_to_target = math.atan2(
            self.target.y - telemetry_data.y, self.target.x - telemetry_data.x
        )
        yaw_error = angle_to_target - telemetry_data.yaw
        yaw_error_deg = math.degrees(yaw_error)

        while yaw_error_deg > 180:
            yaw_error_deg -= 360
        while yaw_error_deg < -180:
            yaw_error_deg += 360

        if abs(yaw_error_deg) > 5.0:
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                yaw_error_deg,
                5,
                0,
                1,
                0,
                0,
                0,
            )
            return f"CHANGE YAW: {yaw_error_deg}"

        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
