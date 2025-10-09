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
        # args,  # Put your own arguments here
        local_logger: logger.Logger,
    ) -> tuple:
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """

        return True, Telemetry(cls.__private_key, connection, local_logger)

        # Create a Telemetry object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        # args,  # Put your own arguments here
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        self.connection = connection
        self.local_logger = local_logger
        self.telemetry_data = TelemetryData()
        # Do any intializiation here

    def run(
        self,
        # args,  # Put your own arguments here
    ) -> TelemetryData:
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp

        position_msg = self.connection.recv_match(type="LOCAL_POSITION_NED", blocking=False)
        attitude_msg = self.connection.recv_match(type="ATTITUDE", blocking=False)

        if position_msg is not None:
            self.telemetry_data.time_since_boot = getattr(
                position_msg, "time_boot_ms", self.last_telemetry.time_since_boot
            )
            self.telemetry_data.x = getattr(position_msg, "x", self.last_telemetry.x)
            self.telemetry_data.y = getattr(position_msg, "y", self.last_telemetry.y)
            self.telemetry_data.z = getattr(position_msg, "z", self.last_telemetry.z)
            self.telemetry_data.x_velocity = getattr(
                position_msg, "vx", self.last_telemetry.x_velocity
            )
            self.telemetry_data.y_velocity = getattr(
                position_msg, "vy", self.last_telemetry.y_velocity
            )
            self.telemetry_data.z_velocity = getattr(
                position_msg, "vz", self.last_telemetry.z_velocity
            )

            self.local_logger.info("Position Updated!")

            # Update last known attitude
        if attitude_msg is not None:
            self.telemetry_data.roll = getattr(attitude_msg, "roll", self.last_telemetry.roll)
            self.telemetry_data.pitch = getattr(attitude_msg, "pitch", self.last_telemetry.pitch)
            self.telemetry_data.yaw = getattr(attitude_msg, "yaw", self.last_telemetry.yaw)
            self.telemetry_data.roll_speed = getattr(
                attitude_msg, "rollspeed", self.last_telemetry.roll_speed
            )
            self.telemetry_data.pitch_speed = getattr(
                attitude_msg, "pitchspeed", self.last_telemetry.pitch_speed
            )
            self.telemetry_data.yaw_speed = getattr(
                attitude_msg, "yawspeed", self.last_telemetry.yaw_speed
            )

            self.local_logger.info("Attitude Updated!")

        self.local_logger.info(
            f" Telemetry Data: {self.telemetry_data}, Time Stamp: {self.telemetry_data.time_since_boot}"
        )

        return self.telemetry_data


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
