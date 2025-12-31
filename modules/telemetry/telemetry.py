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
    ) -> "tuple[bool, Telemetry | None]":
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        try:
            telemetry = cls(cls.__private_key, connection, local_logger)
            return True, telemetry
        except Exception as e:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Failed to create Telemetry: {e}")
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        self._connection = connection
        self._logger = local_logger

        self._last_attitude = None
        self._last_position = None

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
        timeout_s = 1.0
        start_time = time.time()

        self._last_attitude = None
        self._last_position = None

        while time.time() - start_time <= timeout_s:

            msg = self._connection.recv_match(
                type=["ATTITUDE", "LOCAL_POSITION_NED"],
                blocking=True,
                timeout=0.2,
            )

            if msg is None:
                if time.time() - start_time > timeout_s:
                    continue

            start_time = time.time()

            msg_type = msg.get_type()

            if msg_type == "ATTITUDE":
                self._last_attitude = msg
            elif msg_type == "LOCAL_POSITION_NED":
                self._last_position = msg

            if self._last_attitude and self._last_position:
                time_since_boot = max(
                    self._last_attitude.time_boot_ms,
                    self._last_position.time_boot_ms,
                )

                return TelemetryData(
                    time_since_boot=time_since_boot,
                    x=self._last_position.x,
                    y=self._last_position.y,
                    z=self._last_position.z,
                    x_velocity=self._last_position.vx,
                    y_velocity=self._last_position.vy,
                    z_velocity=self._last_position.vz,
                    roll=self._last_attitude.roll,
                    pitch=self._last_attitude.pitch,
                    yaw=self._last_attitude.yaw,
                    roll_speed=self._last_attitude.rollspeed,
                    pitch_speed=self._last_attitude.pitchspeed,
                    yaw_speed=self._last_attitude.yawspeed,
                )


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
