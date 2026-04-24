#!/usr/bin/env python3
"""
把 app/static/cad_symbols/*.svg 解析并生成 JS 对象字面量，
嵌入到 DEFAULT_DEVICE_ICONS，每个图标按 iconKey 分类着色。

用法:  python3 scripts/tools/build_device_icons.py
输出:  打印 JS 代码片段，复制到 system-diagram-core.js 里
"""
import os, re, sys
import xml.etree.ElementTree as ET

SYMBOLS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'app', 'static', 'cad_symbols')
SYMBOLS_DIR = os.path.abspath(SYMBOLS_DIR)

# 按 iconKey 分类着色
COLOR_RULES = {
    # 天线：绿色
    'antenna_indoor': '#22c55e',
    'antenna_exproof': '#22c55e',
    'antenna_outdoor': '#22c55e',
    'antenna_panel': '#22c55e',
    # ORU/OMU 远端/主单元：紫色
    'oru': '#a855f7',
    'omu': '#a855f7',
    'oru_wall': '#a855f7',
    # 合路/耦合/功分 + 放大/剥离：蓝色（RF 链路元件）
    'combiner': '#3b82f6',
    'coupler': '#3b82f6',
    'splitter': '#3b82f6',
    'rf_amplifier': '#3b82f6',
    'signal_stripper': '#3b82f6',
    # 对讲机 + 配件充电：橙色
    'radio_handheld': '#f59e0b',
    'radio_display': '#f59e0b',
    'multi_charger': '#f59e0b',
    # MARK 1000：青色（网络设备）
    'mark1000': '#06b6d4',
    # 基础设施机柜：蓝灰
    'base_station': '#64748b',
    'charging_cabinet': '#64748b',
}

NS = '{http://www.w3.org/2000/svg}'

def parse_svg(path):
    """返回 (viewBox, paths_list) where paths_list = [{d, fill}, ...]"""
    tree = ET.parse(path)
    root = tree.getroot()
    vb_attr = root.get('viewBox', '0 0 64 64').strip().split()
    vb = [float(v) for v in vb_attr[:4]]

    paths = []
    for p in root.iter():
        tag = p.tag.split('}')[-1] if '}' in p.tag else p.tag
        if tag == 'path':
            d = (p.get('d') or '').strip()
            if not d: continue
            cls = p.get('class', '')
            # EVERTAC sprite 的 st0 class = fill-rule:evenodd，默认填充
            # 否则按 path fill
            fill_attr = p.get('fill', '')
            paths.append({'d': d, 'class': cls, 'fill': fill_attr})
        elif tag == 'rect':
            # rect → path
            x = float(p.get('x', 0)); y = float(p.get('y', 0))
            w = float(p.get('width', 0)); h = float(p.get('height', 0))
            d = f'M{x} {y}h{w}v{h}h{-w}z'
            paths.append({'d': d, 'class': '', 'fill': p.get('fill', '')})
    return vb, paths

def normalize_and_color(vb, paths, icon_key):
    """把 viewBox 归一化到 0 0 64 64，坐标重新映射；套上统一颜色。"""
    x0, y0, w, h = vb
    color = COLOR_RULES.get(icon_key, '#64748b')
    # 计算缩放 + 偏移：viewBox → (0,0, 64, 64)，保持纵横比居中
    scale = min(64.0 / w, 64.0 / h) if w > 0 and h > 0 else 1.0
    new_w = w * scale
    new_h = h * scale
    off_x = (64 - new_w) / 2 - x0 * scale
    off_y = (64 - new_h) / 2 - y0 * scale

    # 转换每个 path 的 d 坐标
    new_paths = []
    for p in paths:
        new_d = transform_path_d(p['d'], off_x, off_y, scale)
        new_paths.append({
            'd': new_d,
            'fill': color,
            'opacity': 1.0,
        })
    return [0, 0, 64, 64], new_paths

# SVG path 命令正则：单字母 + 数字序列
_CMD = re.compile(r'([MmLlHhVvCcSsQqTtAaZz])|(-?\d+\.?\d*(?:[eE][+-]?\d+)?)')

def transform_path_d(d, off_x, off_y, scale):
    """按 (off_x, off_y, scale) 线性变换 SVG path d 属性的所有绝对坐标。
    相对命令（小写）只需缩放，不需要平移。
    """
    tokens = _CMD.findall(d)
    out = []
    i = 0
    last_cmd = None
    while i < len(tokens):
        cmd_tok, num_tok = tokens[i]
        if cmd_tok:
            cmd = cmd_tok
            out.append(cmd)
            last_cmd = cmd
            i += 1
            continue
        # 数字：根据 last_cmd 判断是否需要平移 + 缩放
        cmd = last_cmd or 'M'
        upper_cmds = cmd.isupper()  # 大写 = 绝对

        # 读取该命令需要的参数个数
        arg_counts = {
            'M': 2, 'L': 2, 'T': 2,
            'H': 1, 'V': 1,
            'C': 6, 'S': 4, 'Q': 4,
            'A': 7,
            'Z': 0,
        }
        n = arg_counts.get(cmd.upper(), 2)
        if n == 0:
            i += 1
            continue

        # 读 n 个数字
        args = []
        for _ in range(n):
            while i < len(tokens) and not tokens[i][1]:
                i += 1
            if i >= len(tokens): break
            args.append(float(tokens[i][1]))
            i += 1

        if len(args) < n: break

        # 根据命令类型变换
        if cmd in ('M', 'L', 'T'):
            out.append(f'{args[0]*scale + off_x:.3f}')
            out.append(f'{args[1]*scale + off_y:.3f}')
        elif cmd in ('m', 'l', 't'):
            out.append(f'{args[0]*scale:.3f}')
            out.append(f'{args[1]*scale:.3f}')
        elif cmd == 'H':
            out.append(f'{args[0]*scale + off_x:.3f}')
        elif cmd == 'h':
            out.append(f'{args[0]*scale:.3f}')
        elif cmd == 'V':
            out.append(f'{args[0]*scale + off_y:.3f}')
        elif cmd == 'v':
            out.append(f'{args[0]*scale:.3f}')
        elif cmd in ('C', 'c'):
            for k in range(0, 6, 2):
                if cmd == 'C':
                    out.append(f'{args[k]*scale + off_x:.3f}')
                    out.append(f'{args[k+1]*scale + off_y:.3f}')
                else:
                    out.append(f'{args[k]*scale:.3f}')
                    out.append(f'{args[k+1]*scale:.3f}')
        elif cmd in ('S', 's', 'Q', 'q'):
            pairs = 2  # S/Q 各 2 对
            for k in range(0, n, 2):
                if cmd.isupper():
                    out.append(f'{args[k]*scale + off_x:.3f}')
                    out.append(f'{args[k+1]*scale + off_y:.3f}')
                else:
                    out.append(f'{args[k]*scale:.3f}')
                    out.append(f'{args[k+1]*scale:.3f}')
        elif cmd in ('A', 'a'):
            # rx ry rot large sweep ex ey
            out.append(f'{args[0]*scale:.3f}')  # rx
            out.append(f'{args[1]*scale:.3f}')  # ry
            out.append(f'{args[2]:.3f}')        # rot 不缩放
            out.append(f'{int(args[3])}')       # large
            out.append(f'{int(args[4])}')       # sweep
            if cmd == 'A':
                out.append(f'{args[5]*scale + off_x:.3f}')
                out.append(f'{args[6]*scale + off_y:.3f}')
            else:
                out.append(f'{args[5]*scale:.3f}')
                out.append(f'{args[6]*scale:.3f}')

    return ' '.join(out)


def main():
    print('// === Auto-generated from app/static/cad_symbols/ (run scripts/tools/build_device_icons.py) ===')
    print('const DEVICE_ICONS_FROM_DWG = {')
    for f in sorted(os.listdir(SYMBOLS_DIR)):
        if not f.endswith('.svg'): continue
        key = os.path.splitext(f)[0]
        try:
            vb, paths = parse_svg(os.path.join(SYMBOLS_DIR, f))
            new_vb, new_paths = normalize_and_color(vb, paths, key)
            # 输出 JS 代码
            js_paths = []
            for p in new_paths:
                js_paths.append(
                    "{d:'" + p['d'] + "',fill:'" + p['fill'] + "',stroke:'none'}"
                )
            print(f"  {key}: {{viewBox:'0 0 64 64', paths:[" + ','.join(js_paths) + "]},")
        except Exception as e:
            print(f'// ERROR {key}: {e}', file=sys.stderr)
    print('};')

if __name__ == '__main__':
    main()
