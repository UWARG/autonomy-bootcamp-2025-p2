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
# The two MAVLink messages that make up a single TelemetryData
ATTITUDE_MESSAGE = "ATTITUDE"
LOCAL_POSITION_NED_MESSAGE = "LOCAL_POSITION_NED"


class Telemetry:
    """
    Telemetry class to read position and attitude (orientation).
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        timeout: float,
        local_logger: logger.Logger,
    ) -> "tuple[True, Telemetry] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Telemetry object.

        connection: MAVLink connection to the drone.
        timeout: How long to wait for both messages before giving up, in seconds.
        local_logger: Existing logger from the worker process.

        Returns whether the object was created and the object itself.
        """
        # Without a connection there are no messages to read
        if connection is None:
            local_logger.error("No connection was provided", True)
            return False, None

        # A non-positive timeout would expire before any message could be read
        if timeout <= 0:
            local_logger.error(f"Timeout must be positive, got {timeout}", True)
            return False, None

        return True, Telemetry(cls.__private_key, connection, timeout, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        timeout: float,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        # Do any intializiation here
        self.__connection = connection
        self.__timeout = timeout
        self.__logger = local_logger

    def run(
        self,
    ) -> "tuple[bool, TelemetryData | None]":
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.

        Returns whether both messages arrived in time and the combined data.
        """
        # Read MAVLink message LOCAL_POSITION_NED (32)
        # Read MAVLink message ATTITUDE (30)
        # Return the most recent of both, and use the most recent message's timestamp
        attitude = None
        position = None

        # Both messages have to arrive within the timeout, so the deadline is shared between them
        deadline = time.time() + self.__timeout
        while attitude is None or position is None:
            remaining = deadline - time.time()
            if remaining <= 0:
                break

            try:
                message = self.__connection.recv_match(
                    type=[ATTITUDE_MESSAGE, LOCAL_POSITION_NED_MESSAGE],
                    blocking=True,
                    timeout=remaining,
                )
            # Catching all exceptions for library call
            # pylint: disable-next=broad-exception-caught
            except Exception as e:
                self.__logger.error(f"Could not receive telemetry: {e}", True)
                return False, None

            # Timed out waiting for a message
            if message is None:
                break

            # Keep only the most recent of each message type
            if message.get_type() == ATTITUDE_MESSAGE:
                attitude = message
            else:
                position = message

        # Only part of the pair arrived, so there is nothing complete to report
        if attitude is None or position is None:
            self.__logger.warning(
                f"Timed out after {self.__timeout}s before receiving both "
                f"{ATTITUDE_MESSAGE} and {LOCAL_POSITION_NED_MESSAGE}, restarting",
                True,
            )
            return False, None

        telemetry_data = TelemetryData(
            # The timestamp is shared, so use the one from the more recent message
            time_since_boot=max(attitude.time_boot_ms, position.time_boot_ms),
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

        return True, telemetry_data


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
