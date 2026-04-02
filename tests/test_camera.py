import unittest
from unittest.mock import patch

import cv2

from config import CAMERA_INDEX, FRAME_HEIGHT, FRAME_WIDTH
from vision.camera import create_camera


class FakeCap:
    def __init__(self, opened=True):
        self._opened = opened
        self.released = False
        self.set_calls = []

    def isOpened(self):
        return self._opened

    def set(self, prop, value):
        self.set_calls.append((prop, value))
        return True

    def release(self):
        self.released = True


class CameraTests(unittest.TestCase):
    @patch("vision.camera.cv2.VideoCapture")
    def test_create_camera_sets_resolution_when_opened(self, mock_capture):
        fake_cap = FakeCap(opened=True)
        mock_capture.return_value = fake_cap

        cap = create_camera()

        self.assertIs(cap, fake_cap)
        self.assertEqual(
            [
                (cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH),
                (cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT),
            ],
            fake_cap.set_calls,
        )
        mock_capture.assert_called_once_with(CAMERA_INDEX)

    @patch("vision.camera.cv2.VideoCapture")
    def test_create_camera_raises_when_open_fails(self, mock_capture):
        fake_cap = FakeCap(opened=False)
        mock_capture.return_value = fake_cap

        with self.assertRaisesRegex(RuntimeError, "cannot open camera index"):
            create_camera()

        self.assertTrue(fake_cap.released)


if __name__ == "__main__":
    unittest.main()
