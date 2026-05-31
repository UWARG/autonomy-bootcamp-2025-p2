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
        local_logger: logger.Logger,
    ) -> "tuple[True, Telemetry] | tuple[False, None]":
        """
        Fallible create (instantiation) method to create a Telemetry object.
        """
        if connection is None:
            local_logger.error("Failed to create Telemetry: connection is None", True)
            return False, None

        instance = cls(cls.__private_key, connection, local_logger)
        return True, instance

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"
        self.__connection = connection
        self.__logger = local_logger

    def run(self) -> "tuple[bool, TelemetryData | None]":
        """
        Receive LOCAL_POSITION_NED and ATTITUDE messages from the drone,
        combining them together to form a single TelemetryData object.
        """
        window_start = time.time()
        received_attitude = False
        received_position = False
        attitude_msg = None
        position_msg = None

        while True:
            elapsed = time.time() - window_start
            if elapsed >= 1.0:
                self.__logger.error(
                    "Telemetry timed out: did not receive both ATTITUDE and LOCAL_POSITION_NED within 1 second.",
                    True,
                )
                return False, None

            remaining_time = 1.0 - elapsed

            try:
                # Read either ATTITUDE or LOCAL_POSITION_NED
                msg = self.__connection.recv_match(
                    type=["ATTITUDE", "LOCAL_POSITION_NED"], blocking=True, timeout=remaining_time
                )
            except Exception as e:
                self.__logger.error(f"Error receiving telemetry message: {e}", True)
                return False, None

            if msg is not None:
                msg_type = msg.get_type()
                if msg_type == "ATTITUDE":
                    attitude_msg = msg
                    received_attitude = True
                elif msg_type == "LOCAL_POSITION_NED":
                    position_msg = msg
                    received_position = True

                # If both are received, construct and return TelemetryData
                if received_attitude and received_position:
                    assert attitude_msg is not None
                    assert position_msg is not None

                    time_since_boot = max(attitude_msg.time_boot_ms, position_msg.time_boot_ms)

                    telemetry_data = TelemetryData(
                        time_since_boot=time_since_boot,
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


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
