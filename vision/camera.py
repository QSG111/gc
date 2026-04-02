import cv2

from config import CAMERA_INDEX, FRAME_HEIGHT, FRAME_WIDTH


def create_camera():
    # 创建摄像头并设置分辨率，打开失败时直接抛出异常给上层处理。
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"cannot open camera index {CAMERA_INDEX}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return cap
