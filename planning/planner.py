from config import FORWARD_RATIO


def plan_direction(drive_ratio, obstacle_info):
    # 基础规划策略：
    # 1. 正前方有障碍时优先绕开
    # 2. 中间通路足够宽时直行
    # 3. 否则朝障碍更少的一侧转向
    if obstacle_info["blocked"]:
        if obstacle_info["left_ratio"] < obstacle_info["right_ratio"]:
            motion = "L"
        else:
            motion = "R"
    elif drive_ratio >= FORWARD_RATIO:
        motion = "F"
    elif obstacle_info["left_ratio"] < obstacle_info["right_ratio"]:
        motion = "L"
    else:
        motion = "R"

    return {
        "drive_ratio": drive_ratio,
        "motion": motion,
    }
