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
    local_logger: logger.Logger,
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    connection: Establishes communication between workers using pymavlink library
    controller: How the main process communicates with the workers
    local_logger: Logs the results of heartbeat messages in log files
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

    value, sender_instance = heartbeat_sender.HeartbeatSender.create(connection, local_logger)
    # Check if connection can be established
    if not value:
        local_logger.error("Failed to establish heartbeat sender", True)
        return

    # Main loop: do work.
    while not controller.is_exit_requested():
        # check if controller is paused
        controller.check_pause()

        # send heartbeat signal through running instance
        start = time.time()
        result = sender_instance.run()
        time_elapsed = time.time() - start
        local_logger.info("Heartbeat sent")

        # create a system for time to be exactly one second
        sleep_time = 1 - time_elapsed
        time.sleep(sleep_time)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
