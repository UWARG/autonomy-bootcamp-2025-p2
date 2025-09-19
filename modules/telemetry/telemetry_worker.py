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
    controller: worker_controller.WorkerController,
    queue = queue_proxy_wrapper.QueueProxyWrapper
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    connection is the activate mavLINK connection to the drone and GCS 
    controller manages worker process, when a worker should exit, etc
    queue is where worker communication happens
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
    results, tele = telemetry.Telemetry.create(connection, local_logger)

    # Main loop: do work.
    if not results: 
        local_logger.error("Error running telemetry worker, failed to create.")
        return

    while not controller.is_exit_requested():
        try:
            info = tele.run(local_logger)
            if info: 
                local_logger.info(f"Telemetry data queued: {info}", True)
                queue.queue.put(info)
            else: 
                local_logger.error("Telemetry run failed", True)
        except Exception as e:
            local_logger.error(f"Error when running telemetry object {e}", True)
        
        time.sleep(1)
# include any telemtry related commands

    local_logger.info("Worker has stopped.", True)
    


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
