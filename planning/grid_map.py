import cv2
import numpy as np


def build_grid_map(mask, rows=6, cols=8):
    # 把二值图离散成小栅格，便于后续扩展更复杂的路径规划。
    height, width = mask.shape
    cell_h = max(height // rows, 1)
    cell_w = max(width // cols, 1)
    grid = np.zeros((rows, cols), dtype=np.uint8)

    for r in range(rows):
        for c in range(cols):
            cell = mask[r * cell_h : (r + 1) * cell_h, c * cell_w : (c + 1) * cell_w]
            if cell.size == 0:
                continue
            ratio = float(cv2.countNonZero(cell)) / float(cell.size)
            # 当前栅格中白色区域占比足够大，就记为可通行。
            grid[r, c] = 1 if ratio > 0.35 else 0

    return grid
