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
    args=None,
    queue = queue_proxy_wrapper.QueueProxyWrapper
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    connection is the activate mavLINK connection to the drone and GCS 
    controller manages worker process, when a worker should exit, etc
    queue is where worker communication happens
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

    result, receiver = heartbeat_receiver.HeartbeatReceiver.create( connection, local_logger
    )

    # Main loop: do work.

    if not result:
        local_logger.error("Error with configuring the heartbeat receiver worker")


    while not controller.is_exit_requested():
        try:
            receiver.run(local_logger=local_logger)
            status = receiver.status
            queue.queue.put(status)
        except Exception as e:
            local_logger.error(f"Error with receiver: {e}", True)
        return
    


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
