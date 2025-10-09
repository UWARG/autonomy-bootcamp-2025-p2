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
    heartbeat_period: float,
    disconnect_threshold: int,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection: MAVLink connection to receive heartbeats from
    heartbeat_period: Expected time between heartbeats in seconds
    disconnect_threshold: Number of missed heartbeats before disconnect
    output_queue: Queue to send connection status updates
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
    # Instantiate class object (heartbeat_receiver.HeartbeatReceiver)
    (
        result,
        heartbeat_receiver_instance,
    ) = heartbeat_receiver.HeartbeatReceiver.create(connection, disconnect_threshold, local_logger)
    if not result:
        local_logger.error("Failed to create HeartbeatReceiver instance")
        return

    # Get Pylance to stop complaining
    assert heartbeat_receiver_instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        # Method blocks worker if pause has been requested
        controller.check_pause()

        # Try to receive heartbeat
        result, status = heartbeat_receiver_instance.run(heartbeat_period)
        if not result:
            local_logger.error("Failed to check heartbeat")
            continue

        # Put status into output queue
        output_queue.queue.put(status)
        local_logger.debug(f"Status: {status}", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
