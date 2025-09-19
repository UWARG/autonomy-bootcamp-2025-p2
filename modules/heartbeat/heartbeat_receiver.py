"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil
from ..common.modules.logger import logger
from typing import Tuple, Optional, Literal
import time

# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatReceiver:
    """
    HeartbeatReceiver class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        local_logger: logger.Logger,
        args=None
    ) ->Tuple[Literal[True], "HeartbeatReceiver"] | Tuple[Literal[False], None]:
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """

        try:
            instance = cls(cls.__private_key, connection, local_logger, args)
            return True, instance
        except Exception as e: 
            local_logger.error(f"Failed to create heart beat receiever object. ${e}")
            return False, None 
    
    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        local_logger, 
        args=None,
        
        ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here

        self.connection = connection
        self.local_logger = local_logger
        self.args=args
        self.status="Disconnected"
        self.missed_heartbeats = 0

    def run(
        self,
        local_logger: logger.Logger,
    ) -> bool:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """

        try: 
            drone_return = self.connection.recv_match(type="HEARTBEAT")
            if not drone_return:
                if self.status != "Connected": 
                    self.local_logger.info("Reconnected", True)
                self.missed_heartbeats = 0 
                self.status = "Connected"
                self.local_logger.info= (f"Status: {self.status}", True)

            else:
                self.local_logger.error(f"Missed Heart Beat", True)
                self.missed_heartbeats += 1 

                if self.missed_heartbeats >=5 and self.status != "Disconnected": 
                    self.local_logger.error(f"Disconnected, missed 5 or more heartbeats", True)
                    self.status= "Disconnected"

        except Exception as e:
            self.local_logger.error(f"Failed: {e}", True)

        time.sleep(1)
            




    # =================================================================================================
    #                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =================================================================================================
