"""
Telemtry worker that gathers GPS data.
"""

import os
import pathlib
import time

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
    timeout: float,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection: MAVLink connection to receive telemetry from
    timeout: Timeout in seconds for receiving both messages
    output_queue: Queue to send TelemetryData objects
    controller: Worker controller to handle pause/exit requests
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
    result, telemetry_instance = telemetry.Telemetry.create(connection, timeout, local_logger)
    if not result:
        local_logger.error("Failed to create Telemetry instance")
        return

    # Get Pylance to stop complaining
    assert telemetry_instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        # Method blocks worker if pause has been requested
        controller.check_pause()

        # Get telemetry data
        result, telemetry_data = telemetry_instance.run()
        if not result:
            local_logger.warning("Failed to get telemetry data")
            continue

        # Put telemetry data into output queue
        output_queue.queue.put(telemetry_data)
        local_logger.debug(f"Telemetry: {telemetry_data}", True)

        time.sleep(0.1)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
