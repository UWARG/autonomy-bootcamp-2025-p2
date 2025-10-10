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
    heartbeat_period: float,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection: MAVLink connection to send heartbeats through
    heartbeat_period: Time in seconds between heartbeats
    controller: Worker controller to handle pause/exit requests
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
    (
        result,
        heartbeat_sender_instance,
    ) = heartbeat_sender.HeartbeatSender.create(connection)
    if not result:
        local_logger.error("Failed to create HeartbeatSender instance")
        return

    # Get Pylance to stop complaining
    assert heartbeat_sender_instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        # Method blocks worker if pause has been requested
        controller.check_pause()

        # Send heartbeat
        result = heartbeat_sender_instance.run()
        if not result:
            local_logger.error("Failed to send heartbeat")
            continue

        local_logger.debug("Sent heartbeat", True)

        # Wait for the heartbeat period
        time.sleep(heartbeat_period)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
