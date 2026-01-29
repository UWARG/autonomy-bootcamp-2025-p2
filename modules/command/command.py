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
        target: Position,  # Put your own arguments here
        local_logger: logger.Logger,
    ) -> tuple[
        bool,
        Command,  # pylint: disable=undefined-variable ### I dont know why its getting mad at me for this
    ]:
        """
        Falliable create (instantiation) method to create a Command object.
        """
        return True, cls(  # pylint: disable=undefined-variable
            cls.__private_key, connection=connection, target=target, local_logger=local_logger
        )

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        # Put your own arguments here
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.target = target
        self.local_logger = local_logger
        self.num_of_runs = 0
        self.total_velocity = Position(0, 0, 0)

    def run(self, telemetry_data: telemetry.TelemetryData) -> str:
        """
        Run the command worker, calculate velocity, and orient drone towards target
        """
        # Calculating the average velocity
        self.num_of_runs += 1
        self.total_velocity.x += telemetry_data.x_velocity
        self.total_velocity.y += telemetry_data.y_velocity
        self.total_velocity.z += telemetry_data.z_velocity

        self.local_logger.info(
            f"current velocity: ({self.total_velocity.x/self.num_of_runs}, {self.total_velocity.y/self.num_of_runs}, {self.total_velocity.z/self.num_of_runs})"
        )

        # Checking vertical (z) difference
        dz = telemetry_data.z - self.target.z
        if dz >= 0.5 or dz <= -0.5:
            self.local_logger.info(f"TARGET Z IS OFF, MOVING {dz} METERS")
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
                self.target.z,
            )
            return f"CHANGE ALTITUDE: {self.target.z-telemetry_data.z}"

        # Calculate bearing to target
        dx = self.target.x - telemetry_data.x
        dy = self.target.y - telemetry_data.y
        bearing_rad = math.atan2(dy, dx)
        bearing_deg = math.degrees(bearing_rad)

        # Current yaw in degrees
        current_yaw_deg = math.degrees(telemetry_data.yaw)

        # Calculate yaw difference
        delta_yaw_deg = bearing_deg - current_yaw_deg

        # Normalize
        delta_yaw_deg = (delta_yaw_deg + 180) % 360 - 180

        if abs(delta_yaw_deg) > 5:
            self.local_logger.info("TARGET NOT IN SIGHT, TURNING")
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                abs(delta_yaw_deg),
                5.0,
                -1 if delta_yaw_deg >= 0 else 1,
                1,
                0,
                0,
                0,
            )
            return f"CHANGE YAW: {delta_yaw_deg}"
        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
