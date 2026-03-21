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
    disconnect_threshold: int,
    controller: worker_controller.WorkerController,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
) -> None:
    """
    Worker process.

    The connection argument is used to connect is the MAVLink connection
    allowing heartbeat messages to be recieved. The controller gives access to
    be able to stop/pause the worker. The output_queue sends curernt state to
    main.
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
        connection=connection,
        disconnect_threshold=disconnect_threshold,
        local_logger=local_logger,
    )

    if not result:
        local_logger.error("Error: Heartbeat not recieved.", True)
        return

    assert receiver is not None

    while not controller.is_exit_requested():
        controller.check_pause()
        state = receiver.run()
        output_queue.queue.put(state)

        try:
            run_result = receiver.run()
            output_queue.queue.put(run_result)
            local_logger.info(f"Reported state: {run_result}.", True)

        except Exception as ex:  # pylint: disable=broad-exception-caught
            local_logger.error(f"Failed: {ex}.", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
