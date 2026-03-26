from config import TARGET_LOST_TOLERANCE_FRAMES
from mission.task_config import GAME_RULES


class RescueMission:
    def __init__(self, tasks):
        # tasks 是已经按优先级排好的任务列表。
        self.tasks = tasks
        self.task_index = 0
        # phase 表示当前任务处于哪一个比赛阶段。
        self.phase = "SEARCH"
        self.substep_index = 0
        # 当前车上载着的目标数量。
        self.load_count = 0
        # 已经确认送入安全区的任务数量。
        self.delivered_count = 0
        # 已经完成的任务集合，用来做后续任务解锁。
        self.completed_tasks = set()
        # 投放确认帧计数，避免一帧误判就切任务。
        self.drop_confirm_count = 0
        # 目标短暂丢失时先缓冲几帧，避免一闪而过就退回搜索。
        self.target_lost_count = 0
        self.last_action = "SEARCH"
        self.finished = False

    def current_task(self):
        if self.task_index >= len(self.tasks):
            return None
        return self.tasks[self.task_index]

    def _shared_targets_unlocked(self):
        # 共享目标在己方普通目标完成后才允许执行。
        return "friendly_ordinary" in self.completed_tasks

    def _task_is_unlocked(self, task):
        if task is None:
            return False
        if not task["must_finish_before_shared"]:
            return self._shared_targets_unlocked()
        return True

    def _danger_task_requires_empty_load(self, task):
        # 危险目标必须单独搬运，只要车上还有任何载荷就不能执行。
        if task is None:
            return False
        if not GAME_RULES["danger_must_be_single"]:
            return False
        pre_pickup_phases = {"SEARCH", "ALIGN", "APPROACH", "PICKUP"}
        return (
            task["target_type"] == "danger"
            and self.load_count > 0
            and self.phase in pre_pickup_phases
        )

    def _should_continue_collecting(self, task):
        # 普通目标和核心目标允许继续累计装载，直到达到当前任务的最大载荷。
        if task is None:
            return False
        if not task.get("allow_multi_carry", False):
            return False
        return self.load_count < task.get("max_carry_count", GAME_RULES["max_carry_count"])

    def _advance_to_next_unlocked_task(self):
        # 跳过尚未解锁的任务，找到当前真正该做的那一项。
        while self.task_index < len(self.tasks):
            task = self.current_task()
            if self._task_is_unlocked(task):
                return task
            self.task_index += 1
        self.finished = True
        self.phase = "DONE"
        return None

    def _build_result(self, task, action, note):
        # 统一返回给主循环的状态结构，便于显示和调试。
        return {
            "phase": self.phase,
            "task_name": task["display_name"] if task else "none",
            "target_type": task["target_type"] if task else "none",
            "target_color": task["target_color"] if task else "none",
            "safe_zone_visible": False,
            "action": action,
            "note": note,
            "finished": self.finished,
            "task_index": self.task_index,
            "task_count": len(self.tasks),
            "carry_count": self.load_count,
            "load_count": self.load_count,
            "delivered_count": self.delivered_count,
            "shared_unlocked": self._shared_targets_unlocked(),
            "target_lost_count": self.target_lost_count,
        }

    def update(self, frame_width, target_info, quality_ok, safe_zone_info):
        # 每一帧根据当前观测更新一次任务状态机。
        task = self._advance_to_next_unlocked_task()
        if task is None:
            result = self._build_result(None, "S", "mission_done")
            result["safe_zone_visible"] = safe_zone_info["friendly_found"]
            self.finished = True
            self.phase = "DONE"
            return result

        action = "S"
        note = "waiting"

        if not quality_ok:
            # 画面质量差时优先停车，避免盲动。
            self.last_action = "S"
            result = self._build_result(task, "S", "quality_low")
            result["safe_zone_visible"] = safe_zone_info["friendly_found"]
            return result

        if self._danger_task_requires_empty_load(task):
            # 如果当前轮到危险目标，但车上仍有载荷，优先清空载荷再继续。
            self.phase = "GO_SAFE_ZONE"
            action = task["safe_zone_search_action"]
            note = "danger_requires_empty_load"
            result = self._build_result(task, action, note)
            result["safe_zone_visible"] = safe_zone_info["friendly_found"]
            return result

        center_tolerance = task["center_tolerance"]
        stop_area = task["stop_area"]

        if self.phase == "SEARCH":
            # 搜索阶段：没看到目标就继续搜，看到目标就进入对中。
            if not target_info["found"]:
                action = task["search_action"]
                note = f"search_{task['target_color']}"
            else:
                self.target_lost_count = 0
                self.phase = "ALIGN"
                action = "S"
                note = f"{task['target_color']}_found"

        elif self.phase == "ALIGN":
            # 对中阶段：让目标尽量回到画面中心附近。
            if not target_info["found"]:
                self.target_lost_count += 1
                action = "S"
                note = f"target_lost_hold_{self.target_lost_count}"
                if self.target_lost_count >= TARGET_LOST_TOLERANCE_FRAMES:
                    self.target_lost_count = 0
                    self.phase = "SEARCH"
                    action = task["search_action"]
                    note = f"{task['target_color']}_lost"
            else:
                self.target_lost_count = 0
                offset = target_info["center_x"] - frame_width / 2.0
                if abs(offset) <= center_tolerance:
                    self.phase = "APPROACH"
                    action = "S"
                    note = f"{task['target_color']}_aligned"
                elif offset < 0:
                    action = "L"
                    note = "align_left"
                else:
                    action = "R"
                    note = "align_right"

        elif self.phase == "APPROACH":
            # 接近阶段：目标面积足够大时认为已经靠近到可抓取距离。
            if not target_info["found"]:
                self.target_lost_count += 1
                action = "S"
                note = f"target_lost_hold_{self.target_lost_count}"
                if self.target_lost_count >= TARGET_LOST_TOLERANCE_FRAMES:
                    self.target_lost_count = 0
                    self.phase = "SEARCH"
                    action = task["search_action"]
                    note = f"{task['target_color']}_lost"
            else:
                self.target_lost_count = 0
                if target_info["area"] >= stop_area:
                    self.phase = "PICKUP"
                    self.substep_index = 0
                    action = "S"
                    note = "close_enough"
                else:
                    action = "F"
                    note = f"approach_{task['target_color']}"

        elif self.phase == "PICKUP":
            # 抓取阶段按预设动作序列逐步执行。
            self.target_lost_count = 0
            sequence = task["pickup_sequence"]
            action = sequence[self.substep_index]
            note = f"pickup_action_{self.substep_index + 1}"
            self.substep_index += 1
            if self.substep_index >= len(sequence):
                self.load_count = min(
                    self.load_count + 1,
                    task.get("max_carry_count", GAME_RULES["max_carry_count"]),
                )
                self.substep_index = 0
                if self._should_continue_collecting(task):
                    self.phase = "SEARCH"
                    note = "collect_next_target"
                else:
                    self.phase = "GO_SAFE_ZONE"
                    note = "load_ready_for_safe_zone"

        elif self.phase == "GO_SAFE_ZONE":
            # 找到己方安全区后直接接近，否则继续搜索安全区。
            self.target_lost_count = 0
            if safe_zone_info["friendly_found"]:
                action = "F"
                note = "approach_safe_zone"
                if safe_zone_info["friendly_area"] >= task["safe_zone_stop_area"]:
                    self.phase = "DROP"
                    self.substep_index = 0
            else:
                action = task["safe_zone_search_action"]
                note = "search_safe_zone"

        elif self.phase == "DROP":
            # 投放阶段也按动作序列执行。
            self.target_lost_count = 0
            sequence = task["drop_sequence"]
            action = sequence[self.substep_index]
            note = f"drop_action_{self.substep_index + 1}"
            self.substep_index += 1
            if self.substep_index >= len(sequence):
                self.phase = "CONFIRM_DROP"
                self.drop_confirm_count = 0

        elif self.phase == "CONFIRM_DROP":
            # 投放后需要连续若干帧确认，才算真正完成任务。
            self.target_lost_count = 0
            if safe_zone_info["friendly_found"] and safe_zone_info["friendly_area"] >= task["safe_zone_stop_area"]:
                self.drop_confirm_count += 1
                action = "S"
                note = f"confirm_drop_{self.drop_confirm_count}"
                if self.drop_confirm_count >= task.get("drop_confirm_frames", 1):
                    self.load_count = 0
                    self.delivered_count += 1
                    self.completed_tasks.add(task["display_name"])
                    self.phase = "NEXT_TASK"
                    note = "drop_confirmed"
            else:
                self.drop_confirm_count = 0
                self.phase = "GO_SAFE_ZONE"
                action = task["safe_zone_search_action"]
                note = "drop_unconfirmed"

        elif self.phase == "NEXT_TASK":
            # 当前任务闭环后切换到下一个任务。
            self.target_lost_count = 0
            self.task_index += 1
            self.substep_index = 0
            task = self._advance_to_next_unlocked_task()
            if task is None:
                self.phase = "DONE"
                self.finished = True
                action = "S"
                note = "mission_done"
            else:
                self.phase = "SEARCH"
                action = "S"
                note = f"next_{task['display_name']}"

        elif self.phase == "DONE":
            # 全部任务结束后维持停车。
            self.target_lost_count = 0
            self.finished = True
            action = "S"
            note = "mission_done"

        self.last_action = action
        result = self._build_result(task, action, note)
        result["safe_zone_visible"] = safe_zone_info["friendly_found"]
        return result
