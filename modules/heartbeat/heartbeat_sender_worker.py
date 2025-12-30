"""
Heartbeat worker that sends heartbeats periodically.
"""

import os
import pathlib
import time

from pymavlink import mavutil

from utilities.workers import worker_controller
from . import heartbeat_sender
from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
def heartbeat_sender_worker(
    connection: mavutil.mavfile,
    send_period_s: float,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process.

    connection: MAVLink connection used to send heartbeat messages.
    send_period_s: how often to send heartbeat (seconds), e.g. 1.0.
    controller: pause/exit control from main/test.
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
    ok, heartbeat_sender_instance = heartbeat_sender.HeartbeatSender.create(connection)
    if not ok or heartbeat_sender_instance is None:
        local_logger.error("Failed to create HeartbeatSender", True)
        return

    # Main loop: send heartbeat periodically until exit requested
    local_logger.info(f"send_period_s={send_period_s}", True)

    while not controller.is_exit_requested():
        controller.check_pause()

        sent = heartbeat_sender_instance.run()
        if not sent:
            local_logger.warning("Heartbeat send failed", True)

        time.sleep(send_period_s)


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
