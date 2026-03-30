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
    state_queue_wrapper: queue_proxy_wrapper.QueueProxyWrapper,
    period: float = 1,
    # Place your own arguments here
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    args... describe what the arguments are

    controller: worker controller
    state_queue_wrapper: queue to output TelemetryData objects
    period: frequency of output
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

    success, tele = telemetry.Telemetry.create(connection, local_logger, period)

    if not success:
        local_logger.error("Failed to create Telemetry object")
        return

    local_logger.info("Telemetry started", True)

    # Main loop: do work.

    while not controller.is_exit_requested():
        controller.check_pause()
        try:
            state = tele.run()
            if state is not None:
                state_queue_wrapper.queue.put(state)
        except Exception as e:  # pylint: disable=broad-exception-caught
            local_logger.error("Run function failed: " + str(e))
    local_logger.info("Telemetry worker stopped")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
