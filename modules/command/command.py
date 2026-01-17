"""
Decision-making logic.
"""

import math

from pymavlink import mavutil

from ..common.modules.logger import logger
from ..telemetry import telemetry
from . import command


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
        return True, Command(cls.__private_key, connection, target, args, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        args,  # Put your own arguments here
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.local_logger = local_logger
        self.target = target
        self._velocity_sum = [0.0, 0.0, 0.0]
        self._velocity_count = 0

    def run(
        self,
        data: telemetry.TelemetryData,
        target: command.Position
    ):
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far
        msg = []

        vx = data.x_velocity
        vy = data.y_velocity
        vz = data.z_velocity
        
        self._velocity_sum[0] += vx
        self._velocity_sum[1] += vy
        self._velocity_sum[2] += vz
        self._velocity_count += 1
        
        avg_velocity = (
            round(self._velocity_sum[0] / self._velocity_count, 2),
            round(self._velocity_sum[1] / self._velocity_count, 2),
            round(self._velocity_sum[2] / self._velocity_count, 2),
        )
        self.local_logger.info(f"AVERAGE VELOCITY: {avg_velocity} m/s", True)

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
        altitude_delta = target.z - data.z
        if abs(altitude_delta) > 0.5:
            # param1 should be the target altitude (absolute), not the delta
            self.connection.mav.command_long_send(1, 0, 113, 0, target.z, 0, 0, 0, 0, 0, 0)
            msg.append(f"CHANGE ALTITUDE: {round(altitude_delta, 3)}")
        
        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system
        yaw = math.atan2(target.y - data.y, target.x - data.x) - data.yaw
        
        while yaw > math.pi:
            yaw -= 2 * math.pi
        while yaw < -math.pi:
            yaw += 2 * math.pi
        deg = math.degrees(yaw)

        if abs(deg) > 5:
            # convert to mavlink direction to match convention (-1 = ccw, 1 = cw)
            direction = -1 if deg > 0 else 1
            self.connection.mav.command_long_send(1, 0, 115, 0, abs(deg), 0, direction, 1, 0, 0, 0)
            msg.append(f"CHANGE YAW: {round(deg, 3)}")
        
        return "\n".join(msg) if msg else None
        


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
