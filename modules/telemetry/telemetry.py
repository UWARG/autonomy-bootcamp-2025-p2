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
        period: float = 1,
    ) -> "tuple[True, Telemetry] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        try:
            instance = cls(cls.__private_key, connection, local_logger, period)
        except (ValueError, TypeError, RuntimeError) as e:
            local_logger.error("Failed to create Telemetry instance: " + str(e))
            return False, None
        local_logger.debug("Telemetry instance created", True)
        return True, instance

        # Create a Telemetry object

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,  # Put your own arguments here
        local_logger: logger.Logger,
        period: float,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        self.connection = connection
        self.local_logger = local_logger
        self.period = period
        # Do any intializiation here

    def run(self) -> TelemetryData | None:  # Put your own arguments here
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp

        attitude = None
        position = None

        start_time = time.time()

        while time.time() - start_time < self.period:
            msg = self.connection.recv_match(
                type=["ATTITUDE", "LOCAL_POSITION_NED"], blocking=False
            )

            if msg is None:
                continue
            if msg.get_type() == "ATTITUDE":
                attitude = msg
                self.local_logger.debug("Received ATTITUDE")
            elif msg.get_type() == "LOCAL_POSITION_NED":
                position = msg
                self.local_logger.debug("Received LOCAL_POSITION_NED")

            if attitude and position:
                break

        if attitude and position:
            timestamp = max(attitude.time_boot_ms, position.time_boot_ms)

            telemetry = TelemetryData(
                timestamp,
                position.x,  # m
                position.y,  # m
                position.z,  # m
                position.vx,  # m/s
                position.vy,  # m/s
                position.vz,  # m/s
                attitude.roll,  # rad
                attitude.pitch,  # rad
                attitude.yaw,  # rad
                attitude.rollspeed,  # rad/s
                attitude.pitchspeed,  # rad/s
                attitude.yawspeed,  # rad/s
            )
            return telemetry

        self.local_logger.warning("Telemetry timeout")
        return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
