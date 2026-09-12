#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 doc.json + translations.json 合成英文技术设计参考（SG/海外用）。

两个出口，同一份译文：
  en/<slug>.md      英文成品（交付给海外工程师）
  review/<slug>.md  中英对照（给审校人逐条核对，成品不含中文）

定位：这不是 DG/TJ 08—2406—2022 的翻译版，是 Evertac 署名的技术设计参考，
只抽与司法辖区无关的工程内容（实测全文 784 条里 671 条,85%）。凡是引到中国
频率划分 / GB 标准 / 中国建筑分类与消防体系的地方，译文里留 [REF-CHECK: ...]
标记，由审校人替换成 IMDA/MCMC、IEC/SS、SCDF/BOMBA 的对应项。

用法：
  python3 scripts/temp/build_en_reference.py            # 全部已配置章节
  python3 scripts/temp/build_en_reference.py --only 14  # 只出某章
"""
import sys, os, json, re, argparse

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
SRC = P.DOC_JSON
EN_DIR = P.EN
OUT_DIR = os.path.join(P.BUILD, 'md')

# 全量：16 章 + 附录 A–N。英文标题取自 translations.json 的章节译文，
# 这里只维护 slug（文件名/URL 用，要稳定）。
CH_SLUG = {
    '1': 'general-provisions', '2': 'terms-and-abbreviations', '3': 'application-sites',
    '4': 'system-network-architecture', '5': 'system-functions', '6': 'system-design',
    '7': 'signal-source', '8': 'distributed-antenna-system', '9': 'digital-terminals',
    '10': 'supporting-design', '11': 'electromagnetic-environment',
    '12': 'safety-protection-and-earthing', '13': 'installation-and-construction',
    '14': 'system-performance-testing', '15': 'project-acceptance',
    '16': 'operation-and-maintenance',
}
APPX_SLUG = {
    'A': 'appendix-a-frequency-quantity', 'B': 'appendix-b-das-performance',
    'C': 'appendix-c-path-loss', 'D': 'appendix-d-service-functions',
    'E': 'appendix-e-work-stages', 'F': 'appendix-f-incoming-inspection',
    'G': 'appendix-g-installation-inspection', 'H': 'appendix-h-performance-report',
    'J': 'appendix-j-test-methods', 'K': 'appendix-k-acceptance-schedule',
    'L': 'appendix-l-trial-run', 'M': 'appendix-m-acceptance-forms',
    'N': 'appendix-n-om-records',
}

HEADER = """# {title}

**Evertac Technical Design Reference — Two-Way Radio In-Building Systems**
{num} of {total_note}

> **What this document is.** An engineering design reference compiled by Evertac. The
> methodology is referenced from the Shanghai engineering construction standard
> *DG/TJ 08—2406—2022, Technical standard for two-way radio communication
> system engineering* (effective 1 May 2023). Clause numbering is kept aligned with that
> source so the two can be read side by side.
>
> **What this document is not.** It is not a translation of that standard and it carries no
> regulatory force in any jurisdiction. Frequency allocations, EMF limits, emergency-responder
> requirements and referenced product/installation codes are jurisdiction-specific — every such
> point is flagged `[REF-CHECK]` below and must be replaced with the local equivalent
> (IMDA / MCMC for spectrum, IEC / SS for equipment and installation, SCDF / BOMBA for
> emergency-responder coverage) before use on a project.
>
> **Modal verbs**, following the source standard's convention:
> 应 = *shall* (mandatory) · 宜 = *should* (recommended) · 可 = *may* (permitted) ·
> 不得 / 不应 = *shall not*.
>
> **Abbreviations.** BDA = bi-directional amplifier (干线放大器) · OMU = optical fiber
> master unit (光纤近端机) · ORU = optical fiber remote unit (光纤远端机) ·
> DAS = distributed antenna system (分布式天馈系统) · POI = point of interface
> (多系统合路平台) · CNR = carrier-to-noise ratio · BER = bit error ratio ·
> VSWR = voltage standing wave ratio · EIRP = equivalent isotropically radiated power ·
> PIM = passive intermodulation.

---
"""

TOTAL_NOTE = "16 chapters and Appendices A–N"


def load():
    doc = json.load(open(SRC, encoding='utf-8'))
    tr = json.load(open(os.path.join(EN_DIR, 'translations.json'), encoding='utf-8'))
    return doc, tr, L.load_glossary()


def units(doc):
    """切出 [(kind, key, title_en, slug, start, end)]：16 章 + 附录 A–N。"""
    marks = []
    for i, n in enumerate(doc):
        if n.get('type') == 'chapter':
            marks.append(('ch', n['num'], i))
        elif n.get('type') == 'appendix':
            marks.append(('appx', n['id'], i))
    out = []
    for j, (kind, key, start) in enumerate(marks):
        end = marks[j + 1][2] if j + 1 < len(marks) else len(doc)
        slug = (CH_SLUG if kind == 'ch' else APPX_SLUG).get(key)
        if slug:
            out.append((kind, key, start, end, slug))
    return out


def chapter_span(doc, num):
    start = None
    for i, n in enumerate(doc):
        if n.get('type') == 'chapter' and n.get('num') == num:
            start = i
        elif start is not None and n.get('type') in ('chapter', 'appendix'):
            return start, i
    return start, len(doc)


def cn_text(n):
    return n.get('text') or n.get('title') or ''


READER_KEY = 'twr-ibs-ref-en'


def render(doc, a, b, tr, gl, bilingual, missing):
    """渲染一章。bilingual=True 时每条下面附原文，供审校对照。"""
    out = []

    def emit(en, cn=None, prefix='', wrap=None):
        if en is None:
            en = '⟨UNTRANSLATED⟩'
        line = f'{prefix}{en}'
        if wrap:
            line = wrap(line)
        out.append(line)
        if bilingual and cn:
            out.append(f'\n<sub>原文：{cn}</sub>')

    for i in range(a, b):
        n = doc[i]
        t = n.get('type')
        key = str(i)
        en = tr.get(key)
        if t in ('chapter', 'section', 'clause', 'item', 'subitem', 'note', 'p') and en is None:
            missing.append((i, t, cn_text(n)[:40]))

        if t == 'chapter':
            continue                                   # 章标题由 HEADER 承担
        if t == 'section':
            out.append(f"\n## {n['num']}　{en or '⟨UNTRANSLATED⟩'}\n")
            if bilingual:
                out.append(f'<sub>原文：{n["title"]}</sub>\n')
        elif t == 'clause':
            emit(en, cn_text(n), prefix=f"\n**{n['num']}**　")
            out.append('')
        elif t == 'item':
            emit(en, cn_text(n), prefix=f"\n{n['label']}. ")
        elif t == 'subitem':
            emit(en, cn_text(n), prefix=f"\n    {n['label']} ")
        elif t == 'note':
            emit(en, cn_text(n), prefix='\n> ')
            out.append('')
        elif t == 'p':
            emit(en, cn_text(n), prefix='\n')
        elif t == 'figure':
            cap = tr.get(f"fig:{n['id']}")
            out.append(f"\n> **Figure {n['id']}　{cap or '⟨UNTRANSLATED⟩'}**"
                       f" — diagram to be re-labelled from the Chinese reader"
                       f" (all labels are HTML text, not raster).\n")
            if cap is None:
                missing.append((i, 'figure', n['id']))
        elif t == 'table':
            out.append('\n' + L.table_md(n, tr, gl, miss=None,
                                         reader_url=f'/wiki/play/{READER_KEY}') + '\n')
        elif t == 'formula':
            fh = n['html']
            for cn_s in sorted(tr.get('figlabels', {}), key=len, reverse=True):
                fh = fh.replace(cn_s, tr['figlabels'][cn_s])
            out.append(f"\n<p style=\"text-align:center\">{fh}"
                       f"{'　' + n['tag'] if n.get('tag') else ''}</p>\n")
        elif t == 'defs':
            items = tr.get(f'defs:{i}')
            if items:
                out.append('\nwhere:')
                out += [f"- *{k}* — {v}" for k, v in items]
                out.append('')
            else:
                missing.append((i, 'defs', ''))
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='只出某一章/附录，如 14 或 J')
    args = ap.parse_args()

    doc, tr, gl = load()
    os.makedirs(os.path.join(OUT_DIR, 'en'), exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, 'review'), exist_ok=True)

    skip = set(tr.get('_skip') or [])
    all_missing, refchecks, total = [], [], 0
    for kind, key, a, b, slug in units(doc):
        if args.only and args.only != key:
            continue
        title_en = tr.get(str(a)) or ''
        label = f'{key}' if kind == 'ch' else f'Appendix {key}'
        header = HEADER.format(title=f'{label}　{title_en}', num=label, total_note=TOTAL_NOTE)

        missing = []
        en_md = header + render(doc, a, b, tr, gl, False, missing)
        rv_md = header + render(doc, a, b, tr, gl, True, [])
        missing = [m for m in missing if m[0] not in skip]

        open(os.path.join(OUT_DIR, 'en', slug + '.md'), 'w', encoding='utf-8').write(en_md)
        open(os.path.join(OUT_DIR, 'review', slug + '.md'), 'w', encoding='utf-8').write(rv_md)

        hits = re.findall(r'\[REF-CHECK: ([^\]]+)\]', en_md)
        refchecks += [(label, h) for h in hits]
        all_missing += [(label,) + m for m in missing]
        total += len(en_md)
        flag = '⚠️' if missing else '  '
        print(f'{label:<12} {title_en[:38]:<40} {len(en_md):>6} 字符  未译 {len(missing):>2} {flag} REF-CHECK {len(hits)}')

    cl = ['# REF-CHECK 清单 —— 需要本地对应项的引用', '',
          '每条都是中国专属引用，译文里已就地标注。请填右列。', '',
          '| 章/附录 | 待替换的中国引用 | 本地对应项（请填） |', '|---|---|---|']
    for label, h in refchecks:
        cl.append(f'| {label} | {h} |  |')
    open(os.path.join(OUT_DIR, 'REF-CHECK.md'), 'w', encoding='utf-8').write('\n'.join(cl) + '\n')

    print(f'\n合计 {total/1024:.0f} KB，REF-CHECK {len(refchecks)} 条 → <build>/md/REF-CHECK.md')
    if all_missing:
        print(f'⚠️ 未译 {len(all_missing)} 条：')
        for m in all_missing[:20]:
            print('   %s [%s] %s %s' % m)
    else:
        print('✅ 全部节点已译')


if __name__ == '__main__':
    main()
