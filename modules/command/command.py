"""
Decision-making logic.
"""

import math
import time 
from pymavlink import mavutil
import time

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
    ):
        """
        Falliable create (instantiation) method to create a Command object.
        """
        pass  #  Create a Command object
        try: 
            cmd = (cls.__private_key, connection, target, local_logger)
            return cmd, True 
        
        except Exception as e:
            local_logger.error(f"Failure to create command object: {e}")
            return False, None 

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection=connection, 
        self.target = target, 
        self.local_logger = local_logger
        self.start_pos = None
        self.start_time = None
        self.data = None
        self.time = time 

    def run(self,
        data: telemetry.TelemetryData
    ):
        """
        Make a decision based on received telemetry data.
        """
        # Log average velocity for this trip so far

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below

        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system

        messages_all= []

        if self.start_pos is None:
            self.start_pos = Position(data.x, data.y, data.z)
            self.start_time = time.time()

        if self.previous_data:
            time_elapsed = time.time() - self.start_time

            if time_elapsed > 0: 
                dx = data.x - self.start_pos.x
                dy = data.y - self.status_pos.y
                dz = data.z - self.status_pos.z

                displacement = math.sqrt(dx**2, + dy**2 + dz**2)
                avg_velocity = displacement / time_elapsed
                message_pos = self.local_logger.info(f"Average velocity for this trip so far: {avg_velocity:.2}", True)
                messages_all.append(message_pos)

                self.previous.data = data

        
        drone_altitude = self.target.y - data.y
        if abs(drone_altitude) > 0.5: 
            self.connection.mav.command_long_self(
                command=mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                target_system = 1,
                target_component = 0,
                confirmation = 0,
                param1 = 0, 
                param2 = 0, 
                param3 = 0, 
                param4 = 0,
                param5 = 0, 
                param6 = 0,
                param7 = self.target.y,
            )
            message_alt = self.local_logger.info(f"CHANGE_ALTITUDE: {drone_altitude:.2}", True)
            messages_all.append(message_alt)
            return [messages_all]




        x = self.target.x - data.x 
        y = self.target.y - data.y
        yaw_angle_radians_want = math.atan2(x,y) #the angle between the x axis and the vector towards the point
        yaw_calc=yaw_angle_radians_want-data.yaw
        yaw_calc_2 = (yaw_calc + math.pi) % (2 * math.pi) - math.pi  
        yaw_calc_degrees = math.degrees(yaw_calc_2)

        if abs(yaw_calc_degrees) > 5:
            self.connection.mav.command_long_self(
                command=mavutil.mavlink.MAV_CMD_CONDITION_YAW,
                target_system = 1,
                target_component = 0,
                confirmation = 0,
                param1 = yaw_calc_degrees, 
                param2 = 5, 
                param3 = 1, 
                param4 = 1,
                param5 = 0, 
                param6 = 0,
                param7 = 0,
            )
            message_yaw = self.local_logger.info(f"CHANGE_YAW: {yaw_calc_degrees:.2}", True)
            messages_all.append(message_yaw)
            return [messages_all]

        return []



    



            


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
