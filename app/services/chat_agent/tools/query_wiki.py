# -*- coding: utf-8 -*-
"""
Chat 版 Wiki 知识库问答工具。

直接复用 app/services/wiki/querier.query_wiki()，让 chat agent 的 AI
自主判断何时查询公司内部知识库（产品手册、规章制度、FAQ、流程规范等）。
"""
from __future__ import annotations

import logging
from typing import Any

from app.services.cli_agent.tools import BaseTool

logger = logging.getLogger(__name__)


class QueryWikiTool(BaseTool):
    name = 'query_wiki_knowledge'
    description = (
        '查询公司内部 Wiki 知识库。\n'
        '- 适用场景：产品手册、规章制度、FAQ、流程规范、内部政策等非实时业务数据的知识性问题。\n'
        '- 不适用：实时业务数据查询（客户/项目/报价等）请用 query_pma_database。\n'
        '- 返回基于知识库文章的回答和引用来源。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'question': {
                'type': 'string',
                'description': '要查询的问题（自然语言）',
            },
            'topic': {
                'type': 'string',
                'description': '可选，限定搜索的知识库主题（如 HR、销售）',
            },
        },
        'required': ['question'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        question = (tool_input or {}).get('question', '').strip()
        topic = (tool_input or {}).get('topic')

        if not question:
            return {'error': '问题不能为空'}

        try:
            from app.services.wiki.querier import query_wiki

            result = query_wiki(question, topic=topic)
            answer = result.get('answer', '')
            cited = result.get('cited_articles', [])

            # 格式化引用来源
            sources = []
            for a in cited:
                title = a.get('title', '')
                topic_name = a.get('topic', '')
                if title:
                    sources.append(f'{topic_name}/{title}' if topic_name else title)

            return {
                'answer': answer,
                'sources': sources,
                'search_hit_count': result.get('search_hit_count', 0),
            }
        except Exception as e:
            logger.warning(f'[QueryWiki] 查询失败: {e}', exc_info=True)
            return {'answer': '知识库查询暂时不可用，请稍后重试。', 'sources': []}
