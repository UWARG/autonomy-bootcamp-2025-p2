"""
Command worker to make decisions based on Telemetry Data.
"""

import os
import pathlib
import queue  # imported to use catch queue.Empty


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
    input_queue_wrapper: queue_proxy_wrapper.QueueProxyWrapper,
    output_queue_wrapper: queue_proxy_wrapper.QueueProxyWrapper,
    target: command.Position,
    # Place your own arguments here
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    input_queue_wrapper: input queue to take in TelemetryData objects
    output_queue_wrapper: output queue to send to command.py
    target: target position to base telemtry data on
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
    success, com = command.Command.create(connection, target, local_logger, output_queue_wrapper)

    if not success:
        local_logger.error("Failed to create command object")
        return

    local_logger.info("Command object started", True)

    # Main loop: do work.

    while not controller.is_exit_requested():
        controller.check_pause()
        try:
            tele = input_queue_wrapper.queue.get(timeout=1)
        except queue.Empty:
            continue
        try:
            com.run(tele)
        except (AttributeError, TypeError, ValueError) as e:
            local_logger.error("Failed to process telemetry: " + str(e))
    local_logger.info("Command worker stopped")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
