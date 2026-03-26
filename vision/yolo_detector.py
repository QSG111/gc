from vision.color_targets import empty_target_info
from vision.detector_interface import BaseDetector


class YoloDetector(BaseDetector):
    """预留给后续 YOLOv8 接入的检测器接口。"""

    def __init__(self, model_path=None):
        self.model_path = model_path
        self.model = None

    def load(self):
        """后续在这里加载 YOLO 模型。"""
        return None

    def detect(self, frame, processed, color_names):
        """返回与 ColorDetector 相同结构的检测结果。"""
        return {
            color_name: empty_target_info(color_name)
            for color_name in color_names
        }
