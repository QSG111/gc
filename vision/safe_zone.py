import cv2

from mission.task_config import GAME_RULES
from vision.color_targets import build_color_mask


def detect_safe_zones(hsv_frame):
    """Detect friendly and enemy safe-zone color blocks.

    The current implementation only checks the top and bottom parts
    of the frame, which matches the赛场示意图中的安全区大致位置.
    """
    hsv = hsv_frame
    height, width = hsv.shape[:2]
    rois = {
        "top": hsv[: int(height * 0.35), :],
        "bottom": hsv[int(height * 0.65) :, :],
    }

    friendly_color = GAME_RULES["friendly_color"]
    enemy_color = GAME_RULES["enemy_color"]

    info = {
        "friendly_color": friendly_color,
        "enemy_color": enemy_color,
        "friendly_found": False,
        "friendly_area": 0.0,
        "friendly_region": "none",
        "enemy_found": False,
        "enemy_area": 0.0,
        "enemy_region": "none",
    }

    for region_name, roi in rois.items():
        friendly_mask = build_color_mask(roi, friendly_color)
        enemy_mask = build_color_mask(roi, enemy_color)
        friendly_area = float(cv2.countNonZero(friendly_mask))
        enemy_area = float(cv2.countNonZero(enemy_mask))

        if friendly_area > info["friendly_area"]:
            info["friendly_area"] = friendly_area
            info["friendly_found"] = friendly_area > 3000
            info["friendly_region"] = region_name

        if enemy_area > info["enemy_area"]:
            info["enemy_area"] = enemy_area
            info["enemy_found"] = enemy_area > 3000
            info["enemy_region"] = region_name

    return info
