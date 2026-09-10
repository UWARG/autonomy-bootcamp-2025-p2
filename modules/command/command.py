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
# The drone's autopilot, which is what the commands are addressed to
TARGET_SYSTEM = 1
TARGET_COMPONENT = 0

# First transmission of every command, so nothing needs to be confirmed
CONFIRMATION = 0

# Unused COMMAND_LONG parameters
EMPTY_PARAMETER = 0

# MAV_CMD_CONDITION_YAW expects the rotation direction in a right handed system
COUNTER_CLOCKWISE = -1
CLOCKWISE = 1

# MAV_CMD_CONDITION_YAW is given an offset from the current yaw rather than an absolute angle
RELATIVE_ANGLE = 1

# A full turn, used to wrap angles into the range [-180, 180] degrees
FULL_TURN = 360
HALF_TURN = 180


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
        height_tolerance: float,
        angle_tolerance: float,
        altitude_speed: float,
        turning_speed: float,
        local_logger: logger.Logger,
    ) -> "tuple[True, Command] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Command object.

        connection: MAVLink connection to the drone.
        target: Point in 3D space that the drone should face and match the altitude of.
        height_tolerance: How far off the target's altitude the drone may be, in metres.
        angle_tolerance: How far away from the target the drone may face, in degrees.
        altitude_speed: How quickly the drone ascends and descends, in metres per second.
        turning_speed: How quickly the drone yaws, in degrees per second.
        local_logger: Existing logger from the worker process.

        Returns whether the object was created and the object itself.
        """
        # Create a Command object
        # Without a connection there is nowhere to send commands
        if connection is None:
            local_logger.error("No connection was provided", True)
            return False, None

        # There is no point in space to aim at
        if target is None:
            local_logger.error("No target was provided", True)
            return False, None

        # A negative tolerance can never be satisfied, so the drone would command forever
        if height_tolerance < 0 or angle_tolerance < 0:
            local_logger.error(
                f"Tolerances cannot be negative, got {height_tolerance}m and {angle_tolerance}deg",
                True,
            )
            return False, None

        # The drone would never reach the target if it does not move
        if altitude_speed <= 0 or turning_speed <= 0:
            local_logger.error(
                f"Speeds must be positive, got {altitude_speed}m/s and {turning_speed}deg/s",
                True,
            )
            return False, None

        return True, Command(
            cls.__private_key,
            connection,
            target,
            height_tolerance,
            angle_tolerance,
            altitude_speed,
            turning_speed,
            local_logger,
        )

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        height_tolerance: float,
        angle_tolerance: float,
        altitude_speed: float,
        turning_speed: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__target = target
        self.__height_tolerance = height_tolerance
        self.__angle_tolerance = angle_tolerance
        self.__altitude_speed = altitude_speed
        self.__turning_speed = turning_speed
        self.__logger = local_logger

        # Telemetry reports arrive perfectly periodically and each velocity is the average over
        # one period, so summing them and dividing by the count gives the average for the trip
        self.__velocity_sum = Position(0.0, 0.0, 0.0)
        self.__report_count = 0

    def __update_average_velocity(self, telemetry_data: telemetry.TelemetryData) -> Position:
        """
        Fold the newest velocity reading into the average velocity of the trip so far.

        Returns the average velocity.
        """
        self.__velocity_sum.x += telemetry_data.x_velocity
        self.__velocity_sum.y += telemetry_data.y_velocity
        self.__velocity_sum.z += telemetry_data.z_velocity
        self.__report_count += 1

        return Position(
            self.__velocity_sum.x / self.__report_count,
            self.__velocity_sum.y / self.__report_count,
            self.__velocity_sum.z / self.__report_count,
        )

    def __change_altitude(self, delta_z: float) -> str:
        """
        Command the drone to climb or descend to the target's altitude.

        delta_z: How far the drone has to move along z, in metres.

        Returns the message to report to the main process.
        """
        self.__connection.mav.command_long_send(
            TARGET_SYSTEM,
            TARGET_COMPONENT,
            mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
            CONFIRMATION,
            self.__altitude_speed,  # param1: rate of ascent/descent
            EMPTY_PARAMETER,  # param2
            EMPTY_PARAMETER,  # param3
            EMPTY_PARAMETER,  # param4
            EMPTY_PARAMETER,  # param5
            EMPTY_PARAMETER,  # param6
            self.__target.z,  # param7: target altitude
        )

        return f"CHANGE_ALTITUDE: {delta_z}"

    def __change_yaw(self, delta_yaw: float) -> str:
        """
        Command the drone to rotate to face the target.

        delta_yaw: How far the drone has to rotate, in degrees, in the range [-180, 180].

        Returns the message to report to the main process.
        """
        self.__connection.mav.command_long_send(
            TARGET_SYSTEM,
            TARGET_COMPONENT,
            mavutil.mavlink.MAV_CMD_CONDITION_YAW,
            CONFIRMATION,
            abs(delta_yaw),  # param1: angle to turn by, the sign is given by param3
            self.__turning_speed,  # param2: angular speed
            COUNTER_CLOCKWISE if delta_yaw > 0 else CLOCKWISE,  # param3: direction
            RELATIVE_ANGLE,  # param4: the angle is an offset from the current yaw
            EMPTY_PARAMETER,  # param5
            EMPTY_PARAMETER,  # param6
            EMPTY_PARAMETER,  # param7
        )

        return f"CHANGING_YAW: {delta_yaw}"

    def run(
        self,
        telemetry_data: telemetry.TelemetryData,
    ) -> "tuple[bool, str | None]":
        """
        Make a decision based on received telemetry data.

        telemetry_data: The drone's most recent position and orientation.

        Returns whether a command was sent and the message to report to the main process.
        """
        # Log average velocity for this trip so far
        average_velocity = self.__update_average_velocity(telemetry_data)
        self.__logger.info(
            "Average velocity: "
            f"({average_velocity.x}, {average_velocity.y}, {average_velocity.z}) m/s",
            True,
        )

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
        # Getting to the right altitude comes first, so the drone is level with the target
        delta_z = self.__target.z - telemetry_data.z
        if abs(delta_z) > self.__height_tolerance:
            return True, self.__change_altitude(delta_z)

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system
        # The yaw that would point the drone at the target, measured from the x axis
        target_yaw = math.atan2(
            self.__target.y - telemetry_data.y,
            self.__target.x - telemetry_data.x,
        )

        # Wrap into [-180, 180] so the drone always turns the short way around
        delta_yaw = math.degrees(target_yaw - telemetry_data.yaw)
        delta_yaw = (delta_yaw + HALF_TURN) % FULL_TURN - HALF_TURN

        if abs(delta_yaw) > self.__angle_tolerance:
            return True, self.__change_yaw(delta_yaw)

        # The drone is already level with the target and facing it, so there is nothing to command
        return False, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
