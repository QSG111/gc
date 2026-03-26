import cv2

from mission.task_config import GAME_RULES
from vision.color_targets import build_color_mask


SAFE_ZONE_FOUND_AREA = 3000
SAFE_ZONE_DANGER_AREA = 12000


def detect_safe_zones(hsv_frame):
    """检测己方和对方安全区颜色块。"""
    hsv = hsv_frame
    height, _ = hsv.shape[:2]

    # 按赛场示意图，安全区更可能出现在画面上下区域，
    # 所以这里只截取上下两个 ROI，减少计算量和误检。
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
        "friendly_danger_close": False,
        "enemy_found": False,
        "enemy_area": 0.0,
        "enemy_region": "none",
        "enemy_danger_close": False,
    }

    for region_name, roi in rois.items():
        friendly_mask = build_color_mask(roi, friendly_color)
        enemy_mask = build_color_mask(roi, enemy_color)
        friendly_area = float(cv2.countNonZero(friendly_mask))
        enemy_area = float(cv2.countNonZero(enemy_mask))

        if friendly_area > info["friendly_area"]:
            info["friendly_area"] = friendly_area
            info["friendly_found"] = friendly_area > SAFE_ZONE_FOUND_AREA
            info["friendly_region"] = region_name
            info["friendly_danger_close"] = (
                region_name == "bottom" and friendly_area > SAFE_ZONE_DANGER_AREA
            )

        if enemy_area > info["enemy_area"]:
            info["enemy_area"] = enemy_area
            info["enemy_found"] = enemy_area > SAFE_ZONE_FOUND_AREA
            info["enemy_region"] = region_name
            info["enemy_danger_close"] = (
                region_name == "bottom" and enemy_area > SAFE_ZONE_DANGER_AREA
            )

    return info
