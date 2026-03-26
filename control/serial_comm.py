from config import SERIAL_BAUDRATE, SERIAL_ENABLED, SERIAL_PORT, SERIAL_TIMEOUT
from control.protocol import motion_to_byte

try:
    import serial
except Exception:
    serial = None


class SerialController:
    def __init__(self):
        # last_command 用于避免连续发送完全相同的指令。
        self.last_command = None
        self.ser = None

        if not SERIAL_ENABLED:
            return
        if serial is None:
            print("pyserial unavailable, serial output disabled")
            return

        try:
            self.ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=SERIAL_TIMEOUT)
        except Exception as exc:
            print(f"serial open failed: {exc}")
            self.ser = None

    def send(self, command):
        # 重复命令直接忽略，减轻串口负担，也避免下位机反复触发同一动作。
        if command == self.last_command:
            return
        self.last_command = command
        print(f"motion={command}")
        cmd_byte = motion_to_byte(command)
        if self.ser is not None and cmd_byte is not None:
            self.ser.write(bytes([cmd_byte]))

    def close(self):
        # 程序退出前主动关闭串口。
        if self.ser is not None:
            self.ser.close()
