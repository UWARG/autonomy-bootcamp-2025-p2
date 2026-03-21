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
    z_speed: float,
    height_tolerance: float,
    angle_tolerance: float,
    turning_speed: float,
    input_queue: queue_proxy_wrapper.QueueProxyWrapper,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection: MAVLink connection used to talk to the drone
    target: target point the drone should face and match altitude with
    z_speed: altitude change speed
    height_tolerance: maximum allowed altitude error
    angle_tolerance: maximum allowed yaw error in degrees
    turning_speed: yaw turning speed
    input_queue: receives TelemetryData objects
    output_queue: sends status strings to main
    controller: controls pause/exit of worker
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
        connection,
        target,
        z_speed,
        height_tolerance,
        angle_tolerance,
        turning_speed,
        local_logger,
    )

    if not result:
        local_logger.error("command_instance failed to create", True)
        return

    assert command_instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        controller.check_pause()

        telemetry_data = input_queue.queue.get()
        if telemetry_data is None:
            break

        result, value = command_instance.run(telemetry_data)

        if not result:
            continue

        if value is not None:
            output_queue.queue.put(value)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
