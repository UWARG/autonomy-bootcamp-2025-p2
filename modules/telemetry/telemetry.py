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
        timeout: float,
        local_logger: logger.Logger,
    ) -> tuple[bool, "Telemetry | None"]:
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        if timeout <= 0:
            print("ERROR: Timeout must be > 0")
            return (False, None)
        return (True, cls(cls.__private_key, connection, timeout, local_logger))

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        timeout: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.timeout = timeout
        self.local_logger = local_logger

    def run(self) -> TelemetryData | None:
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp
        start_time = time.time()
        position = self.connection.recv_match(
            type="LOCAL_POSITION_NED", blocking=True, timeout=self.timeout
        )
        time_taken = self.timeout - (time.time() - start_time)
        if time_taken <= 0:
            self.local_logger.error("Timeout before ATTITUDE reached")
            return None

        attitude = self.connection.recv_match(type="ATTITUDE", blocking=True, timeout=time_taken)
        if position is None or attitude is None:
            self.local_logger.error("Did not receieve both messages")
            return None

        most_recent_time = max(position.time_boot_ms, attitude.time_boot_ms)

        telemetry_data = TelemetryData(
            time_since_boot=most_recent_time,
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
            yaw_speed=attitude.yawspeed,
        )

        return telemetry_data


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
