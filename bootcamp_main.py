"""
Bootcamp F2025

Main process to setup and manage all the other working processes
"""

import multiprocessing as mp

# import queue
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
HEARTBEAT_QUEUE_MAX_SIZE = 10
TELEMETRY_QUEUE_MAX_SIZE = 10
COMMAND_QUEUE_MAX_SIZE = 10

# Set worker counts
HEARTBEAT_SENDER_WORKER_COUNT = 1
HEARTBEAT_RECEIVER_WORKER_COUNT = 1
TELEMETRY_WORKER_COUNT = 1
COMMAND_WORKER_COUNT = 1

# Any other constants
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
    heartbeat_to_main_queue = queue_proxy_wrapper.QueueProxyWrapper(
        mp_manager,
        HEARTBEAT_QUEUE_MAX_SIZE,
    )

    telemetry_to_command_queue = queue_proxy_wrapper.QueueProxyWrapper(
        mp_manager,
        TELEMETRY_QUEUE_MAX_SIZE,
    )

    command_to_main_queue = queue_proxy_wrapper.QueueProxyWrapper(
        mp_manager,
        COMMAND_QUEUE_MAX_SIZE,
    )

    # Create worker properties for each worker type (what inputs it takes, how many workers)
    # Heartbeat sender
    result, sender_properties = worker_manager.WorkerProperties.create(
        HEARTBEAT_SENDER_WORKER_COUNT,  # How many workers
        heartbeat_sender_worker.heartbeat_sender_worker,  # What's the function that this worker runs
        (connection,),
        [],  # Note that input/output queues must be in the proper order
        [],
        controller,  # Worker controller
        main_logger,  # Main logger to log any failures during worker creation
    )
    if not result:
        print("Failed to create arguments for Sender")
        return -1

    # Heartbeat receiver
    result, receiver_properties = worker_manager.WorkerProperties.create(
        HEARTBEAT_RECEIVER_WORKER_COUNT,  # How many workers
        heartbeat_receiver_worker.heartbeat_receiver_worker,  # What's the function that this worker runs
        (connection,),
        [],  # Note that input/output queues must be in the proper order
        [heartbeat_to_main_queue],
        controller,  # Worker controller
        main_logger,  # Main logger to log any failures during worker creation
    )
    if not result:
        print("Failed to create arguments for Receiver")
        return -1

    # Telemetry
    result, telemetry_properties = worker_manager.WorkerProperties.create(
        TELEMETRY_WORKER_COUNT,  # How many workers
        telemetry_worker.telemetry_worker,  # What's the function that this worker runs
        (connection,),
        [],  # Note that input/output queues must be in the proper order
        [telemetry_to_command_queue],
        controller,  # Worker controller
        main_logger,  # Main logger to log any failures during worker creation
    )
    if not result:
        print("Failed to create arguments for Telemetry")
        return -1

    # Command
    result, command_properties = worker_manager.WorkerProperties.create(
        COMMAND_WORKER_COUNT,  # How many workers
        command_worker.command_worker,  # What's the function that this worker runs
        (
            connection,
            TARGET,
        ),
        [telemetry_to_command_queue],
        [command_to_main_queue],
        controller,  # Worker controller
        main_logger,  # Main logger to log any failures during worker creation
    )
    if not result:
        print("Failed to create arguments for Command")
        return -1

    # Create the workers (processes) and obtain their managers
    # sender manager
    worker_managers: list[worker_manager.WorkerManager] = []

    result, sender_manager = worker_manager.WorkerManager.create(
        worker_properties=sender_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Sender")
        return -1

    assert sender_manager is not None

    worker_managers.append(sender_manager)

    # receiver manager
    result, receiver_manager = worker_manager.WorkerManager.create(
        worker_properties=receiver_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Receiver")
        return -1

    assert receiver_manager is not None

    worker_managers.append(receiver_manager)

    # telemetry manager
    result, telemetry_manager = worker_manager.WorkerManager.create(
        worker_properties=telemetry_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Telemetry")
        return -1

    assert telemetry_manager is not None

    worker_managers.append(telemetry_manager)

    # Define command manager
    result, command_manager = worker_manager.WorkerManager.create(
        worker_properties=command_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Command")
        return -1

    assert command_manager is not None

    worker_managers.append(command_manager)

    # Start worker processes
    for manager in worker_managers:
        manager.start_workers()

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects
    start_time = time.time()
    while (time.time() - start_time) < 100:
        if not heartbeat_to_main_queue.queue.empty():
            if heartbeat_to_main_queue.queue.get_nowait() == "Disconnected":
                break
            main_logger.info(f"Heartbeat Status: {heartbeat_to_main_queue.queue.get_nowait()}")
        if not command_to_main_queue.queue.empty():
            main_logger.info(f"Command info: {command_to_main_queue.queue.get_nowait()}")

    # Stop the processes
    controller.request_exit()
    main_logger.info("Requested exit")

    # Fill and drain queues from END TO START
    command_to_main_queue.fill_and_drain_queue()
    heartbeat_to_main_queue.fill_and_drain_queue()
    telemetry_to_command_queue.fill_and_drain_queue()
    main_logger.info("Queues cleared")

    # Clean up worker processes
    for manager in worker_managers:
        manager.join_workers()
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
