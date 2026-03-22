from config import SIDE_COLOR


GAME_RULES = {
    "friendly_color": SIDE_COLOR,
    "enemy_color": "blue" if SIDE_COLOR == "red" else "red",
    "max_carry_count": 3,
    "danger_must_be_single": True,
}

TARGET_SPECS = {
    # Friendly ordinary targets must be handled first according to the rules.
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
        "allow_multi_carry": True,
    },
    # Core targets are shared targets with lower priority than friendly ones.
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
        "allow_multi_carry": True,
    },
    # Danger targets should stay isolated in later logic.
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
        "allow_multi_carry": False,
    },
}


def build_task_queue():
    """Build the default mission order from rule priority."""
    specs = [
        TARGET_SPECS["friendly_ordinary"],
        TARGET_SPECS["core_target"],
        TARGET_SPECS["danger_target"],
    ]
    return sorted(specs, key=lambda item: item["priority"])
