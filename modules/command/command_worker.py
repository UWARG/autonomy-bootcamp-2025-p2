"""
Command worker to make decisions based on Telemetry Data.
"""

import os
import pathlib
import queue  ### added this for the queue.empty exception

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
    controller: worker_controller.WorkerController,
    input_queue: queue_proxy_wrapper.queue,
    output_queue: queue_proxy_wrapper.queue,
    # Place your own arguments here
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
    # Instantiate class object (command.Command)
    is_created, command_obj = command.Command.create(
        connection=connection, target=target, local_logger=local_logger
    )
    if not is_created:
        local_logger.info("command worker was not created succesfully")
        controller.request_exit()
        return

    # Main loop: do work.
    while not controller.is_exit_requested():
        try:
            current_data = input_queue.get(timeout=1)
            result = command_obj.run(current_data)
            if result is not None:
                output_queue.put(result)
        except queue.Empty:
            # No data available, check exit flag and continue
            continue


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
