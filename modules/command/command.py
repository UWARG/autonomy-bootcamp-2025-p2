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
        args,  # Put your own arguments here
        local_logger: logger.Logger,
    ):
        """
        Falliable create (instantiation) method to create a Command object.
        """
        try:
            instance = Command(Command.__private_key, connection, target, args, local_logger)
            return True, instance
        except Exception:  # pylint: disable=broad-except
            local_logger.error("Failed to create Command")
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        args,  # Put your own arguments here  # pylint: disable=unused-argument
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self._connection = connection
        self._target = target
        self._logger = local_logger
        self._velocities = []  # For average velocity calculation

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,
    ):
        """
        Make a decision based on received telemetry data.
        """
        if telemetry_data is None:
            return None

        # Calculate and log average velocity
        current_velocity = math.sqrt(
            telemetry_data.x_velocity**2
            + telemetry_data.y_velocity**2
            + telemetry_data.z_velocity**2
        )
        self._velocities.append(current_velocity)
        avg_velocity = sum(self._velocities) / len(self._velocities)
        self._logger.info(f"Average velocity: {avg_velocity:.2f} m/s")

        # Check altitude difference
        height_diff = abs(telemetry_data.z - self._target.z)
        if height_diff > 0.5:  # HEIGHT_TOLERANCE
            # Send altitude change command
            delta_z = self._target.z - telemetry_data.z
            self._connection.mav.command_long_send(
                1,
                0,  # target_system, target_component
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,  # confirmation
                1.0,  # param1: ascent/descent rate (m/s)
                0,
                0,
                0,
                0,
                0,  # param2-6: unused
                self._target.z,  # param7: target altitude
            )
            return f"CHANGE ALTITUDE: {delta_z:.2f}"

        # Check yaw difference
        target_yaw = math.atan2(
            self._target.y - telemetry_data.y, self._target.x - telemetry_data.x
        )
        yaw_diff = target_yaw - telemetry_data.yaw

        # Normalize yaw difference to [-pi, pi]
        while yaw_diff > math.pi:
            yaw_diff -= 2 * math.pi
        while yaw_diff < -math.pi:
            yaw_diff += 2 * math.pi

        if abs(math.degrees(yaw_diff)) > 5.0:  # ANGLE_TOLERANCE
            # Send yaw change command
            self._connection.mav.command_long_send(
                1,
                0,  # target_system, target_component
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,  # confirmation
                math.degrees(yaw_diff),  # param1: target angle (relative)
                5.0,  # param2: angular speed (deg/s)
                0,  # param3: direction (0=shortest, 1=CW, -1=CCW)
                1,  # param4: relative angle (1=relative, 0=absolute)
                0,
                0,
                0,  # param5-7: unused
            )
            return f"CHANGE YAW: {math.degrees(yaw_diff):.2f}"

        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
