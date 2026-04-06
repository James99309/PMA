# -*- coding: utf-8 -*-
"""
Token 用量追踪

设计参考: claw-code runtime/src/usage.rs (MIT)
见 THIRD_PARTY_NOTICES.md。

每轮 LLM 调用返回后,记录:
    - input_tokens        本次发出去的 token 数
    - output_tokens       本次模型生成的 token 数
    - cache_creation_input_tokens  写入 prompt cache 的 token 数
    - cache_read_input_tokens      从 prompt cache 读出的 token 数
    - model               具体的模型名
    - timestamp

这些数据:
    1. 挂在 Message 对象的 usage 字段上,持久化到 cli_sessions.messages
    2. 同时累加到 cli_sessions.usage_total,供状态条显示
    3. 用于压缩触发判断(见 compaction.py)

Token 估算(不调 API 的离线估算):
    因为 claw-code 的"字符数 ÷ 4"对中文严重低估,这里用:
        汉字数 × 1.5 + 英文字符数 / 4 + JSON 符号数 × 0.3
    每 CLI_TOKEN_CALIBRATION_INTERVAL 轮调用一次 anthropic.count_tokens()
    做一次精确校准,把估算偏差拉回。

TODO(stage-1): 实现 TurnUsage 数据类
TODO(stage-1): 实现 UsageTracker(累计、获取快照、估算成本)
TODO(stage-3): 实现 estimate_tokens_offline(text) -> int  (中文优化)
TODO(stage-3): 实现 calibrate_with_api(client, messages)
"""

# 占位:阶段 1 实现
