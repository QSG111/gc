import time

from config import (
    SERIAL_BAUDRATE,
    SERIAL_ENABLED,
    SERIAL_PORT,
    SERIAL_REPEAT_INTERVAL_SEC,
    SERIAL_TIMEOUT,
)
from control.protocol import motion_to_byte

try:
    import serial
except Exception:
    serial = None


class SerialController:
    CONTINUOUS_COMMANDS = {"F", "L", "R", "B", "S", "SEARCH", "FAST_RIGHT", "TURN_AND_ADVANCE"}

    def __init__(self, serial_port=None, time_fn=None, repeat_interval=None):
        # Resend drive commands at a low rate so the base keeps receiving motion updates.
        self.last_command = None
        self.last_send_time = None
        self.ser = None
        self.time_fn = time_fn or time.monotonic
        self.repeat_interval = (
            SERIAL_REPEAT_INTERVAL_SEC if repeat_interval is None else repeat_interval
        )

        if not SERIAL_ENABLED:
            return
        if serial is None:
            print("pyserial unavailable, serial output disabled")
            return

        try:
            port = SERIAL_PORT if serial_port is None else serial_port
            self.ser = serial.Serial(port, SERIAL_BAUDRATE, timeout=SERIAL_TIMEOUT)
        except Exception as exc:
            print(f"serial open failed: {exc}")
            self.ser = None

    def send(self, command):
        # One-shot arm/drop actions still send only on change to avoid retriggering.
        now = self.time_fn()
        same_command = command == self.last_command
        continuous = command in self.CONTINUOUS_COMMANDS
        repeat_due = (
            same_command
            and continuous
            and self.last_send_time is not None
            and (now - self.last_send_time) >= self.repeat_interval
        )

        if same_command and not repeat_due:
            return

        self.last_command = command
        self.last_send_time = now
        print(f"motion={command}")
        cmd_byte = motion_to_byte(command)
        if self.ser is not None and cmd_byte is not None:
            try:
                self.ser.write(bytes([cmd_byte]))
            except Exception as exc:
                print(f"serial write failed: {exc}")
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None
                # 恢复为可重试状态，避免后续同指令被“重复过滤”吞掉。
                self.last_command = None
                self.last_send_time = None

    def close(self):
        if self.ser is not None:
            self.ser.close()
