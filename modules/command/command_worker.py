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
    height_tolerance: float,
    z_speed: float,
    angle_tolerance: float,
    turning_speed: float,
    input_queue: queue_proxy_wrapper.QueueProxyWrapper,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection: MAVLink connection to drone
    target: Target position (Position object)
    height_tolerance: Tolerance for altitude (meters)
    z_speed: Speed for altitude changes (m/s)
    angle_tolerance: Tolerance for yaw angle (degrees)
    turning_speed: Speed for yaw changes (deg/s)
    input_queue: Queue to receive telemetry data from
    output_queue: Queue to send command strings to
    controller: Controller for pause/exit signals
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
        height_tolerance,
        z_speed,
        angle_tolerance,
        turning_speed,
        local_logger,
    )
    if not result:
        local_logger.error("Failed to create Command instance")
        return

    # Get Pylance to stop complaining
    assert command_instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        controller.check_pause()

        # Get telemetry data from input queue
        try:
            telemetry_data = input_queue.queue.get(timeout=0.1)
        except:  # noqa: E722  # pylint: disable=bare-except
            continue

        # Process telemetry data and get command decision
        result, command_str = command_instance.run(telemetry_data)
        if not result:
            local_logger.error("Command run failed")
            continue

        # If there's a command to output, send it to the output queue
        if command_str is not None:
            output_queue.queue.put(command_str)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
