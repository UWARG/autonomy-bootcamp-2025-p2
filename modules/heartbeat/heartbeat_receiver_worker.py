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
    heartbeat_period_s: float,
    disconnect_threshold: int,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
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
    # Instantiate class object (heartbeat_receiver.HeartbeatReceiver)
    ok, instance = heartbeat_receiver.HeartbeatReceiver.create(
        connection,
        heartbeat_period_s,
        disconnect_threshold,
        local_logger,
    )
    if not ok:
        local_logger.error("Failed to create HeartbeatReceiver instance", True)
        return
    assert instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        controller.check_pause()
        try:
            _ok, state = instance.run(local_logger)
        except Exception as e:  # pylint: disable=broad-except
            local_logger.error(f"Heartbeat receive failed: {e}", True)
            state = "Disconnected"
        output_queue.queue.put(state)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
