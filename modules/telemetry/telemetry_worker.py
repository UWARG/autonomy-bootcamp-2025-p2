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
    local_logger: logger.Logger,  # Place your own arguments here
    controller: worker_controller.WorkerController,
    output_queue: queue_proxy_wrapper.QueueProxyWrapper,
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
    result, tel_data = telemetry.Telemetry.create(
        connection=connection,
        local_logger=local_logger,
    )
    if not result:
        local_logger.error("tel_data object was unable to be created", True)
        return

    assert tel_data is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        controller.check_pause()

        try:
            run_result, telemetry_data = tel_data.run()

            if run_result and telemetry_data is not None:
                output_queue.queue.put(telemetry_data)
                local_logger.info("Sucessfully ran telemetry program", True)
        except RuntimeError as exc:
            local_logger.error(f"Unsucessful in returning telemetry data: {exc}", True)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
