"""
Heartbeat worker that receives heartbeats periodically.
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
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
) -> None:
    """
    Worker process.

    connection is the connection to the drone. Gets passed to the heartbeat_sender.
    controller is how the main process communicates to this worker process.
    connection_status_queue is a queue of length 1 that contains the connection status
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
    # Instantiate class object
    result, heartbeat_instance = heartbeat_receiver.HeartbeatReceiver.create(
        connection, local_logger
    )
    if not result:
        local_logger.error("Worker failed to create heartbeat_instance")
        return

    # Loop forever until exit has been requested (producer)
    while not controller.is_exit_requested():
        # Method blocks worker if pause has been requested
        controller.check_pause()

        # All of the work should be done within the class
        # Getting the output is as easy as calling a single method
        result, connection_status = heartbeat_instance.run_receive_heartbeat()

        # Check result
        if not result:
            continue

        output_queue.queue.put(connection_status)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
