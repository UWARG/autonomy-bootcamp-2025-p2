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
    controller: worker_controller.WorkerController,  # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    connection : communicate with the drone via MAVLink
    controller : tell the worker when to pause/exit.
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
    result, sender = heartbeat_sender.HeartbeatSender.create(connection)
    if not result:
        local_logger.error("ERROR: Worker failed to instantiate HeartbeatSender", True)
        return
    assert sender is not None

    # Main loop: do work.
    while not controller.is_exit_requested():

        # Method blocks worker if pause has been requested
        controller.check_pause()

        start = time.time()

        result, value = sender.run()
        if not result:
            local_logger.error("ERROR: Worker failed to send heartbeat", True)
        else:
            local_logger.info(value, True)

        elapsed = time.time() - start
        time.sleep(max(0, 1.0 - elapsed))


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
