# -*- coding: utf-8 -*-
"""
Chat Agent 子模块

与 cli_agent 架构相同(直连 Anthropic SDK + 本地 Agent Loop + tool use),
但权限模型不同:使用**前端权限**(access_control.get_viewable_data)过滤数据,
而非 cli_agent 的 cli_* 独立权限。

适用于嵌在 PMA 聊天界面中的 AI 对话,取代现有基于 OpenClaw 的路径。

入口:
    from app.services.chat_agent.agent_loop import ChatAgentLoop

    loop = ChatAgentLoop(conversation_id=123, user=current_user)
    for event in loop.run(user_input='帮我查下本月新增客户'):
        # event: {'type': 'content', 'text': '...'}
        #        {'type': 'tool_status', 'name': '...'}
        #        {'type': 'done', 'model': '...', 'prompt_tokens': N, 'completion_tokens': N,
        #         'full_text': '...'}
        ...
"""
