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
    period: float = 1,
    # Place your own arguments here
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    args... describe what the arguments are

    connection: a mavutil.mavfile connection
    controller: WorkerController to stop the worker
    period: how often to send heartbeats (seconds)
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

    # Main loop: do work.
    success, sender = heartbeat_sender.HeartbeatSender.create(connection, local_logger)

    if not success:
        local_logger.error("Failed to create Heartbeat sender")
        return

    local_logger.info("Heartbeat sender started", True)

    try:
        sender.run()
        local_logger.debug("Initial heartbeat sent")
    except Exception as e:  # pylint: disable=broad-exception-caught
        local_logger.error("Failed to send initial heartbeat: " + str(e))

    start_time = time.time()

    while not controller.is_exit_requested():
        controller.check_pause()
        end_time = time.time()

        try:
            if (
                end_time - start_time >= period + 1e-10
            ):  # adds 1e-10 because otherwise it runs too fast
                sender.run()
                local_logger.debug("heartbeat sent", True)
                start_time = time.time()

        except Exception as e:  # pylint: disable=broad-exception-caught
            local_logger.error("Heartbeat Failed: " + str(e))

    local_logger.info("Heartbeat sender stopped")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
