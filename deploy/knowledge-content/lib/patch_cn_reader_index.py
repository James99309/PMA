#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给中文阅读器的检索索引补上"条目"一级。

转换包生成的 index 只到"条"（509 条，全是 cl-/sec-/tb-/ch-/fg-/ap-/sp-），
条文底下那些编号条目（item / subitem）没进索引。后果：搜「底噪」只命中
2.1.30 的术语定义，命中不了 8.3.5-5 里真正的设计规则 —— 而这本标准大量
实质内容恰恰在条目层。英文版生成时已经补了，这里给中文版做同样的事。

做法：不重建索引（避免动转换器已经调好的 label/text），而是把每个条目
插到它父条的索引项之后，id 指向父条锚点，点击照样滚到该条。

用法：python3 scripts/temp/patch_cn_reader_index.py
      之后重新 build_dgtj_reader.py 打包即可。
"""
import sys, os, json, re

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

import paths as P
SRC = P.SRC


def main():
    doc = json.load(open(P.DOC_JSON, encoding='utf-8'))
    raw = open(os.path.join(SRC, 'content.js'), encoding='utf-8').read()
    std = json.loads(raw.split('=', 1)[1].strip().rstrip(';'))

    # 条号 → 该条底下的条目（保持原文顺序）
    by_clause = {}
    cur = None
    for n in doc:
        t = n.get('type')
        if t == 'clause':
            cur = n['num']
        elif t in ('item', 'subitem') and cur:
            txt = re.sub(r'<[^>]+>', '', n.get('text') or '')
            if txt.strip():
                by_clause.setdefault(cur, []).append((n.get('label', ''), txt.strip()))

    old = std['index']
    if any(e.get('_item') for e in old):
        print('索引已补过，跳过'); return

    new, added = [], 0
    for e in old:
        new.append(e)
        if e['id'].startswith('cl-'):
            num = e['id'][3:]
            for label, txt in by_clause.get(num, []):
                new.append({'id': e['id'], 'label': f'{num}-{label}', 'text': txt, '_item': 1})
                added += 1
    std['index'] = new

    with open(os.path.join(SRC, 'content.js'), 'w', encoding='utf-8') as f:
        f.write('window.STD = ' + json.dumps(std, ensure_ascii=False))

    print(f'✅ 中文索引 {len(old)} → {len(new)} 条（新增条目级 {added} 条）')
    # 自检：原来搜不到的两个例子
    for kw in ('底噪', '级联'):
        hits = [e for e in new if kw in (e.get('text') or '')]
        print(f'   搜「{kw}」命中 {len(hits)} 条: ' + '、'.join(e['label'] for e in hits[:6]))


if __name__ == '__main__':
    main()
