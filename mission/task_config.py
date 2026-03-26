from config import SIDE_COLOR


# 比赛基础规则配置，状态机和检测逻辑都从这里读取统一约束。
GAME_RULES = {
    "friendly_color": SIDE_COLOR,
    "enemy_color": "blue" if SIDE_COLOR == "red" else "red",
    "max_carry_count": 3,
    "danger_must_be_single": True,
}

# 三类任务的参数表，描述每类目标的搜索、靠近、抓取和投放策略。
TARGET_SPECS = {
    # 己方普通目标必须优先完成，这是共享目标解锁前提。
    "friendly_ordinary": {
        "display_name": "friendly_ordinary",
        "target_color": GAME_RULES["friendly_color"],
        "target_type": "ordinary",
        "priority": 1,
        "must_finish_before_shared": True,
        "search_action": "SEARCH",
        "center_tolerance": 20,
        "stop_area": 18000,
        "pickup_sequence": ["ARM_ROTATE", "ARM_UP"],
        "drop_sequence": ["ACT_STAGE_1", "S"],
        "safe_zone_search_action": "TURN_AND_ADVANCE",
        "safe_zone_stop_area": 35000,
        "drop_confirm_frames": 2,
        "max_carry_count": GAME_RULES["max_carry_count"],
        "allow_multi_carry": True,
    },
    # 核心目标属于共享目标，优先级排在己方普通目标之后。
    "core_target": {
        "display_name": "core_target",
        "target_color": "black",
        "target_type": "core",
        "priority": 2,
        "must_finish_before_shared": False,
        "search_action": "SEARCH",
        "center_tolerance": 24,
        "stop_area": 22000,
        "pickup_sequence": ["ARM_CENTER", "ACT_STAGE_2"],
        "drop_sequence": ["B", "TURN_AND_ADVANCE"],
        "safe_zone_search_action": "TURN_AND_ADVANCE",
        "safe_zone_stop_area": 35000,
        "drop_confirm_frames": 2,
        "max_carry_count": GAME_RULES["max_carry_count"],
        "allow_multi_carry": True,
    },
    # 危险目标必须单独搬运，所以最大载荷限制为 1。
    "danger_target": {
        "display_name": "danger_target",
        "target_color": "yellow",
        "target_type": "danger",
        "priority": 3,
        "must_finish_before_shared": False,
        "search_action": "SEARCH",
        "center_tolerance": 26,
        "stop_area": 15000,
        "pickup_sequence": ["ARM_ROTATE", "ARM_UP"],
        "drop_sequence": ["B", "S"],
        "safe_zone_search_action": "TURN_AND_ADVANCE",
        "safe_zone_stop_area": 35000,
        "drop_confirm_frames": 2,
        "max_carry_count": 1,
        "allow_multi_carry": False,
    },
}


def build_task_queue():
    """按赛规优先级生成默认任务顺序。"""
    specs = [
        TARGET_SPECS["friendly_ordinary"],
        TARGET_SPECS["core_target"],
        TARGET_SPECS["danger_target"],
    ]
    return sorted(specs, key=lambda item: item["priority"])
