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

        try:
            # Create a Command object
            return (True, Command(cls.__private_key, connection, target, local_logger))

        except (AssertionError, TypeError, AttributeError):
            return (False, None)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        """
        Initializes the Command instance with drone connection and target.
        """
        assert key is Command.__private_key, "Use create() method"

        self.connection = connection
        self.target = target
        self.local_logger = local_logger
        self.total_vx = 0
        self.total_vy = 0
        self.total_vz = 0
        self.num_v_datapoints = 0

    def run_generate_command(
        self, telemetry_data: telemetry.TelemetryData
    ) -> "tuple[True, str] | tuple[False, None]":
        try:
            # Log average velocity for this trip so far
            self.total_vx += telemetry_data.x_velocity
            self.total_vy += telemetry_data.y_velocity
            self.total_vz += telemetry_data.z_velocity
            self.num_v_datapoints += 1
            avg_vx, avg_vy, avg_vz = (
                self.total_vx / self.num_v_datapoints,
                self.total_vy / self.num_v_datapoints,
                self.total_vz / self.num_v_datapoints,
            )
            self.local_logger.info(
                f"Average velocity: ({avg_vx:.2f}, {avg_vy:.2f}, {avg_vz:.2f})  m/s"
            )

            # Use COMMAND_LONG (76) message, assume the target_system=1 and target_component=0
            # The appropriate commands to use are instructed below

            # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
            # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
            if abs(telemetry_data.z - self.target.z) > 0.5:
                self.connection.mav.command_long_send(
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
                    float(self.target.z),
                )
                return (True, f"CHANGE_ALTITUDE: {abs(telemetry_data.z - self.target.z)}")

            # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
            # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
            # Positive angle is counter-clockwise as in a right handed system
            dx, dy = self.target.x - telemetry_data.x, self.target.y - telemetry_data.y
            desired_yaw = math.degrees(math.atan2(dy, dx))
            current_yaw = math.degrees(telemetry_data.yaw)
            yaw_error = (desired_yaw - current_yaw + 180) % 360 - 180

            if abs(yaw_error) > 5:
                self.connection.mav.command_long_send(
                    1,
                    0,
                    mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                    0,
                    abs(yaw_error),
                    5.0,
                    (1 if yaw_error > 0 else -1),
                    1,
                    0,
                    0,
                    0,
                )
                return (True, f"CHANGE_YAW: {yaw_error}")

            return (False, None)
        except Exception:  # pylint: disable=broad-exception-caught
            return (False, None)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
