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
        connection: mavutil.mavfile,  # Put your own arguments here
        local_logger: logger.Logger,
    ) -> tuple[bool, Telemetry]:  # pylint: disable=undefined-variable
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        if connection is not None:
            return True, cls(cls.__private_key, connection, local_logger=local_logger)
        local_logger.error("Failed to create a Telemetry object due to missing connection")
        return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,  # Put your own arguments here
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.local_logger = local_logger

    def run(
        self,  # Put your own arguments here
    ) -> Telemetry | None:
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp

        start_time = time.time()
        return_telemetry = TelemetryData()

        local_position = None
        attitude = None
        ### Run until time is greater than one
        while time.time() - start_time <= 1:

            msg = self.connection.recv_match(type=["ATTITUDE", "LOCAL_POSITION_NED"], timeout=0.1)

            if not msg:
                continue
            if msg.get_type() == "LOCAL_POSITION_NED":
                local_position = msg
            if msg.get_type() == "ATTITUDE":
                attitude = msg
            if attitude and local_position:
                break

        # Set telemetry data to corresponding incoming data
        if attitude and local_position:
            return_telemetry.time_since_boot = max(
                local_position.time_boot_ms, attitude.time_boot_ms
            )
            return_telemetry.roll = attitude.roll
            return_telemetry.pitch = attitude.pitch
            return_telemetry.yaw = attitude.yaw
            return_telemetry.roll_speed = attitude.rollspeed
            return_telemetry.pitch_speed = attitude.pitchspeed
            return_telemetry.yaw_speed = attitude.yawspeed
            return_telemetry.x = local_position.x
            return_telemetry.y = local_position.y
            return_telemetry.z = local_position.z
            return_telemetry.x_velocity = local_position.vx
            return_telemetry.y_velocity = local_position.vy
            return_telemetry.z_velocity = local_position.vz
            return return_telemetry
        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
