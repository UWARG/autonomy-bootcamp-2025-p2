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
from time import sleep


def heartbeat_sender_worker(
    connection: mavutil.mavfile,
    controller: worker_controller.WorkerController,
) -> None:
    """
    Worker process to send periodic heartbeats to the drone.

    connection: MAVLink connection file object.
    controller: Worker controller managing process state (exit/pause).
    """
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

    # Instantiate class object (heartbeat_sender.HeartbeatSender)
    result, sender_instance = heartbeat_sender.HeartbeatSender.create(connection, local_logger)
    if not result:
        local_logger.error("Failed to initialize HeartbeatSender", True)
        return

    assert sender_instance is not None

    last_sent_time = 0.0

    # Main loop: do work once per second.
    while not controller.is_exit_requested():
        # Check if the process needs to pause
        controller.check_pause()
        sleep(1)
        success = sender_instance.run()
        if not success:
            local_logger.warning("Heartbeat transmission unsuccessful this period", True)
        last_sent_time = current_time
