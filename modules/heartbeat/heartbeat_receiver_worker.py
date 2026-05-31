"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import heartbeat_receiver
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def heartbeat_receiver_worker(
    connection: mavutil.mavfile,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process to receive heartbeats from the drone and report status.

    connection: MAVLink connection file object.
    output_queue: Synchronized queue proxy to report status back.
    controller: Worker controller managing process state (exit/pause).
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
    # Instantiate class object (heartbeat_receiver.HeartbeatReceiver)
    result, receiver_instance = heartbeat_receiver.HeartbeatReceiver.create(
        connection,
        local_logger
    )
    if not result:
        local_logger.error("Failed to initialize HeartbeatReceiver", True)
        return

    assert receiver_instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        # Check if the process needs to pause
        controller.check_pause()

        # Run receiving logic (blocks for up to 1 second)
        success, state = receiver_instance.run()
        if success:
            output_queue.queue.put(state)
        else:
            local_logger.warning("Heartbeat reception cycle encountered an issue", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
