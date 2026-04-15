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
    ) -> "tuple[bool, Command]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        try:
            return True, cls(cls.__private_key, connection, target, local_logger)
        except OSError as e:
            local_logger.error(f"Error while creating Command instance: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        self._connection = connection
        self._target = target
        self._logger = local_logger
        self._initial_x = None
        self._initial_y = None
        self._initial_z = None
        self._initial_time = None
        self._cur_time = None

        # Do any intializiation here

    def run(self, telemetry_data: telemetry.TelemetryData) -> str:
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

        if self._initial_time is None:
            self._initial_time = 0
            self._cur_time = 0.5
            self._initial_x = telemetry_data.x
            self._initial_y = telemetry_data.y
            self._initial_z = telemetry_data.z
        else:
            elapsed_sec = self._cur_time - self._initial_time
            self._cur_time += 0.5
            avg_vx = (telemetry_data.x - self._initial_x) / elapsed_sec
            avg_vy = (telemetry_data.y - self._initial_y) / elapsed_sec
            avg_vz = (telemetry_data.z - self._initial_z) / elapsed_sec
            self._logger.info(f"Average velocity: ({avg_vx}, {avg_vy}, {avg_vz}) m/s")

        delta_altitude = self._target.z - telemetry_data.z

        if abs(delta_altitude) > 0.5:
            self._connection.mav.command_long_send(
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
                self._target.z,
            )
            return f"CHANGE ALTITUDE: {delta_altitude}"

        target_angle = math.atan2(
            self._target.y - telemetry_data.y, self._target.x - telemetry_data.x
        )
        yaw_error = target_angle - telemetry_data.yaw
        yaw_error_deg = math.degrees(yaw_error)

        while yaw_error_deg > 180:
            yaw_error_deg -= 360
        while yaw_error_deg < -180:
            yaw_error_deg += 360

        if abs(yaw_error_deg) > 5.0:
            self._connection.mav.command_long_send(
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
