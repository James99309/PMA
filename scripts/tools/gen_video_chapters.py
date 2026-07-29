#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视频课程章节自动生成 —— whisper 转写视频 + 讲稿文本对齐 → 每页起始秒 → chapters JSON。

用法:
  # 生成章节并打印(供人工核对,不写库):
  python3 scripts/tools/gen_video_chapters.py --video <video.mp4> --scripts <en_scripts.json>

  # 生成并写入某课程的 chapters 字段:
  python3 scripts/tools/gen_video_chapters.py --video <video.mp4> --scripts <en_scripts.json> \
        --course-key <key> --write

  # scripts 为标题列表(每页一个标题)也可,格式见 --help。

依赖:
  - OpenAI whisper-1(从 OPENAI_API_KEY 或 .env.local 读 key);ffmpeg 抽音频。
  - 讲稿 JSON: {"1":"page1 text","2":"page2 text",...} 或 [{"page":1,"text":"..."},...]

注意:章节标题默认取讲稿每页前若干字;可用 --titles 传一份 {"1":"标题",...} 覆盖。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request


def get_project_root():
    cur = os.path.dirname(os.path.abspath(__file__))
    while cur != '/':
        if os.path.exists(os.path.join(cur, 'app')) and os.path.exists(os.path.join(cur, 'run.py')):
            return cur
        cur = os.path.dirname(cur)
    raise RuntimeError('无法找到项目根目录')

ROOT = get_project_root()
sys.path.insert(0, ROOT)


def _load_key():
    k = os.environ.get('OPENAI_API_KEY')
    if k:
        return k
    envf = os.path.join(ROOT, '.env.local')
    if os.path.exists(envf):
        for line in open(envf, encoding='utf-8'):
            if line.startswith('OPENAI_API_KEY='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    raise RuntimeError('未找到 OPENAI_API_KEY')


def _clean(s):
    return re.sub(r"[\s，。、？！,.?!:：；;\"'“”（）()·\-—]", '', s or '')


def transcribe(video_path, key):
    """抽音频 → whisper-1 带段级时间戳。返回 segments 列表 [{start,end,text}]。"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        audio = f.name
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video_path, '-vn',
                    '-ar', '16000', '-ac', '1', '-codec:a', 'libmp3lame', '-b:a', '48k', audio],
                   check=True)
    print(f'  已抽音频 {os.path.getsize(audio)//1024} KB, 上传 whisper 转写(可能需几分钟)...', flush=True)
    # multipart 手工构造走 curl(大文件更稳)
    outf = audio + '.json'
    subprocess.run(['curl', '-s', '--max-time', '900',
                    '-H', f'Authorization: Bearer {key}',
                    '-F', f'file=@{audio}', '-F', 'model=whisper-1',
                    '-F', 'response_format=verbose_json',
                    '-F', 'timestamp_granularities[]=segment',
                    'https://api.openai.com/v1/audio/transcriptions', '-o', outf], check=True)
    data = json.load(open(outf))
    os.unlink(audio)
    os.unlink(outf)
    if 'segments' not in data:
        raise RuntimeError('whisper 未返回 segments: ' + str(data)[:200])
    return data['segments']


def align(segments, pages):
    """把每页讲稿开头在转写时间轴上定位。pages: [(page_no, text, title)]。
    返回 [{page, start, title}]。用逐字映射 + 滑动相似度。"""
    import difflib
    chars, times = [], []
    for s in segments:
        t = _clean(s['text'])
        chars.append(t)
        times.append((s['start'], s['end']))
    full = ''.join(chars)

    def pos2time(p):
        acc = 0
        for i, t in enumerate(chars):
            if acc + len(t) > p:
                frac = (p - acc) / max(len(t), 1)
                st, en = times[i]
                return st + frac * (en - st)
            acc += len(t)
        return times[-1][1] if times else 0

    result = []
    for page_no, text, title in pages:
        probe = _clean(text)[:30]
        if len(probe) < 8:
            result.append({'page': page_no, 'start': None, 'title': title, '_score': 0.0})
            continue
        best, bp = 0, -1
        for i in range(0, len(full) - len(probe)):
            r = difflib.SequenceMatcher(None, probe, full[i:i + len(probe)]).ratio()
            if r > best:
                best, bp = r, i
        t = round(pos2time(bp), 1) if bp >= 0 else None
        result.append({'page': page_no, 'start': t, 'title': title, '_score': round(best, 2)})

    # 第 1 页强制从 0
    if result:
        result[0]['start'] = 0.0

    # ── 单调性纠错:章节时间必须递增。低分(<0.7)或时间倒退的页视为误定位,
    #    标记后用前后可信页线性插值。视频不倒放,这个约束能修掉文本撞车导致的错位。──
    total_dur = times[-1][1] if times else 0
    n = len(result)
    trusted = [False] * n
    prev_t = -1
    for i, c in enumerate(result):
        ok = (c['start'] is not None and c['_score'] >= 0.7 and c['start'] >= prev_t - 1)
        trusted[i] = ok
        if ok:
            prev_t = c['start']
    result[0]['start'] = 0.0
    trusted[0] = True
    for i in range(n):
        if trusted[i]:
            continue
        # 找前一个可信页
        lo_i = i - 1
        while lo_i >= 0 and not trusted[lo_i]:
            lo_i -= 1
        lo_t = result[lo_i]['start'] if lo_i >= 0 else 0.0
        # 找后一个可信页
        hi_i = i + 1
        while hi_i < n and not trusted[hi_i]:
            hi_i += 1
        hi_t = result[hi_i]['start'] if hi_i < n else total_dur
        gap = hi_i - lo_i
        result[i]['start'] = round(lo_t + (hi_t - lo_t) * (i - lo_i) / max(gap, 1), 1)
        result[i]['_interp'] = True
    return result


def load_scripts(path):
    """讲稿 JSON → [(page_no, text, title)]。title 取正文前 40 字(截到标点)。"""
    data = json.load(open(path, encoding='utf-8'))
    items = []
    if isinstance(data, dict):
        for k in sorted(data, key=lambda x: int(x)):
            items.append((int(k), data[k]))
    else:
        for it in data:
            items.append((int(it['page']), it.get('text') or it.get('en') or ''))
    out = []
    for page_no, text in items:
        # 标题:第一句(到句号/换行),截 42 字
        first = re.split(r'[.。\n!?！？]', text.strip())[0].strip()
        out.append((page_no, text, first[:42]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--video', required=True, help='视频文件路径')
    ap.add_argument('--scripts', required=True, help='讲稿 JSON (每页文本)')
    ap.add_argument('--titles', help='可选:每页标题 JSON {"1":"标题",...} 覆盖自动标题')
    ap.add_argument('--course-key', help='要写入的课程 key')
    ap.add_argument('--write', action='store_true', help='写入课程 chapters 字段(需 --course-key)')
    args = ap.parse_args()

    pages = load_scripts(args.scripts)
    if args.titles:
        tmap = json.load(open(args.titles, encoding='utf-8'))
        pages = [(p, t, tmap.get(str(p), title)) for p, t, title in pages]
    print(f'讲稿 {len(pages)} 页')

    key = _load_key()
    print('转写视频...')
    segs = transcribe(args.video, key)
    print(f'  转写 {len(segs)} 段')

    chapters = align(segs, pages)
    print('\n=== 章节对齐结果(核对低分项)===')
    clean_ch = []
    for c in chapters:
        flag = '↻插值' if c.get('_interp') else ('⚠️低分' if c['_score'] < 0.6 else '')
        mm = f"{int(c['start']//60)}:{int(c['start']%60):02d}" if c['start'] is not None else '--:--'
        print(f"  第{c['page']:2d}页 {mm:>6}  score={c['_score']}  {c['title'][:36]} {flag}")
        clean_ch.append({'page': c['page'], 'start': c['start'] or 0, 'title': c['title']})

    out_json = json.dumps(clean_ch, ensure_ascii=False, indent=1)
    print('\n=== chapters JSON ===')
    print(out_json)

    if args.write:
        if not args.course_key:
            print('❌ --write 需要 --course-key'); sys.exit(1)
        from app import create_app, db
        from app.models.course import InteractiveCourse
        app = create_app()
        with app.app_context():
            row = InteractiveCourse.query.filter_by(key=args.course_key).first()
            if not row:
                print(f'❌ 课程不存在: {args.course_key}'); sys.exit(1)
            row.chapters = json.dumps(clean_ch, ensure_ascii=False)
            db.session.commit()
            print(f'✅ 已写入课程 {args.course_key} 的 chapters ({len(clean_ch)} 章)')


if __name__ == '__main__':
    main()
