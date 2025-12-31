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
    height_tolerance: float,
    z_speed: float,
    angle_tolerance: float,
    turning_speed: float,
) -> None:
    """
    Worker process.

    connection is the MAVLink connection to the drone
    target is the target position
    input_queue is where we receive telemetry data
    output_queue is where we send command status strings
    controller is how the main process communicates to this worker process
    height_tolerance, z_speed, angle_tolerance, turning_speed are command parameters
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

    result, cmd = command.Command.create(
        connection, target, height_tolerance, z_speed, angle_tolerance, turning_speed, local_logger
    )

    if not result:
        local_logger.error("Failed to create command", True)
        return

    assert cmd is not None

    while not controller.is_exit_requested():
        controller.check_pause()

        telemetry_data = input_queue.queue.get()
        if telemetry_data is None:
            continue

        result, status = cmd.run(telemetry_data)

        if not result:
            local_logger.error("Failed to run command", True)
            continue

        output_queue.queue.put(status)

    local_logger.info("Command worker exiting", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
