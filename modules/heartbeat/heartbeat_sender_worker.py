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
) -> None:
    """
    Worker process.

    The connection provides a connection to the drone via MAVLink
    The controller is used to stop and start the operation
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
    # Instantiate class object heartbeat_sender.HeartbeatSender)
    result, object = heartbeat_sender.HeartbeatSender.create(connection)
    if result != True:
        local_logger.error("Failed to create HeartbeatSender", True)
        return

    assert object is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        controller.check_pause()

        try:
            object.run()
            local_logger.info("The heartbeat has been sent.", True)
        except Exception as ex:
            local_logger.error(f"Failed to send heartbeat: {ex}", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
