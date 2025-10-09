"""
Telemetry gathering logic.
"""

import time

from pymavlink import mavutil

from ..common.modules.logger import logger


class TelemetryData:  # pylint: disable=too-many-instance-attributes
    """
    Python struct to represent Telemtry Data. Contains the most
    recent attitude and position reading.
    """

    def __init__(
        self: "TelemetryData",
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

    def __str__(self: "TelemetryData") -> str:
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
        cls: "type[Telemetry]",
        connection: mavutil.mavfile,
        timeout: float,
        local_logger: logger.Logger,
    ) -> "tuple[True, Telemetry] | tuple[False, None]":
        """create telemetry reader"""
        if connection is None or local_logger is None:
            return False, None

        return True, Telemetry(
            cls.__private_key, connection, timeout, local_logger
        )

    def __init__(
        self: "Telemetry",
        key: object,
        connection: mavutil.mavfile,
        timeout: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"
        self.__connection = connection
        self.__logger = local_logger
        self.__timeout = timeout

    def run(
        self: "Telemetry",
    ) -> "tuple[bool, TelemetryData | None]":
        """receive position and attitude messages"""
        start_time = time.time()
        attitude_msg = None
        position_msg = None

        while time.time() - start_time < self.__timeout:
            if attitude_msg is None:
                msg = self.__connection.recv_match(
                    type="ATTITUDE", blocking=False
                )
                if msg:
                    attitude_msg = msg
                    self.__logger.debug("Received ATTITUDE", True)

            if position_msg is None:
                msg = self.__connection.recv_match(
                    type="LOCAL_POSITION_NED", blocking=False
                )
                if msg:
                    position_msg = msg
                    self.__logger.debug("Received LOCAL_POSITION_NED", True)

            if attitude_msg and position_msg:
                time_boot = max(
                    attitude_msg.time_boot_ms, position_msg.time_boot_ms
                )

                telemetry_data = TelemetryData(
                    time_since_boot=time_boot,
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
                return True, telemetry_data

            time.sleep(0.01)

        if attitude_msg is None and position_msg is None:
            self.__logger.warning("Timeout: No telemetry received")
        elif attitude_msg is None:
            self.__logger.warning("Timeout: Missing ATTITUDE message")
        else:
            self.__logger.warning(
                "Timeout: Missing LOCAL_POSITION_NED message"
            )

        return False, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
