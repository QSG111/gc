# rescue_vision

基于 Python + OpenCV 的智能救援车上位机视觉项目。

当前版本重点是做一个比赛可用、算力开销可控、便于继续联调的上位机框架，覆盖：
- 摄像头采集
- 颜色目标识别
- 己方 / 敌方安全区识别
- 任务状态机
- 基础循迹与避障
- 串口动作输出

## 1. 项目定位

项目采用分层结构：
- `vision/` 负责图像预处理、目标识别、安全区识别、障碍检测
- `mission/` 负责赛规相关的任务状态机
- `planning/` 负责基础方向规划和脱困
- `control/` 负责动作决策和串口协议
- `ui/` 负责调试信息显示

设计目标不是照搬旧代码，而是保留“能跑”的同时，把赛规逻辑和感知逻辑拆开，便于后续继续改规则、改参数、接下位机。

## 2. 当前赛规落地情况

当前代码已经接入这些规则：
- 己方普通目标优先
- 共享目标要在己方普通目标完成后才解锁
- 普通目标 / 核心目标支持累计装载，单次最多 3 个
- 危险目标必须单独搬运
- 投放后需要连续确认，不是一做完动作就算成功
- 接近敌方安全区时会优先后退避让
- 目标短暂丢失时会缓冲几帧，不会立刻退回搜索

当前还没有完全闭环的部分：
- 抓取成功的真实视觉确认仍然较弱
- 多目标累计装载后，抓取姿态和机械成功率还需要实机验证
- 安全区阈值、颜色阈值和目标面积阈值都还需要现场调参
- YOLOv8 还只是预留接口，当前默认不启用

## 3. 当前主流程

`main.py` 的每帧执行流程如下：

```text
读取摄像头
-> 图像预处理
-> 可通行区域提取
-> 障碍检测
-> 当前任务目标检测
-> 安全区检测
-> 画面质量评估
-> 状态机更新
-> 动作决策
-> 串口发送
-> 调试画面显示
```

说明：
- 当前默认主要使用颜色检测
- YOLO 未来接入后默认按低频触发，不会每帧都跑
- 调试画面会显示任务阶段、当前目标、安全区状态、敌方安全区风险、最终动作等信息

## 4. 目录结构

```text
rescue_vision/
├─ main.py
├─ config.py
├─ README.md
├─ requirements.txt
├─ control/
│  ├─ decision.py
│  ├─ protocol.py
│  └─ serial_comm.py
├─ mission/
│  ├─ state_machine.py
│  └─ task_config.py
├─ planning/
│  ├─ planner.py
│  ├─ escape.py
│  └─ grid_map.py
├─ ui/
│  └─ overlay.py
├─ utils/
│  └─ fps.py
├─ vision/
│  ├─ camera.py
│  ├─ preprocess.py
│  ├─ path_detect.py
│  ├─ obstacle.py
│  ├─ color_targets.py
│  ├─ color_detector.py
│  ├─ safe_zone.py
│  ├─ quality.py
│  ├─ detector_interface.py
│  ├─ yolo_detector.py
│  └─ postprocess.py
└─ tests/
   └─ test_mission_state_machine.py
```

## 5. 关键模块说明

### vision

- `camera.py`
  打开摄像头并设置分辨率。
- `preprocess.py`
  做高斯模糊、CLAHE 增强，并统一生成 HSV / 灰度图。
- `path_detect.py`
  提取可通行区域，并估计前方中间区域可通行比例。
- `obstacle.py`
  用轻量边缘检测估计左右中三个方向的障碍密度。
- `color_targets.py`
  基于 HSV 阈值检测红 / 蓝 / 黑 / 黄 / 紫等目标。
- `safe_zone.py`
  检测己方和敌方安全区，并给出敌方安全区是否过近。
- `quality.py`
  基于亮度和清晰度判断当前画面是否可靠。
- `yolo_detector.py`
  预留给后续 YOLOv8 接入，目前默认返回空结果。

### mission

- `task_config.py`
  定义比赛规则、任务优先级、抓取 / 投放序列、最大载荷等。
- `state_machine.py`
  实现完整任务流程：
  `SEARCH -> ALIGN -> APPROACH -> PICKUP -> GO_SAFE_ZONE -> DROP -> CONFIRM_DROP -> NEXT_TASK -> DONE`

### control

- `decision.py`
  根据画面质量、任务状态、脱困状态、安全区风险、基础循迹结果决定最终动作。
- `protocol.py`
  把动作名映射为单字节串口协议。
- `serial_comm.py`
  发送串口命令，并自动过滤重复命令。

### planning

- `planner.py`
  根据障碍和可通行区域给出基础方向动作。
- `escape.py`
  通过前后帧差异判断车辆是否可能卡住。
- `grid_map.py`
  预留给后续更复杂路径规划的栅格化模块。

## 6. 当前任务规则

当前抽象出的任务类型：
- `friendly_ordinary`
- `core_target`
- `danger_target`

当前规则行为：
- `friendly_ordinary`
  优先级最高，完成后才解锁共享目标
- `core_target`
  允许累计装载，最多 3 个
- `danger_target`
  必须单独搬运，抓取前要求空载

## 7. YOLO 预留策略

当前默认：
- `USE_YOLO_DETECTOR = False`
- 实际运行只靠颜色检测

后续接 YOLO 时，代码已预留轻量策略：
- `YOLO_FRAME_INTERVAL = 3`
  默认每 3 帧跑一次 YOLO
- `YOLO_SEARCH_ONLY = True`
  默认只在 `SEARCH` 阶段调用 YOLO

也就是说，后续接入 YOLO 时不会默认每帧推理，避免 Orange Pi 之类平台算力占用过高。

## 8. 关键配置

主要配置在 `config.py`：

- `SIDE_COLOR`
  己方颜色，`red` 或 `blue`
- `SERIAL_PORT`
  串口端口，例如 `COM3`
- `SERIAL_ENABLED`
  是否真正打开串口
- `BINARIZE_THRESHOLD`
  可通行区域二值化阈值
- `MIN_BRIGHTNESS`
  最低亮度
- `MIN_LAPLACIAN_VARIANCE`
  最低清晰度
- `YOLO_FRAME_INTERVAL`
  YOLO 触发间隔
- `YOLO_SEARCH_ONLY`
  是否只在搜索阶段启用 YOLO
- `TARGET_LOST_TOLERANCE_FRAMES`
  目标连续丢失多少帧后才退回搜索

## 9. 运行方式

```powershell
cd C:\Users\联想\Desktop\rescue_vision
python main.py
```

退出：
- 按 `q`

## 10. 调试建议

推荐按下面顺序联调：

1. 先关串口，仅看画面
   `SERIAL_ENABLED = False`
2. 验证目标识别和安全区识别
3. 验证状态机是否按预期切换
4. 再打开串口，只测基础动作
5. 最后联调整条任务链

建议重点关注：
- `task / phase / note`
- `carry_count / delivered`
- `safe_zone / enemy_zone / enemy_close`
- `motion`

## 11. 当前测试覆盖

当前 `tests/test_mission_state_machine.py` 已覆盖：
- 投放确认后才算完成
- 敌方安全区过近时必须回退
- 己方普通目标完成后共享目标解锁
- 危险目标抓取前必须空载
- 普通目标可累计装到 3 个
- 目标丢失缓冲几帧后才回搜索

## 12. 后续建议

当前最值得继续做的方向：
- 增强抓取成功确认
- 现场重新标定 HSV 阈值
- 根据摄像头安装高度重调 `stop_area` 和安全区阈值
- 真正接入 YOLOv8，并保持低频触发策略
- 接下位机实机长时间联调
