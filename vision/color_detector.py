from vision.color_targets import detect_targets
from vision.detector_interface import BaseDetector


class ColorDetector(BaseDetector):
    """基于 HSV 颜色分割的轻量目标检测器。"""

    def detect(self, frame, processed, color_names):
        return detect_targets(processed["hsv"], color_names)
