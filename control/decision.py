from config import FORWARD_RATIO, TURN_RATIO


def decide_motion(quality_info, plan_info, escape_info, mission_info):
    if not quality_info["ok"]:
        return "S"
    if mission_info["action"] != "S":
        return mission_info["action"]
    if escape_info["stuck"]:
        return "B"

    motion = plan_info["motion"]
    drive_ratio = plan_info["drive_ratio"]
    if motion == "F" and drive_ratio >= FORWARD_RATIO:
        return "F"
    if drive_ratio >= TURN_RATIO:
        return motion
    return motion
