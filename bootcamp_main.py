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

# from modules.command import command ### didnt use it and pylint was getting mad
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
HEARTBEAT_TO_MAIN_QUEUE_SIZE = 1

TELEMETRY_TO_COMMAND_QUEUE_SIZE = 5
COMMAND_TO_MAIN_QUEUE_SIZE = 5

# Set worker counts
HEARTBEAT_SENDER_COUNT = 1
HEARTBEAT_RECEIVER_COUNT = 1
TELEMETRY_COUNT = 1
COMMAND_COUNT = 1
# Any other constants

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

    ###Here im creating queues under the main mp_manager. All with the sizes stored in the constants above
    heartbeat_to_main_queue = queue_proxy_wrapper.QueueProxyWrapper(
        mp_manager, HEARTBEAT_TO_MAIN_QUEUE_SIZE
    )

    telemetry_to_command_queue = queue_proxy_wrapper.QueueProxyWrapper(
        mp_manager, TELEMETRY_TO_COMMAND_QUEUE_SIZE
    )

    command_to_main_queue = queue_proxy_wrapper.QueueProxyWrapper(
        mp_manager, COMMAND_TO_MAIN_QUEUE_SIZE
    )

    # Create worker properties for each worker type (what inputs it takes, how many workers)
    # Heartbeat sender---------------------

    ### Here i copied the one from the example and put it in here
    result, heartbeat_sender_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_SENDER_COUNT,  # How many workers
        target=heartbeat_sender_worker.heartbeat_sender_worker,  # What's the function that this worker runs
        work_arguments=(  # The function's arguments excluding input/output queues and controller
            connection,
            controller,
        ),
        input_queues=[],  # Note that input/output queues must be in the proper order
        output_queues=[],
        controller=controller,  # Worker controller
        local_logger=main_logger,  # Main logger to log any failures during worker creation
    )
    if not result:
        print("Failed to create arguments for heartbeat_sender")
        return -1

    # Get Pylance to stop complaining
    assert heartbeat_sender_properties is not None

    # Heartbeat receiver----------------
    result, heartbeat_receiver_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_RECEIVER_COUNT,  # How many workers
        target=heartbeat_receiver_worker.heartbeat_receiver_worker,  # What's the function that this worker runs
        work_arguments=(  # The function's arguments excluding input/output queues and controller
            connection,
            controller,
            heartbeat_to_main_queue,
        ),
        input_queues=[],  # Note that input/output queues must be in the proper order
        output_queues=[heartbeat_to_main_queue],
        controller=controller,  # Worker controller
        local_logger=main_logger,  # Main logger to log any failures during worker creation
    )
    if not result:
        print("Failed to create arguments for heartbeat receiver")
        return -1

    # Get Pylance to stop complaining
    assert heartbeat_receiver_properties is not None

    # Telemetry-----------
    result, telemetry_properties = worker_manager.WorkerProperties.create(
        count=TELEMETRY_COUNT,  # How many workers
        target=telemetry_worker.telemetry_worker,  # What's the function that this worker runs
        work_arguments=(  # The function's arguments excluding input/output queues and controller
            connection,
            controller,
            telemetry_to_command_queue,
        ),
        input_queues=[],  # Note that input/output queues must be in the proper order
        output_queues=[telemetry_to_command_queue],
        controller=controller,  # Worker controller
        local_logger=main_logger,  # Main logger to log any failures during worker creation
    )
    if not result:
        print("Failed to create arguments for telemetry")
        return -1

    # Get Pylance to stop complaining
    assert telemetry_properties is not None

    # Command------------------
    result, command_properties = worker_manager.WorkerProperties.create(
        count=COMMAND_COUNT,  # How many workers
        target=command_worker.command_worker,  # What's the function that this worker runs
        work_arguments=(  # The function's arguments excluding input/output queues and controller
            connection,
            (0, 0, 0),  ### The target position, i dont know what to put here
            controller,
            telemetry_to_command_queue,
            command_to_main_queue,
        ),
        input_queues=[
            telemetry_to_command_queue
        ],  # Note that input/output queues must be in the proper order
        output_queues=[command_to_main_queue],
        controller=controller,  # Worker controller
        local_logger=main_logger,  # Main logger to log any failures during worker creation
    )
    if not result:
        print("Failed to create arguments for command")
        return -1

    # Get Pylance to stop complaining
    assert command_properties is not None

    # Create the workers (processes) and obtain their managers

    worker_managers: list[worker_manager.WorkerManager] = []  # List of all worker managers

    ### This is adding all of the managers to a main manager list "worker_managers"
    result, heartbeat_receiver_manager = worker_manager.WorkerManager.create(
        worker_properties=heartbeat_receiver_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for HB receiver")
        return -1

    # Get Pylance to stop complaining
    assert heartbeat_receiver_manager is not None

    worker_managers.append(heartbeat_receiver_manager)

    ### HEARTBEAT SENDER
    result, heartbeat_sender_manager = worker_manager.WorkerManager.create(
        worker_properties=heartbeat_sender_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for HB sender")
        return -1

    # Get Pylance to stop complaining
    assert heartbeat_sender_manager is not None

    worker_managers.append(heartbeat_sender_manager)

    ### TELEMETRY MANAGER
    result, telemetry_manager = worker_manager.WorkerManager.create(
        worker_properties=telemetry_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for telemetry")
        return -1

    # Get Pylance to stop complaining
    assert telemetry_manager is not None

    worker_managers.append(telemetry_manager)

    ### COMMAND MANAGER
    result, command_manager = worker_manager.WorkerManager.create(
        worker_properties=command_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for command")
        return -1

    # Get Pylance to stop complaining
    assert command_manager is not None

    worker_managers.append(command_manager)

    # Start worker processes

    ### going through the list and starting all the workers
    for manager in worker_managers:
        manager.start_workers()

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects

    time_start = time.time()
    continue_running = True
    while time.time() - time_start < 100 and continue_running:
        msg = None
        ### Constantly read from command_to_main queue, with error handling
        try:
            msg = command_to_main_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        ### If a message was read from the queue log it.
        if msg is not None:
            main_logger.info(msg)

        ### Do the same thing for the heartbeat receiver queue
        try:
            msg = heartbeat_to_main_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        ### if the message is disconnected stop running the main file
        if msg == "Disconnected":
            continue_running = False

    # Stop the processes

    controller.request_exit()
    main_logger.info("Requested exit")

    # Fill and drain queues from END TO START

    ### Drain command to main first since it comes after telemetry to command
    command_to_main_queue.fill_and_drain_queue()
    telemetry_to_command_queue.fill_and_drain_queue()

    ### THis is a seperate queue system, so it doesnt matter where i drain it
    heartbeat_to_main_queue.fill_and_drain_queue()
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
