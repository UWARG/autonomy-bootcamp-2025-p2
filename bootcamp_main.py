"""
Bootcamp F2025

Main process to setup and manage all the other working processes
"""

import multiprocessing as mp
import queue
import time
import threading

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

# Set worker counts

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

    input_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, 100)
    output_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, 100)

    # Create worker properties for each worker type (what inputs it takes, how many workers)
    # Heartbeat sender
    result, heartbeat_sender_properties = worker_manager.WorkerProperties.create(
        count=1,
        target=heartbeat_sender_worker.heartbeat_sender_worker,
        work_arguments=(connection,),
        input_queues=[],
        output_queues=[],
        controller=controller,
        local_logger=main_logger,
    )
    if not result or heartbeat_sender_properties is None:
        main_logger.error("Failed to create properties for heartbeat sender")
        return -1

    # Heartbeat receiver
    result, heartbeat_receiver_properties = worker_manager.WorkerProperties.create(
        count=1,
        target=heartbeat_receiver_worker.heartbeat_receiver_worker,
        work_arguments=(connection,),
        input_queues=[],
        output_queues=[output_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result or heartbeat_receiver_properties is None:
        main_logger.error("Failed to create properties for heartbeat receiver")
        return -1

    # Telemetry
    TARGET = command.Position(10, 20, 30)
    result, telemetry_properties = worker_manager.WorkerProperties.create(
        count=1,
        target=telemetry_worker.telemetry_worker,
        work_arguments=(connection,),
        input_queues=[],
        output_queues=[output_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result or telemetry_properties is None:
        main_logger.error("Failed to create properties for telemetry")
        return -1

    # Command
    result, command_properties = worker_manager.WorkerProperties.create(
        count=1,
        target=command_worker.command_worker,
        work_arguments=(connection, TARGET),
        input_queues=[input_queue],
        output_queues=[output_queue],
        controller=controller,
        local_logger=main_logger,
    )
    if not result or command_properties is None:
        main_logger.error("Failed to create properties for command")
        return -1

    # Create the workers (processes) and obtain their managers
    worker_managers: list[worker_manager.WorkerManager] = []

    for name, properties in [
        ("heartbeat_sender", heartbeat_sender_properties),
        ("heartbeat_receiver", heartbeat_receiver_properties),
        ("telemetry", telemetry_properties),
        ("command", command_properties),
    ]:
        result, manager = worker_manager.WorkerManager.create(
            worker_properties=properties,
            local_logger=main_logger,
        )
        if not result or manager is None:
            main_logger.error(f"Failed to create manager for {name}")
            return -1
        worker_managers.append(manager)

    # Start worker processes
    for manager in worker_managers:
        manager.start_workers()

    main_logger.info("Started")

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects
    start_time = time.time()
    while time.time() - start_time < 100:
        try:
            item = output_queue.queue.get(timeout=1.0)
            if item is None:
                break

            if isinstance(item, str):
                if item == "Disconnected":
                    main_logger.info("Drone disconnected. Exiting loop.")
                    break
                elif item == "Connected":
                    # Optionally log drone connection
                    pass
                else:
                    main_logger.info(f"Command worker reported: {item}")
            else:
                # Must be TelemetryData; forward it to command worker
                input_queue.queue.put(item)
        except queue.Empty:
            continue

    # Stop the processes
    controller.request_exit()

    main_logger.info("Requested exit")

    # Fill and drain queues from END TO START
    output_queue.fill_and_drain_queue()
    input_queue.fill_and_drain_queue()

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
