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

        return True, Telemetry(cls.__private_key, connection, timeout, local_logger)

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
        self.__last_attitude = None
        self.__last_position = None
        self.__last_time = time.time()

    def run(
        self: "Telemetry",
    ) -> "tuple[bool, TelemetryData | None]":
        """receive position and attitude messages"""
        self.__last_time = time.time()

        while (time.time() - self.__last_time) < self.__timeout:
            msg = self.__connection.recv_match(blocking=False)
            if msg is None:
                continue

            if msg.get_type() == "LOCAL_POSITION_NED":
                self.__last_position = msg
                self.__last_time = time.time()
                self.__logger.debug("Received LOCAL_POSITION_NED", True)
            elif msg.get_type() == "ATTITUDE":
                self.__last_attitude = msg
                self.__last_time = time.time()
                self.__logger.debug("Received ATTITUDE", True)

            # only return if we have both types
            if not self.__last_position or not self.__last_attitude:
                continue

            position = self.__last_position
            attitude = self.__last_attitude
            if position is not None and attitude is not None:
                telemetry_data = TelemetryData(
                    time_since_boot=max(
                        self.__last_attitude.time_boot_ms,
                        self.__last_position.time_boot_ms,
                    ),
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
                # reset messages after returning
                self.__last_attitude = None
                self.__last_position = None
                return True, telemetry_data

        # reset messages on timeout
        self.__last_attitude = None
        self.__last_position = None
        self.__logger.warning("Timeout: No complete telemetry pair received")
        return False, None


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
