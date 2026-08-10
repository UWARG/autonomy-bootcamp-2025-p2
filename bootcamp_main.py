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
# Must be greater than 0, otherwise the queues cannot be filled with sentinel values on exit
QUEUE_MAX_SIZE = 10

# Set worker counts
# Every worker shares the single connection to the drone, so there is exactly one of each
HEARTBEAT_SENDER_WORKER_COUNT = 1
HEARTBEAT_RECEIVER_WORKER_COUNT = 1
TELEMETRY_WORKER_COUNT = 1
COMMAND_WORKER_COUNT = 1

# Any other constants
# The drone sends and expects a heartbeat once per second
HEARTBEAT_PERIOD = 1  # s

# Missing this many heartbeats in a row means the drone is considered gone
DISCONNECT_THRESHOLD = 5

# The state that the heartbeat receiver reports once the drone is gone
DISCONNECTED = "Disconnected"

# How long to wait for both telemetry messages before giving up on the pair
TELEMETRY_TIMEOUT = 1  # s

# The point in 3D space that the drone flies around, facing it the whole time
TARGET = command.Position(10.0, 20.0, 30.0)

# How far off the target the drone is allowed to be before it gets corrected
HEIGHT_TOLERANCE = 0.5  # m
ANGLE_TOLERANCE = 5  # deg

# How quickly the drone carries out the corrections
ALTITUDE_SPEED = 1  # m/s
TURNING_SPEED = 5  # deg/s

# How long to run before shutting everything down
RUN_DURATION = 100  # s

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
    heartbeat_receiver_to_main_queue = queue_proxy_wrapper.QueueProxyWrapper(
        mp_manager,
        QUEUE_MAX_SIZE,
    )
    telemetry_to_command_queue = queue_proxy_wrapper.QueueProxyWrapper(
        mp_manager,
        QUEUE_MAX_SIZE,
    )
    command_to_main_queue = queue_proxy_wrapper.QueueProxyWrapper(
        mp_manager,
        QUEUE_MAX_SIZE,
    )

    # Create worker properties for each worker type (what inputs it takes, how many workers)
    # Heartbeat sender
    result, heartbeat_sender_worker_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_SENDER_WORKER_COUNT,
        target=heartbeat_sender_worker.heartbeat_sender_worker,
        work_arguments=(
            connection,
            HEARTBEAT_PERIOD,
        ),
        input_queues=[],
        output_queues=[],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        main_logger.error("Failed to create arguments for Heartbeat Sender", True)
        return -1

    # Get Pylance to stop complaining
    assert heartbeat_sender_worker_properties is not None

    # Heartbeat receiver
    result, heartbeat_receiver_worker_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_RECEIVER_WORKER_COUNT,
        target=heartbeat_receiver_worker.heartbeat_receiver_worker,
        work_arguments=(
            connection,
            HEARTBEAT_PERIOD,
            DISCONNECT_THRESHOLD,
        ),
        input_queues=[],
        output_queues=[heartbeat_receiver_to_main_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        main_logger.error("Failed to create arguments for Heartbeat Receiver", True)
        return -1

    # Get Pylance to stop complaining
    assert heartbeat_receiver_worker_properties is not None

    # Telemetry
    result, telemetry_worker_properties = worker_manager.WorkerProperties.create(
        count=TELEMETRY_WORKER_COUNT,
        target=telemetry_worker.telemetry_worker,
        work_arguments=(
            connection,
            TELEMETRY_TIMEOUT,
        ),
        input_queues=[],
        output_queues=[telemetry_to_command_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        main_logger.error("Failed to create arguments for Telemetry", True)
        return -1

    # Get Pylance to stop complaining
    assert telemetry_worker_properties is not None

    # Command
    result, command_worker_properties = worker_manager.WorkerProperties.create(
        count=COMMAND_WORKER_COUNT,
        target=command_worker.command_worker,
        work_arguments=(
            connection,
            TARGET,
            HEIGHT_TOLERANCE,
            ANGLE_TOLERANCE,
            ALTITUDE_SPEED,
            TURNING_SPEED,
        ),
        input_queues=[telemetry_to_command_queue],
        output_queues=[command_to_main_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        main_logger.error("Failed to create arguments for Command", True)
        return -1

    # Get Pylance to stop complaining
    assert command_worker_properties is not None

    # Create the workers (processes) and obtain their managers
    # Data path: telemetry_worker to command_worker, the heartbeat workers stand on their own
    worker_managers: list[worker_manager.WorkerManager] = []

    for worker_properties, worker_description in [
        (heartbeat_sender_worker_properties, "Heartbeat Sender"),
        (heartbeat_receiver_worker_properties, "Heartbeat Receiver"),
        (telemetry_worker_properties, "Telemetry"),
        (command_worker_properties, "Command"),
    ]:
        result, manager = worker_manager.WorkerManager.create(
            worker_properties=worker_properties,
            local_logger=main_logger,
        )
        if not result:
            main_logger.error(f"Failed to create manager for {worker_description}", True)
            return -1

        # Get Pylance to stop complaining
        assert manager is not None

        worker_managers.append(manager)

    # Start worker processes
    for manager in worker_managers:
        manager.start_workers()

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects
    start_time = time.time()
    while time.time() - start_time < RUN_DURATION:
        # The heartbeat receiver reports once per period, which also paces this loop
        try:
            connection_state = heartbeat_receiver_to_main_queue.queue.get(timeout=HEARTBEAT_PERIOD)
        except queue.Empty:
            connection_state = None

        if connection_state is not None:
            main_logger.info(f"Connection state: {connection_state}")

        # The command worker only reports when it actually commands the drone,
        # so there may be any number of messages waiting
        while True:
            try:
                command_message = command_to_main_queue.queue.get_nowait()
            except queue.Empty:
                break

            main_logger.info(f"Command sent: {command_message}")

        # Nothing can be done for a drone that is no longer listening
        if connection_state == DISCONNECTED:
            main_logger.error("Drone disconnected")
            break

    # Stop the processes
    controller.request_exit()

    main_logger.info("Requested exit")

    # Fill and drain queues from END TO START
    telemetry_to_command_queue.fill_and_drain_queue()
    command_to_main_queue.fill_and_drain_queue()
    heartbeat_receiver_to_main_queue.fill_and_drain_queue()

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
