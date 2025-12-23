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
    queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    args... describe what the arguments are
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
    timeout = 1
    count = 0
    connected = True
    success, recieve = heartbeat_receiver.HeartbeatReceiver.create(connection, local_logger)
    if not success:
        local_logger.error("Couldn't create heartbeat reciever")
        return
    while not controller.is_exit_requested():
        detected_heartbeat = recieve.run(timeout + 1e-2)
        if detected_heartbeat is None:
            count += 1
        else:
            count = 0
            connected = True
            local_logger.info("Heartbeat detected")
        if count > 5:
            connected = False
        if not connected:
            queue.queue.put("Disconnected")
        else:
            queue.queue.put("Connected")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
