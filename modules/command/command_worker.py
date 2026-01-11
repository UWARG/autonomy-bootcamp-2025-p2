"""
Command worker to make decisions based on Telemetry Data.
"""

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
    controller: worker_controller.WorkerController,
    telemetry_queue: queue_proxy_wrapper.QueueProxyWrapper,
    command_queue: queue_proxy_wrapper.QueueProxyWrapper,
    # Place your own arguments here
    # Add other necessary worker arguments here
) -> None:
    """
    Worker process.

    args... describe what the arguments are
        connection: MAVLink connection
        target: 3D destination point
        controller: Graceful shutdown controller
        telemetry_queue: Input queue for TelemetryData
        command_queue: Output queue for decision strings
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
    result, command_inst = command.Command.create(connection, target, local_logger)
    if not result or command_inst is None:
        local_logger.error("Failed to create Command instance")
        return

    # Main loop: do work.
    while not controller.is_exit_requested():
        try:
            data = telemetry_queue.queue.get(timeout=0.1)
            report = command_inst.run(data)

            if report is not None:
                command_queue.queue.put(report)
                local_logger.info(f"Decision: {report}")
        except Exception:  # pylint: disable=broad-exception-caught
            continue


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
