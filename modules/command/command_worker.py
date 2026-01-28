"""
Command worker to make decisions based on Telemetry Data.
"""

# pylint: disable=too-many-arguments, too-many-locals

import os
import pathlib

from pymavlink import mavutil

from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from . import command
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def command_worker(
    connection: mavutil.mavfile,
    target: command.Position,
    telemetry_period_s: float,
    z_speed_m_s: float,
    angle_tolerance_deg: float,
    height_tolerance_m: float,
    input_queue: queue_proxy_wrapper.QueueProxyWrapper,
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
    # Instantiate class object (command.Command)
    ok, instance = command.Command.create(
        connection,
        target,
        5.0,  # default turning speed (deg/s)
        local_logger,
    )
    if not ok:
        local_logger.error("Failed to create Command instance", True)
        return
    # Get Pylance to stop complaining
    assert instance is not None

    # Main loop: do work.
    while not controller.is_exit_requested():
        controller.check_pause()
        data = input_queue.queue.get()
        if data is None:
            continue
        try:
            success, output = instance.run(
                data,
                telemetry_period_s,
                z_speed_m_s,
                angle_tolerance_deg,
                height_tolerance_m,
            )
        except Exception as e:  # pylint: disable=broad-except
            local_logger.error(f"Command run failed: {e}", True)
            success, output = False, None
        if success:
            # Log and forward the output
            local_logger.info(str(output), None)
            output_queue.queue.put(output)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
