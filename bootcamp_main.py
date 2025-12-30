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
HEARTBEAT_MAX = 10
TELEMETRY_MAX = 10
REPORT_MAX = 10
HEARTBEAT_SEND_WORKER = 1
HEARTBEAT_REC_WORKER = 1
TELEMETRY_WORKER = 1
COMMAND_WORKER = 1
TARGET = command.Position(1.0, 1.0, 1.0)
RUNTIME = 100

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
    # 1) Controller
    controller = (
        worker_controller.WorkerController()
    )  # or WorkerController(main_logger) if required

    # 2) MP manager
    mp_manager = mp.Manager()

    # 3) Queues (QueueProxyWrapper)
    heartbeat_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, HEARTBEAT_MAX)
    telemetry_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, TELEMETRY_MAX)
    report_queue = queue_proxy_wrapper.QueueProxyWrapper(mp_manager, REPORT_MAX)

    # 4) WorkerProperties.create(...) for each worker

    ok, hb_sender_props = worker_manager.WorkerProperties.create(
        controller=controller,
        count=HEARTBEAT_SEND_WORKER,
        target=heartbeat_sender_worker.heartbeat_sender_worker,
        work_arguments={
            "connection": connection,
            "controller": controller,
        },
        input_queues=[],
        output_queues=[],
        local_logger=main_logger,
    )
    if not ok:
        main_logger.error("Failed to create HeartbeatSender properties")
        return -1

    ok, hb_recv_props = worker_manager.WorkerProperties.create(
        controller=controller,
        count=HEARTBEAT_REC_WORKER,
        target=heartbeat_receiver_worker.heartbeat_receiver_worker,
        work_arguments={
            "connection": connection,
            "heartbeat_queue": heartbeat_queue,
            "controller": controller,
        },
        input_queues=[],
        output_queues=[heartbeat_queue],
        local_logger=main_logger,
    )
    if not ok:
        main_logger.error("Failed to create HeartbeatReceiver properties")
        return -1

    ok, telem_props = worker_manager.WorkerProperties.create(
        controller=controller,
        count=TELEMETRY_WORKER,
        target=telemetry_worker.telemetry_worker,
        work_arguments={
            "connection": connection,
            "telemetry_queue": telemetry_queue,
            "controller": controller,
        },
        input_queues=[],
        output_queues=[telemetry_queue],
        local_logger=main_logger,
    )
    if not ok:
        main_logger.error("Failed to create Telemetry properties")
        return -1

    ok, cmd_props = worker_manager.WorkerProperties.create(
        controller=controller,
        count=COMMAND_WORKER,
        target=command_worker.command_worker,
        work_arguments={
            "connection": connection,
            "target": TARGET,
            "telemetry_queue": telemetry_queue,
            "report_queue": report_queue,
            "controller": controller,
        },
        input_queues=[telemetry_queue],
        output_queues=[report_queue],
        local_logger=main_logger,
    )
    if not ok:
        main_logger.error("Failed to create Command properties")
        return -1

    # 5) WorkerManager.create(...) for each
    ok, hb_sender_mgr = worker_manager.WorkerManager.create(
        worker_properties=hb_sender_props, local_logger=main_logger
    )
    if not ok:
        main_logger.error("Failed to create HeartbeatSender manager")
        return -1

    ok, hb_recv_mgr = worker_manager.WorkerManager.create(
        worker_properties=hb_recv_props, local_logger=main_logger
    )
    if not ok:
        main_logger.error("Failed to create HeartbeatReceiver manager")
        return -1

    ok, telem_mgr = worker_manager.WorkerManager.create(
        worker_properties=telem_props, local_logger=main_logger
    )
    if not ok:
        main_logger.error("Failed to create Telemetry manager")
        return -1

    ok, cmd_mgr = worker_manager.WorkerManager.create(
        worker_properties=cmd_props, local_logger=main_logger
    )
    if not ok:
        main_logger.error("Failed to create Command manager")
        return -1

    # 6) start workers
    hb_sender_mgr.start_workers()
    hb_recv_mgr.start_workers()
    telem_mgr.start_workers()
    cmd_mgr.start_workers()

    main_logger.info("Started")

    # 7) Main loop: read outputs
    start_time = time.time()
    while (time.time() - start_time) < RUNTIME:

        try:
            hb_status = heartbeat_queue.queue.get_nowait()
            main_logger.info(f"Heartbeat status: {hb_status}", True)

            if hb_status == "Disconnected":
                main_logger.warning("Drone disconnected, exiting", True)
                break
        except queue.Empty:
            pass

        try:
            report = report_queue.queue.get_nowait()
            main_logger.info(f"Command report: {report}", True)
        except queue.Empty:
            pass

        time.sleep(0.1)

    # 8) Stop
    controller.request_exit()
    main_logger.info("Requested exit")

    # 9) Fill & drain queues
    report_queue.fill_and_drain_queue()
    telemetry_queue.fill_and_drain_queue()
    heartbeat_queue.fill_and_drain_queue()
    main_logger.info("Queues cleared")

    # 10) Join workers (either direction is usually ok after drain+exit)
    cmd_mgr.join_workers()
    telem_mgr.join_workers()
    hb_recv_mgr.join_workers()
    hb_sender_mgr.join_workers()

    main_logger.info("Stopped")

    # 11) Reset controller
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
