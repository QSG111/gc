import cv2
import numpy as np

from config import MIN_BRIGHTNESS, MIN_LAPLACIAN_VARIANCE


def evaluate_frame_quality(gray_frame):
    gray = gray_frame
    brightness = float(np.mean(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    ok = brightness >= MIN_BRIGHTNESS and sharpness >= MIN_LAPLACIAN_VARIANCE
    return {
        "brightness": brightness,
        "sharpness": sharpness,
        "ok": ok,
    }
