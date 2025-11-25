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
        turning_speed_deg_s: float,
        local_logger: logger.Logger,
    ) -> "tuple[bool, Command | None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        try:
            return True, Command(
                Command.__private_key,
                connection,
                target,
                turning_speed_deg_s,
                local_logger,
            )
        except:  # pylint: disable=bare-except
            local_logger.error("Failed to create Command", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        turning_speed_deg_s: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__target = target
        self.__turning_speed_deg_s = turning_speed_deg_s
        self.__logger = local_logger
        self.__total_time_s = 0.0
        self.__disp_x = 0.0
        self.__disp_y = 0.0
        self.__disp_z = 0.0

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,
        telemetry_period_s: float,
        z_speed_m_s: float,
        angle_tolerance_deg: float,
        height_tolerance_m: float,
    ) -> "tuple[bool, str | None]":
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far
        try:
            # Integrate displacement using average velocities over the time step
            self.__disp_x += float(telemetry_data.x_velocity or 0.0) * telemetry_period_s
            self.__disp_y += float(telemetry_data.y_velocity or 0.0) * telemetry_period_s
            self.__disp_z += float(telemetry_data.z_velocity or 0.0) * telemetry_period_s
            self.__total_time_s += telemetry_period_s
            if self.__total_time_s > 0:
                avg_vx = self.__disp_x / self.__total_time_s
                avg_vy = self.__disp_y / self.__total_time_s
                avg_vz = self.__disp_z / self.__total_time_s
                self.__logger.info(f"Average velocity: ({avg_vx:.3f}, {avg_vy:.3f}, {avg_vz:.3f})")
        except Exception as e:  # pylint: disable=broad-except
            self.__logger.error(f"Error computing average velocity: {e}")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
        if telemetry_data.z is not None:
            delta_z = float(self.__target.z - telemetry_data.z)
            if abs(delta_z) > height_tolerance_m:
                try:
                    self.__connection.mav.command_long_send(
                        1,  # target_system
                        0,  # target_component
                        mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                        0,  # confirmation
                        float(z_speed_m_s),  # param1 ascent/descent m/s
                        0,
                        0,
                        0,
                        0,
                        0,
                        float(self.__target.z),  # param7 target altitude
                    )
                except Exception as e:  # pylint: disable=broad-except
                    self.__logger.error(f"Failed to send altitude command: {e}", True)
                return True, f"CHANGE ALTITUDE: {delta_z}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system
        if (
            telemetry_data.x is not None
            and telemetry_data.y is not None
            and telemetry_data.yaw is not None
        ):
            dx = float(self.__target.x - telemetry_data.x)
            dy = float(self.__target.y - telemetry_data.y)
            desired_yaw = math.atan2(dy, dx)
            delta_rad = desired_yaw - float(telemetry_data.yaw)
            # Normalize to [-pi, pi]
            while delta_rad > math.pi:
                delta_rad -= 2 * math.pi
            while delta_rad < -math.pi:
                delta_rad += 2 * math.pi
            delta_deg = math.degrees(delta_rad)
            if abs(delta_deg) > angle_tolerance_deg:
                direction = -1 if delta_deg >= 0 else 1
                try:
                    self.__connection.mav.command_long_send(
                        1,
                        0,
                        mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                        0,
                        abs(float(delta_deg)),  # angle (deg)
                        float(self.__turning_speed_deg_s),  # turning speed (deg/s)
                        float(direction),  # direction
                        1,  # relative angle
                        0,
                        0,
                        0,
                    )
                except Exception as e:  # pylint: disable=broad-except
                    self.__logger.error(f"Failed to send yaw command: {e}", True)
                return True, f"CHANGE YAW: {delta_deg}"

        return False, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
