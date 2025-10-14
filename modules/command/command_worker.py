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
    controller: worker_controller.WorkerController,
    input_queue: queue_proxy_wrapper.QueueProxyWrapper,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    target: command.Position,
) -> None:
    """
    Worker process.

    connection is the connection to the drone. Gets passed to the heartbeat_sender.
    controller is how the main process communicates to this worker process.
    telemetry_queue is a queue of length 1 that contains the latest telemetry data
    command_queue is a queue of length 2 that contains a description of the commands sent
    target is the 3d position of the target
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
    result, command_instance = command.Command.create(connection, target, local_logger)
    if not result:
        local_logger.error("Worker failed to create command_instance")
        return

    # Loop forever until exit has been requested (producer)
    while not controller.is_exit_requested():
        # Method blocks worker if pause has been requested
        controller.check_pause()

        # Get an item from the queue
        # If the queue is empty, the worker process will block
        # until the queue is non-empty
        telemetry_data = input_queue.queue.get()

        # Exit on sentinel
        if telemetry_data is None:
            break

        # All of the work should be done within the class
        # Getting the output is as easy as calling a single method
        result, string_command = command_instance.run_generate_command(telemetry_data)

        # Check result
        if not result:
            continue

        output_queue.queue.put(string_command)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
