import cv2
import numpy as np

from config import COLOR_MIN_AREA


COLOR_RANGES = {
    "red": [
        (np.array([0, 100, 100]), np.array([10, 255, 255])),
        (np.array([160, 100, 100]), np.array([180, 255, 255])),
        (np.array([0, 50, 50]), np.array([10, 255, 120])),
        (np.array([160, 50, 50]), np.array([180, 255, 120])),
    ],
    "black": [
        (np.array([0, 0, 0]), np.array([180, 255, 35])),
    ],
    "yellow": [
        (np.array([20, 100, 100]), np.array([35, 255, 255])),
    ],
    "purple": [
        (np.array([120, 50, 50]), np.array([145, 255, 255])),
    ],
    "blue": [
        (np.array([100, 120, 50]), np.array([140, 255, 255])),
    ],
}


def build_color_mask(hsv, color_name):
    """Build a binary mask for one logical color."""
    mask = None
    for lower, upper in COLOR_RANGES[color_name]:
        current = cv2.inRange(hsv, lower, upper)
        mask = current if mask is None else cv2.bitwise_or(mask, current)
    return mask


def empty_target_info(color_name="none"):
    """Return a standard empty detection result."""
    return {
        "found": False,
        "color": color_name,
        "area": 0.0,
        "center_x": None,
        "center_y": None,
        "bbox": None,
        "mask": None,
    }


def detect_largest_target(hsv_frame, color_name, min_area=COLOR_MIN_AREA):
    """Detect the largest blob for one target color."""
    mask = build_color_mask(hsv_frame, color_name)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    largest = None
    largest_area = 0.0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= min_area and area > largest_area:
            largest_area = area
            largest = contour

    result = empty_target_info(color_name)
    result["area"] = largest_area
    result["mask"] = mask

    if largest is None:
        return result

    x, y, w, h = cv2.boundingRect(largest)
    result["found"] = True
    result["center_x"] = x + w / 2.0
    result["center_y"] = y + h / 2.0
    result["bbox"] = (x, y, w, h)
    return result


def detect_targets(hsv_frame, color_names):
    """Detect all configured color targets in one frame."""
    return {
        color_name: detect_largest_target(hsv_frame, color_name)
        for color_name in color_names
    }
