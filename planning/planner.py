def plan_direction(drive_ratio, obstacle_info):
    if obstacle_info["blocked"]:
        if obstacle_info["left_ratio"] < obstacle_info["right_ratio"]:
            motion = "L"
        else:
            motion = "R"
    elif drive_ratio >= 0.45:
        motion = "F"
    elif obstacle_info["left_ratio"] < obstacle_info["right_ratio"]:
        motion = "L"
    else:
        motion = "R"

    return {
        "drive_ratio": drive_ratio,
        "motion": motion,
    }
