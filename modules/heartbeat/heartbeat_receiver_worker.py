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
    disconnect: int,
    heartbeat_dur: float,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,  # Place your own arguments here
) -> None:
    """
    Worker process.

    connection: MAVLink Connection b/w drone and worker
    disconnect: Threshold of failed receive attempts before status is disconnected
    output_queue: Queue for output connection status
    controller: worker controller to pause/exit

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
    result, receiver = heartbeat_receiver.HeartbeatReceiver.create(
        connection, heartbeat_dur, disconnect, local_logger
    )
    if not result:
        local_logger.error("ERROR: Worker failed to create HeartbeatReceiver", True)

    assert receiver is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        # check if process is paused
        controller.check_pause()

        result, connected = receiver.run()

        if not result:
            local_logger.error("ERROR: Worker could not run HeartbeatReceiver Successfully", True)
            break

        output_queue.queue.put(connected)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
