import cv2
import numpy as np


def detect_obstacles(frame):
    height, width = frame.shape[:2]
    roi = frame[int(height * 0.45) :, :]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)

    left = edges[:, : width // 3]
    center = edges[:, width // 3 : 2 * width // 3]
    right = edges[:, 2 * width // 3 :]

    total = float(edges.size) if edges.size else 1.0
    left_ratio = float(cv2.countNonZero(left)) / total * 3.0
    center_ratio = float(cv2.countNonZero(center)) / total * 3.0
    right_ratio = float(cv2.countNonZero(right)) / total * 3.0

    return {
        "left_ratio": left_ratio,
        "center_ratio": center_ratio,
        "right_ratio": right_ratio,
        "blocked": center_ratio > 0.12,
    }
