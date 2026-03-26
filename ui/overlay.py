import cv2


def draw_status_panel(
    frame,
    quality_info,
    obstacle_info,
    plan_info,
    escape_info,
    motion_text,
    mission_info,
    safe_zone_info,
):
    # 把当前帧的关键调试信息统一绘制到预览画面上。
    lines = [
        f"brightness: {quality_info['brightness']:.1f}",
        f"sharpness: {quality_info['sharpness']:.1f}",
        f"quality_ok: {quality_info['ok']}",
        f"drive_ratio: {plan_info['drive_ratio']:.2f}",
        f"obstacle_center: {obstacle_info['center_ratio']:.2f}",
        f"blocked: {obstacle_info['blocked']}",
        f"stuck_count: {escape_info['count']}",
        f"frame_diff: {escape_info['diff']:.2f}",
        f"task: {mission_info['task_name']}",
        f"type: {mission_info['target_type']}",
        f"target: {mission_info['target_color']}",
        f"task_idx: {mission_info['task_index'] + 1}/{mission_info['task_count']}",
        f"carry_count: {mission_info['carry_count']}",
        f"delivered: {mission_info['delivered_count']}",
        f"phase: {mission_info['phase']}",
        f"note: {mission_info['note']}",
        f"side: {safe_zone_info['friendly_color']}",
        f"safe_zone: {safe_zone_info['friendly_found']}",
        f"safe_region: {safe_zone_info['friendly_region']}",
        f"enemy_zone: {safe_zone_info['enemy_found']}",
        f"enemy_region: {safe_zone_info['enemy_region']}",
        f"enemy_close: {safe_zone_info['enemy_danger_close']}",
        f"motion: {motion_text}",
    ]

    for idx, text in enumerate(lines):
        cv2.putText(
            frame,
            text,
            (20, 30 + idx * 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
