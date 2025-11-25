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
    timeout_s: float,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    args... describe what the arguments are
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
    ok, instance = telemetry.Telemetry.create(connection, timeout_s, local_logger)
    if not ok:
        local_logger.error("Failed to create Telemetry instance", True)
        return
    assert instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        controller.check_pause()
        try:
            success, data = instance.run()
        except Exception as e:  # pylint: disable=broad-except
            local_logger.error(f"Telemetry gather failed: {e}", True)
            success, data = False, None
        if success:
            # Log and forward data
            local_logger.info(str(data), None)
            output_queue.queue.put(data)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
