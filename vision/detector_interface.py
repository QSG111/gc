class BaseDetector:
    """统一的检测器接口。"""
    # 主循环只依赖这个接口，不关心底层到底是颜色分割还是 YOLO。

    def detect(self, frame, processed, color_names):
        raise NotImplementedError
