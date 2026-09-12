#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只构建阅读器，不碰库、不投放 —— 给 publish-on-nas.sh 的第 2 步用。

容器里 /app/app 只读，publish.py 的投放步骤跑不了；但构建必须在容器里做
（宿主 Synology 没有 Python 运行环境）。所以把「构建」单拎出来。

用法：python3 lib/build_reader_entry.py cn|en
产物：<pkg>/.build/<target>/<key>.html
"""
import sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import paths as P                                   # noqa: E402
from publish import build_reader, COURSES           # noqa: E402


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COURSES:
        raise SystemExit('用法: build_reader_entry.py cn|en')
    target = sys.argv[1]
    html = build_reader(target)
    print(f"   ✅ {html}  ({os.path.getsize(html)//1024} KB)")


if __name__ == '__main__':
    main()
