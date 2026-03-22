import cv2

from config import USE_YOLO_DETECTOR, WINDOW_NAME, YOLO_MODEL_PATH
from control.decision import decide_motion
from control.protocol import motion_to_text
from control.serial_comm import SerialController
from mission.task_config import GAME_RULES, TARGET_SPECS, build_task_queue
from mission.state_machine import RescueMission
from planning.escape import EscapeMonitor
from planning.planner import plan_direction
from ui.overlay import draw_status_panel
from vision.camera import create_camera
from vision.color_detector import ColorDetector
from vision.color_targets import empty_target_info
from vision.postprocess import merge_detection_results
from vision.obstacle import detect_obstacles
from vision.path_detect import extract_drive_mask, mask_center_ratio
from vision.preprocess import preprocess_frame
from vision.quality import evaluate_frame_quality
from vision.safe_zone import detect_safe_zones
from vision.yolo_detector import YoloDetector


def resolve_current_target(current_task, all_targets):
    """Select the active target for the current mission step."""
    if current_task is None:
        return empty_target_info()
    return all_targets.get(current_task["target_color"], empty_target_info(current_task["target_color"]))


def draw_target_overlay(preview, target_info):
    """Draw the current target box on the debug preview."""
    if not target_info["found"] or target_info["bbox"] is None:
        return

    x, y, w, h = target_info["bbox"]
    cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 255), 2)
    cv2.putText(
        preview,
        f"{target_info['color']} area={target_info['area']:.0f}",
        (x, max(y - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2,
    )


def build_detectors():
    """Create the current OpenCV detector and optional YOLO detector."""
    color_detector = ColorDetector()
    yolo_detector = YoloDetector(YOLO_MODEL_PATH) if USE_YOLO_DETECTOR else None
    if yolo_detector is not None:
        yolo_detector.load()
    return color_detector, yolo_detector


def main():
    color_detector, yolo_detector = build_detectors()
    cap = create_camera()
    serial_controller = SerialController()
    escape_monitor = EscapeMonitor()
    mission = RescueMission(build_task_queue())
    target_colors = sorted({spec["target_color"] for spec in TARGET_SPECS.values()})

    while True:
        ok, frame = cap.read()
        if not ok:
            print("cannot read camera frame")
            break

        # Precompute common representations once per frame to avoid
        # repeated BGR->HSV and BGR->GRAY conversions.
        processed = preprocess_frame(frame)
        hsv_frame = processed["hsv"]
        gray_frame = processed["gray"]

        drive_mask = extract_drive_mask(hsv_frame)
        obstacle_info = detect_obstacles(frame)
        color_results = color_detector.detect(frame, processed, target_colors)
        yolo_results = (
            yolo_detector.detect(frame, processed, target_colors)
            if yolo_detector is not None
            else {color_name: empty_target_info(color_name) for color_name in target_colors}
        )
        all_targets = merge_detection_results(color_results, yolo_results, target_colors)
        safe_zone_info = detect_safe_zones(hsv_frame)
        quality_info = evaluate_frame_quality(gray_frame)
        center_ratio = mask_center_ratio(drive_mask)
        plan_info = plan_direction(center_ratio, obstacle_info)
        escape_info = escape_monitor.update(frame, plan_info["motion"])
        current_task = mission.current_task()
        target_info = resolve_current_target(current_task, all_targets)

        # The mission state machine decides what stage the robot is in:
        # search, align, approach, pick up, go to safe zone, or drop.
        mission_info = mission.update(frame.shape[1], target_info, quality_info["ok"], safe_zone_info)
        motion = decide_motion(quality_info, plan_info, escape_info, mission_info)

        serial_controller.send(motion)

        mask_bgr = cv2.cvtColor(drive_mask, cv2.COLOR_GRAY2BGR)
        preview = cv2.hconcat([frame, mask_bgr])
        draw_status_panel(
            preview,
            quality_info=quality_info,
            obstacle_info=obstacle_info,
            plan_info=plan_info,
            escape_info=escape_info,
            motion_text=motion_to_text(motion),
            mission_info=mission_info,
            safe_zone_info=safe_zone_info,
        )
        draw_target_overlay(preview, target_info)

        cv2.imshow(WINDOW_NAME, preview)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    serial_controller.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
