import cv2

from config import (
    USE_YOLO_DETECTOR,
    WINDOW_NAME,
    YOLO_FRAME_INTERVAL,
    YOLO_MODEL_PATH,
    YOLO_SEARCH_ONLY,
)
from control.decision import decide_motion
from control.protocol import motion_to_text
from control.serial_comm import SerialController
from mission.state_machine import RescueMission
from mission.task_config import build_task_queue
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


TARGET_TRACKING_PHASES = {"SEARCH", "ALIGN", "APPROACH", "PICKUP"}


def build_runtime():
    # 统一初始化运行时依赖，主循环里只保留读帧和处理流程。
    color_detector = ColorDetector()
    yolo_detector = None
    if USE_YOLO_DETECTOR:
        yolo_detector = YoloDetector(YOLO_MODEL_PATH)
        yolo_detector.load()

    cap = create_camera()
    return {
        "cap": cap,
        "serial": SerialController(),
        "escape_monitor": EscapeMonitor(),
        "mission": RescueMission(build_task_queue()),
        "color_detector": color_detector,
        "yolo_detector": yolo_detector,
        "frame_index": 0,
        "last_yolo_results": {},
        "last_yolo_frame": -1,
    }


def current_task_colors(mission):
    # 只在找目标、对中、接近、抓取这几个阶段检测当前目标颜色，
    # 避免每一帧都把所有目标颜色都跑一遍。
    current_task = mission.current_task()
    if current_task is None:
        return []
    if mission.phase not in TARGET_TRACKING_PHASES:
        return []
    return [current_task["target_color"]]


def resolve_target_info(current_task, detections):
    # 从当前帧检测结果里取出当前任务真正关心的目标。
    if current_task is None:
        return empty_target_info()
    return detections.get(current_task["target_color"], empty_target_info(current_task["target_color"]))


def should_run_yolo(runtime, mission, target_colors):
    # YOLO 只在启用后才参与，并且默认只在搜索阶段低频运行。
    if runtime["yolo_detector"] is None or not target_colors:
        return False
    if YOLO_SEARCH_ONLY and mission.phase != "SEARCH":
        return False
    interval = max(int(YOLO_FRAME_INTERVAL), 1)
    return runtime["frame_index"] % interval == 0


def get_yolo_results(frame, processed, target_colors, runtime):
    # 非触发帧直接复用上一轮 YOLO 结果，降低算力占用。
    mission = runtime["mission"]
    if not should_run_yolo(runtime, mission, target_colors):
        return runtime["last_yolo_results"]

    yolo_results = runtime["yolo_detector"].detect(frame, processed, target_colors)
    runtime["last_yolo_results"] = yolo_results
    runtime["last_yolo_frame"] = runtime["frame_index"]
    return yolo_results


def detect_current_targets(frame, processed, target_colors, runtime):
    # 当前项目默认先走颜色检测，YOLO 作为低频补充检测。
    if not target_colors:
        runtime["last_yolo_results"] = {}
        return {}

    color_results = runtime["color_detector"].detect(frame, processed, target_colors)
    if runtime["yolo_detector"] is None:
        return color_results

    yolo_results = get_yolo_results(frame, processed, target_colors, runtime)
    return merge_detection_results(color_results, yolo_results, target_colors)


def process_frame(frame, runtime):
    # 单帧处理函数，把主循环里的细节集中到这里，方便后续继续调赛规逻辑。
    mission = runtime["mission"]
    current_task = mission.current_task()
    target_colors = current_task_colors(mission)

    # 预处理阶段统一生成 HSV 和灰度图，减少重复颜色空间转换。
    processed = preprocess_frame(frame)
    hsv = processed["hsv"]
    gray = processed["gray"]

    # 轻量视觉链路：可通行区域、障碍、当前任务目标、安全区、画面质量。
    drive_mask = extract_drive_mask(hsv)
    obstacle_info = detect_obstacles(frame)
    detections = detect_current_targets(frame, processed, target_colors, runtime)
    safe_zone_info = detect_safe_zones(hsv)
    quality_info = evaluate_frame_quality(gray)
    center_ratio = mask_center_ratio(drive_mask)
    plan_info = plan_direction(center_ratio, obstacle_info)
    escape_info = runtime["escape_monitor"].update(frame, plan_info["motion"])
    target_info = resolve_target_info(current_task, detections)

    # 状态机负责比赛流程，主循环只给它提供当前帧观测结果。
    mission_info = mission.update(frame.shape[1], target_info, quality_info["ok"], safe_zone_info)
    motion = decide_motion(quality_info, plan_info, escape_info, mission_info, safe_zone_info)

    return {
        "drive_mask": drive_mask,
        "quality_info": quality_info,
        "obstacle_info": obstacle_info,
        "plan_info": plan_info,
        "escape_info": escape_info,
        "safe_zone_info": safe_zone_info,
        "mission_info": mission_info,
        "target_info": target_info,
        "motion": motion,
    }


def draw_target_box(frame, target_info):
    # 只把当前任务目标画出来，避免调试画面信息过多。
    if not target_info["found"] or target_info["bbox"] is None:
        return

    x, y, w, h = target_info["bbox"]
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
    cv2.putText(
        frame,
        f"{target_info['color']} area={target_info['area']:.0f}",
        (x, max(y - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2,
    )


def show_debug_window(frame, frame_result):
    # 左侧保留原画面，右侧显示可通行区域二值图，便于现场调参。
    mask_bgr = cv2.cvtColor(frame_result["drive_mask"], cv2.COLOR_GRAY2BGR)
    preview = cv2.hconcat([frame, mask_bgr])
    draw_status_panel(
        preview,
        quality_info=frame_result["quality_info"],
        obstacle_info=frame_result["obstacle_info"],
        plan_info=frame_result["plan_info"],
        escape_info=frame_result["escape_info"],
        motion_text=motion_to_text(frame_result["motion"]),
        mission_info=frame_result["mission_info"],
        safe_zone_info=frame_result["safe_zone_info"],
    )
    draw_target_box(preview, frame_result["target_info"])
    cv2.imshow(WINDOW_NAME, preview)


def release_runtime(runtime):
    # 统一释放串口、摄像头和窗口资源。
    runtime["serial"].close()
    runtime["cap"].release()
    cv2.destroyAllWindows()


def main():
    # 主函数尽量保持顺序化，方便现场直接看流程。
    runtime = build_runtime()
    cap = runtime["cap"]

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            print("cannot read camera frame")
            break

        # 处理当前帧，得到状态机动作和调试信息。
        frame_result = process_frame(frame, runtime)
        runtime["serial"].send(frame_result["motion"])
        show_debug_window(frame, frame_result)
        runtime["frame_index"] += 1

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    release_runtime(runtime)


if __name__ == "__main__":
    main()
