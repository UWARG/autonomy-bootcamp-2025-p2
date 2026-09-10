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
    period: float,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection is the MAVLink connection to the drone.
    period is how long to wait between heartbeats, in seconds.
    controller is how the main process communicates to this worker process.
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
        local_logger.error("Failed to create HeartbeatSender", True)
        return

    # Get Pylance to stop complaining
    assert sender is not None

    # Main loop: do work.
    # The drone expects a heartbeat exactly once per period, so send on a fixed schedule
    # instead of sleeping for a whole period after each send. Sleeping only for the time
    # remaining in the period stops the sending and logging time from adding up as drift.
    next_heartbeat_time = time.time()

    # Loop forever until exit has been requested (producer)
    while not controller.is_exit_requested():
        # Method blocks worker if pause has been requested
        controller.check_pause()

        # All of the work should be done within the class
        result = sender.run()

        # Check result
        if not result:
            local_logger.error("Failed to send a heartbeat", True)
        else:
            local_logger.info("Sent a heartbeat", True)

        # Wait out the remainder of this period
        next_heartbeat_time += period
        time.sleep(max(0.0, next_heartbeat_time - time.time()))


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
