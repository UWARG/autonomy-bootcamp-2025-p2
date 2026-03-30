"""
Decision-making logic.
"""

import math

from pymavlink import mavutil

# I'm using queue_proxy_wrapper in command.py directly, so I imported here
from utilities.workers import queue_proxy_wrapper

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
        # Put your own arguments here
        local_logger: logger.Logger,
        output_queue_wrapper: queue_proxy_wrapper.QueueProxyWrapper,
    ) -> "tuple[True, Command] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """

        try:
            instance = cls(
                cls.__private_key, connection, target, local_logger, output_queue_wrapper
            )
        except (AssertionError, TypeError, ValueError) as e:
            local_logger.error("Failed to create Command instance: " + str(e))
            return False, None
        local_logger.debug("Command instance created", True)
        return True, instance

        #  Create a Command object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        # Put your own arguments here
        local_logger: logger.Logger,
        output_queue_wrapper: queue_proxy_wrapper.QueueProxyWrapper,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        self.connection = connection
        self.target = target
        self.local_logger = local_logger
        self.sum_vx = 0
        self.sum_vy = 0
        self.sum_vz = 0
        self.count = 0
        self.output_queue_wrapper = output_queue_wrapper

        # Do any intializiation here

    def run(
        self,  # Put your own arguments here
        tele: telemetry.TelemetryData,
    ) -> None:
        """
        Finds the difference between the target telemetry and current telemetry;
        Sends a command in the form of a TelemetryData object to correct this
        """

        vx = tele.x_velocity
        vy = tele.y_velocity
        vz = tele.z_velocity

        self.sum_vx += vx
        self.sum_vy += vy
        self.sum_vz += vz

        self.count += 1

        avg_vx = self.sum_vx / self.count
        avg_vy = self.sum_vy / self.count
        avg_vz = self.sum_vz / self.count

        self.local_logger.debug(f"Avg Velocity:  ({avg_vx}, {avg_vy}, {avg_vz})")

        # Make a decision based on received telemetry data.

        # Log average velocity for this trip so far

        dx = self.target.x - tele.x
        dy = self.target.y - tele.y
        dz = self.target.z - tele.z
        target_yaw = math.atan2(dy, dx)
        dyaw = target_yaw - tele.yaw
        dyaw = (dyaw + math.pi) % (2 * math.pi) - math.pi
        dyaw_deg = math.degrees(dyaw)
        direction = 1 if dyaw_deg < 0 else -1

        if abs(dz) > 0.5:
            self.connection.mav.command_long_send(
                self.connection.target_system,
                self.connection.target_component,
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
            self.output_queue_wrapper.queue.put(f"Change Altitude: {dz}")

        elif abs(dyaw_deg) > 5:
            self.connection.mav.command_long_send(
                self.connection.target_system,
                self.connection.target_component,
                mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                0,
                dyaw_deg,
                5,
                direction,
                1,
                0,
                0,
                0,
            )
            self.output_queue_wrapper.queue.put(f"Change YAW: {dyaw_deg}")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
