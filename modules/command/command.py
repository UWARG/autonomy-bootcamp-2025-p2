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
        Fallible create (instantiation) method to create a Command object.
        """
        if connection is None or target is None:
            local_logger.error("Failed to create Command: connection or target is None", True)
            return False, None

        instance = cls(cls.__private_key, connection, target, local_logger)
        return True, instance

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
        self.__logger = local_logger

        # Setup running average velocity components
        self.__total_reports = 0
        self.__sum_vx = 0.0
        self.__sum_vy = 0.0
        self.__sum_vz = 0.0

    def run(self, telemetry_data: telemetry.TelemetryData) -> "tuple[bool, str | None]":
        """
        Make a decision based on received telemetry data.
        """
        if telemetry_data is None:
            self.__logger.error("TelemetryData is None in Command.run", True)
            return False, None

        # 1. Update and log average velocity for this trip so far (3D vector)
        if (
            telemetry_data.x_velocity is not None
            and telemetry_data.y_velocity is not None
            and telemetry_data.z_velocity is not None
        ):
            self.__total_reports += 1
            self.__sum_vx += telemetry_data.x_velocity
            self.__sum_vy += telemetry_data.y_velocity
            self.__sum_vz += telemetry_data.z_velocity

            avg_vx = self.__sum_vx / self.__total_reports
            avg_vy = self.__sum_vy / self.__total_reports
            avg_vz = self.__sum_vz / self.__total_reports

            self.__logger.info(
                f"Average velocity so far: x={avg_vx:.4f}, y={avg_vy:.4f}, z={avg_vz:.4f}",
                True
            )

        # 2. Adjust height using the command MAV_CMD_CONDITION_CHANGE_ALT (113)
        if telemetry_data.z is not None:
            delta_z = self.__target.z - telemetry_data.z
            if abs(delta_z) > 0.5:
                try:
                    self.__connection.mav.command_long_send(
                        1,  # target_system
                        0,  # target_component
                        mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                        0,  # confirmation
                        1.0,  # param1: speed (Z_SPEED = 1 m/s)
                        0.0,  # param2
                        0.0,  # param3
                        0.0,  # param4
                        0.0,  # param5
                        0.0,  # param6
                        self.__target.z,  # param7: target altitude
                    )
                    return True, f"CHANGE ALTITUDE: {delta_z}"
                except Exception as e:
                    self.__logger.error(f"Failed to send CHANGE_ALT command: {e}", True)
                    return False, None

        # 3. Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115)
        if (
            telemetry_data.x is not None
            and telemetry_data.y is not None
            and telemetry_data.yaw is not None
        ):
            dx = self.__target.x - telemetry_data.x
            dy = self.__target.y - telemetry_data.y

            desired_yaw = math.atan2(dy, dx)
            delta_yaw = desired_yaw - telemetry_data.yaw

            # Normalize angle to range [-pi, pi]
            delta_yaw = (delta_yaw + math.pi) % (2 * math.pi) - math.pi

            # Convert to degrees
            delta_yaw_deg = math.degrees(delta_yaw)

            if abs(delta_yaw_deg) > 5.0:
                try:
                    # Direction of rotation: -1 for counter-clockwise, 1 for clockwise
                    direction = -1 if delta_yaw_deg >= 0 else 1
                    self.__connection.mav.command_long_send(
                        1,  # target_system
                        0,  # target_component
                        mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                        0,  # confirmation
                        abs(delta_yaw_deg),  # param1: angle
                        5.0,  # param2: speed (TURNING_SPEED = 5 deg/s)
                        direction,  # param3: direction
                        1.0,  # param4: relative offset flag (1 = relative)
                        0.0,  # param5
                        0.0,  # param6
                        0.0,  # param7
                    )
                    return True, f"CHANGE YAW: {delta_yaw_deg}"
                except Exception as e:
                    self.__logger.error(f"Failed to send YAW command: {e}", True)
                    return False, None

        return True, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
