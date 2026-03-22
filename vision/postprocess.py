from vision.color_targets import empty_target_info


def merge_detection_results(color_results, yolo_results, color_names):
    """Merge classical OpenCV detections with future YOLO detections.

    Current strategy:
    - prefer YOLO if it has a valid detection
    - otherwise fall back to color-based OpenCV detection
    """
    merged = {}
    for color_name in color_names:
        yolo_item = yolo_results.get(color_name, empty_target_info(color_name))
        color_item = color_results.get(color_name, empty_target_info(color_name))
        merged[color_name] = yolo_item if yolo_item["found"] else color_item
    return merged
