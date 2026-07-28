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
        local_logger: logger.Logger,
    ) -> "tuple[True, Telemetry] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        return True, Telemetry(cls.__private_key, connection, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__logger = local_logger
        self.__latest_data = TelemetryData()

    def run(
        self,
    ) -> "tuple[bool, TelemetryData]":
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        start = time.time()

        # Read MAVLink message LOCAL_POSITION_NED (32)
        position = self.__connection.recv_match(type="LOCAL_POSITION_NED", blocking=True, timeout=1)

        duration = time.time() - start

        # Read MAVLink message ATTITUDE (30)
        attitude = self.__connection.recv_match(
            type="ATTITUDE", blocking=True, timeout=max(0, 1 - duration)
        )  # both messages should be received in 1s

        if position is None or attitude is None:
            self.__logger.error("ERROR: TelemetryData timeout", True)
            return True, None

        # Update position & velocity
        if position is not None:
            self.__latest_data.x = position.x
            self.__latest_data.y = position.y
            self.__latest_data.z = position.z

            self.__latest_data.x_velocity = position.vx
            self.__latest_data.y_velocity = position.vy
            self.__latest_data.z_velocity = position.vz

        # Update attitude
        if attitude is not None:
            self.__latest_data.roll = attitude.roll
            self.__latest_data.pitch = attitude.pitch
            self.__latest_data.yaw = attitude.yaw

            self.__latest_data.roll_speed = attitude.rollspeed
            self.__latest_data.pitch_speed = attitude.pitchspeed
            self.__latest_data.yaw_speed = attitude.yawspeed

        # Return the most recent of both, and use the most recent message's timestamp
        if position is not None and attitude is not None:
            self.__latest_data.time_since_boot = max(position.time_boot_ms, attitude.time_boot_ms)
            return True, self.__latest_data

        return True, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
