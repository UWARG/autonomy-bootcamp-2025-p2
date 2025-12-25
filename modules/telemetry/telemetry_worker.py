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
    controller: worker_controller.WorkerController,
    local_logger: logger.Logger,
    output: queue_proxy_wrapper.QueueProxyWrapper,
) -> None:
    """
    Worker process.

    connection: Connection to Drone using MavLink
    output: queue of things to be acted upon by workers
    local_logger: instance of logger class that writes in logs files
    controller: Controls interactivity of workers
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
        local_logger.error("Could not create telemetry instance")
        return
    local_logger.info("Telemetry instance created")

    # Main loop: do work.
    while not controller.is_exit_requested():
        controller.check_pause()

        value, data = telemetry_instance.run()
        if not value:
            local_logger.warning("Telemetry data not received, timed out")
            break
        output.queue.put(data)
        local_logger.info(f"Telemetry data {data}")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
