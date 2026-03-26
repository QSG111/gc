import cv2
import numpy as np


class EscapeMonitor:
    def __init__(self, stagnation_limit=12, diff_threshold=2.5):
        # prev_gray 用于比较前后帧差异，判断车辆是否“看起来没动”。
        self.prev_gray = None
        self.stagnation_count = 0
        self.stagnation_limit = stagnation_limit
        self.diff_threshold = diff_threshold

    def update(self, frame, planned_motion):
        # 当前方计划是前进，但连续多帧画面变化都很小，就认为可能卡住了。
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        status = {
            "stuck": False,
            "diff": 999.0,
            "count": self.stagnation_count,
            "suggested_motion": planned_motion,
        }

        if self.prev_gray is not None:
            diff = float(np.mean(cv2.absdiff(gray, self.prev_gray)))
            status["diff"] = diff

            if planned_motion == "F" and diff < self.diff_threshold:
                self.stagnation_count += 1
            else:
                self.stagnation_count = 0

        self.prev_gray = gray
        status["count"] = self.stagnation_count

        if self.stagnation_count >= self.stagnation_limit:
            status["stuck"] = True
            status["suggested_motion"] = "B"
            # 触发一次脱困后把计数清零，避免连续重复触发。
            self.stagnation_count = 0

        return status
