"""
Heartbeat sending logic.
"""

from pymavlink import mavutil
from typing import Tuple, Optional, Literal
from ..common.modules.logger import logger
import time
# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatSender:
    """
    HeartbeatSender class to send a heartbeat
    """

    __private_key = object() # used for proper instantiation control, cannot call class until create()

    @classmethod #class method for create in case of failure (avoids crashing)
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
        args=None, 
        
    ) -> Tuple[Literal[True], "HeartbeatSender"] | Tuple[Literal[False], None]:
        """
        Falliable create (instantiation) method to create a HeartbeatSender object.
        """

        try:
            instance = cls(cls.__private_key, connection, local_logger, args)
            return True, instance 
        except Exception as e: 
            local_logger.error(f"Failed to create HeartbeatSender object: ${e}")
            return False, None 

    

    def __init__( #makes sure run() only happens when create() is successful
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger, 
        args=None,
    ):
        assert key is HeartbeatSender.__private_key, "Use create() method"

        # Do any intializiation here

        self.connection = connection
        self.local_logger = local_logger
        self.args = args

    def run(self, 
        local_logger: logger.Logger) -> bool:
        """
        Attempt to send a heartbeat message.
        Returns True if sent successfully, False if failed.
        """
        try:
            self.connection.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
            local_logger.info("Heartbeat sent!")
            return True
        except Exception as e:
            local_logger.error(f"Failed to send heartbeat: {e}")
            return False

# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
