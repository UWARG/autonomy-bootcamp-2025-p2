"""
Telemetry gathering logic.
"""

import time

from pymavlink import mavutil

from typing import Tuple, Optional, Literal
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
    ) -> Tuple[Literal[True], "Telemetry"] | Tuple[Literal[False], None]:
        
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        try:
            telemetry = cls(cls.__private_key, connection, local_logger)
            return True, telemetry
        except Exception as e:
            local_logger.error(f"Failed to create telemetry object: {e}")
            return False, None
        
    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        self.connection = connection
        self.local_logger = local_logger
        self.alt = None
        self.pos = None

    def run(
        self,

        ) -> TelemetryData | None:
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp
        timeout = 1.0
        start = time.time()

        try:
            while((time.time() - start) < timeout):
                msg = self.connection.recv_match(type=["ATTITUDE", "LOCAL_POSITION_NED"], blocking=False, timeout=0.0
)

                if msg is None:
                    time.sleep(0.01)
                    continue

                if msg.get_type() == "LOCAL_POSITION_NED":
                    self.last_pos = msg
                elif msg.get_type() == "ATTITUDE":
                    self.last_attitude = msg

                if self.last_pos and self.last_attitude:

                    telemetry_data = TelemetryData(
                        time_since_boot=max(self.last_attitude.time_boot_ms, self.last_pos.time_boot_ms),
                        x=self.last_pos.x,
                        y=self.last_pos.y,
                        z=self.last_pos.z,
                        x_velocity=self.last_pos.vx,
                        y_velocity=self.last_pos.vy,
                        z_velocity=self.last_pos.vz,
                        roll=self.last_attitude.roll,
                        pitch=self.last_attitude.pitch,
                        yaw=self.last_attitude.yaw,
                        roll_speed=self.last_attitude.rollspeed,
                        pitch_speed=self.last_attitude.pitchspeed,
                        yaw_speed=self.last_attitude.yawspeed
                    )
                    self.last_attitude = None
                    self.last_pos = None
                    return telemetry_data

            self.last_attitude = None
            self.last_pos = None
            return None 
        
        except Exception as e:
            self.local_logger.error(f"Error trying to create telemetry data object: {e}", True)
            return None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
