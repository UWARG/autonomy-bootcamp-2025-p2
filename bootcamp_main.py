"""
Bootcamp F2025

Main process to setup and manage all the other working processes
"""

import multiprocessing as mp
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
QUEUE_MAX_SIZE = 10

# Set worker counts
WORKER_COUNT = 1

# Any other constants
RUN_TIME = 100  # seconds
TARGET = command.Position(0, 0, 0)

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
    mp_manager = mp.Manager()

    # Create queues
    heartbeat_receiver_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, QUEUE_MAX_SIZE)
    telemetry_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, QUEUE_MAX_SIZE)
    command_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, QUEUE_MAX_SIZE)

    # Create worker properties for each worker type (what inputs it takes, how many workers)
    # Heartbeat sender
    result, hb_sender_props = worker_manager.WorkerProperties.create(
        WORKER_COUNT,
        heartbeat_sender_worker.heartbeat_sender_worker,
        (connection,),
        [],
        [],
        controller,
        main_logger,
    )
    if not result:
        main_logger.error("Failed to create heartbeat sender properties", True)
        return -1
    assert hb_sender_props is not None

    # Heartbeat receiver
    result, hb_receiver_props = worker_manager.WorkerProperties.create(
        WORKER_COUNT,
        heartbeat_receiver_worker.heartbeat_receiver_worker,
        (connection,),
        [],
        [heartbeat_receiver_queue],
        controller,
        main_logger,
    )
    if not result:
        main_logger.error("Failed to create heartbeat receiver properties", True)
        return -1
    assert hb_receiver_props is not None

    # Telemetry
    result, telemetry_props = worker_manager.WorkerProperties.create(
        WORKER_COUNT,
        telemetry_worker.telemetry_worker,
        (connection,),
        [],
        [telemetry_queue],
        controller,
        main_logger,
    )
    if not result:
        main_logger.error("Failed to create telemetry properties", True)
        return -1
    assert telemetry_props is not None

    # Command
    result, command_props = worker_manager.WorkerProperties.create(
        WORKER_COUNT,
        command_worker.command_worker,
        (connection, TARGET),
        [telemetry_queue],
        [command_queue],
        controller,
        main_logger,
    )
    if not result:
        main_logger.error("Failed to create command properties", True)
        return -1
    assert command_props is not None

    # Create the workers (processes) and obtain their managers
    result, hb_sender_mgr = worker_manager.WorkerManager.create(hb_sender_props, main_logger)
    if not result:
        main_logger.error("Failed to create heartbeat sender manager", True)
        return -1
    assert hb_sender_mgr is not None

    result, hb_receiver_mgr = worker_manager.WorkerManager.create(hb_receiver_props, main_logger)
    if not result:
        main_logger.error("Failed to create heartbeat receiver manager", True)
        return -1
    assert hb_receiver_mgr is not None

    result, telemetry_mgr = worker_manager.WorkerManager.create(telemetry_props, main_logger)
    if not result:
        main_logger.error("Failed to create telemetry manager", True)
        return -1
    assert telemetry_mgr is not None

    result, command_mgr = worker_manager.WorkerManager.create(command_props, main_logger)
    if not result:
        main_logger.error("Failed to create command manager", True)
        return -1
    assert command_mgr is not None

    # Start worker processes
    hb_sender_mgr.start_workers()
    hb_receiver_mgr.start_workers()
    telemetry_mgr.start_workers()
    command_mgr.start_workers()

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects
    start_time = time.time()
    is_connected = True
    while is_connected and time.time() - start_time < RUN_TIME:
        try:
            heartbeat_status = heartbeat_receiver_queue.queue.get_nowait()
            if heartbeat_status == "Disconnected":
                main_logger.warning("Drone disconnected", True)
                is_connected = False
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        try:
            cmd_output = command_queue.queue.get_nowait()
            if cmd_output is not None:
                main_logger.info(f"Command: {cmd_output}", True)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    # Stop the processes
    controller.request_exit()

    main_logger.info("Requested exit")

    # Fill and drain queues from END TO START
    command_queue.fill_and_drain_queue()
    telemetry_queue.fill_and_drain_queue()
    heartbeat_receiver_queue.fill_and_drain_queue()

    main_logger.info("Queues cleared")

    # Clean up worker processes
    hb_sender_mgr.join_workers()
    hb_receiver_mgr.join_workers()
    telemetry_mgr.join_workers()
    command_mgr.join_workers()

    main_logger.info("Stopped")

    # We can reset controller in case we want to reuse it
    # Alternatively, create a new WorkerController instance
    controller.clear_exit()

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
