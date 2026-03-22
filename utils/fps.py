import time


class FPSCounter:
    def __init__(self):
        self.last_time = time.time()

    def tick(self):
        now = time.time()
        delta = now - self.last_time
        self.last_time = now
        if delta <= 0:
            return 0.0
        return 1.0 / delta
