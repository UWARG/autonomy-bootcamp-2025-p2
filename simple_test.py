#!/usr/bin/env python3
"""
Simple test script to validate worker implementations without complex multiprocessing.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from modules.heartbeat.heartbeat_sender import HeartbeatSender
from modules.heartbeat.heartbeat_receiver import HeartbeatReceiver
from modules.telemetry.telemetry import Telemetry, TelemetryData
from modules.command.command import Command, Position
from modules.common.modules.logger import logger


def test_heartbeat_sender() -> bool:
    """Test HeartbeatSender creation"""
    print("Testing HeartbeatSender...")

    # Mock connection object
    class MockConnection:
        class mav:
            @staticmethod
            def heartbeat_send(*args: object) -> bool:
                print(f"  Mock heartbeat sent with args: {args}")
                return True

    mock_conn = MockConnection()
    result, sender = HeartbeatSender.create(mock_conn, None)
    if not result:
        print("  FAIL: Could not create HeartbeatSender")
        return False

    success = sender.run(None)
    if success:
        print("  PASS: HeartbeatSender working")
        return True
    else:
        print("  FAIL: HeartbeatSender.run() failed")
        return False


def test_telemetry_data() -> bool:
    """Test TelemetryData creation"""
    print("Testing TelemetryData...")

    data = TelemetryData(
        time_since_boot=1000,
        x=1.0,
        y=2.0,
        z=3.0,
        x_velocity=0.5,
        y_velocity=0.6,
        z_velocity=0.7,
        roll=0.1,
        pitch=0.2,
        yaw=0.3,
        roll_speed=0.01,
        pitch_speed=0.02,
        yaw_speed=0.03,
    )

    if data.x == 1.0 and data.y == 2.0 and data.z == 3.0:
        print("  PASS: TelemetryData working")
        return True
    else:
        print("  FAIL: TelemetryData values incorrect")
        return False


def test_command() -> bool:
    """Test Command creation and logic"""
    print("Testing Command...")

    # Mock logger
    class MockLogger:
        def info(self, msg: str) -> None:
            print(f"    LOG: {msg}")

        def error(self, msg: str) -> None:
            print(f"    ERROR: {msg}")

    # Mock connection
    class MockConnection:
        class mav:
            @staticmethod
            def command_long_send(*args: object) -> bool:
                print(f"    Mock command sent: {args}")
                return True

    mock_conn = MockConnection()
    mock_logger = MockLogger()
    target = Position(10, 20, 30)

    result, command = Command.create(mock_conn, target, None, mock_logger)
    if not result:
        print("  FAIL: Could not create Command")
        return False

    # Test with telemetry data that should trigger altitude change
    telemetry_data = TelemetryData(
        time_since_boot=1000,
        x=10,
        y=20,
        z=29,  # 1m below target
        x_velocity=1.0,
        y_velocity=0.0,
        z_velocity=0.0,
        roll=0,
        pitch=0,
        yaw=0,
        roll_speed=0,
        pitch_speed=0,
        yaw_speed=0,
    )

    result = command.run(telemetry_data)
    if result and "CHANGE ALTITUDE" in result:
        print("  PASS: Command altitude logic working")
        return True
    else:
        print(f"  FAIL: Command returned: {result}")
        return False


def main() -> bool:
    """Run all tests"""
    print("=== Simple Worker Tests ===")

    tests = [
        test_heartbeat_sender,
        test_telemetry_data,
        test_command,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ERROR: Test failed with exception: {e}")

    print(f"\n=== Results: {passed}/{total} tests passed ===")
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
