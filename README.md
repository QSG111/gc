# rescue_vision

基于 Python + OpenCV 的救援小车上位机视觉与任务控制项目。

当前版本目标是先保证比赛可用、便于联调，再逐步升级为更强感知与更完整协议。

## 项目结构

```text
rescue_vision/
├─ main.py                  # 主循环：感知 -> 状态机 -> 决策 -> 串口
├─ config.py                # 全局参数
├─ vision/                  # 视觉模块
├─ mission/                 # 任务状态机与规则
├─ planning/                # 基础规划与脱困
├─ control/                 # 动作协议与串口发送
├─ ui/                      # 调试信息叠加显示
└─ tests/                   # 单元测试
```

## 单帧主流程

`main.py` 每帧执行顺序如下：

1. 采集摄像头画面
2. 图像预处理（模糊、可选 CLAHE、生成 HSV/灰度）
3. 提取可通行区域
4. 检测障碍物密度
5. 检测当前任务目标（颜色检测，YOLO 可选低频补充）
6. 检测己方/敌方安全区
7. 评估画质（亮度与清晰度）
8. 更新任务状态机
9. 融合状态机与规划信息做动作决策
10. 串口发送动作并显示调试画面

## 任务与规则

任务类型：

- `friendly_ordinary`
- `core_target`
- `danger_target`

已实现关键规则：

- 己方普通目标优先，完成后才解锁共享目标。
- 普通/核心目标支持累计装载，默认最多 3 个。
- 危险目标要求空载后再抓取，且单独搬运。
- 投放后需要连续确认，避免误判“已完成”。
- 目标短暂丢失有容错帧，避免状态抖动。

状态机主阶段：

`SEARCH -> ALIGN -> APPROACH -> PICKUP -> GO_SAFE_ZONE -> DROP -> CONFIRM_DROP -> NEXT_TASK -> DONE`

## 运行方式

```powershell
cd C:\Users\联想\Desktop\rescue_vision
python main.py
```

退出：按 `q`。

## 常用调参项（config.py）

- `SIDE_COLOR`: 己方颜色（`red` / `blue`）
- `SERIAL_ENABLED`: 是否启用串口发送
- `BINARIZE_THRESHOLD`: 可通行区阈值
- `MIN_BRIGHTNESS`: 最低亮度
- `MIN_LAPLACIAN_VARIANCE`: 最低清晰度
- `TARGET_LOST_TOLERANCE_FRAMES`: 目标丢失容错帧数
- `YOLO_FRAME_INTERVAL`: YOLO 触发间隔帧
- `YOLO_SEARCH_ONLY`: 是否只在 SEARCH 阶段触发 YOLO

## 测试

```powershell
python -m unittest discover -s tests -v
```

## 编码说明

项目文本统一使用 UTF-8。若终端出现中文乱码，请先切换终端代码页到 UTF-8 后再查看文本内容。
