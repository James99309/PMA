#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成英文版交互阅读器的源包（再交给 build_dgtj_reader.py 打成单文件）。

阅读器的内容就是 `window.STD = {meta, toc, index, html}` 一坨结构化数据。
这里按同样结构生成英文版：
  - meta / toc / index / html 全部由 doc.json + translations.json 合成
  - 排版样式沿用中文版（h2/h3/条文/表格的 inline style 逐字照抄），保证视觉一致
  - 图不重画：从中文 content.js 里原样抽出 <figure>（本来就是 HTML/CSS 画的），
    再按 figlabels 把图内中文标签替换成英文（长串优先，避免 "射频同轴电缆"
    被 "射频" 先吃掉）
  - 外壳 .dc.html 复用中文版，替换掉侧栏抬头/检索框/回到顶部等 UI 串

只含已翻译章节（当前 4/8/14），侧栏抬头标明 partial draft。

用法：
  python3 scripts/temp/build_en_reader.py
  python3 scripts/temp/build_dgtj_reader.py data/temp/dgtj-en-src --key twr-ibs-ref-en
"""
import sys, os, re, json, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dgtj_en_lib as L

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
CN_SRC = P.SRC
EN_DIR = P.EN
OUT = os.path.join(P.BUILD, 'en-src')

# 全量：16 章 + 附录 A–N（顺序按原标准）
CHAPTERS = [str(i) for i in range(1, 17)]
APPENDICES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N']

# 中文版的 inline style，逐字沿用
S_H2 = ('display:flex;align-items:baseline;gap:.6em;font:600 1.5rem/1.45 var(--serif);'
        'margin:3.8rem 0 1.6rem;padding-top:1.2rem;border-top:2px solid var(--accent)')
S_H3 = ('display:flex;align-items:baseline;gap:.55em;font:600 1.12rem/1.65 var(--serif);'
        'margin:2.5rem 0 .9rem')
S_P = 'margin:.9rem 0;text-align:justify'
S_NUM = ('color:var(--accent);font-weight:600;margin-right:.45em;'
         'font-variant-numeric:tabular-nums')
S_ITEM = 'margin:.55rem 0 .55rem 1.5rem;text-align:justify'
S_SUB = 'margin:.45rem 0 .45rem 3rem;text-align:justify'
S_NOTE = 'margin:.8rem 0;font-size:.9em;color:#6f6a61;text-align:justify'
S_FIGWRAP = 'margin:2.1rem 0'
S_CAP = 'margin-bottom:.6rem;font-size:.92em;text-align:center'


def load():
    doc = json.load(open(P.DOC_JSON, encoding='utf-8'))
    tr = json.load(open(os.path.join(EN_DIR, 'translations.json'), encoding='utf-8'))
    raw = open(os.path.join(CN_SRC, 'content.js'), encoding='utf-8').read()
    cn = json.loads(raw.split('=', 1)[1].strip().rstrip(';'))
    return doc, tr, cn


def unit_span(doc, kind, key):
    """章(kind='chapter'/num) 或 附录(kind='appendix'/id) 的节点区间。"""
    s = None
    for i, n in enumerate(doc):
        if s is None:
            if n.get('type') == kind and (n.get('num') or n.get('id')) == key:
                s = i
        elif n.get('type') in ('chapter', 'appendix'):
            return s, i
    return s, len(doc)


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def translate_figure(fig_html, figlabels):
    """把图内中文标签换成英文。长串优先，否则短词会先命中把长串切碎。"""
    out = fig_html
    for cn in sorted(figlabels, key=len, reverse=True):
        out = out.replace(cn, figlabels[cn])
    return out


def md_table_to_html(md, tid):
    """translations.json 里的表是 markdown，这里转成与中文版同款的 HTML 表。"""
    lines = [l for l in md.strip().split('\n') if l.strip()]
    title = ''
    body = []
    note = ''
    for l in lines:
        if l.startswith('**Table'):
            title = re.sub(r'^\*\*|\*\*$', '', l).strip()
        elif l.startswith('>'):
            note += l.lstrip('> ').strip() + ' '
        elif l.startswith('|'):
            body.append([c.strip() for c in l.strip('|').split('|')])
    rows = [r for r in body if not all(set(c) <= set('-: ') for c in r)]
    if not rows:
        return ''
    head, rest = rows[0], rows[1:]
    h = (f'<figure id="tb-{tid}" style="{S_FIGWRAP}">'
         f'<figcaption style="{S_CAP}"><b style="font-weight:600">{esc(title)}</b></figcaption>')
    if note:
        h += (f'<div style="margin:.4rem 0 .7rem;font-size:.85em;color:#9c2b1f;'
              f'text-align:left">{esc(note.strip())}</div>')
    h += ('<div class="tw"><table style="width:100%;border-collapse:collapse;'
          'font-size:.9em;line-height:1.5"><thead><tr>')
    h += ''.join(f'<th>{esc(c)}</th>' for c in head)
    h += '</tr></thead><tbody>'
    for r in rest:
        h += '<tr>' + ''.join(f'<td class="l">{esc(c)}</td>' for c in r) + '</tr>'
    return h + '</tbody></table></div></figure>'


def terminology_html(tr):
    """术语对照表：BDA / OMU / ORU 这类简称首次出现前先给定义，海外工程师才对得上。"""
    rows = tr.get('terminology') or []
    if not rows:
        return ''
    h = (f'<h3 id="terms" style="{S_H3}"><span>Abbreviations</span></h3>'
         '<div class="tw"><table style="width:100%;border-collapse:collapse;'
         'font-size:.9em;line-height:1.5"><thead><tr>'
         '<th>Abbr.</th><th>Term</th><th>源标准用词</th></tr></thead><tbody>')
    for a, en, cn in rows:
        h += (f'<tr><td class="c"><b>{a}</b></td><td class="l">{en}</td>'
              f'<td class="l">{cn}</td></tr>')
    return h + '</tbody></table></div>'


def build(doc, tr, cn):
    figs = {m.group(1): m.group(0) for m in
            re.finditer(r'<figure id="(fg-[^"]+)"[^>]*>.*?</figure>', cn['html'], re.S)}
    figlabels = tr.get('figlabels', {})

    html, toc, index = [], [], []

    html.append(
        f'<h2 id="intro" style="{S_H2}"><span>Evertac Technical Design Reference</span></h2>'
        f'<p style="{S_P}"><b>Two-Way Radio In-Building Systems.</b> '
        'An engineering design reference compiled by Evertac. The methodology is referenced from '
        'the Shanghai engineering construction standard DG/TJ 08&mdash;2406&mdash;2022 '
        '(effective 1 May 2023); clause numbering is kept aligned with that source.</p>'
        f'<p style="{S_P}"><b>This is not a translation of that standard and carries no regulatory '
        'force.</b> Frequency allocations, EMF limits, emergency-responder requirements and '
        'referenced product / installation codes are jurisdiction-specific: every such point is '
        'marked <b style="color:#9c2b1f">[REF-CHECK]</b> and must be replaced with the local '
        'equivalent (IMDA / MCMC, IEC / SS, SCDF / BOMBA) before use on a project.</p>'
        f'<p style="{S_P}"><b>Modal verbs:</b> <i>shall</i> = mandatory &middot; '
        '<i>should</i> = recommended &middot; <i>may</i> = permitted &middot; '
        '<i>shall not</i> = prohibited.</p>'
        f'<p style="{S_P};color:#9c2b1f"><b>Complete &mdash; 16 chapters and Appendices A&ndash;N. '
        'Pending technical review of the [REF-CHECK] items.</b></p>'
        + terminology_html(tr))
    toc.append({'id': 'intro', 'label': 'About this reference'})
    index.append({'id': 'intro', 'label': 'About', 'text': 'Evertac Technical Design Reference two-way radio in-building systems abbreviations BDA OMU ORU DAS POI'})

    gl = L.load_glossary()
    seq = [('chapter', c) for c in CHAPTERS] + [('appendix', x) for x in APPENDICES]
    for kind, ch in seq:
        a, b = unit_span(doc, kind, ch)
        if a is None:
            continue
        is_appx = kind == 'appendix'
        cid = (f'ap-{ch}' if is_appx else f'ch-{ch}')
        num_label = (f'App. {ch}' if is_appx else ch)
        ch_title = tr.get(str(a)) or ''
        html.append(f'<h2 id="{cid}" style="{S_H2}">'
                    f'<span style="color:var(--accent);white-space:nowrap">{num_label}</span>'
                    f'<span>{esc(ch_title)}</span></h2>')
        node = {'id': cid, 'label': ch_title, 'num': num_label, 'children': []}
        toc.append(node)
        index.append({'id': cid,
                      'label': (f'Appendix {ch}' if is_appx else f'Chapter {ch}'),
                      'text': ch_title})

        cur_clause = cur_num = None
        for i in range(a, b):
            n = doc[i]
            t = n.get('type')
            en = tr.get(str(i))
            if t == 'section':
                sid = f'sec-{n["num"]}'
                html.append(f'<h3 id="{sid}" style="{S_H3}">'
                            f'<span style="color:var(--accent)">{n["num"]}</span>'
                            f'<span>{esc(en or n["title"])}</span></h3>')
                node['children'].append({'id': sid, 'label': en or n['title'], 'num': n['num']})
                index.append({'id': sid, 'label': n['num'], 'text': en or n['title']})
            elif t == 'clause':
                lid = cur_clause = f'cl-{n["num"]}'
                cur_num = n['num']
                html.append(f'<p id="{lid}" style="{S_P}">'
                            f'<span style="{S_NUM}">{n["num"]}</span>{esc(en or "")}</p>')
                index.append({'id': lid, 'label': n['num'], 'text': en or ''})
            elif t in ('item', 'subitem'):
                style = S_ITEM if t == 'item' else S_SUB
                html.append(f'<p style="{style}">'
                            f'<span style="{S_NUM}">{n["label"]}</span>{esc(en or "")}</p>')
                # 条目也进检索索引 —— 中文原版只索引到"条"这一级，像
                # "noise floor"（8.3.4-1 / 8.3.5-5）这种只存在于条目里的设计
                # 规则就永远搜不到。这里把条目挂到父条的锚点上。
                if en and cur_clause:
                    index.append({'id': cur_clause,
                                  'label': f'{cur_num}-{n["label"]}',
                                  'text': en})
            elif t == 'note':
                html.append(f'<p style="{S_NOTE}">{esc(en or "")}</p>')
            elif t == 'figure':
                fid = f'fg-{n["id"]}'
                raw = figs.get(fid)
                cap = tr.get(f'fig:{n["id"]}', '')
                if raw:
                    html.append(translate_figure(raw, figlabels))
                else:
                    html.append(f'<figure id="{fid}" style="{S_FIGWRAP}">'
                                f'<figcaption style="{S_CAP}"><b>Figure {n["id"]}</b>&nbsp;&nbsp;'
                                f'{esc(cap)}</figcaption></figure>')
                index.append({'id': fid, 'label': f'Figure {n["id"]}', 'text': cap})
            elif t == 'table':
                html.append(L.table_html(n, tr, gl, S_FIGWRAP, S_CAP))
                index.append({'id': f'tb-{n["id"]}', 'label': f'Table {n["id"]}',
                              'text': L.table_title(n, gl)})
            elif t == 'formula':
                # 公式 HTML 里也会有中文（如 J.0.7 的"接通呼叫次数/呼叫总次数"），
                # 走同一套 figlabels 替换
                fhtml = translate_figure(n['html'], figlabels)
                html.append(f'<p style="text-align:center;margin:1.2rem 0">{fhtml}'
                            f'{"&nbsp;&nbsp;" + n["tag"] if n.get("tag") else ""}</p>')
            elif t == 'defs':
                items = tr.get(f'defs:{i}')
                if items:
                    html.append(f'<p style="{S_ITEM}">where: ' + '; '.join(
                        f'<i>{esc(k)}</i> = {esc(v)}' for k, v in items) + '</p>')

    return {
        'meta': {
            'code': 'Evertac DMR Design Reference',
            'code2': 'Complete · 16 chapters + Appendices A–N',
            'title': 'Two-Way Radio In-Building Systems',
            'en': 'Engineering design reference — methodology referenced from DG/TJ 08—2406—2022',
            'issuer': 'Evertac Solutions',
            'effective': 'Pending technical review',
        },
        'toc': toc,
        'index': index,
        'html': ''.join(html),
    }


def build_shell(tr):
    """复用中文外壳，替换 UI 串。"""
    src = [f for f in os.listdir(CN_SRC) if f.endswith('.dc.html')][0]
    s = open(os.path.join(CN_SRC, src), encoding='utf-8').read()
    # 封面块/侧栏里的标准号是硬编码在外壳 HTML 里的（不是从 meta 取）。
    # 这里按 HTML 片段整段替换 —— 不能用裸字符串 "DG/TJ 08—2406—2022" 做 key，
    # 否则会把我们自己译文里那句 "Methodology referenced from DG/TJ..." 也改掉。
    FRAGMENTS = [
        ('<span>DG/TJ 08—2406—2022</span>', '<span>EVERTAC DESIGN REFERENCE</span>'),
        ('<span>J 16909—2023</span>', '<span>Rev. A · 2026</span>'),
        ('color:#918a7c">DG/TJ 08—2406—2022</div>',
         'color:#918a7c">16 chapters + App. A–N</div>'),
        ('Technical standard for two-way radio communication system engineering',
         'Engineering design reference — system architecture, distributed antenna system, '
         'performance testing and acceptance'),
        ('2023 年 5 月 1 日', '3 of 16 chapters translated'),
        ("'DG/TJ 08—2406—2022\u3000专用数字无线对讲通信系统工程技术标准'",
         "'Evertac Technical Design Reference'"),
    ]
    for a, b in FRAGMENTS:
        s = s.replace(a, b)

    # 先改 JS 里的拼接表达式，再跑 ui 字典：反过来的话 '检索结果' 已被替换，
    # 表达式就匹配不上，会留下一个孤零零的 '条'
    s = s.replace("'检索结果 ' + results.length + ' 条'", "results.length + ' results'")
    s = s.replace("'未找到匹配内容'", "'No matching content'")
    ui = tr.get('ui', {})
    for cn in sorted(ui, key=len, reverse=True):   # 长串优先，短串会切碎长串
        s = s.replace(cn, ui[cn])
    # 侧栏抬头三行来自 meta，模板里是硬编码中文标题的地方已由 ui 覆盖
    return s


def main():
    doc, tr, cn = load()
    std = build(doc, tr, cn)

    os.makedirs(OUT, exist_ok=True)
    shutil.copy2(os.path.join(CN_SRC, 'support.js'), os.path.join(OUT, 'support.js'))
    with open(os.path.join(OUT, 'content.js'), 'w', encoding='utf-8') as f:
        f.write('window.STD = ' + json.dumps(std, ensure_ascii=False))
    with open(os.path.join(OUT, 'EN-DMR-Reference.dc.html'), 'w', encoding='utf-8') as f:
        f.write(build_shell(tr))

    # 术语表的「源标准用词」列是**有意保留**的中文（BDA↔干线放大器 这种对照，
    # SG 工程师跟 CN 同事对话时要用），查残留时把这一段排除掉
    body = re.sub(r'<h3 id="terms".*?</table></div>', '', std['html'], flags=re.S)
    left = len(re.findall(r'[一-鿿]', body))
    zh_terms = len(re.findall(r'[一-鿿]', std['html'])) - left
    print(f"✅ 英文阅读器源包 → {OUT}")
    print(f"   目录 {len(std['toc'])} 项 / 检索索引 {len(std['index'])} 条 / 正文 {len(std['html'])} 字符")
    print(f"   正文残留中文：{left}" + ('  ⚠️ 需检查' if left else '  ✅ 无'))
    print(f"   术语表中文对照：{zh_terms} 字（有意保留）")


if __name__ == '__main__':
    main()
