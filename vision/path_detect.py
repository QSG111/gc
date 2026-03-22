import cv2
import numpy as np

from config import BINARIZE_THRESHOLD


def extract_drive_mask(hsv_frame):
    v_channel = hsv_frame[:, :, 2]
    _, mask = cv2.threshold(v_channel, BINARIZE_THRESHOLD, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def mask_center_ratio(mask):
    height, width = mask.shape
    roi = mask[int(height * 0.55) :, int(width * 0.33) : int(width * 0.66)]
    if roi.size == 0:
        return 0.0
    return float(cv2.countNonZero(roi)) / float(roi.size)
