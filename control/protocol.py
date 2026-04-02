# 上位机动作名到下位机单字节协议的映射表。
COMMAND_BYTES = {
    "S": 0x00,
    "F": 0x01,
    "SEARCH": 0x01,
    "L": 0x03,
    "B": 0x05,
    "R": 0x07,
    "ARM_ROTATE": 0x10,
    "ARM_UP": 0x11,
    "ARM_DOWN": 0x13,
    "ARM_CENTER": 0x15,
    "FAST_RIGHT": 0x21,
    "ACT_STAGE_1": 0x22,
    "ACT_STAGE_2": 0x23,
    "REJECT_ITEM": 0x24,
    "TURN_AND_ADVANCE": 0x09,
}

# 调试窗口显示用的动作文字。
MOTION_TEXT = {
    "F": "FORWARD",
    "L": "LEFT",
    "R": "RIGHT",
    "S": "STOP",
    "B": "BACK",
    "SEARCH": "SEARCH",
    "FAST_RIGHT": "FAST_RIGHT",
    "ARM_ROTATE": "ARM_ROTATE",
    "ARM_UP": "ARM_UP",
    "ARM_DOWN": "ARM_DOWN",
    "ARM_CENTER": "ARM_CENTER",
    "ACT_STAGE_1": "ACT_STAGE_1",
    "ACT_STAGE_2": "ACT_STAGE_2",
    "REJECT_ITEM": "REJECT_ITEM",
    "TURN_AND_ADVANCE": "TURN_AND_ADVANCE",
}


def motion_to_text(motion):
    return MOTION_TEXT.get(motion, motion)


def motion_to_byte(motion):
    # 把上位机动作转换成串口发送字节。
    return COMMAND_BYTES.get(motion)
