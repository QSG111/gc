from vision.color_targets import empty_target_info


def merge_detection_results(color_results, yolo_results, color_names):
    """融合传统 OpenCV 检测结果和 YOLO 检测结果。"""
    # 当前策略很简单：YOLO 只要有有效结果就优先使用，
    # 否则回退到颜色分割结果。
    merged = {}
    for color_name in color_names:
        yolo_item = yolo_results.get(color_name, empty_target_info(color_name))
        color_item = color_results.get(color_name, empty_target_info(color_name))
        merged[color_name] = yolo_item if yolo_item["found"] else color_item
    return merged
