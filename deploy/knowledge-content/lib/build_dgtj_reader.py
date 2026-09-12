#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「HTML5 标准格式转换」包构建成 PMA 互动课程可上传的单文件课件。

输入：解压后的转换包目录（含 *.dc.html / support.js / content.js / build/doc.json）
输出：
  - <out>/dgtj08-2406-2022.html    单文件自包含课件（无任何外部请求）
  - <out>/1.png                    课程卡封面（原 PDF 第 1 页，1280x720）

做了三件事：
  1. 内联 React / ReactDOM（原本从 unpkg 拉，国内不稳）——dc-runtime 见
     window.React 已存在就不会再发 CDN 请求（Babel 仅 kind==='jsx' 才拉，本件不触发）。
  2. 删掉 Google Fonts 的 preconnect/link（实测 50+ 个 fonts.gstatic.com 请求，
     国内不可达），字体栈回退到 CSS 变量里已写好的 Songti SC / SimSun。
  3. 内联 support.js + content.js，产出单文件 → 管理员可直接走 /wiki/at 上传 UI。

用法：
  python3 scripts/temp/build_dgtj_reader.py <解压目录> [输出目录]
"""
import sys, os, re, io

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths as P

# React UMD 随包走：NAS 内网拉不到 unpkg，也避免构建结果依赖外网
REACT_URL = 'react.production.min.js'
REACT_DOM_URL = 'react-dom.production.min.js'

COURSE_KEY = 'dgtj08-2406-2022'


def _read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def _fetch_vendor(name, _cache_dir=None):
    """读随包携带的 React UMD。"""
    return _read(os.path.join(P.VENDOR, name))


def _inline_script(js):
    """内联 JS 时防止 </script> 提前闭合（本包实测为 0，仍保留兜底）。"""
    return js.replace('</script', r'<\/script')


def _mask_xdc_markers(js):
    """把 support.js 源码里的 `<x-dc` / `</x-dc>` 字面量藏起来（值不变）。

    dc-runtime 启动后会 fetch(location.href) 把整页源码再 parseDcText 一遍
    （靠这一步把 encodeCase 改写过的 <sc-raw-table> 还原成真 <table>）。
    parseDcText 是**纯文本扫描**：找第一个 `<x-dc>` 和最后一个 `</x-dc>` 当模板边界。
    而 support.js 自己的源码里就带着这两个字面量（第 39/41 行的正则与字符串、
    1670 行的报错文案）—— 内联进页面后，它会把自己的源码当成模板起点，
    整页渲染出一堆 JS 源码。

    用 \x64（= 'd' 的十六进制转义）改写：正则/字符串的**运行时值完全不变**，
    但源码文本里不再出现可被扫描到的标记。
    """
    subs = [
        (r'/<x-dc(?:\s[^>]*)?>/', r'/<x-\x64c(?:\s[^>]*)?>/'),
        ('"</x-dc>"', '"</x-\\x64c>"'),
        ('<x-dc> block', '<x-\\x64c> block'),
    ]
    for a, b in subs:
        assert a in js, f'support.js 里没找到待屏蔽的标记: {a}'
        js = js.replace(a, b)
    assert '<x-dc' not in js and '</x-dc>' not in js, 'x-dc 标记仍有残留'
    return js


def build_html(src_dir, out_dir, key=COURSE_KEY):
    dc = [f for f in os.listdir(src_dir) if f.endswith('.dc.html')]
    if not dc:
        raise SystemExit(f'{src_dir} 下没有 *.dc.html')
    html = _read(os.path.join(src_dir, dc[0]))
    support = _read(os.path.join(src_dir, 'support.js'))
    content = _read(os.path.join(src_dir, 'content.js'))

    cache = os.path.join(out_dir, '_vendor')
    react = _fetch_vendor(REACT_URL, cache)
    react_dom = _fetch_vendor(REACT_DOM_URL, cache)

    # 1) 去 Google Fonts（preconnect x2 + stylesheet x1）
    before = html
    html = re.sub(r'\s*<link rel="preconnect" href="https://fonts\.(googleapis|gstatic)\.com"[^>]*>', '', html)
    html = re.sub(r'\s*<link href="https://fonts\.googleapis\.com/css2[^"]*" rel="stylesheet">', '', html)
    assert 'fonts.googleapis' not in html and 'fonts.gstatic' not in html, '去字体 CDN 失败'
    assert html != before

    # 2) 内联 React + ReactDOM + support.js + content.js —— 全部放进 <head>。
    #
    # ⚠️ 位置是关键，不能图省事就地替换 <script src="content.js">：
    # 那个标签在 <helmet> 里，属于 dc 模板区。dc-runtime 会 fetch(location.href)
    # 把整页源码重新 parseDcText 一遍 —— 这一步不是可有可无的：encodeCase 先把
    # 模板里的 <table> 改写成 <sc-raw-table>，靠这次重解析 + RAW_UNWRAP 才还原成
    # 真表格。content.js 那 640KB 里全是 HTML 字符串，塞进模板区会让重解析认错边界
    # （实测整页渲染出 support.js 源码）。
    # 之前用 window.__resources={} 关掉重解析算是治标：页面不乱码了，但 50 张表
    # 全卡在 <sc-raw-table> 中间态、没有边框（原始多文件包渲染的是 50 张真 <table>）。
    # 正解是把内联脚本移出模板区，让重解析照常跑。
    head_js = (
        '<script>/* react 18.3.1 (inlined, 原 unpkg) */\n' + _inline_script(react) + '\n</script>\n'
        '<script>/* react-dom 18.3.1 (inlined, 原 unpkg) */\n' + _inline_script(react_dom) + '\n</script>\n'
        '<script>/* content.js (inlined) */\n' + _inline_script(content) + '\n</script>\n'
        '<script>/* dc-runtime support.js (inlined) */\n' + _mask_xdc_markers(_inline_script(support)) + '\n</script>'
    )
    html, n1 = re.subn(r'<script src="\./support\.js"></script>', lambda m: head_js, html, count=1)
    assert n1 == 1, '未找到 support.js 引用'

    # 模板区里那个 content.js 引用直接删掉（内容已提到 <head>）
    html, n2 = re.subn(r'<script src="content\.js"></script>', '', html, count=1)
    assert n2 == 1, '未找到 content.js 引用'

    assert 'unpkg.com' not in html.split('var REACT_URL')[0], 'CDN 引用残留'

    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, key + '.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    return out


def build_cover(src_dir, out_dir):
    """课程卡封面 → 1024x576（对齐既有课程缩略图规格）。

    优先用 <out_dir>/cover-src.png（设计出的封面图）；没有才回退到原 PDF 第 1 页。
    """
    override = os.path.join(out_dir, 'cover-src.png')
    if os.path.isfile(override):
        from PIL import Image
        img = Image.open(override).convert('RGB').resize((1024, 576), Image.LANCZOS)
        out = os.path.join(out_dir, '1.png')
        img.save(out, optimize=True)
        return out

    pdf = None
    for cand in ('original.pdf',):
        p = os.path.join(src_dir, cand)
        if os.path.isfile(p):
            pdf = p
            break
    if not pdf:
        up = os.path.join(src_dir, 'uploads')
        if os.path.isdir(up):
            for f in os.listdir(up):
                if f.lower().endswith('.pdf'):
                    pdf = os.path.join(up, f)
                    break
    if not pdf:
        print('⚠️  未找到原始 PDF，跳过封面生成')
        return None

    import fitz
    from PIL import Image
    doc = fitz.open(pdf)
    pix = doc[0].get_pixmap(dpi=150)
    img = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    # 卡片只有 132px 高：整页缩下去字太小，裁标题区（规范名/标准号/主编单位）
    top, bot = 0.06, 0.62
    img = img.crop((0, int(img.height * top), img.width, int(img.height * bot)))
    W, H = 1280, 720
    scale = min(W * 0.86 / img.width, H * 0.92 / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    canvas = Image.new('RGB', (W, H), (252, 251, 248))
    canvas.paste(img, ((W - img.width) // 2, (H - img.height) // 2))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, '1.png')
    canvas.save(out)
    doc.close()
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('src', help='解压/生成的源包目录')
    ap.add_argument('out', nargs='?', help='输出目录')
    ap.add_argument('--key', help='课程 key（决定输出文件名），缺省 dgtj08-2406-2022')
    ap.add_argument('--no-cover', action='store_true', help='跳过封面（publish.py 自带封面）')
    a = ap.parse_args()
    src = a.src
    out = a.out or os.path.join(get_project_root(), 'data', 'temp', 'dgtj-build')
    if a.key:
        COURSE_KEY = a.key

    html = build_html(src, out, a.key or COURSE_KEY)
    print(f'✅ 单文件课件: {html}  ({os.path.getsize(html)/1024:.0f} KB)')
    cover = None if a.no_cover else build_cover(src, out)
    if cover:
        print(f'✅ 课程封面:   {cover}  ({os.path.getsize(cover)/1024:.0f} KB)')
    print('\n下一步：')
    print('  1) /wiki/at → 上传课程，选这个 html，key 填 dgtj08-2406-2022')
    print(f'  2) 封面放到 app/course_assets/{COURSE_KEY}.thumbs/1.png，并置 has_thumbs=true')
