import unittest

from control.decision import decide_motion
from config import ENABLE_LOAD_REVIEW, TARGET_LOST_TOLERANCE_FRAMES
from mission.state_machine import RescueMission
from mission.task_config import TARGET_SPECS, build_task_queue
from config import SIDE_COLOR


def target(found=False, center_x=320.0, area=0.0):
    return {
        "found": found,
        "color": SIDE_COLOR,
        "area": area,
        "center_x": center_x,
        "center_y": 240.0 if found else None,
        "bbox": (0, 0, 10, 10) if found else None,
        "mask": None,
    }


def safe_zone(found=False, area=0.0):
    enemy_color = "blue" if SIDE_COLOR == "red" else "red"
    return {
        "friendly_color": SIDE_COLOR,
        "enemy_color": enemy_color,
        "friendly_found": found,
        "friendly_area": area,
        "friendly_region": "bottom" if found else "none",
        "friendly_danger_close": found and area > 12000.0,
        "enemy_found": False,
        "enemy_area": 0.0,
        "enemy_region": "none",
        "enemy_danger_close": False,
    }


class RescueMissionTests(unittest.TestCase):
    def test_drop_must_be_confirmed_before_task_completion(self):
        mission = RescueMission(build_task_queue())
        mission.completed_tasks.add("friendly_ordinary")
        mission.task_index = 2

        mission.update(640, target(found=False), True, safe_zone())
        mission.update(640, target(found=True, center_x=320.0, area=2000.0), True, safe_zone())
        mission.update(640, target(found=True, center_x=320.0, area=2000.0), True, safe_zone())
        mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())

        pickup_1 = mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())
        pickup_2 = mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())
        self.assertEqual("GO_SAFE_ZONE", mission.phase)
        self.assertEqual(1, pickup_2["carry_count"])

        mission.update(640, target(), True, safe_zone(found=True, area=40000.0))
        drop_1 = mission.update(640, target(), True, safe_zone(found=True, area=40000.0))
        drop_2 = mission.update(640, target(), True, safe_zone(found=True, area=40000.0))
        confirm_1 = mission.update(640, target(), True, safe_zone(found=True, area=40000.0))
        confirm_2 = mission.update(640, target(), True, safe_zone(found=True, area=40000.0))

        self.assertEqual("B", drop_1["action"])
        self.assertEqual("S", drop_2["action"])
        self.assertEqual("CONFIRM_DROP", confirm_1["phase"])
        self.assertEqual("confirm_drop_1", confirm_1["note"])
        self.assertEqual("NEXT_TASK", confirm_2["phase"])
        self.assertEqual("drop_confirmed", confirm_2["note"])
        self.assertEqual(0, confirm_2["carry_count"])
        self.assertEqual(1, confirm_2["delivered_count"])

    def test_friendly_targets_can_accumulate_until_max_carry(self):
        mission = RescueMission(build_task_queue())

        mission.update(640, target(found=True, center_x=320.0, area=2000.0), True, safe_zone())
        mission.update(640, target(found=True, center_x=320.0, area=2000.0), True, safe_zone())
        mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())
        mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())
        pickup_2 = mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())

        self.assertEqual("SEARCH", pickup_2["phase"])
        self.assertEqual("collect_next_target", pickup_2["note"])
        self.assertEqual(1, pickup_2["carry_count"])

        mission.phase = "PICKUP"
        mission.substep_index = 0
        mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())
        pickup_4 = mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())

        self.assertEqual("SEARCH", pickup_4["phase"])
        self.assertEqual(2, pickup_4["carry_count"])

        mission.phase = "PICKUP"
        mission.substep_index = 0
        mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())
        pickup_6 = mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())

        self.assertEqual("GO_SAFE_ZONE", pickup_6["phase"])
        self.assertEqual("load_ready_for_safe_zone", pickup_6["note"])
        self.assertEqual(3, pickup_6["carry_count"])

    def test_shared_targets_unlock_after_friendly_task_completes(self):
        mission = RescueMission(build_task_queue())

        self.assertFalse(mission._shared_targets_unlocked())
        self.assertEqual("friendly_ordinary", mission.current_task()["display_name"])

        mission.completed_tasks.add("friendly_ordinary")
        mission.task_index = 1

        result = mission.update(640, target(found=False), True, safe_zone())
        self.assertTrue(result["shared_unlocked"])
        self.assertEqual("core_target", result["task_name"])

    def test_target_loss_is_buffered_before_returning_to_search(self):
        mission = RescueMission(build_task_queue())
        mission.phase = "ALIGN"

        for lost_index in range(TARGET_LOST_TOLERANCE_FRAMES - 1):
            result = mission.update(640, target(found=False), True, safe_zone())
            self.assertEqual("ALIGN", result["phase"])
            self.assertEqual(lost_index + 1, result["target_lost_count"])

        result = mission.update(640, target(found=False), True, safe_zone())
        self.assertEqual("SEARCH", result["phase"])
        self.assertEqual("SEARCH", result["action"])
        self.assertEqual(f"{SIDE_COLOR}_lost", result["note"])

    def test_enemy_safe_zone_close_forces_back_off(self):
        motion = decide_motion(
            quality_info={"ok": True},
            plan_info={"motion": "F", "drive_ratio": 0.9},
            escape_info={"stuck": False},
            mission_info={"action": "F", "phase": "GO_SAFE_ZONE"},
            safe_zone_info={
                "friendly_found": False,
                "friendly_area": 0.0,
                "friendly_region": "none",
                "friendly_danger_close": False,
                "enemy_found": True,
                "enemy_area": 18000.0,
                "enemy_region": "bottom",
                "enemy_danger_close": True,
            },
        )
        self.assertEqual("B", motion)

    def test_danger_target_requires_empty_load(self):
        mission = RescueMission(build_task_queue())
        mission.completed_tasks.add("friendly_ordinary")
        mission.task_index = 2
        mission.load_count = 1
        mission.phase = "SEARCH"

        result = mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())

        self.assertEqual("GO_SAFE_ZONE", result["phase"])
        self.assertEqual("danger_requires_empty_load", result["note"])
        self.assertEqual("TURN_AND_ADVANCE", result["action"])

    def test_pickup_stays_on_existing_flow_when_review_disabled(self):
        mission = RescueMission(build_task_queue())

        mission.update(640, target(found=True, center_x=320.0, area=2000.0), True, safe_zone())
        mission.update(640, target(found=True, center_x=320.0, area=2000.0), True, safe_zone())
        mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())
        mission.update(640, target(found=True, center_x=320.0, area=25000.0), True, safe_zone())
        result = mission.update(
            640,
            target(found=True, center_x=320.0, area=25000.0),
            True,
            safe_zone(),
            load_review_info={"available": True, "reject_required": True, "reason": "wrong_item"},
        )

        self.assertFalse(ENABLE_LOAD_REVIEW)
        self.assertEqual("SEARCH", result["phase"])
        self.assertEqual("collect_next_target", result["note"])

    def test_review_and_reject_phases_are_reserved_but_safe_when_disabled(self):
        task = dict(TARGET_SPECS["friendly_ordinary"])
        task["review_after_pickup"] = True
        mission = RescueMission([task])
        mission.phase = "REVIEW_LOAD"
        mission.load_count = 1

        review_result = mission.update(
            640,
            target(found=False),
            True,
            safe_zone(),
            load_review_info={"available": True, "reject_required": True, "reason": "wrong_item"},
        )

        self.assertEqual("SEARCH", review_result["phase"])
        self.assertEqual("collect_next_target", review_result["note"])


if __name__ == "__main__":
    unittest.main()
