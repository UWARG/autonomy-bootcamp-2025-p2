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
    ) -> "tuple [True, Command] | [False, None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        return True, cls(
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
        self.local_logger = local_logger
        self.target = target
        self.connection = connection

        self.max_angle = math.radians(5)
        self.altitude_tolerance = 0.5

        self.vxi = 0
        self.vyi = 0
        self.vzi = 0
        self.times_received = 0

    def run(self, data: telemetry.TelemetryData) -> "tuple[True, str] | tuple [False, None]":
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far
        self.vxi += data.x_velocity
        self.vyi += data.y_velocity
        self.vzi += data.z_velocity
        self.times_received += 1

        avg_vx = self.vxi / self.times_received
        avg_vy = self.vyi / self.times_received
        avg_vz = self.vzi / self.times_received

        self.local_logger.info(f"Average velocity: ({avg_vx}, {avg_vy}, {avg_vz}) m/s")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
        height_diff = self.target.z - data.z
        if data.z is not None and abs(height_diff) > self.altitude_tolerance:
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
            return True, f"CHANGE_ALTITUDE {height_diff:.2f}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system
        if data.yaw is not None:
            dx = self.target.x - data.x
            dy = self.target.y - data.y
            yaw_diff = (math.atan2(dy, dx) - data.yaw + math.pi) % (2 * math.pi) - math.pi

            if abs(yaw_diff) > self.max_angle:
                yaw_diff_deg = math.degrees(yaw_diff)
                if yaw_diff_deg >= 0:
                    direction = -1
                else:
                    direction = 1
                self.connection.mav.command_long_send(
                    1,
                    0,
                    mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                    0,
                    yaw_diff_deg,
                    5,
                    direction,
                    1,
                    0,
                    0,
                    0,
                )
                return True, f"CHANGING YAW {yaw_diff_deg:.2f}"

        self.local_logger.error("Could not run command")
        return False, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
