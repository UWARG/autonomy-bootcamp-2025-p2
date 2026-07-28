"""
Bootcamp F2025

Main process to setup and manage all the other working processes
"""

import multiprocessing as mp
import queue  # pylint: disable=unused-import
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
HEARTBEAT_STATUS_QUEUE_MAX_SIZE = 5
TELEMETRY_QUEUE_MAX_SIZE = 5
COMMAND_QUEUE_MAX_SIZE = 5
# Set worker counts
HEARTBEAT_SENDER_COUNT = 2
HEARTBEAT_RECEIVER_COUNT = 2
TELEMETRY_WORKER_COUNT = 2
COMMAND_WORKER_COUNT = 2
# Any other constants
TARGET = command.Position(10, 20, 30)
HEIGHT_TOLERANCE = 0.5
Z_SPEED = 1.0
ANGLE_TOLERANCE = 5.0
TURNING_SPEED = 5.0
HEARTBEAT_PERIOD = 1.0
DISCONNECT_THRESHOLD = 5
TELEMETRY_PERIOD = 1.0
RUN_DURATION = 100  # seconds
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
    heartbeat_status_queue = queue_proxy_wrapper.QueueProxyWrapper(
        manager,
        HEARTBEAT_STATUS_QUEUE_MAX_SIZE,
    )
    telemetry_status_queue = queue_proxy_wrapper.QueueProxyWrapper(
        manager,
        TELEMETRY_QUEUE_MAX_SIZE,
    )
    command_status_queue = queue_proxy_wrapper.QueueProxyWrapper(
        manager,
        COMMAND_QUEUE_MAX_SIZE,
    )

    # Create worker properties for each worker type (what inputs it takes, how many workers)
    # Heartbeat sender
    # Heartbeat sender
    # Worker signature: heartbeat_sender_worker(connection, heartbeat_period, controller)
    result, heartbeat_sender_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_SENDER_COUNT,
        target=heartbeat_sender_worker.heartbeat_sender_worker,
        work_arguments=(connection, HEARTBEAT_PERIOD),
        input_queues=[],
        output_queues=[],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create arguments for HeartbeatSender")
        return -1

    assert heartbeat_sender_properties is not None
    # Heartbeat receiver
    result, heartbeat_receiver_properties = worker_manager.WorkerProperties.create(
        count=HEARTBEAT_RECEIVER_COUNT,
        target=heartbeat_receiver_worker.heartbeat_receiver_worker,
        work_arguments=(connection, DISCONNECT_THRESHOLD, HEARTBEAT_PERIOD),
        input_queues=[],
        output_queues=[heartbeat_status_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create arguments for HeartbeatReceiver")
        return -1

    assert heartbeat_receiver_properties is not None

    # Telemetry
    result, telemetry_properties = worker_manager.WorkerProperties.create(
        count=TELEMETRY_WORKER_COUNT,
        target=telemetry_worker.telemetry_worker,
        work_arguments=(connection, TELEMETRY_PERIOD),
        input_queues=[],
        output_queues=[telemetry_status_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create arguments for Telemetry")
        return -1

    assert telemetry_properties is not None
    # Command
    result, command_properties = worker_manager.WorkerProperties.create(
        count=COMMAND_WORKER_COUNT,
        target=command_worker.command_worker,
        work_arguments=(
            connection,
            TARGET,
            HEIGHT_TOLERANCE,
            Z_SPEED,
            ANGLE_TOLERANCE,
            TURNING_SPEED,
        ),
        input_queues=[telemetry_status_queue],
        output_queues=[command_status_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create arguments for Command")
        return -1

    assert command_properties is not None
    # Create the workers (processes) and obtain their managers
    worker_managers: list[worker_manager.WorkerManager] = []  # List of all worker managers

    result, hb_sender_manager = worker_manager.WorkerManager.create(
        worker_properties=heartbeat_sender_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for HeartbeatSender Worker")
        return -1

    # Get Pylance to stop complaining
    assert hb_sender_manager is not None

    worker_managers.append(hb_sender_manager)

    result, hb_receiver_manager = worker_manager.WorkerManager.create(
        worker_properties=heartbeat_receiver_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for HeartbeatReceiver Worker")
        return -1

    # Get Pylance to stop complaining
    assert hb_receiver_manager is not None

    worker_managers.append(hb_receiver_manager)

    result, telemetry_manager = worker_manager.WorkerManager.create(
        worker_properties=telemetry_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Telemetry Worker")
        return -1

    # Get Pylance to stop complaining
    assert telemetry_manager is not None

    worker_managers.append(telemetry_manager)

    result, command_manager = worker_manager.WorkerManager.create(
        worker_properties=command_properties,
        local_logger=main_logger,
    )
    if not result:
        print("Failed to create manager for Command Worker")
        return -1

    # Get Pylance to stop complaining
    assert command_manager is not None

    worker_managers.append(command_manager)

    # Start worker processes
    for mgr in worker_managers:
        mgr.start_workers()

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects
    start_time = time.time()
    connected = True

    while (time.time() - start_time) < RUN_DURATION and connected:
        try:
            connected = heartbeat_status_queue.queue.get(timeout=1.0)
            if not connected:
                main_logger.warning("Drone Disconnected!", True)
        except Exception:  # pylint: disable=broad-except
            pass

        try:
            command_read = command_status_queue.queue.get_nowait()
            main_logger.info(f"Command Message: {command_read}", True)
        except Exception:  # pylint: disable=broad-except
            pass
    # Stop the processes
    controller.request_exit()

    main_logger.info("Requested exit")

    # Fill and drain queues from END TO START
    heartbeat_status_queue.fill_and_drain_queue()
    telemetry_status_queue.fill_and_drain_queue()
    command_status_queue.fill_and_drain_queue()

    main_logger.info("Queues cleared")

    # Clean up worker processes
    for mgr in worker_managers:
        mgr.join_workers()
    main_logger.info("Stopped")

    # We can reset controller in case we want to reuse it
    controller.clear_exit()
    # Alternatively, create a new WorkerController instance

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
