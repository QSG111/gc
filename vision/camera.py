import cv2

from config import CAMERA_INDEX, FRAME_HEIGHT, FRAME_WIDTH


def create_camera():
    # 创建摄像头并按配置设置分辨率。
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return cap
