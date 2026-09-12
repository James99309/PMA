#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 DG/TJ 08—2406—2022 的结构化 doc.json 切成 wiki 文章入库（不走 Opus 编译）。

为什么不走现成的 raw-file ingest：
  原 PDF 135 页 / 2.8MB，超过 wiki 的 30 页上限；且 LLM 重述会丢表格和条文号。
  转换包里的 build/doc.json 已是 100% 结构化（956 节点：chapter/section/clause/
  item/table/figure/formula/defs），直接机械转 markdown —— 准确率 100%、0 token。

切片：总览 1 篇 + 第 1~16 章各 1 篇 + 附录 2 篇 = 19 篇，topic=行业知识。
  按章切是因为 wiki 问答走 title+summary 的 GIN 召回 top-5 再喂全文，
  一篇 135 页会挤掉其它文章，按章切召回更准、上下文更省。

用法：
  python3 scripts/temp/ingest_dgtj_standard.py <doc.json 路径> --dry-run   # 只出 md + 统计
  python3 scripts/temp/ingest_dgtj_standard.py <doc.json 路径> --commit    # 落盘 + 建 DB 行
"""
import sys, os, re, json, argparse

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
ROOT = P.project_root()
sys.path.insert(0, ROOT)

TOPIC = '行业知识'
SLUG_PREFIX = 'dgtj08-2406-2022'
COURSE_KEY = 'dgtj08-2406-2022'
STD_CODE = 'DG/TJ 08—2406—2022'
STD_NAME = '专用数字无线对讲通信系统工程技术标准'

# 章 → slug 里的英文短名（wiki 既有文章都是英文 kebab slug）
CH_SLUG = {
    '1': 'general-provisions', '2': 'terms-and-abbreviations', '3': 'application-sites',
    '4': 'network-architecture', '5': 'system-functions', '6': 'system-design',
    '7': 'signal-source', '8': 'distributed-antenna-system', '9': 'digital-terminals',
    '10': 'supporting-design', '11': 'electromagnetic-environment', '12': 'safety-and-grounding',
    '13': 'construction-and-installation', '14': 'performance-testing', '15': 'acceptance',
    '16': 'operation-and-maintenance',
}

# 附录分组：有正文的计算/测试方法 vs 纯检验记录表格
APPX_METHOD = ['A', 'B', 'C', 'D', 'J']
APPX_FORMS = ['E', 'F', 'G', 'H', 'K', 'L', 'M', 'N']

# 超过这个字符数的表格只留标题+指向阅读器（Erlang 表这类几千格的数据表，
# 塞进文章会把问答上下文挤爆，查数值用阅读器更合适）
TABLE_CHAR_LIMIT = 4000


# ══════════════════════════════════════════════════════════════════
# doc.json → markdown
# ══════════════════════════════════════════════════════════════════

def _grid(page):
    """把带 rowspan/colspan 的 rows 展开成规整二维网格（跨格文本重复填充）。

    重复而不是留空，是因为文章要喂给问答模型：每行自带完整定语，
    模型不用回头找合并单元格的表头。
    """
    nR, nC = page.get('nR', 0), page.get('nC', 0)
    grid = [[None] * nC for _ in range(nR)]
    for r, row in enumerate(page.get('rows', [])):
        c = 0
        for cell in row:
            while c < nC and grid[r][c] is not None:
                c += 1
            if c >= nC:
                break
            t = (cell.get('t') or '').replace('\n', ' ').strip()
            for dr in range(cell.get('rs', 1)):
                for dc in range(cell.get('cs', 1)):
                    if r + dr < nR and c + dc < nC:
                        grid[r + dr][c + dc] = t
            c += cell.get('cs', 1)
    return [[(x if x is not None else '') for x in row] for row in grid]


def table_md(node):
    """table 节点 → markdown 表格（多页表拼接，跳过续页重复表头）。"""
    pages = node.get('pages') or []
    rows = []
    for i, p in enumerate(pages):
        g = _grid(p)
        if i > 0 and rows and g and g[0] == rows[0]:
            g = g[1:]          # 续页重复的表头
        rows.extend(g)
    if not rows:
        return ''
    head, body = rows[0], rows[1:]
    nC = len(head)

    def esc(s):
        return s.replace('|', '\\|')

    out = ['| ' + ' | '.join(esc(x) for x in head) + ' |',
           '|' + '|'.join(['---'] * nC) + '|']
    for r in body:
        r = (r + [''] * nC)[:nC]
        out.append('| ' + ' | '.join(esc(x) for x in r) + ' |')
    return '\n'.join(out)


def node_md(n):
    t = n.get('type')
    if t == 'chapter':
        return f"\n## 第{n['num']}章　{n['title']}\n"
    if t == 'section':
        return f"\n### {n['num']}　{n['title']}\n"
    if t == 'subhead':
        return f"\n**{n['title']}**\n"
    if t == 'appendix':
        return f"\n## 附录{n['id']}　{n['title']}\n"
    if t == 'special':
        return f"\n### {n['title']}\n"
    if t == 'clause':
        return f"\n**{n['num']}**　{n['text']}\n"
    if t == 'p':
        return f"\n{n['text']}\n"
    if t == 'item':
        return f"\n- **{n['label']}** {n['text']}"
    if t == 'subitem':
        return f"\n  - {n['label']} {n['text']}"
    if t == 'note':
        return f"\n> {n['text']}\n"
    if t == 'figure':
        return (f"\n> **图{n['id']}　{n['title']}**"
                f"（图形见[交互阅读器](/wiki/play/{COURSE_KEY})）\n")
    if t == 'formula':
        tag = f"　{n['tag']}" if n.get('tag') else ''
        return f"\n<p style=\"text-align:center\">{n['html']}{tag}</p>\n"
    if t == 'defs':
        lines = ['', '式中：']
        lines += [f"- {k} —— {v}" for k, v in n.get('items', [])]
        return '\n'.join(lines) + '\n'
    if t == 'table':
        md = table_md(n)
        head = f"\n**表{n['id']}　{n['title']}**\n"
        if not md:
            return head
        if len(md) > TABLE_CHAR_LIMIT:
            return (head + f"\n> 本表共 {md.count(chr(10))} 行，数据量大，"
                    f"完整表格见[交互阅读器](/wiki/play/{COURSE_KEY})。\n")
        return head + '\n' + md + '\n'
    return ''


def render_nodes(nodes):
    """拼接节点 markdown。

    item/subitem 结尾不带换行（避免 loose list 多出一层 <p>），所以列表项后面
    紧跟条文/图注/表格时只有一个 \n —— markdown 会把它当成列表项的续行吞进去
    （实测第 3.2.2 条被缩进到「3」条目里）。这里按需补一个空行断开。
    """
    out = []
    for n in nodes:
        c = node_md(n)
        if not c:
            continue
        if out and not out[-1].endswith('\n') and not c.startswith(('\n- ', '\n  - ')):
            out.append('\n')
        out.append(c)
    return ''.join(out)


# ══════════════════════════════════════════════════════════════════
# 切片
# ══════════════════════════════════════════════════════════════════

def split_units(doc):
    """返回 [{'kind','key','title','nodes'}]：front / ch<N> / appx<ID> / tail。"""
    units, cur = [], {'kind': 'front', 'key': 'front', 'title': '前置', 'nodes': []}
    for n in doc:
        t = n.get('type')
        if t == 'chapter':
            units.append(cur)
            cur = {'kind': 'ch', 'key': n['num'], 'title': n['title'], 'nodes': [n]}
        elif t == 'appendix':
            units.append(cur)
            cur = {'kind': 'appx', 'key': n['id'], 'title': n['title'], 'nodes': [n]}
        elif t == 'special' and n.get('title') == '本标准用词说明':
            units.append(cur)
            cur = {'kind': 'tail', 'key': 'tail', 'title': '本标准用词说明', 'nodes': [n]}
        else:
            cur['nodes'].append(n)
    units.append(cur)
    return units


def extract_terms(doc):
    """从第 2.1 节的术语条文里抽中文术语名（条文形如「信号源signalsource指…」）。"""
    terms = []
    for n in doc:
        if n.get('type') == 'clause' and str(n.get('num', '')).startswith('2.1.'):
            m = re.match(r'^([一-鿿、，,]+)', n.get('text', ''))
            if m:
                terms.append(m.group(1).rstrip('、，,'))
    return terms


HEADER_TMPL = """> **出处**：上海市工程建设规范《{name}》{code}（J 16909—2023），2022-12-19 批准，2023-05-01 施行。
> 主编单位：华东建筑设计研究院有限公司、上海建筑设计研究院有限公司、上海市无线电协会。
> **本文是标准原文的结构化转录**（条文号、表格与原文一致），图形与排版见[交互阅读器](/wiki/play/{key})。
"""


def build_article(unit, terms):
    """→ (slug, title, summary, markdown)"""
    if unit['kind'] in ('overview', 'appx-group'):
        return unit['slug'], unit['title'], unit['summary'], unit['md']

    body = render_nodes(unit['nodes'])
    header = HEADER_TMPL.format(name=STD_NAME, code=STD_CODE, key=COURSE_KEY)

    if unit['kind'] == 'ch':
        num = unit['key']
        slug = f"{SLUG_PREFIX}-ch{int(num):02d}-{CH_SLUG.get(num, 'chapter')}"
        title = f"{STD_CODE} 第{num}章　{unit['title']}"
        secs = [f"{n['num']} {n['title']}" for n in unit['nodes'] if n.get('type') == 'section']
        clauses = [n['num'] for n in unit['nodes'] if n.get('type') == 'clause']
        tables = [f"表{n['id']}" for n in unit['nodes'] if n.get('type') == 'table']
        figs = [f"图{n['id']}" for n in unit['nodes'] if n.get('type') == 'figure']
        hit = [t for t in terms if t in body]
        parts = [f"上海市工程建设规范 {STD_CODE}《{STD_NAME}》第{num}章「{unit['title']}」条文全文。"]
        if secs:
            parts.append('小节：' + '、'.join(secs) + '。')
        if clauses:
            parts.append(f"条文 {clauses[0]}–{clauses[-1]}（共 {len(clauses)} 条）。")
        if tables:
            parts.append('含 ' + '、'.join(tables) + '。')
        if figs:
            parts.append('含 ' + '、'.join(figs) + '。')
        if hit:
            parts.append('涉及术语：' + '、'.join(hit[:14]) + '。')
        parts.append('关键词：上海 地方标准 专用数字无线对讲 DMR 对讲通信系统 工程技术标准 '
                     '强制性条文 设计 施工 验收 运维。')
        summary = ' '.join(parts)
        md = f"# {title}\n\n{header}\n{body}"
        return slug, title, summary, md

    if unit['kind'] == 'overview':
        return unit['slug'], unit['title'], unit['summary'], unit['md']

    if unit['kind'] == 'appx-group':
        return unit['slug'], unit['title'], unit['summary'], unit['md']

    return None


def build_overview(doc, units, terms):
    chs = [u for u in units if u['kind'] == 'ch']
    appx = [u for u in units if u['kind'] == 'appx']
    front = next(u for u in units if u['kind'] == 'front')
    tail = next((u for u in units if u['kind'] == 'tail'), None)

    lines = [f"# {STD_CODE}　{STD_NAME}（总览）", '',
             HEADER_TMPL.format(name=STD_NAME, code=STD_CODE, key=COURSE_KEY), '',
             '## 适用范围', '',
             '本市各类房屋建筑及其附属设施场所中 150MHz、400MHz 频段专用数字无线对讲通信系统，'
             '以及 350MHz 频段消防应急救援对讲通信系统的工程建设。', '',
             '## 章节地图', '']
    for u in chs:
        num = u['key']
        slug = f"{SLUG_PREFIX}-ch{int(num):02d}-{CH_SLUG.get(num, 'chapter')}"
        secs = [n['title'] for n in u['nodes'] if n.get('type') == 'section']
        lines.append(f"- **第{num}章 {u['title']}** — [{TOPIC}/{slug}]({TOPIC}/{slug})"
                     + ('：' + '、'.join(secs) if secs else ''))
    lines += ['', '## 附录', '']
    for u in appx:
        grp = '计算与方法' if u['key'] in APPX_METHOD else '检验/记录表格'
        lines.append(f"- **附录{u['key']}** {u['title']}（{grp}）")
    lines += ['', '## 术语（第 2.1 节定义）', '',
              '、'.join(terms) + '。', '',
              '## 发布与前言', '']
    lines.append(render_nodes(front['nodes']))
    if tail:
        lines.append(render_nodes(tail['nodes']))

    title = f"{STD_CODE}《{STD_NAME}》总览"
    summary = (f"上海市工程建设规范 {STD_CODE}（J 16909—2023）《{STD_NAME}》总览："
               f"适用范围、16 章结构地图、附录 A–N 清单、第 2.1 节全部 {len(terms)} 个术语定义、"
               f"前言与用词说明。150MHz 400MHz 350MHz 消防应急救援 专用数字无线对讲 DMR "
               f"上海 地方标准 2023-05-01 施行 华东建筑设计研究院。"
               f"术语：{'、'.join(terms[:16])}。")
    return {'kind': 'overview', 'slug': f'{SLUG_PREFIX}-overview',
            'title': title, 'summary': summary, 'md': '\n'.join(lines)}


def build_appx_group(units, keys, slug_suffix, title_cn, extra_kw):
    picked = [u for u in units if u['kind'] == 'appx' and u['key'] in keys]
    body = ''
    for u in picked:
        body += render_nodes(u['nodes'])
    md = (f"# {STD_CODE}　附录{'、'.join(keys)}　{title_cn}\n\n"
          + HEADER_TMPL.format(name=STD_NAME, code=STD_CODE, key=COURSE_KEY) + '\n' + body)
    summary = (f"{STD_CODE}《{STD_NAME}》{title_cn}（附录 "
               + '、'.join(f"{u['key']} {u['title']}" for u in picked) + f"）。{extra_kw}")
    return {'kind': 'appx-group', 'slug': f'{SLUG_PREFIX}-{slug_suffix}',
            'title': f"{STD_CODE} 附录{'、'.join(keys)}　{title_cn}",
            'summary': summary, 'md': md}


# ══════════════════════════════════════════════════════════════════
# 入库
# ══════════════════════════════════════════════════════════════════

def commit(articles, owner_id, scope):
    from app import create_app, db
    from app.models.knowledge import KnowledgeWikiArticle
    from app.services.wiki import storage
    from app.services.wiki.paths import ensure_wiki_structure
    from datetime import datetime

    app = create_app()
    with app.app_context():
        ensure_wiki_structure()
        if not owner_id:
            from app.models.user import User
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                raise SystemExit('库里没有 admin 用户，请用 --owner-id 指定')
            owner_id = admin.id
            print(f'owner_id 未指定，用 admin: {admin.username} (id={owner_id})')
        done = []
        for slug, title, summary, md in articles:
            path = storage.write_article(TOPIC, slug, md)
            row = KnowledgeWikiArticle.query.filter_by(topic=TOPIC, slug=slug).first()
            if not row:
                row = KnowledgeWikiArticle(topic=TOPIC, slug=slug, owner_id=owner_id)
                db.session.add(row)
            row.title = title
            row.summary = summary
            row.file_path = path
            row.content_length = len(md)
            row.compile_model = 'mechanical/doc.json'
            row.last_compiled_at = datetime.now()
            row.scope = scope
            done.append(slug)
        db.session.commit()
        print(f'✅ 入库 {len(done)} 篇 → topic={TOPIC} scope={scope}')
        for s in done:
            print('   -', s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('doc_json', nargs='?', default=P.DOC_JSON)
    ap.add_argument('--commit', action='store_true')
    ap.add_argument('--out', default=os.path.join(P.BUILD, 'cn-wiki'))
    ap.add_argument('--owner-id', type=int, default=0,
                    help='文章 owner；缺省取库里第一个 admin')
    ap.add_argument('--scope', default='company')
    args = ap.parse_args()

    doc = json.load(open(args.doc_json, encoding='utf-8'))
    units = split_units(doc)
    terms = extract_terms(doc)

    built = [build_overview(doc, units, terms)]
    built += [u for u in units if u['kind'] == 'ch']
    built.append(build_appx_group(
        units, APPX_METHOD, 'appendix-methods', '计算方法与性能指标',
        'Erlang 频率数量计算 天馈性能指标 空间损耗计算 业务功能说明 测试方法 驻波比 无源互调 场强测试。'))
    built.append(build_appx_group(
        units, APPX_FORMS, 'appendix-forms', '检验与验收记录表格',
        '进场核准检验 安装检验 第三方检测报告 验收检验项目 试运行时间表 验收记录表 运维记录表。'))

    articles = [build_article(u, terms) for u in built]
    articles = [a for a in articles if a]

    os.makedirs(args.out, exist_ok=True)
    total = 0
    print(f'{"slug":<52} {"正文":>8} {"摘要":>6}  标题')
    for slug, title, summary, md in articles:
        with open(os.path.join(args.out, slug + '.md'), 'w', encoding='utf-8') as f:
            f.write(md)
        total += len(md)
        print(f'{slug:<52} {len(md):>8} {len(summary):>6}  {title}')
    print(f'\n合计 {len(articles)} 篇 / {total/1024:.0f} KB，md 已写到 {args.out}')

    if args.commit:
        commit(articles, args.owner_id, args.scope)
    else:
        print('（--dry-run 模式：未写 wiki 存储、未建 DB 行）')


if __name__ == '__main__':
    main()
