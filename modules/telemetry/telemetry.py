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
        # Put your own arguments here
        local_logger: logger.Logger,
    ) -> tuple[bool, "Command | None"]:
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        return True, cls(cls.__private_key, connection, local_logger)  # Create a Telemetry object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        # Put your own arguments here
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.logger = local_logger

    def run(
        self,
        # Put your own arguments here
    ) -> TelemetryData | None:
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp

        pos_msg = None
        att_msg = None
        start_time = time.time()

        while time.time() - start_time < 1.0:
            msg = self.connection.recv_match(
                type=["LOCAL_POSITION_NED", "ATTITUDE"], blocking=True, timeout=0.1
            )

            if not msg:
                continue

            if msg.get_type() == "LOCAL_POSITION_NED":
                pos_msg = msg
            elif msg.get_type() == "ATTITUDE":
                att_msg = msg

            if pos_msg and att_msg:
                latest_timestamp = max(pos_msg.time_boot_ms, att_msg.time_boot_ms)

                return TelemetryData(
                    time_since_boot=latest_timestamp,
                    x=pos_msg.x,
                    y=pos_msg.y,
                    z=pos_msg.z,
                    x_velocity=pos_msg.vx,
                    y_velocity=pos_msg.vy,
                    z_velocity=pos_msg.vz,
                    roll=att_msg.roll,
                    pitch=att_msg.pitch,
                    yaw=att_msg.yaw,
                    roll_speed=att_msg.rollspeed,
                    pitch_speed=att_msg.pitchspeed,
                    yaw_speed=att_msg.yawspeed,
                )

        self.logger.error("Telemetry timed out: Failed to receive both messages within 1 second.")
        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
