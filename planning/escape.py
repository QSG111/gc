import cv2
import numpy as np


class EscapeMonitor:
    def __init__(self, stagnation_limit=12, diff_threshold=2.5):
        self.prev_gray = None
        self.stagnation_count = 0
        self.stagnation_limit = stagnation_limit
        self.diff_threshold = diff_threshold

    def update(self, frame, planned_motion):
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
            self.stagnation_count = 0

        return status
