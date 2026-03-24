"""
Command worker to make decisions based on Telemetry Data.
"""

import os
import pathlib
import queue

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import command
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
    input_queue: queue_proxy_wrapper.QueueProxyWrapper,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection is the MAVLink connection to the drone.
    target is the 3D position the drone should face and match altitude with.
    input_queue receives TelemetryData objects.
    output_queue receives command strings sent to the drone.
    controller is used by main to signal the worker to stop.
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
    # Instantiate class object (command.Command)
    result, commander = command.Command.create(connection, target, local_logger)
    if not result:
        local_logger.error("Failed to create Command")
        return

    assert commander is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        controller.check_pause()

        try:
            data = input_queue.queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if data is None:
            break

        results = commander.run(data)
        for result_str in results:
            local_logger.info(result_str)
            output_queue.queue.put(result_str)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
