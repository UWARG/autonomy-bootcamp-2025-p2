"""
Telemtry worker that gathers GPS data.
"""

import time
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
    telemetry_period: float,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection: MAVLink connection between the drone and worker
    output_queue: queue with telemetry data
    telemetry_period: period b/w telemetry readings
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
    # Instantiate class object (telemetry.Telemetry)
    result, telemetry_instance = telemetry.Telemetry.create(connection, local_logger)
    if not result:
        local_logger.error("ERROR: Worker failed to create a Telemetry instance", True)

    assert telemetry_instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        # Method blocks worker if pause has been requested
        controller.check_pause()

        start = time.time()

        result, tel_data = telemetry_instance.run()
        if not result:
            local_logger.error("ERROR: Could not run Telemetry", True)
            continue

        if tel_data is not None:
            output_queue.queue.put(tel_data)

        elapsed = time.time() - start
        time.sleep(max(0.0, telemetry_period - elapsed))


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
