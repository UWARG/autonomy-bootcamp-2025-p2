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
        Fallible create (instantiation) method to create a Command object.
        """
        try:
            obj = cls(cls.__private_key, connection, target, local_logger)
            return True, obj
        except Exception as e:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Failed to create Command: {e}", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        # Put your own arguments here
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        self._connection = connection
        self._target = target
        self._logger = local_logger

        self._vel_sum_x = 0.0
        self._vel_sum_y = 0.0
        self._vel_sum_z = 0.0
        self._vel_count = 0

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

        self._vel_sum_x += telemetry_data.x_velocity or 0.0
        self._vel_sum_y += telemetry_data.y_velocity or 0.0
        self._vel_sum_z += telemetry_data.z_velocity or 0.0
        self._vel_count += 1

        avg_vx = self._vel_sum_x / self._vel_count
        avg_vy = self._vel_sum_y / self._vel_count
        avg_vz = self._vel_sum_z / self._vel_count

        self._logger.info(
            f"Average velocity so far: ({avg_vx:.2f}, {avg_vy:.2f}, {avg_vz:.2f})",
            True,
        )

        delta_z = self._target.z - telemetry_data.z
        if abs(delta_z) > 0.5:
            self._connection.mav.command_long_send(
                1,  # target_system
                0,  # target_component
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,  # 113
                0,
                1.0,  # climb/descent speed
                0,
                0,
                0,
                0,
                0,
                self._target.z,  # target altitude
            )
            return f"CHANGE ALTITUDE: {delta_z:.2f}"

        dx = self._target.x - telemetry_data.x
        dy = self._target.y - telemetry_data.y

        desired_yaw_deg = math.degrees(math.atan2(dy, dx))
        current_yaw_deg = math.degrees(telemetry_data.yaw)

        yaw_error = (desired_yaw_deg - current_yaw_deg + 180) % 360 - 180

        if abs(yaw_error) > 5:
            direction = 1 if yaw_error >= 0 else -1

            self._connection.mav.command_long_send(
                1,  # target_system
                0,  # target_component
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                abs(yaw_error),
                5.0,  # turning speed
                direction,  # direction
                1,
                0,
                0,
                0,
            )
            return f"CHANGE YAW: {yaw_error:.2f}"

        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
