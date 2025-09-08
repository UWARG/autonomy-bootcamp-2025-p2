"""
Telemetry gathering logic.
"""

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
        try:
            instance = Telemetry(Telemetry.__private_key, connection, args, local_logger)
            return True, instance
        except Exception:  # pylint: disable=broad-except
            local_logger.error("Failed to create Telemetry")
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        args,  # Put your own arguments here  # pylint: disable=unused-argument
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        # Do any intializiation here
        self._connection = connection
        self._logger = local_logger

    def run(
        self,
        timeout_seconds: float = 1.0,
    ):
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        position_msg = self._connection.recv_match(
            type="LOCAL_POSITION_NED", blocking=True, timeout=timeout_seconds
        )

        # Read MAVLink message ATTITUDE (30)
        attitude_msg = self._connection.recv_match(
            type="ATTITUDE", blocking=True, timeout=timeout_seconds
        )

        if not position_msg or not attitude_msg:
            self._logger.warning("Timeout receiving telemetry messages")
            return None

        # Use most recent timestamp
        most_recent_time = max(position_msg.time_boot_ms, attitude_msg.time_boot_ms)

        return TelemetryData(
            time_since_boot=most_recent_time,
            x=position_msg.x,
            y=position_msg.y,
            z=position_msg.z,
            x_velocity=position_msg.vx,
            y_velocity=position_msg.vy,
            z_velocity=position_msg.vz,
            roll=attitude_msg.roll,
            pitch=attitude_msg.pitch,
            yaw=attitude_msg.yaw,
            roll_speed=attitude_msg.rollspeed,
            pitch_speed=attitude_msg.pitchspeed,
            yaw_speed=attitude_msg.yawspeed,
        )


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
