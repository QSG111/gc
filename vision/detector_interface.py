class BaseDetector:
    """Unified detector interface.

    The current project uses HSV-based color detection first.
    Later, a YOLOv8 detector can implement the same method so the
    main loop does not need to change.
    """

    def detect(self, frame, processed, color_names):
        raise NotImplementedError
