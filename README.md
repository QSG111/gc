# rescue_car

救援小车视觉控制项目。

当前版本以颜色检测为主，YOLO 为辅，主流程按固定状态机运行：

- `SEARCH -> GRAB -> GRAB_CONFIRM -> DELIVER`
- `decision.py` 只负责方向决策
- `executor.py` 只负责动作执行
- `main.py` 负责状态切换、抓取确认和整体调度

## 目录结构

```text
camera.py    摄像头读取
detect.py    颜色目标检测、安全区检测、低频 YOLO 辅助检测
decision.py  搜索/投放阶段的方向决策
executor.py  抓取与释放动作序列执行
path.py      地面可通行方向分析
quality.py   画面质量判断
escape.py    SEARCH 阶段的简单脱困
serial.py    串口指令映射与发送
main.py      状态机、抓取确认、运输流程与模块调度
```

## 当前比赛规则实现

本次已在现有代码基础上按最小改动接入以下抓球规则：

### 1. 队伍颜色约束

- 红队只能抓 `red_ball`
- 蓝队只能抓 `blue_ball`
- 对方颜色球在检测阶段直接过滤，不进入候选目标

### 2. 黑球规则

- `black_ball` 两队都可以抓
- 作为普通球处理
- 普通球累计最多抓 `3` 个

### 3. 黄球规则

- `yellow_ball` 只能抓 `1` 个
- 不能作为第一个抓取目标
- 若已经抓过黄球，则后续检测阶段直接忽略

### 4. 优先级规则

- `yellow_ball` 优先级为 `120`
- 本队球优先级为 `100`
- `black_ball` 优先级为 `80`

## 状态变量

规则状态保存在 `Detector` 内部：

```python
self.normal_count = 0
self.yellow_picked = False
```

含义如下：

- `normal_count`：已成功抓取的普通球累计数量
- `yellow_picked`：是否已经成功抓取过黄球

## 规则落点

### 1. 目标过滤

规则主要落在 [detect.py](C:/Users/联想/Desktop/rescue_car/detect.py) 的颜色目标生成阶段：

- 过滤对方颜色球
- 当 `normal_count >= 3` 时，不再生成本队球和黑球候选
- 当 `yellow_picked == True` 时，不再生成黄球候选
- 当 `normal_count == 0` 时，不生成黄球候选

### 2. 目标选择

当前抓取候选仍然优先使用颜色检测结果：

- `main.py` 中 `pick_grab_candidate()` 仍从 `color_target` 取抓取目标
- `_pick_best_target()` 按优先级、面积和中心偏差综合打分

### 3. 抓取成功后的状态更新

在 `GRAB_CONFIRM` 确认成功后调用：

```python
detector.register_pick_result(action_context["target_label"])
```

更新规则如下：

- 抓到 `yellow_ball`：`yellow_picked = True`
- 抓到其他球：`normal_count += 1`

## 当前流程说明

### 1. SEARCH

- 始终运行颜色检测
- 仅在画面质量良好时低频运行 YOLO
- 若目标满足抓取条件，则切换到 `GRAB`

### 2. GRAB

- `main.py` 进入 `GRAB` 后，只触发一次 `ActionExecutor.trigger_grab()`
- `executor.py` 按固定时序执行停车、下放、闭合、抬起、后退

### 3. GRAB_CONFIRM

- 抓取动作完成后进入确认状态
- 连续多帧确认目标已从原位置消失，才判定抓取成功
- 成功后更新夹爪占用状态和比赛规则状态
- 超时未确认则回到 `SEARCH`

### 4. DELIVER

- `DecisionMaker.decide_delivery()` 只负责朝安全区行驶
- 到达安全区后由 `main.py` 触发释放动作
- 释放完成后清空夹爪占用状态并回到 `SEARCH`

## 说明

- 当前程序仍按双夹爪结构工作，因此“同时携带数量”受夹爪数量限制
- 本次新增的 `normal_count` 约束的是“普通球累计抓取上限 3 个”，不是单次同时携带 3 个
- 调试画面叠字仍保留英文短标签，因为 `cv2.putText` 默认字体对中文支持较差，直接改中文会影响可读性

## 运行

安装基础依赖：

```powershell
pip install opencv-python numpy
```

如需 YOLO：

```powershell
pip install ultralytics
```

运行：

```powershell
python main.py
```

默认是串口调试模式：

```python
SerialController(port="COM3", baudrate=115200, enable_serial=False)
```

上车前按实际串口修改 `port`，并将 `enable_serial` 改为 `True`。
