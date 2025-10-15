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
        """
        Make a decision based on received telemetry data.
        """

        try:

            # Log average velocity for this trip so far

            # keep track of total x, y, and z velocities
            self.total_vx += telemetry_data.x_velocity
            self.total_vy += telemetry_data.y_velocity
            self.total_vz += telemetry_data.z_velocity
            self.num_v_datapoints += 1

            # calculate averages
            avg_vx = self.total_vx / self.num_v_datapoints
            avg_vy = self.total_vy / self.num_v_datapoints
            avg_vz = self.total_vz / self.num_v_datapoints

            # print
            self.local_logger.info(
                f"Average velocity: ({avg_vx:.2f}, {avg_vy:.2f}, {avg_vz:.2f})  m/s"
            )

            # Use COMMAND_LONG (76) message, assume the target_system=1 and target_component=0
            # The appropriate commands to use are instructed below

            # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
            # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

            if abs(telemetry_data.z - self.target.z) > 0.5:
                self.connection.mav.command_long_send(
                    1,  # Target system ID
                    0,  # Target component ID
                    mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,  # ID of command to send
                    0,  # Confirmation
                    1,  # param1: Descent / Ascend rate.	m/s
                    0,
                    0,
                    0,
                    0,
                    0,
                    self.target.z,  # param7: target altitude
                )

                return (True, f"CHANGE_ALTITUDE: {abs(telemetry_data.z - self.target.z)}")

            # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
            # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
            # Positive angle is counter-clockwise as in a right handed system

            # get vector from drone to target
            dx = self.target.x - telemetry_data.x
            dy = self.target.y - telemetry_data.y

            # get vector angle
            desired_yaw = math.atan2(dy, dx)

            yaw_error = desired_yaw - telemetry_data.yaw
            yaw_error = (math.degrees(yaw_error) + 180) % 360 - 180  # normalize to [-180, 180]

            if abs(yaw_error) > 5:
                self.connection.mav.command_long_send(
                    1,  # target system
                    0,  # target component
                    mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                    0,  # confirmation
                    abs(yaw_error),  # param1: yaw angle to turn (deg)
                    5,  # param2: yaw speed (deg/s)
                    0,  # 0 = shortest direction, as per mavlink's documentation
                    1,  # param4: set to relative
                    0,
                    0,
                    0,
                )

                return (True, f"CHANGE_YAW: {yaw_error}")

            return (False, None)

        except (AssertionError, TypeError, AttributeError):
            self.local_logger.error("command.py failed to generate commands")
            return (False, None)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
