#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性脚本：清空 wiki/ 并对所有 raw 文件全量重新 ingest，
让旧 Wiki 文章带上 docx 嵌入图（Task 4 引入的能力）。

执行流程：
1. 备份 wiki/ 目录到 wiki_backup_<timestamp>/
2. 备份 knowledge_wiki_articles 元数据到 data/temp/wiki_articles_backup_<timestamp>.json
3. 用户确认后清空 articles 表 + 删除 wiki/<topic>/*.md（保留 index.md / log.md / _assets/）
4. 按 raw_id 顺序重新 ingest_raw_file(raw.id)
5. 打印每一步状态与最终统计

执行：
    export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
        python3 scripts/temp/backfill_wiki_with_images.py

回滚：
    脚本输出会显示备份目录路径。如果重生成的文章质量不达标：
    - 删除当前 wiki/<topic>/*.md 和 _assets/<slug>/ 目录
    - 把 wiki_backup_<timestamp>/ 中的 .md 拷回
    - 用 wiki_articles_backup_*.json 中的快照恢复 DB
"""
import sys, os
import json
import shutil
from datetime import datetime
from pathlib import Path


def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")


sys.path.insert(0, get_project_root())

from app import create_app, db  # noqa: E402
from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle  # noqa: E402
from app.services.wiki.compiler import ingest_raw_file, IngestError  # noqa: E402
from app.services.wiki.paths import get_wiki_dir  # noqa: E402


def backup_wiki_dir() -> Path:
    """整目录备份 wiki/ 到 wiki_backup_<ts>/。"""
    src = get_wiki_dir()
    if not src.exists():
        print(f'⚠️  wiki/ 目录不存在: {src}（无内容可备份）')
        return src.parent / 'wiki_backup_empty'
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    dst = src.parent / f'wiki_backup_{ts}'
    print(f'📦 备份 wiki/ → {dst}')
    shutil.copytree(src, dst)
    print(f'✅ 备份完成 ({sum(1 for _ in dst.rglob("*"))} 个条目)')
    return dst


def backup_articles_db() -> Path:
    """把 knowledge_wiki_articles 全表序列化到 data/temp/。"""
    root = Path(get_project_root())
    out_dir = root / 'data' / 'temp'
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    out_path = out_dir / f'wiki_articles_backup_{ts}.json'
    arts = KnowledgeWikiArticle.query.order_by(KnowledgeWikiArticle.id).all()
    payload = [a.to_dict(include_content=False) for a in arts]
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f'📦 已备份 {len(payload)} 条 knowledge_wiki_articles 到 {out_path}')
    return out_path


def confirm(prompt: str) -> bool:
    ans = input(f'{prompt} [y/N] ').strip().lower()
    return ans == 'y'


def clear_existing(wiki_root: Path) -> int:
    """删除 wiki/<topic>/*.md (但保留 index.md / log.md / _assets/)，
    清空 knowledge_wiki_articles 表。返回删除的 .md 文件数。"""
    deleted = 0
    if wiki_root.exists():
        for topic_dir in wiki_root.iterdir():
            if not topic_dir.is_dir():
                continue
            if topic_dir.name.startswith('_'):
                continue  # _assets 等下划线开头目录跳过
            for md in topic_dir.glob('*.md'):
                if md.name in ('index.md', 'log.md'):
                    continue
                md.unlink()
                deleted += 1
    n_articles = KnowledgeWikiArticle.query.delete()
    db.session.commit()
    print(f'🧹 已删除 {deleted} 个 .md 文件 + 清空 {n_articles} 条 article 记录')
    return deleted


def reingest_all() -> tuple[int, int]:
    """对所有 raw 文件按 id 顺序重新 ingest。返回 (成功, 失败) 计数。"""
    raws = KnowledgeRawFile.query.order_by(KnowledgeRawFile.id).all()
    print(f'\n🔄 开始重编译 {len(raws)} 个 raw 文件 ...\n')
    ok, fail = 0, 0
    for i, raw in enumerate(raws, 1):
        title = raw.title or raw.raw_path
        print(f'[{i}/{len(raws)}] raw_id={raw.id} title={title[:60]}')
        try:
            raw.ingest_status = 'pending'
            raw.ingest_error = None
            db.session.commit()
            result = ingest_raw_file(raw.id)
            ops = result.get('operations') or []
            usage = result.get('usage') or {}
            print(
                f'    ✅ {len(ops)} ops | usage in={usage.get("input_tokens", 0)} '
                f'out={usage.get("output_tokens", 0)}'
            )
            ok += 1
        except IngestError as e:
            print(f'    ❌ IngestError: {e}')
            fail += 1
        except Exception as e:
            print(f'    ❌ {type(e).__name__}: {e}')
            fail += 1
    return ok, fail


def main():
    app = create_app()
    with app.app_context():
        print('═' * 64)
        print('Wiki 知识库回填：补全 docx 嵌入图')
        print('═' * 64)

        n_raws = KnowledgeRawFile.query.count()
        n_articles = KnowledgeWikiArticle.query.count()
        print(f'\n当前数据：raw_files={n_raws}, articles={n_articles}\n')

        if n_raws == 0:
            print('没有 raw 文件可以编译，退出。')
            return

        if not confirm(
            f'⚠️  此操作会：\n'
            f'  1. 备份 wiki/ 整目录到 wiki_backup_<ts>/\n'
            f'  2. 备份 knowledge_wiki_articles 到 data/temp/wiki_articles_backup_*.json\n'
            f'  3. 清空 wiki/<topic>/*.md 与 articles 表\n'
            f'  4. 对全部 {n_raws} 个 raw 文件调用 Claude Opus 重新编译（**会产生 API 费用**）\n\n'
            f'继续？'
        ):
            print('已取消。')
            return

        wiki_dir = get_wiki_dir()
        backup_dir = backup_wiki_dir()
        articles_backup = backup_articles_db()
        clear_existing(wiki_dir)

        ok, fail = reingest_all()

        print('\n' + '═' * 64)
        print('完成')
        print('═' * 64)
        print(f'成功: {ok} | 失败: {fail}')
        print(f'wiki/ 备份: {backup_dir}')
        print(f'articles 备份: {articles_backup}')
        print()
        if fail > 0:
            print('⚠️  有失败项，请检查日志。可用上述备份恢复。')
        else:
            print('✅ 全部成功。建议人工抽查 2-3 篇文章质量再决定是否保留。')


if __name__ == '__main__':
    main()
