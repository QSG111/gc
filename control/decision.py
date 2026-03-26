from config import FORWARD_RATIO, TURN_RATIO


SAFE_ZONE_PHASES = {"GO_SAFE_ZONE", "DROP", "CONFIRM_DROP"}


def decide_motion(quality_info, plan_info, escape_info, mission_info, safe_zone_info):
    # 动作决策优先级：
    # 1. 画面异常先停车
    # 2. 接近敌方安全区时优先避让
    # 3. 任务状态机动作优先
    # 4. 卡住时先后退脱困
    # 5. 最后才走基础循迹结果
    if not quality_info["ok"]:
        return "S"

    enemy_close = safe_zone_info["enemy_danger_close"]
    in_safe_zone_task = mission_info["phase"] in SAFE_ZONE_PHASES
    if in_safe_zone_task and enemy_close and not safe_zone_info["friendly_found"]:
        return "B"

    if mission_info["action"] != "S":
        if mission_info["action"] == "F" and in_safe_zone_task and enemy_close:
            return "B"
        return mission_info["action"]

    if escape_info["stuck"]:
        return "B"

    motion = plan_info["motion"]
    drive_ratio = plan_info["drive_ratio"]

    # 直行要求的可通行区域更充分，转向阈值可以稍微低一点。
    if motion == "F" and drive_ratio >= FORWARD_RATIO:
        return "F"
    if drive_ratio >= TURN_RATIO:
        return motion
    return motion
