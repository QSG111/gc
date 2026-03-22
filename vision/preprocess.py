import cv2
import numpy as np

from config import (
    CLAHE_CLIP_LIMIT,
    CLAHE_TILE_GRID_SIZE,
    ENABLE_CLAHE,
    GAUSSIAN_KERNEL_SIZE,
)


def preprocess_frame(frame):
    """OpenCV preprocessing before detection.

    This stage is where we improve image quality before later YOLO use:
    - denoise with Gaussian blur
    - enhance local contrast with CLAHE
    - prepare gray / hsv views once per frame
    """
    blurred = cv2.GaussianBlur(frame, (GAUSSIAN_KERNEL_SIZE, GAUSSIAN_KERNEL_SIZE), 0)
    enhanced = apply_clahe_if_enabled(blurred)
    hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
    return {
        "input": frame,
        "blurred": blurred,
        "enhanced": enhanced,
        "hsv": hsv,
        "gray": gray,
    }


def apply_clahe_if_enabled(frame):
    if not ENABLE_CLAHE:
        return frame

    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=CLAHE_CLIP_LIMIT,
        tileGridSize=(CLAHE_TILE_GRID_SIZE, CLAHE_TILE_GRID_SIZE),
    )
    l_channel = clahe.apply(l_channel)
    merged = cv2.merge((l_channel, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
