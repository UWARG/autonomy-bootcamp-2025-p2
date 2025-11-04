"""
Command worker to make decisions based on Telemetry Data.
"""

import os
import pathlib

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

    local_logger.info("Logger initialized for Command Worker", True)

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Instantiate class object (command.Command)

    result, command_instance = command.Command.create(connection, target, local_logger)

    if not result:
        local_logger.error("Could not initialize Command object")
        return

    local_logger.info("Command object created successfully")

    # Main loop: do work
    while not controller.is_exit_requested():
        controller.check_pause()

        try:
            current_telemetry = input_queue.queue.get(timeout=0.5)

            if current_telemetry is None:
                local_logger.warning("Received None from telemetry queue")
                continue

            command_string = command_instance.run(current_telemetry)

            if command_string:
                output_queue.queue.put(command_string)

        except TimeoutError:
            local_logger.debug("Queue timeout or error")
            continue

    local_logger.info("Command worker stopped")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
