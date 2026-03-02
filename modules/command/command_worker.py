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
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    local_logger: logger.Logger,
    controller: worker_controller.WorkerController,
    telemetry_queue: queue_proxy_wrapper.QueueProxyWrapper,
) -> None:
    """
    Worker process.

    connection: Connection to Drone using MavLink
    target: current position of drone
    output_queue: queue of things to send to main
    local_logger: instance of logger class that writes in logs files
    controller: Controls interactivity of workers
    telemetry_queue: queue from telemetry worker
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
    value, command_object = command.Command.create(connection, target, local_logger)

    if not value:
        local_logger.error("Could not create command instance")
    else:
        # Main loop: do work.
        while not controller.is_exit_requested():
            controller.check_pause()

            data = telemetry_queue.queue.get()
            if data is not None:
                local_logger.info("Received telemetry data")

            result, change = command_object.run(data)
            if result and data is not None:
                output_queue.queue.put(change)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
