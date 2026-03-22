from vision.color_targets import detect_targets
from vision.detector_interface import BaseDetector


class ColorDetector(BaseDetector):
    """Fallback detector based on HSV color segmentation."""

    def detect(self, frame, processed, color_names):
        return detect_targets(processed["hsv"], color_names)
