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

from utilities.workers.worker_manager import WorkerManager, WorkerProperties


# MAVLink connection
CONNECTION_STRING = "tcp:localhost:12345"

# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
# Set queue max sizes (<= 0 for infinity)
QUEUE_MAX = 0
# Set worker counts
NUM_HEARTBEAT_SENDER = 1
NUM_HEARTBEAT_RECEIVER = 1
NUM_TELEMETRY = 1
NUM_COMMAND = 1
# Any other constants
MAIN_LOOP = 60
TARGET_POSITION = command.Position(10, 20, 30)
PERIOD = 1
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
    heartbeat_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, maxsize=QUEUE_MAX)
    telemetry_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, maxsize=QUEUE_MAX)
    command_queue = queue_proxy_wrapper.QueueProxyWrapper(manager, maxsize=QUEUE_MAX)
    # Create worker properties for each worker type (what inputs it takes, how many workers)

    # Heartbeat sender

    success, heartbeat_sender_props = WorkerProperties.create(
        heartbeat_sender_worker.heartbeat_sender_worker,
        NUM_HEARTBEAT_SENDER,
        (connection, controller, PERIOD),
        input_queues=[],
        output_queues=[],
        controller=controller,
        local_logger=main_logger,
    )
    if not success:
        main_logger.error("Couldn't create properties")
    # Heartbeat receiver

    success, heartbeat_receiver_props = WorkerProperties.create(
        heartbeat_receiver_worker.heartbeat_receiver_worker,
        NUM_HEARTBEAT_RECEIVER,
        (connection, controller, heartbeat_queue, PERIOD),
        input_queues=[],
        output_queues=[],
        controller=controller,
        local_logger=main_logger,
    )
    if not success:
        main_logger.error("Couldn't create properties")
    # Telemetry

    success, telemetry_props = WorkerProperties.create(
        telemetry_worker.telemetry_worker,
        NUM_TELEMETRY,
        (connection, controller, telemetry_queue, PERIOD),
        input_queues=[],
        output_queues=[],
        controller=controller,
        local_logger=main_logger,
    )
    if not success:
        main_logger.error("Couldn't create properties")
    # Command

    success, command_props = WorkerProperties.create(
        command_worker.command_worker,
        NUM_COMMAND,
        (connection, controller, telemetry_queue, command_queue, TARGET_POSITION),
        input_queues=[],
        output_queues=[],
        controller=controller,
        local_logger=main_logger,
    )
    if not success:
        main_logger.error("Couldn't create properties")
    # Create the workers (processes) and obtain their managers

    # Heartbeat sender
    success, hb_sender_mgr = WorkerManager.create(heartbeat_sender_props, main_logger)
    hb_sender_mgr.start_workers()
    if not success:
        main_logger.error("Couldn't create workers")
    # Heartbeat receiver
    success, hb_receiver_mgr = WorkerManager.create(heartbeat_receiver_props, main_logger)
    hb_receiver_mgr.start_workers()
    if not success:
        main_logger.error("Couldn't create workers")
    # Telemetry
    success, telem_mgr = WorkerManager.create(telemetry_props, main_logger)
    telem_mgr.start_workers()
    if not success:
        main_logger.error("Couldn't create workers")
    # Command
    success, cmd_mgr = WorkerManager.create(command_props, main_logger)
    cmd_mgr.start_workers()
    if not success:
        main_logger.error("Couldn't create workers")

    worker_managers = [hb_sender_mgr, hb_receiver_mgr, telem_mgr, cmd_mgr]
    # Start worker processes

    main_logger.info("Started")

    start_time = time.time()

    queues = [
        ("Command", command_queue),
        ("Telemetry", telemetry_queue),
        ("Heartbeat", heartbeat_queue),
    ]

    try:
        # for the duration of the main_loop
        while time.time() - start_time < MAIN_LOOP and not controller.is_exit_requested():
            for name, q in queues:
                try:
                    msg = q.queue.get_nowait()
                    if name == "Heartbeat" and msg == "Disconnected":
                        main_logger.warning("Drone disconnected, requesting exit")
                        controller.request_exit()
                    else:
                        main_logger.debug(f"{name} message: {msg}")
                except queue.Empty:
                    pass

    except Exception as e:  # pylint: disable=broad-exception-caught
        main_logger.info(f"Could not get from queues: {e}")
    finally:
        controller.request_exit()

    # Main's work: read from all queues that output to main, and log any commands that we make
    # Continue running for 100 seconds or until the drone disconnects

    # Stop the processes

    main_logger.info("Requested exit")

    for wm in worker_managers:
        for worker in wm._WorkerManager__workers:  # pylint: disable=protected-access
            if worker.is_alive():
                worker.terminate()
                worker.join()

    # for q in [command_queue, telemetry_queue, heartbeat_queue]:
    #     try:
    #         while True:
    #             q.queue.get_nowait()
    #     except queue.Empty:
    #         pass
    command_queue.fill_and_drain_queue()
    heartbeat_queue.fill_and_drain_queue()
    telemetry_queue.fill_and_drain_queue()

    # Fill and drain queues from END TO START

    main_logger.info("Queues cleared")

    # Clean up worker processes

    main_logger.info("Stopped")

    # We can reset controller in case we want to reuse it
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
