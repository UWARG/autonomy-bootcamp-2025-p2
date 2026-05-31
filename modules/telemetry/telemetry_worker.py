"""
Telemtry worker that gathers GPS data.
"""

import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import telemetry
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def telemetry_worker(
    connection: mavutil.mavfile,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process to collect telemetry from the drone and queue it.

    connection: MAVLink connection file object.
    output_queue: Synchronized queue proxy to pass telemetry data.
    controller: Worker controller managing process state (exit/pause).
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
    # Instantiate class object (telemetry.Telemetry)
    result, telemetry_instance = telemetry.Telemetry.create(connection, local_logger)
    if not result:
        local_logger.error("Failed to initialize Telemetry", True)
        return

    assert telemetry_instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        # Check if the process needs to pause
        controller.check_pause()

        # Run receiving logic (blocks for up to 1 second)
        success, telemetry_data = telemetry_instance.run()
        if success and telemetry_data is not None:
            output_queue.queue.put(telemetry_data)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
