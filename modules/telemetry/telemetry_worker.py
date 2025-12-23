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
    queue: queue_proxy_wrapper.QueueProxyWrapper,  # Place your own arguments here
    # Add other necessary worker arguments here
) -> None:
    """
    Docstring for telemetry_worker

    :param connection: connection object
    :type connection: mavutil.mavfile
    :param controller: controller object
    :type controller: worker_controller.WorkerController
    :param queue: output queue
    :type queue: queue_proxy_wrapper.QueueProxyWrapper
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
    _, telemetry_obj = telemetry.Telemetry.create(connection, local_logger)
    while not controller.is_exit_requested():
        data = telemetry_obj.run()
        time.sleep(0.1)
        if data is not None and data != "Not Ready":
            queue.queue.put("Recieved Telemetry Data")
            local_logger.info(data)
        elif data is None:
            local_logger.info("timeout")
    # Main loop: do work.


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
