class RescueMission:
    def __init__(self, tasks):
        self.tasks = tasks
        self.task_index = 0
        self.phase = "SEARCH"
        self.substep_index = 0
        self.carry_count = 0
        self.last_action = "SEARCH"
        self.finished = False

    def current_task(self):
        if self.task_index >= len(self.tasks):
            return None
        return self.tasks[self.task_index]

    def _build_result(self, task, action, note):
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
            "carry_count": self.carry_count,
        }

    def update(self, frame_width, target_info, quality_ok, safe_zone_info):
        task = self.current_task()
        if task is None:
            result = self._build_result(None, "S", "mission_done")
            result["safe_zone_visible"] = safe_zone_info["friendly_found"]
            self.finished = True
            self.phase = "DONE"
            return result

        action = "S"
        note = "waiting"

        if not quality_ok:
            self.last_action = "S"
            result = self._build_result(task, "S", "quality_low")
            result["safe_zone_visible"] = safe_zone_info["friendly_found"]
            return result

        center_tolerance = task["center_tolerance"]
        stop_area = task["stop_area"]

        if self.phase == "SEARCH":
            if not target_info["found"]:
                action = task["search_action"]
                note = f"search_{task['target_color']}"
            else:
                self.phase = "ALIGN"
                action = "S"
                note = f"{task['target_color']}_found"

        elif self.phase == "ALIGN":
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
            if not target_info["found"]:
                self.phase = "SEARCH"
                action = task["search_action"]
                note = f"{task['target_color']}_lost"
            elif target_info["area"] >= stop_area:
                self.phase = "PICKUP"
                self.substep_index = 0
                action = "S"
                note = "close_enough"
            else:
                action = "F"
                note = f"approach_{task['target_color']}"

        elif self.phase == "PICKUP":
            sequence = task["pickup_sequence"]
            action = sequence[self.substep_index]
            note = f"pickup_action_{self.substep_index + 1}"
            self.substep_index += 1
            if self.substep_index >= len(sequence):
                self.carry_count += 1
                self.phase = "GO_SAFE_ZONE"
                self.substep_index = 0

        elif self.phase == "GO_SAFE_ZONE":
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
            sequence = task["drop_sequence"]
            action = sequence[self.substep_index]
            note = f"drop_action_{self.substep_index + 1}"
            self.substep_index += 1
            if self.substep_index >= len(sequence):
                self.phase = "NEXT_TASK"

        elif self.phase == "NEXT_TASK":
            self.task_index += 1
            self.substep_index = 0
            if self.task_index >= len(self.tasks):
                self.phase = "DONE"
                self.finished = True
                action = "S"
                note = "mission_done"
            else:
                task = self.current_task()
                self.phase = "SEARCH"
                action = "S"
                note = f"next_{task['display_name']}"

        elif self.phase == "DONE":
            self.finished = True
            action = "S"
            note = "mission_done"

        self.last_action = action
        result = self._build_result(task, action, note)
        result["safe_zone_visible"] = safe_zone_info["friendly_found"]
        return result
