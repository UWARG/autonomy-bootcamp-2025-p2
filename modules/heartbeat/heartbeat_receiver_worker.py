"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

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
    heartbeat_period: float,
    error_tolerance: float,
    disconnect_threshold: int,
) -> None:
    """
    Worker process.

    connection: MAVLink connection used to receive heartbeat messages from the drone.
    controller: WorkerController used to pause or stop the worker loop.
    output_queue: Queue used to send heartbeat status updates back to the main thread.
    heartbeat_period: Expected time between heartbeats (seconds), e.g. 1.0.
    error_tolerance: Extra time allowed when waiting for a heartbeat (seconds).
    disconnect_threshold: Number of consecutive missed heartbeats before
                        the connection is considered disconnected.
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
    ok, heartbeat_receiver_instance = heartbeat_receiver.HeartbeatReceiver.create(
        connection, disconnect_threshold, local_logger
    )
    if not ok or heartbeat_receiver_instance is None:
        local_logger.error("Failed to create HeartbeatReceiver", True)
        return

    # Main loop: receive heartbeat periodically until exit requested
    local_logger.info(f"heartbeat_period={heartbeat_period}", True)

    while not controller.is_exit_requested():
        controller.check_pause()

        got_heartbeat, is_connected = heartbeat_receiver_instance.run(
            heartbeat_period + error_tolerance
        )

        if not is_connected:
            local_logger.info("Drone disconnected, stopping heartbeat receiver", True)
            break

        if not got_heartbeat:
            local_logger.warning("Heartbeat missed", True)
        output_queue.queue.put({"got_heartbeat": got_heartbeat, "connected": is_connected})

        time.sleep(heartbeat_period)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
