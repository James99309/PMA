# -*- coding: utf-8 -*-
"""Wiki Lint 质检服务

把整个 Wiki 喂给 Claude Opus，让它检查：
- broken_link: outbound_refs 指向不存在的文章
- orphan: 没有被任何其他文章引用
- conflict: 两篇文章对同一事实的说法不一致
- outdated: 内容明显过时
- missing_summary: summary 为空或过短

可选应用 auto_fixes（只处理坏链接、缺摘要等安全操作）。

⚠️ 注意 Wiki 规模：当文章 > 50 篇或总字数 > 300K 时，Lint 单次请求可能
接近 Claude Opus 4.6 的 1M 上下文上限。代码里做了粗略估算日志，未来
可能需要分批或降采样。
"""
import json
import logging
from datetime import datetime
from typing import Any

from app import db
from app.models.knowledge import KnowledgeWikiArticle
from app.services.wiki import claude_client, prompts, storage

logger = logging.getLogger(__name__)


class LintError(RuntimeError):
    pass


# 粗略警告阈值：user prompt 超过这个字节数时 log 警告
LARGE_PROMPT_WARN_BYTES = 500_000


# ══════════════════════════════════════════════════════════════════
# 公开入口
# ══════════════════════════════════════════════════════════════════

def lint_wiki(
    *,
    apply_auto_fixes: bool = False,
    topic: str | None = None,
    claude: claude_client.WikiClaudeClient | None = None,
) -> dict[str, Any]:
    """对整个（或某 topic 的）Wiki 做一次质检。

    Args:
        apply_auto_fixes: 是否应用 Claude 判定为可自动修复的操作
        topic: 可选限制 topic（None 表示全库）
        claude: 可选 Claude 客户端（测试用 mock）

    Returns:
        {
            'issues': [...],
            'auto_fixes_applied': int,
            'summary': str,
            'usage': {...},
            'article_count': int,
        }
    """
    q = KnowledgeWikiArticle.query
    if topic:
        q = q.filter_by(topic=topic)
    articles = q.order_by(KnowledgeWikiArticle.topic, KnowledgeWikiArticle.slug).all()

    if not articles:
        return {
            'issues': [],
            'auto_fixes_applied': 0,
            'summary': 'Wiki 为空，无需质检',
            'usage': {'input_tokens': 0, 'output_tokens': 0, 'model': 'n/a'},
            'article_count': 0,
        }

    user_msg = _build_lint_user_prompt(articles)
    if len(user_msg) > LARGE_PROMPT_WARN_BYTES:
        logger.warning(
            f'[Lint] prompt 体积 {len(user_msg) / 1024:.1f}KB，接近上下文上限，建议按 topic 分批'
        )

    own_client = False
    if claude is None:
        claude = claude_client.WikiClaudeClient()
        own_client = True
    try:
        logger.info(
            f'[Lint] articles={len(articles)} prompt={len(user_msg)}B apply_auto_fixes={apply_auto_fixes}'
        )
        resp = claude.complete(
            system=prompts.LINT_SYSTEM,
            user=user_msg,
            model=claude_client.LINT_MODEL,
            max_tokens=16000,
        )
    finally:
        if own_client:
            claude.close()

    result = _parse_lint_response(resp.text)

    # 应用自动修复
    applied = 0
    if apply_auto_fixes:
        applied = _apply_auto_fixes(result.get('auto_fixes') or [])

    # 写日志
    storage.append_log(
        'lint',
        f'articles={len(articles)} issues={len(result.get("issues") or [])} '
        f'auto_fixes_applied={applied}\n{result.get("summary", "")}',
    )

    return {
        'issues': result.get('issues') or [],
        'auto_fixes_applied': applied,
        'summary': result.get('summary', ''),
        'usage': resp.usage,
        'article_count': len(articles),
    }


# ══════════════════════════════════════════════════════════════════
# 内部
# ══════════════════════════════════════════════════════════════════

def _build_lint_user_prompt(articles: list[KnowledgeWikiArticle]) -> str:
    parts: list[str] = ['## 所有文章']
    for art in articles:
        content = storage.read_article_content(art.file_path)
        parts.append(f'\n### {art.topic}/{art.slug}.md — {art.title}')
        parts.append(f'summary: {art.summary or "(空)"}')
        parts.append(f'outbound_refs: {json.dumps(art.outbound_refs or [], ensure_ascii=False)}')
        parts.append('---')
        parts.append(content or '(空文件)')
    return '\n'.join(parts)


def _parse_lint_response(text: str) -> dict[str, Any]:
    s = (text or '').strip()
    if not s:
        raise LintError('Claude Lint 返回空响应')

    # 尝试直接解析
    try:
        data = json.loads(s)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 代码块
    import re
    m = re.search(r'```(?:json)?\s*\n(.*?)```', s, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(1).strip())
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    # 尝试提取第一个 { ... } 块
    brace_start = s.find('{')
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(s)):
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        data = json.loads(s[brace_start:i + 1])
                        if isinstance(data, dict):
                            return data
                    except json.JSONDecodeError:
                        pass
                    break

    raise LintError(f'Claude Lint 返回非法 JSON；前 500 字符:\n{s[:500]}')


def _apply_auto_fixes(auto_fixes: list[dict]) -> int:
    """按 Claude 给出的 auto_fixes 列表覆盖文件 + 更新 DB 记录。

    每条 fix 必须包含 article (格式 "<topic>/<slug>") 和 new_content。
    返回实际应用的条数。
    """
    applied = 0
    now = datetime.utcnow()
    for fix in auto_fixes:
        article_ref = fix.get('article') or ''
        new_content = fix.get('new_content') or ''
        description = fix.get('description', '')
        if not article_ref or not new_content:
            logger.warning(f'[Lint] auto_fix 缺字段，跳过: {fix}')
            continue
        if '/' not in article_ref:
            logger.warning(f'[Lint] auto_fix article 格式错，应为 topic/slug: {article_ref}')
            continue
        topic, slug = article_ref.split('/', 1)
        art = KnowledgeWikiArticle.query.filter_by(topic=topic, slug=slug).first()
        if art is None:
            logger.warning(f'[Lint] auto_fix 目标文章不存在: {article_ref}')
            continue
        storage.write_article(topic, slug, new_content)
        art.content_length = len(new_content)
        art.last_compiled_at = now
        # compile_model 保持不变，因为这只是 lint 修复，不算正式 compile
        applied += 1
        logger.info(f'[Lint] auto-fix {article_ref}: {description}')
    if applied:
        db.session.commit()
    return applied
