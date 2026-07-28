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
    height_tolerance: float,
    z_speed: float,
    angle_tolerance: float,
    turn_speed: float,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection: MAVLink connection b/w drone & worker
    target: position of target
    output_queue: queue of commands made to drone
    controller: worker controller to pause/exit process
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
    result, command_instance = command.Command.create(
        connection, target, height_tolerance, z_speed, angle_tolerance, turn_speed, local_logger
    )
    if not result:
        local_logger.error("ERROR: Could not initialize Command object")

    assert command_instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        # Method blocks worker if pause has been requested
        controller.check_pause()

        try:
            tel_data = input_queue.queue.get(timeout=1)
        except Exception:  # pylint: disable=broad-except
            continue
        result, message = command_instance.run(tel_data)
        if not result:
            local_logger.error("Failed to run Command", True)
            continue

        if message is not None:
            output_queue.queue.put(message)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
