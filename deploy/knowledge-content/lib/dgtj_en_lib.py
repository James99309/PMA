#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英文版共用逻辑：术语表查词 + 表格/网格处理。

被 build_en_reference.py（出 markdown）和 build_en_reader.py（出阅读器）共用，
避免两边各写一份表格转换逻辑然后慢慢跑偏。

表格有两条路：
  1. translations.json 里有 `table:<id>` 覆写 → 直接用（人工精修过的表）
  2. 没有 → 按 glossary.json 逐格查词自动生成；查不到的格子原样保留并计入
     未译清单（宁可露出中文被发现，也不要悄悄丢内容）
"""
import os, sys, re, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths as P

EN_DIR = P.EN
GLOSSARY = os.path.join(EN_DIR, 'glossary.json')

CJK = re.compile(r'[一-鿿]')


def load_glossary():
    if not os.path.isfile(GLOSSARY):
        return {}
    return json.load(open(GLOSSARY, encoding='utf-8'))


def has_cjk(s):
    return bool(CJK.search(s or ''))


def gtr(text, gl, miss=None):
    """查词。命中返回英文；没命中原样返回并记进 miss。

    先整串查；查不到再尝试「纯符号/数字/单位」这类本来就不用翻的格子。
    """
    t = (text or '').strip()
    if not t or not has_cjk(t):
        return t
    if t in gl:
        return gl[t]
    # 多行合并的格子：逐行查，全中则拼回去
    parts = [p.strip() for p in re.split(r'\s{2,}|\n', t) if p.strip()]
    if len(parts) > 1 and all(p in gl or not has_cjk(p) for p in parts):
        return ' '.join(gl.get(p, p) for p in parts)
    if miss is not None:
        miss.append(t)
    return t


def grid(page):
    """带 rowspan/colspan 的 rows → 规整二维网格（跨格文本重复填充）。"""
    nR, nC = page.get('nR', 0), page.get('nC', 0)
    g = [[None] * nC for _ in range(nR)]
    for r, row in enumerate(page.get('rows', [])):
        c = 0
        for cell in row:
            while c < nC and g[r][c] is not None:
                c += 1
            if c >= nC:
                break
            t = (cell.get('t') or '').replace('\n', ' ').strip()
            for dr in range(cell.get('rs', 1)):
                for dc in range(cell.get('cs', 1)):
                    if r + dr < nR and c + dc < nC:
                        g[r + dr][c + dc] = t
            c += cell.get('cs', 1)
    return [[x or '' for x in row] for row in g]


def table_rows(node):
    """多页表拼接（跳过续页重复表头）。"""
    rows = []
    for i, p in enumerate(node.get('pages') or []):
        gr = grid(p)
        if i > 0 and rows and gr and gr[0] == rows[0]:
            gr = gr[1:]
        rows += gr
    return rows


def table_title(node, gl, miss=None):
    return f"Table {node['id']}  " + gtr(node.get('title', ''), gl, miss)


TABLE_CHAR_LIMIT = 4000


def table_md(node, tr, gl, miss=None, reader_url=''):
    """→ markdown 表。优先用 translations.json 的人工覆写。"""
    override = tr.get(f"table:{node['id']}")
    if override:
        return override
    rows = table_rows(node)
    if not rows:
        return f"**{table_title(node, gl, miss)}**\n"
    rows = [[gtr(c, gl, miss) for c in r] for r in rows]
    head, body = rows[0], rows[1:]
    nC = len(head)
    esc = lambda s: s.replace('|', '\\|')
    out = [f'**{table_title(node, gl, miss)}**', '',
           '| ' + ' | '.join(esc(x) for x in head) + ' |',
           '|' + '|'.join(['---'] * nC) + '|']
    for r in body:
        r = (r + [''] * nC)[:nC]
        out.append('| ' + ' | '.join(esc(x) for x in r) + ' |')
    md = '\n'.join(out)
    if len(md) > TABLE_CHAR_LIMIT and reader_url:
        return (f'**{table_title(node, gl, miss)}**\n\n'
                f'> {len(body)} rows of data — see the [interactive reader]({reader_url}) '
                f'for the full table.\n')
    return md


def md_table_to_html(md, tid, s_figwrap, s_cap):
    """translations.json 里的人工表是 markdown，转成与中文版同款 HTML 表。"""
    lines = [l for l in md.strip().split('\n') if l.strip()]
    title, note, body = '', '', []
    for l in lines:
        if l.startswith('**Table'):
            title = re.sub(r'^\*\*|\*\*$', '', l).strip()
        elif l.startswith('>'):
            note += l.lstrip('> ').strip() + ' '
        elif l.startswith('|'):
            body.append([c.strip() for c in l.strip('|').split('|')])
    rows = [r for r in body if not all(set(c) <= set('-: ') for c in r)]
    return _html_table(title, note, rows, tid, s_figwrap, s_cap)


def table_html(node, tr, gl, s_figwrap, s_cap, miss=None):
    """→ 阅读器用的 HTML 表。优先人工覆写，否则按 glossary 自动转。"""
    override = tr.get(f"table:{node['id']}")
    if override:
        return md_table_to_html(override, node['id'], s_figwrap, s_cap)
    rows = [[gtr(c, gl, miss) for c in r] for r in table_rows(node)]
    return _html_table(table_title(node, gl, miss), '', rows, node['id'], s_figwrap, s_cap)


def _esc(s):
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _html_table(title, note, rows, tid, s_figwrap, s_cap):
    if not rows:
        return ''
    head, rest = rows[0], rows[1:]
    h = (f'<figure id="tb-{tid}" style="{s_figwrap}">'
         f'<figcaption style="{s_cap}"><b style="font-weight:600">{_esc(title)}</b></figcaption>')
    if note:
        h += (f'<div style="margin:.4rem 0 .7rem;font-size:.85em;color:#9c2b1f;'
              f'text-align:left">{_esc(note.strip())}</div>')
    h += ('<div class="tw"><table style="width:100%;border-collapse:collapse;'
          'font-size:.9em;line-height:1.5"><thead><tr>')
    h += ''.join(f'<th>{_esc(c)}</th>' for c in head)
    h += '</tr></thead><tbody>'
    for r in rest:
        h += '<tr>' + ''.join(f'<td class="l">{_esc(c)}</td>' for c in r) + '</tr>'
    return h + '</tbody></table></div></figure>'
