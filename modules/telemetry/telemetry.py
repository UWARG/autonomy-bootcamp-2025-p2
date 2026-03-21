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
        local_logger: logger.Logger,
    ) -> "tuple[bool, Telemetry]":
        """
        Falliable create (instantiation) method to create a Telemetry object.
        """
        return True, Telemetry(cls.__private_key, connection, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Telemetry.__private_key, "Use create() method"

        self.__connection = connection
        self.__local_logger = local_logger

    def run(
        self,
    ) -> "tuple[bool, TelemetryData | None]":
        """
        Receive telemetry messages and return the latest combined telemetry data.
        """
        attitude_msg = None
        position_msg = None

        while True:
            msg = self.__connection.recv_match(
                type=["ATTITUDE", "LOCAL_POSITION_NED"],
                blocking=True,
                timeout=1.0,
            )

            if msg is None:
                self.__local_logger.error(
                    "Unable to get both attitude and position data",
                    True,
                )
                return False, None

            if msg.get_type() == "ATTITUDE":
                attitude_msg = msg
            elif msg.get_type() == "LOCAL_POSITION_NED":
                position_msg = msg

            if attitude_msg is not None and position_msg is not None:
                break

        time_to_boot_result = max(
            position_msg.time_boot_ms,
            attitude_msg.time_boot_ms,
        )

        telemetry_data = TelemetryData(
            time_since_boot=time_to_boot_result,
            yaw=attitude_msg.yaw,
            x=position_msg.x,
            y=position_msg.y,
            z=position_msg.z,
        )

        # Return the most recent of both, and use the most recent message's timestamp
        return True, telemetry_data


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
