import unittest

from control.protocol import motion_to_byte
from control.serial_comm import SerialController


class FakeSerial:
    def __init__(self):
        self.writes = []
        self.closed = False

    def write(self, payload):
        self.writes.append(payload)

    def close(self):
        self.closed = True


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def advance(self, delta):
        self.now += delta


class BrokenSerial:
    def write(self, payload):
        raise OSError("device disconnected")

    def close(self):
        return None


class SerialControllerTests(unittest.TestCase):
    def test_repeats_continuous_motion_after_interval(self):
        clock = FakeClock()
        fake_serial = FakeSerial()
        controller = SerialController(time_fn=clock.monotonic, repeat_interval=0.2)
        controller.ser = fake_serial

        controller.send("F")
        controller.send("F")
        clock.advance(0.19)
        controller.send("F")
        clock.advance(0.01)
        controller.send("F")

        self.assertEqual([b"\x01", b"\x01"], fake_serial.writes)

    def test_does_not_repeat_one_shot_action_without_change(self):
        clock = FakeClock()
        fake_serial = FakeSerial()
        controller = SerialController(time_fn=clock.monotonic, repeat_interval=0.2)
        controller.ser = fake_serial

        controller.send("ARM_UP")
        clock.advance(1.0)
        controller.send("ARM_UP")

        self.assertEqual([b"\x11"], fake_serial.writes)

    def test_command_change_sends_immediately(self):
        clock = FakeClock()
        fake_serial = FakeSerial()
        controller = SerialController(time_fn=clock.monotonic, repeat_interval=0.2)
        controller.ser = fake_serial

        controller.send("F")
        controller.send("L")
        controller.send("S")

        self.assertEqual([b"\x01", b"\x03", b"\x00"], fake_serial.writes)

    def test_write_failure_disables_port_and_keeps_retryable_state(self):
        clock = FakeClock()
        controller = SerialController(time_fn=clock.monotonic, repeat_interval=0.2)
        controller.ser = BrokenSerial()

        controller.send("F")

        self.assertIsNone(controller.ser)
        self.assertIsNone(controller.last_command)
        self.assertIsNone(controller.last_send_time)

    def test_reject_item_has_protocol_byte(self):
        self.assertEqual(0x24, motion_to_byte("REJECT_ITEM"))


if __name__ == "__main__":
    unittest.main()
