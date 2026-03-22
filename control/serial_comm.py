from config import SERIAL_BAUDRATE, SERIAL_ENABLED, SERIAL_PORT, SERIAL_TIMEOUT
from control.protocol import motion_to_byte

try:
    import serial
except Exception:
    serial = None


class SerialController:
    def __init__(self):
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
        if command == self.last_command:
            return
        self.last_command = command
        print(f"motion={command}")
        cmd_byte = motion_to_byte(command)
        if self.ser is not None and cmd_byte is not None:
            self.ser.write(bytes([cmd_byte]))

    def close(self):
        if self.ser is not None:
            self.ser.close()
