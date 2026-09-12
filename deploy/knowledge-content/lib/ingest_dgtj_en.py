#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把英文技术设计参考入库（SG/OVS 用）。

跟中文版入库的关键差别：**summary 必须是英文**。
wiki 问答的召回走 `to_tsvector('simple', title || summary)` 的 GIN 索引，
正文不进索引 —— summary 是中文的话，英文提问一条都命不中（不是翻译质量问题，
是压根搜不到）。所以这里每篇的 summary 是手写的英文关键词密集摘要。

默认带 DRAFT 横幅：9 条 REF-CHECK 未填完之前，不能让人当定稿引用。

用法：
  DATABASE_URL=postgresql://nijie@localhost:5432/pma_local_ovs \\
  python3 scripts/temp/ingest_dgtj_en.py --commit
"""
import sys, os, argparse
from datetime import datetime

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

import paths as P
sys.path.insert(0, P.project_root())

EN_DIR = os.path.join(P.BUILD, 'md', 'en')
TOPIC = 'Industry-Knowledge'

DRAFT_BANNER = (
    '> ⚠️ **DRAFT — pending technical review.** Jurisdiction-specific citations are still '
    'flagged `[REF-CHECK]` and have not been replaced with local equivalents. '
    'Do not quote to customers or authorities in this state.\n\n'
)

SRC = P.DOC_JSON

KEYWORDS = ('two-way radio in-building system, DMR, walkie talkie coverage, distributed antenna '
            'system DAS, bi-directional amplifier BDA, optical fiber master unit OMU, optical fiber '
            'remote unit ORU, point of interface POI, leaky feeder, in-building radio coverage, '
            'Evertac design reference')


def build_articles():
    """从 doc.json + translations.json 自动生成 29 篇的标题/摘要/文件名。

    摘要是英文检索的**唯一**召回面（GIN 只索引 title+summary，正文不进索引），
    所以这里把小节标题、条文区间、表号图号、术语缩写全塞进去，宁长勿短。
    """
    import json as _json
    doc = _json.load(open(SRC, encoding='utf-8'))
    tr = _json.load(open(os.path.join(P.EN, 'translations.json'), encoding='utf-8'))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_en_reference as R

    arts = []
    for kind, key, a, b, slug in R.units(doc):
        title_en = tr.get(str(a)) or ''
        label = f'Ch.{key}' if kind == 'ch' else f'App. {key}'
        secs, clauses, tables, figs = [], [], [], []
        for i in range(a, b):
            n = doc[i]
            t = n.get('type')
            if t == 'section':
                secs.append(f"{n['num']} {tr.get(str(i)) or ''}".strip())
            elif t == 'clause':
                clauses.append(n['num'])
            elif t == 'table':
                tables.append(f"Table {n['id']}")
            elif t == 'figure':
                figs.append(f"Figure {n['id']}")
        parts = [f"Evertac technical design reference for two-way radio in-building systems, "
                 f"{label} {title_en}."]
        if secs:
            parts.append('Sections: ' + '; '.join(secs) + '.')
        if clauses:
            parts.append(f"Clauses {clauses[0]} to {clauses[-1]} ({len(clauses)} clauses).")
        if tables:
            parts.append('Contains ' + ', '.join(tables[:12]) + '.')
        if figs:
            parts.append('Contains ' + ', '.join(figs[:8]) + '.')
        parts.append('Keywords: ' + KEYWORDS + '.')
        arts.append({
            'file': slug + '.md',
            'slug': 'twr-ibs-ref-' + slug,
            'title': f'Two-Way Radio In-Building Systems — {label} {title_en}',
            'summary': ' '.join(parts),
        })
    return arts


ARTICLES = build_articles()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--commit', action='store_true', help='真正写库（缺省只预览）')
    ap.add_argument('--scope', default='company')
    ap.add_argument('--topic', default=TOPIC)
    ap.add_argument('--no-draft-banner', action='store_true')
    args = ap.parse_args()

    if not os.environ.get('DATABASE_URL'):
        raise SystemExit('请用 DATABASE_URL 显式指定目标库，避免误写 CN 库')
    print('目标库:', os.environ['DATABASE_URL'].rsplit('/', 1)[-1])

    payload = []
    for a in ARTICLES:
        path = os.path.join(EN_DIR, a['file'])
        if not os.path.isfile(path):
            raise SystemExit(f'缺文件 {path}，先跑 build_en_reference.py')
        md = open(path, encoding='utf-8').read()
        if not args.no_draft_banner:
            # 横幅插在 H1 之后
            lines = md.split('\n')
            i = next((k for k, l in enumerate(lines) if l.startswith('# ')), -1)
            md = '\n'.join(lines[:i + 1]) + '\n\n' + DRAFT_BANNER + '\n'.join(lines[i + 1:])
        payload.append((a, md))
        print(f"  {a['slug']:<50} 正文 {len(md):>6}  摘要 {len(a['summary']):>4}")

    if not args.commit:
        print('\n（预览模式，未写库。加 --commit 落库）')
        return

    from app import create_app, db
    from app.models.knowledge import KnowledgeWikiArticle
    from app.models.user import User
    from app.services.wiki import storage
    from app.services.wiki.paths import ensure_wiki_structure

    app = create_app()
    with app.app_context():
        ensure_wiki_structure()
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            raise SystemExit('目标库没有 admin 用户')
        for a, md in payload:
            path = storage.write_article(args.topic, a['slug'], md)
            row = KnowledgeWikiArticle.query.filter_by(topic=args.topic, slug=a['slug']).first()
            if not row:
                row = KnowledgeWikiArticle(topic=args.topic, slug=a['slug'], owner_id=admin.id)
                db.session.add(row)
            row.title = a['title']
            row.summary = a['summary']
            row.file_path = path
            row.content_length = len(md)
            row.compile_model = 'manual/en-translation'
            row.last_compiled_at = datetime.now()
            row.scope = args.scope
        db.session.commit()
        print(f'\n✅ 入库 {len(payload)} 篇 → topic={args.topic} scope={args.scope} owner={admin.username}')


if __name__ == '__main__':
    main()
