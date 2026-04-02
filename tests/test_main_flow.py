import unittest
from unittest.mock import patch

from main import build_load_review_info
from mission.state_machine import RescueMission
from mission.task_config import build_task_queue


class MainFlowTests(unittest.TestCase):
    def test_review_info_is_none_when_feature_disabled(self):
        mission = RescueMission(build_task_queue())
        mission.phase = "REVIEW_LOAD"
        with patch("main.ENABLE_LOAD_REVIEW", False):
            self.assertIsNone(build_load_review_info(mission))

    def test_review_info_bypasses_when_enabled_and_in_review_phase(self):
        mission = RescueMission(build_task_queue())
        mission.phase = "REVIEW_LOAD"
        with patch("main.ENABLE_LOAD_REVIEW", True):
            info = build_load_review_info(mission)

        self.assertEqual(
            {
                "available": True,
                "reject_required": False,
                "reason": "review_bypassed",
            },
            info,
        )

    def test_review_info_is_none_outside_review_phase(self):
        mission = RescueMission(build_task_queue())
        mission.phase = "SEARCH"
        with patch("main.ENABLE_LOAD_REVIEW", True):
            self.assertIsNone(build_load_review_info(mission))


if __name__ == "__main__":
    unittest.main()
