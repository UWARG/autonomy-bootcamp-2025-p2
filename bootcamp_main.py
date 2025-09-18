"""
Bootcamp F2025

Main process to setup and manage all the other working processes
"""

import multiprocessing as mp
import queue
import time

from pymavlink import mavutil

from modules.common.modules.logger import logger
from modules.common.modules.logger import logger_main_setup
from modules.common.modules.read_yaml import read_yaml
from modules.command import command
from modules.command import command_worker
from modules.heartbeat import heartbeat_receiver_worker
from modules.heartbeat import heartbeat_sender_worker
from modules.telemetry import telemetry_worker
from utilities.workers import queue_proxy_wrapper
from utilities.workers import worker_controller
from utilities.workers import worker_manager


# MAVLink connection
CONNECTION_STRING = "tcp:localhost:12345"

# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
# Set queue max sizes (<= 0 for infinity)
QUEUE_MAX_SIZE = 0

# Set worker counts
HEARTBEAT_SENDER_COUNT = 1
HEARTBEAT_RECEIVER_COUNT = 1
TELEMETRY_WORKER_COUNT = 1
COMMAND_WORKER_COUNT = 1

# Any other constants
RUN_TIME = 100  # seconds

# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================


def main() -> int:
    """
    Main function.
    """
    # Configuration settings
    result, config = read_yaml.open_config(logger.CONFIG_FILE_PATH)
    if not result:
        print("ERROR: Failed to load configuration file")
        return -1

    # Get Pylance to stop complaining
    assert config is not None

    # Setup main logger
    result, main_logger, _ = logger_main_setup.setup_main_logger(config)
    if not result:
        print("ERROR: Failed to create main logger")
        return -1

    # Get Pylance to stop complaining
    assert main_logger is not None

    # Create a connection to the drone. Assume that this is safe to pass around to all processes
    # In reality, this will not work, but to simplify the bootamp, preetend it is allowed
    # To test, you will run each of your workers individually to see if they work
    # (test "drones" are provided for you test your workers)
    # NOTE: If you want to have type annotations for the connection, it is of type mavutil.mavfile
    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.wait_heartbeat(timeout=30)  # Wait for the "drone" to connect

    # =============================================================================================
    #                          ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
    # =============================================================================================
    # Create a worker controller

    controller = worker_controller.WorkerController()
    # Create a multiprocess manager for synchronized queues
    manager = mp.Manager()
    # Create queues
    heartbeat_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, maxsize=QUEUE_MAX_SIZE)
    telemetry_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, maxsize=QUEUE_MAX_SIZE)
    command_output_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, maxsize=QUEUE_MAX_SIZE)
    command_input_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, maxsize=QUEUE_MAX_SIZE)
    # Create worker properties for each worker type (what inputs it takes, how many workers)
    workers = []
    # Heartbeat sender
    for _ in range(HEARTBEAT_SENDER_COUNT):
        workers.append(
            worker_manager.Worker(
                target=heartbeat_sender_worker.heartbeat_sender_worker,
                args=(connection, heartbeat_queue),
            )
        )

    # Heartbeat receiver
    for _ in range(HEARTBEAT_RECEIVER_COUNT):
        workers.append(
            worker_manager.Worker(
                target=heartbeat_receiver_worker.heartbeat_receiver_worker,
                args=(connection, heartbeat_queue),
            )
        )

    # Telemetry
    for _ in range(TELEMETRY_WORKER_COUNT):
        workers.append(
            worker_manager.Worker(
                target=telemetry_worker.telemetry_worker, args=(connection, telemetry_queue)
            )
        )

    # Command
    target_position = command.Position(10, 20, 30)
    for _ in range(COMMAND_WORKER_COUNT):
        workers.append(
            worker_manager.Worker(
                target=command_worker.command_worker,
                args=(connection, target_position, command_input_queue, command_output_queue),
            )
        )

    # Create the workers (processes) and obtain their managers
    controller.add_workers(workers)
    # Start worker processes
    controller.start_all()
    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects
    start_time = time.time()
    while time.time() - start_time < RUN_TIME:
        try:
            msg = command_output_queue.get(timeout=1)
            main_logger.info(f"Command output: {msg}")
        except queue.Empty:
            pass

    # Stop the processes
    controller.stop_all()
    main_logger.info("Requested exit")

    # Fill and drain queues from END TO START
    for q in [command_output_queue, telemetry_queue, heartbeat_queue]:
        while True:
            try:
                _ = q.get_nowait()
            except queue.Empty:
                break
    main_logger.info("Queues cleared")

    # Clean up worker processes
    controller.join_all()
    main_logger.info("Stopped")

    # We can reset controller in case we want to reuse it
    # Alternatively, create a new WorkerController instance
    controller.reset()
    # =============================================================================================
    #                          ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
    # =============================================================================================

    return 0


if __name__ == "__main__":
    result_main = main()
    if result_main < 0:
        print(f"Failed with return code {result_main}")
    else:
        print("Success!")
