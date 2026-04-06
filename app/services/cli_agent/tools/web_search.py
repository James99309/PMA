# -*- coding: utf-8 -*-
"""
web_search 工具:使用 Tavily API 搜索公网公开信息

用途:
    补充 PMA 数据库里没有的公开信息,比如:
    - 客户公司的最新动态、注册地、行业背景
    - 项目所在地的政策、物流、展会
    - 行业趋势、竞品情报、标准规范
    - 事实性查询(天气、新闻、汇率等)

不要用于:
    - PMA 内部业务数据查询(这些请用 query_pma_database)
    - 闲聊、笑话、情感、创作(CLI 角色不做这些)

依赖:
    pip install tavily-python
    环境变量 TAVILY_API_KEY

注册:在 tools/__init__.py 的 get_default_registry() 里按需加入
"""
from __future__ import annotations

import logging
import os
from typing import Any

from app.services.cli_agent.tools import BaseTool
from app.services.cli_agent.config import CLI_TOOL_RESULT_MAX_TOKENS

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    name = 'web_search'
    description = (
        '搜索公网公开信息。用于查询 PMA 数据库里没有的公开数据,'
        '例如:客户公司的最新动态/注册地/行业背景、项目所在地政策、'
        '竞品信息、行业标准、事实性问题(天气/新闻/汇率/地理等)。\n'
        '返回搜索结果的摘要 + Tavily 自动生成的答案(如果 include_answer=true)。\n'
        '**不要用于**查询 PMA 内部业务数据(客户/项目/报价等)——那些用 query_pma_database。'
    )
    input_schema = {
        'type': 'object',
        'properties': {
            'query': {
                'type': 'string',
                'description': '自然语言搜索查询,用目标信息的语言(中文问题用中文查)',
            },
            'search_depth': {
                'type': 'string',
                'enum': ['basic', 'advanced'],
                'description': 'basic 速度快(默认),advanced 更全面但慢一倍。一般用 basic',
            },
            'max_results': {
                'type': 'integer',
                'description': '返回的结果数,1-10,默认 5',
                'minimum': 1,
                'maximum': 10,
            },
        },
        'required': ['query'],
    }

    def execute(self, tool_input: dict, context: dict) -> Any:
        api_key = os.environ.get('TAVILY_API_KEY', '').strip()
        if not api_key:
            return {
                'error': (
                    '未配置 TAVILY_API_KEY 环境变量。'
                    '请管理员在 .env.local 添加 TAVILY_API_KEY=tvly-xxxxx 并重启服务。'
                )
            }

        query = (tool_input or {}).get('query', '').strip()
        if not query:
            return {'error': 'query 参数不能为空'}

        search_depth = (tool_input or {}).get('search_depth', 'basic')
        max_results = int((tool_input or {}).get('max_results', 5))
        max_results = max(1, min(max_results, 10))

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=api_key)
            response = client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=True,
                include_raw_content=False,
                include_images=False,
            )
        except Exception as e:
            logger.exception('[CLI Agent] web_search Tavily 调用失败')
            return {'error': f'web_search 调用失败: {e}'}

        # 整理结果:保留 answer 和精简的 result 列表
        answer = response.get('answer') or ''
        results = []
        for r in response.get('results', [])[:max_results]:
            results.append({
                'title': r.get('title', ''),
                'url': r.get('url', ''),
                'snippet': (r.get('content', '') or '')[:500],
                'score': r.get('score'),
            })

        output: dict = {
            'query': query,
            'answer': answer,
            'results': results,
            'result_count': len(results),
        }

        # token 安全:过大则截断 results 的 snippet
        import json
        estimated_tokens = len(json.dumps(output, ensure_ascii=False)) // 3
        if estimated_tokens > CLI_TOOL_RESULT_MAX_TOKENS:
            for r in results:
                r['snippet'] = (r.get('snippet', '') or '')[:200]
            output['truncated'] = True
            output['hint'] = '结果较大已截断 snippet 为前 200 字符'

        logger.info(
            f'[CLI Agent] web_search query={query!r} → {len(results)} 条,'
            f'answer_chars={len(answer)}'
        )
        return output
