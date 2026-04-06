# -*- coding: utf-8 -*-
"""
规则化上下文压缩

设计参考: claw-code runtime/src/compact.rs + summary_compression.rs (MIT)
见 THIRD_PARTY_NOTICES.md。

核心原则:
    压缩时不调 LLM,纯规则从老消息里抽取结构化摘要。
    这比 LLM 摘要快、免费、且可复现。

    相比 claw-code 的代码场景,PMA 压缩器要提取的是**业务实体**:
        - 涉及的客户 ID / 项目 ID / 报价单号
        - SQL 查询里用到的表名
        - 金额数字和时间范围
        - 最近用户请求的主题
    而不是 claw-code 的文件路径、TODO 关键词。

触发条件(见 config.py):
    总 token >= CLI_CONTEXT_HARD_COMPACT
    AND 消息数 > CLI_KEEP_RECENT_MESSAGES

压缩行为:
    1. 保留最近 CLI_KEEP_RECENT_MESSAGES 条原样不动
    2. 其余消息全部送入 summarize_old_messages()
    3. 生成的摘要包裹在 <compacted_summary>...</compacted_summary>
    4. 作为一条新的 user 消息插入到保留段开头
    5. 如果上次压缩的摘要还在,合并成"之前压缩的 + 新压缩的"

TODO(stage-3): 实现 should_compact(conversation) -> bool
TODO(stage-3): 实现 compact(conversation) -> Conversation
TODO(stage-3): 实现 extract_business_entities(messages) -> dict
TODO(stage-3): 实现 merge_with_previous_summary(old_summary, new_summary)
"""

# 占位:阶段 3 实现
