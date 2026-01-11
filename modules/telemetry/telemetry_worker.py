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
    controller: worker_controller.WorkerController,  # Place your own arguments here
    telemetry_queue: queue_proxy_wrapper.QueueProxyWrapper,
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    args... describe what the arguments are
        connection: MAVLink connection to the drone
        controller: the shared worker controller
        telemetry_queue: Queue to send the objects of TelemetryData to
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
    result, telemetry_inst = telemetry.Telemetry.create(connection, local_logger)
    if not result or telemetry_inst is None:
        local_logger.error("Failed to create Telemetry instance")
        return

    # Main loop: do work.
    while not controller.is_exit_requested():
        data = telemetry_inst.run()
        if data:
            telemetry_queue.queue.put(data)
            local_logger.info("Telemetry data successfully gathered and queued")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
