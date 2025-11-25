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
        timeout_s: float,
        local_logger: logger.Logger,
    ) -> "tuple[bool, Telemetry | None]":
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        try:
            return True, Telemetry(
                Telemetry.__private_key,
                connection,
                timeout_s,
                local_logger,
            )
        except:  # pylint: disable=bare-except
            local_logger.error("Failed to create Telemetry", True)
            return False, None

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        timeout_s: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__timeout_s = timeout_s
        self.__logger = local_logger

    def run(
        self,
        _unused: None | object = None,
    ) -> "tuple[bool, TelemetryData | None]":
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp
        deadline = time.time() + self.__timeout_s
        latest_att = None
        latest_pos = None
        while time.time() < deadline and (latest_att is None or latest_pos is None):
            timeout = max(0.0, deadline - time.time())
            try:
                msg = self.__connection.recv_match(blocking=True, timeout=timeout)
            except Exception as e:  # pylint: disable=broad-except
                self.__logger.error(f"Exception while receiving telemetry: {e}", True)
                msg = None
            if not msg:
                break
            mtype = msg.get_type()
            if mtype == "ATTITUDE":
                latest_att = msg
            elif mtype == "LOCAL_POSITION_NED":
                latest_pos = msg

        if latest_att is None or latest_pos is None:
            # Timeout without both messages
            return False, None

        # Most recent timestamp across both
        time_ms = max(int(latest_att.time_boot_ms), int(latest_pos.time_boot_ms))

        data = TelemetryData(
            time_since_boot=time_ms,
            x=float(latest_pos.x),
            y=float(latest_pos.y),
            z=float(latest_pos.z),
            x_velocity=float(latest_pos.vx),
            y_velocity=float(latest_pos.vy),
            z_velocity=float(latest_pos.vz),
            roll=float(latest_att.roll),
            pitch=float(latest_att.pitch),
            yaw=float(latest_att.yaw),
            roll_speed=float(latest_att.rollspeed),
            pitch_speed=float(latest_att.pitchspeed),
            yaw_speed=float(latest_att.yawspeed),
        )

        return True, data


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
