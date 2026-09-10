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
    angle_tolerance: float,
    altitude_speed: float,
    turning_speed: float,
    input_queue: queue_proxy_wrapper.QueueProxyWrapper,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection is the MAVLink connection to the drone.
    target is the point in 3D space that the drone should face and match the altitude of.
    height_tolerance is how far off the target's altitude the drone may be, in metres.
    angle_tolerance is how far away from the target the drone may face, in degrees.
    altitude_speed is how quickly the drone ascends and descends, in metres per second.
    turning_speed is how quickly the drone yaws, in degrees per second.
    input_queue is the data queue, which is fed by the telemetry worker.
    output_queue is the data queue, which reports the commands made to the main process.
    controller is how the main process communicates to this worker process.
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
        angle_tolerance,
        altitude_speed,
        turning_speed,
        local_logger,
    )
    if not result:
        local_logger.error("Failed to create Command", True)
        return

    # Get Pylance to stop complaining
    assert command_instance is not None

    # Main loop: do work.
    # Loop forever until exit has been requested or sentinel value (consumer)
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
        # The class is reponsible for unpacking the intermediate type
        result, message = command_instance.run(telemetry_data)

        # Check result, no command was needed for this telemetry data
        if not result:
            continue

        local_logger.info(message, True)

        # Put an item into the queue
        # If the queue is full, the worker process will block
        # until the queue is non-empty
        output_queue.queue.put(message)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
