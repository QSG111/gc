# rescue_vision

基于 Python + OpenCV 的智能救援车视觉上位机项目。

当前目标是面向 2026 广东省大学生工程实践与创新能力大赛智能救援赛项，完成：
- 摄像头采集
- 目标识别
- 安全区识别
- 任务状态机
- 上位机到下位机串口控制

## 1. 项目定位

本项目采用分层结构：
- 上位机负责视觉识别、任务决策、状态机调度
- 下位机负责底盘运动控制和机械执行

当前代码以比赛可落地为目标，不照搬学长代码，而是吸收其有效经验后做模块化重构，便于后续改赛规、改阈值、改任务流程。

## 2. 赛规摘要

已根据赛规文档整理出的关键约束如下：
- 机器人必须自主运行
- 比赛中不能使用无线通信
- 场地约为 2400mm x 2400mm
- 双方各有出发区和安全区
- 安全区颜色为红或蓝，比赛前抽签确定己方颜色
- 救援目标包含普通目标、核心目标、危险目标
- 必须先将己方普通目标送入己方安全区，之后才能转运共享目标
- 单次转运目标数不能超过 3 个
- 危险目标必须单独转运

对视觉上位机的直接影响：
- 程序必须支持红蓝阵营切换
- 程序必须区分不同目标类型
- 程序必须支持安全区识别
- 程序必须支持规则优先级，而不是单纯颜色跟踪

## 3. 当前代码架构

```text
rescue_vision/
├─ main.py
├─ config.py
├─ requirements.txt
├─ README.md
├─ control/
│  ├─ decision.py
│  ├─ protocol.py
│  └─ serial_comm.py
├─ mission/
│  ├─ state_machine.py
│  └─ task_config.py
├─ planning/
│  ├─ escape.py
│  ├─ grid_map.py
│  └─ planner.py
├─ ui/
│  └─ overlay.py
├─ utils/
│  └─ fps.py
└─ vision/
   ├─ camera.py
   ├─ color_targets.py
   ├─ obstacle.py
   ├─ path_detect.py
   ├─ preprocess.py
   ├─ quality.py
   └─ safe_zone.py
```

## 4. 主程序流程

`main.py` 每一帧的执行流程：

```text
读取摄像头
-> 图像预处理
-> 可通行区域提取
-> 障碍物检测
-> 多颜色目标检测
-> 安全区检测
-> 画面质量评估
-> 任务状态机更新
-> 最终动作决策
-> 串口发送给下位机
-> 界面调试显示
```

## 5. 模块说明

### vision

- `camera.py`
  负责打开摄像头。
- `preprocess.py`
  负责基础滤波和颜色空间转换。
- `path_detect.py`
  负责提取可通行区域。
- `obstacle.py`
  负责粗略障碍检测。
- `color_targets.py`
  负责按颜色识别目标，当前支持 `red / blue / black / yellow / purple`。
- `safe_zone.py`
  负责识别红蓝安全区。
- `quality.py`
  负责亮度和清晰度判断。

### mission

- `task_config.py`
  负责定义任务规则、阵营颜色和目标参数。
- `state_machine.py`
  负责比赛任务状态机。

当前状态机阶段包括：
- `SEARCH`
- `ALIGN`
- `APPROACH`
- `PICKUP`
- `GO_SAFE_ZONE`
- `DROP`
- `NEXT_TASK`
- `DONE`

### control

- `protocol.py`
  负责把动作名称映射为下位机字节指令。
- `serial_comm.py`
  负责串口发送。
- `decision.py`
  负责综合质量、安全、状态机、避障结果，输出最终动作。

### planning

- `planner.py`
  基础方向规划。
- `escape.py`
  简单脱困逻辑。
- `grid_map.py`
  栅格地图占位模块，后续可扩展。

### ui

- `overlay.py`
  将调试信息绘制到窗口。

## 6. 当前任务模型

当前已按赛规抽象出三类任务：
- `friendly_ordinary`
- `core_target`
- `danger_target`

当前支持的规则方向：
- 阵营颜色切换
- 己方普通目标优先
- 核心目标和危险目标独立配置
- 安全区搜索与接近

当前还没有完全落地的规则：
- 精确统计一次搬运数量
- 危险目标单独转运的真实完成判据
- 己方普通目标已完成后的解锁条件
- 安全区投放完成检测

## 7. 串口协议

当前在 `control/protocol.py` 中定义了单字节协议，示例：

- `S -> 0x00` 停止
- `F -> 0x01` 前进
- `L -> 0x03` 左转
- `B -> 0x05` 后退
- `R -> 0x07` 右转
- `ARM_ROTATE -> 0x10`
- `ARM_UP -> 0x11`
- `ARM_DOWN -> 0x13`
- `ARM_CENTER -> 0x15`
- `FAST_RIGHT -> 0x21`
- `ACT_STAGE_1 -> 0x22`
- `ACT_STAGE_2 -> 0x23`
- `TURN_AND_ADVANCE -> 0x09`

具体字节值需要和下位机代码最终统一。

## 8. 关键配置

主要配置文件为 `config.py`。

当前重要参数：
- `SIDE_COLOR`
  己方颜色，当前可设为 `red` 或 `blue`
- `SERIAL_PORT`
  Windows 下串口号，例如 `COM3`
- `SERIAL_ENABLED`
  是否真正打开串口
- `BINARIZE_THRESHOLD`
  通行区域提取阈值
- `MIN_BRIGHTNESS`
  最低亮度
- `MIN_LAPLACIAN_VARIANCE`
  最低清晰度

## 9. 运行方式

在 Windows PowerShell 中运行：

```powershell
cd C:\Users\联想\Desktop\rescue_vision
python main.py
```

退出：
- 按 `q`

## 10. 当前开发进度

已完成：
- 项目基础骨架
- 摄像头读取
- 画面显示
- 可通行区域检测
- 障碍检测
- 多颜色目标检测
- 基础任务状态机
- 安全区检测第一版
- 串口字节协议第一版

下一阶段建议：
- 加入安全区投放完成判定
- 加入红蓝阵营一键切换测试
- 加入危险目标单独转运约束
- 加入更稳定的动作执行器
- 根据真实赛场图像重新标定 HSV 阈值
- 接入下位机联调

## 11. 注意事项

- 当前程序是比赛上位机框架，不是最终定型版本。
- 真实比赛效果会强依赖摄像头位置、光照、场地材质和机械执行精度。
- 所有颜色阈值、安全区识别阈值、停止面积阈值都需要现场调参。
- 如果比赛现场规则补充发生变化，优先修改 `mission/task_config.py` 和 `mission/state_machine.py`。

## 12. 队内分工建议

如果你们是一个多成员小组，推荐按下面方式拆分：

- 视觉上位机
  负责 `vision/`、`mission/`、`ui/`、参数调试、摄像头安装位置优化。
- 下位机控制
  负责底盘运动、串口接收、动作执行、机械臂控制、电机调试。
- 机械结构
  负责夹取结构、转运结构、强度与重量控制、快速拆装维护。
- 联调与测试
  负责记录问题、收集视频、统计成功率、场景复现。

建议明确一个人负责最终串口协议文档，避免上位机和下位机各写一套。

## 13. 文件修改指南

如果你要改某种能力，优先看这些文件：

- 想改阵营颜色
  修改 `config.py` 里的 `SIDE_COLOR`
- 想改目标顺序和规则
  修改 `mission/task_config.py`
- 想改比赛流程
  修改 `mission/state_machine.py`
- 想改颜色阈值
  修改 `vision/color_targets.py`
- 想改安全区识别
  修改 `vision/safe_zone.py`
- 想改避障和普通移动
  修改 `planning/planner.py` 和 `vision/obstacle.py`
- 想改发给下位机的指令
  修改 `control/protocol.py`
- 想改串口端口和开关
  修改 `config.py`

## 14. 上下位机联调流程

建议按下面顺序联调：

1. 先不开串口
   将 `SERIAL_ENABLED = False`
   先确认画面、目标框、状态机、调试文字正常。

2. 再开串口但只发简单移动指令
   将 `SERIAL_ENABLED = True`
   先只验证 `S / F / L / R / B`

3. 再验证机械动作指令
   验证：
   - `ARM_ROTATE`
   - `ARM_UP`
   - `ARM_DOWN`
   - `ARM_CENTER`
   - `ACT_STAGE_1`
   - `ACT_STAGE_2`

4. 最后验证完整任务链
   搜索目标 -> 对中 -> 靠近 -> 抓取 -> 去安全区 -> 投放

联调时一定要记录：
- 发出的动作名
- 下位机收到的字节
- 实际执行效果
- 是否有延迟或误动作

## 15. 调参建议

现场最常调的参数通常有：

- `COLOR_MIN_AREA`
  太小会误检，太大会漏检
- `MIN_BRIGHTNESS`
  太高会频繁停机，太低会在暗光下误运行
- `MIN_LAPLACIAN_VARIANCE`
  太高会把正常画面判成模糊
- `BINARIZE_THRESHOLD`
  影响地面和通行区域分割
- `center_tolerance`
  影响目标对中精度
- `stop_area`
  影响什么时候判定“离目标足够近”
- `safe_zone_stop_area`
  影响什么时候判定“到达安全区”

建议调参方法：

1. 先固定摄像头高度和角度
2. 每次只改 1 个参数
3. 每次改完都录一段视频
4. 记录“变好还是变坏”，不要凭感觉反复乱改

## 16. 推荐测试顺序

不要一上来就跑完整比赛流程，按下面顺序测试：

1. 摄像头是否稳定
2. 红蓝黑黄目标是否能识别
3. 安全区是否能识别
4. 状态机切换是否正确
5. 串口发送是否正确
6. 小车是否能按指令移动
7. 抓取动作是否稳定
8. 投放动作是否稳定
9. 连续完成完整流程

## 17. 当前问题清单

当前版本已经能跑，但还存在这些工程缺口：

- 还没有“投放完成”的真实视觉判定
- 还没有精确统计一次是否超过 3 个目标
- 还没有危险目标单独转运的硬约束检查
- 还没有对“己方普通目标是否已完成”做真实闭环确认
- 还没有根据赛场真实图像做颜色阈值标定
- 还没有接入实际下位机长期联调结果

这些不是 bug，而是后续必须完成的赛场化工作。

## 18. 建议保留的文档

为了避免后面聊天太长、信息丢失，建议项目里长期保留这几份文档：

- `README.md`
  项目总说明
- `protocol_notes.md`
  上下位机字节协议说明
- `tuning_notes.md`
  参数调试记录
- `test_log.md`
  每次测试的问题和结果

如果后面需要，我可以继续帮你把这 3 个文档也直接建出来。
