from vision.color_targets import empty_target_info
from vision.detector_interface import BaseDetector


class YoloDetector(BaseDetector):
    """Reserved interface for future YOLOv8 integration.

    Expected future work:
    - load a YOLOv8 model
    - map detection classes to project target colors/types
    - output the same structure as ColorDetector.detect()
    """

    def __init__(self, model_path=None):
        self.model_path = model_path
        self.model = None

    def load(self):
        """Load the YOLOv8 model here in the future.

        Recommended future implementation:
        - from ultralytics import YOLO
        - self.model = YOLO(self.model_path)
        """
        return None

    def detect(self, frame, processed, color_names):
        """Return YOLO detections with the same structure as ColorDetector."""
        return {
            color_name: empty_target_info(color_name)
            for color_name in color_names
        }
