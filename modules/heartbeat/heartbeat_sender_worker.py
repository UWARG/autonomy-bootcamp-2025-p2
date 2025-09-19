"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import worker_controller
from . import heartbeat_sender
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def heartbeat_sender_worker(
    connection: mavutil.mavfile,
    controller: worker_controller.WorkerController,
    #use proper type annotations int
    # Place your own arguments here
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    args... describe what the arguments are
    Arguments contain information transmitted from workers via connection proccesses through HEARTBEAT messages.
    These HEARTBEAT messages are sent periodically to indicate the system is alive and functioning. Controllers
    controller the information flow from different workers.
    """
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    # Instantiate logger
    worker_name = pathlib.Path(__file__).stem
    process_id = os.getpid()
    result, local_logger = logger.Logger.create(f"{worker_name}_{process_id}", True)
    if not result:
        print("ERROR: Worker failed to create logger")
        return

    # Get Pylance to stop complaining
    assert local_logger is not None

    local_logger.info("Logger initialized", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Instantiate class object (heartbeat_sender.HeartbeatSender)
    result, sender = heartbeat_sender.HeartbeatSender.create(
        connection, local_logger)

    # Main loop: do work.

    if not result:
        local_logger.error("Failed to create heart beat sender")
        return


    while not controller.is_exit_requested(): 
        try: 
            success = sender.run()
            if not success:
                local_logger.error("Failed to send heartbeat")

        except Exception as e: 
            local_logger.error(f"Error with heartbeat: {e}", True)
        time.sleep(1)


        


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
