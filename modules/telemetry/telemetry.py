"""
Telemetry gathering logic.
"""
import time

from pymavlink import mavutil

from ..common.modules.logger import logger


class TelemetryData:  # pylint: disable=too-many-instance-attributes
    """
    Python struct to represent Telemtry Data. Contains the most recent attitude and position reading.
    """

    def __init__(
        self,
        time_since_boot: int | None = None,  # ms
        x: float | None = None,  # m
        y: float | None = None,  # m
        z: float | None = None,  # m
        x_velocity: float | None = None,  # m/s
        y_velocity: float | None = None,  # m/s
        z_velocity: float | None = None,  # m/s
        roll: float | None = None,  # rad
        pitch: float | None = None,  # rad
        yaw: float | None = None,  # rad
        roll_speed: float | None = None,  # rad/s
        pitch_speed: float | None = None,  # rad/s
        yaw_speed: float | None = None,  # rad/s
    ) -> None:
        self.time_since_boot = time_since_boot
        self.x = x
        self.y = y
        self.z = z
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.z_velocity = z_velocity
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.roll_speed = roll_speed
        self.pitch_speed = pitch_speed
        self.yaw_speed = yaw_speed

    def __str__(self) -> str:
        return f"""{{
            time_since_boot: {self.time_since_boot},
            x: {self.x},
            y: {self.y},
            z: {self.z},
            x_velocity: {self.x_velocity},
            y_velocity: {self.y_velocity},
            z_velocity: {self.z_velocity},
            roll: {self.roll},
            pitch: {self.pitch},
            yaw: {self.yaw},
            roll_speed: {self.roll_speed},
            pitch_speed: {self.pitch_speed},
            yaw_speed: {self.yaw_speed}
        }}"""


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Telemetry:
    """
    Telemetry class to read position and attitude (orientation).
    """

    __private_key = object()


    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        args,  # Put your own arguments here
        local_logger: logger.Logger,
    ):
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        # Create a Telemetry object
        return True, Telemetry(cls.__private_key, connection, args, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        args,  # Put your own arguments here
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.local_logger = local_logger

    def run(
        self,
        args,  # Put your own arguments here
    ):
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp
        start = time.time()

        position = None
        attitude = None

        # both are received or 1 second has passed
        while time.time() - start < 1:
            pos_msg = self.connection.recv_match(type='LOCAL_POSITION_NED', blocking=False)
            if pos_msg is not None:
                position = pos_msg

            att_msg = self.connection.recv_match(type='ATTITUDE', blocking=False)
            if att_msg is not None:
                attitude = att_msg

            # if both are received
            if position is not None and attitude is not None:
                latest = max(attitude.time_boot_ms, position.time_boot_ms)
                
                return TelemetryData(
                    time_since_boot=latest,
                    x=position.x,
                    y=position.y,
                    z=position.z,
                    x_velocity=position.vx,
                    y_velocity=position.vy,
                    z_velocity=position.vz,
                    roll=attitude.roll,
                    pitch=attitude.pitch,
                    yaw=attitude.yaw,
                    roll_speed=attitude.rollspeed,
                    pitch_speed=attitude.pitchspeed,
                    yaw_speed=attitude.yawspeed
                )
            
        self.local_logger.error("One or more messages were not received within time limit.", True)

        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
