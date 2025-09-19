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
    controller: worker_controller.WorkerController,   # Add other necessary worker arguments here
    dataq = queue_proxy_wrapper.QueueProxyWrapper,
    outputq = queue_proxy_wrapper.QueueProxyWrapper,
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

    result, cmd = command.Command.create(connection=connection, local_logger=local_logger, target=target)

    # Main loop: do work.

    if not result: 
        local_logger.error("Failure with command worker")
        return

    while not controller.is_exit_requested():
        try:
            data = dataq.queue.queue.get(timeout=1)
            if data:
                messages = cmd.run(data)
                for info in messages: 
                    outputq.queue.get(info)

        except Exception as e:
            local_logger.error(f"Error in worker loop: {e}", True )

            # add any command specific 
        local_logger.info(f"Command worker has stopped working: {e}")


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
