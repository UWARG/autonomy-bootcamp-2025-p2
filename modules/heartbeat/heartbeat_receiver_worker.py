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
    controller: worker_controller.WorkerController,
    state_queue_wrapper: queue_proxy_wrapper.QueueProxyWrapper,
    period: float = 1,
    error: float = 1e-2,
    threshold: int = 5,
    # Place your own arguments here
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    controller: worker controller
    state_queue_wrapper: queue to output the receiver's state
    period: heartbeat period
    error: allowed error for the heartbeat to received within
    threshold: number of heartbeats missed before considered disconnected
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
    success, receiver = heartbeat_receiver.HeartbeatReceiver.create(connection, local_logger)

    if not success:
        local_logger.error("Failed to create Heartbeat receiver")
        return

    local_logger.info("Heartbeat receiver started", True)

    # Main loop: do work.

    while not controller.is_exit_requested():
        controller.check_pause()
        try:
            state = receiver.run(period, error, threshold)
            state_queue_wrapper.queue.put(state)
        except Exception as e:  # pylint: disable=broad-exception-caught
            local_logger.error("Run function failed: " + str(e))

    local_logger.info("Heartbeat receiver stopped")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
