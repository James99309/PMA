#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译完整性检查工具 v2.0

检测三类问题：
1. 缺少翻译标记 - 中文文本未用 _() 包裹
2. 缺少翻译条目 - 已标记但 messages.po 中没有对应翻译
3. 缺少徽章映射 - 状态/类型值需要检查样式配置

使用方式：
    python3 scripts/tools/check_translations.py                    # 检查所有页面
    python3 scripts/tools/check_translations.py -f <file>          # 检查指定文件
    python3 scripts/tools/check_translations.py --interactive      # 交互式逐页检查
"""

import re
import os
import sys
import glob
import argparse

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

PROJECT_ROOT = get_project_root()
os.chdir(PROJECT_ROOT)

# 状态/类型值列表（用于徽章映射检测）
STATUS_VALUES = [
    # 通用状态
    '草稿', '待审批', '已审批', '已驳回', '已取消', '进行中', '已完成', 'pending',
    # 产品状态
    '新建', '研发中', '待入库', '审批中', '已入库', '在售', '停产', '即将上市',
    # 客户状态
    '活跃', '非活跃', '已关闭', '潜在', '正式',
    # 报销状态
    '已锁定', '未锁定',
    # 项目状态
    '跟进中', '已立项', '已丢单', '已中标', '已结束',
    # 审批状态
    'approved', 'rejected', 'recalled',
]


def load_existing_translations():
    """加载现有的翻译条目"""
    po_file = 'app/translations/en/LC_MESSAGES/messages.po'
    translations = set()

    if os.path.exists(po_file):
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取所有 msgid
        msgid_pattern = re.compile(r'^msgid "(.+)"$', re.MULTILINE)
        translations = set(msgid_pattern.findall(content))

    return translations


def analyze_template(filepath, existing_translations):
    """分析单个模板文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    results = {
        'missing_marker': [],      # 缺少翻译标记
        'missing_translation': [], # 缺少翻译条目
        'badge_mapping': [],       # 徽章映射
    }

    # 1. 找出已标记但可能缺少翻译的文本
    translated_pattern = r"_\(['\"]([^'\"]+)['\"]"
    for match in re.finditer(translated_pattern, content):
        text = match.group(1)
        # 检查是否包含中文
        if re.search(r'[\u4e00-\u9fff]', text):
            if text not in existing_translations:
                # 找到行号
                pos = match.start()
                line_num = content[:pos].count('\n') + 1
                results['missing_translation'].append({
                    'line': line_num,
                    'text': text,
                })

    # 2. 分析每一行，找出未标记的中文
    in_jinja_comment = False
    in_css_comment = False

    for line_num, line in enumerate(lines, 1):
        original_line = line

        # 跳过 Jinja 注释块
        if '{#' in line:
            in_jinja_comment = True
        if '#}' in line:
            in_jinja_comment = False
            continue
        if in_jinja_comment:
            continue

        # 跳过 HTML 注释
        if '<!--' in line and '-->' not in line:
            continue
        if '-->' in line and '<!--' not in line:
            continue
        if '<!--' in line and '-->' in line:
            line = re.sub(r'<!--.*?-->', '', line)

        # 跳过 JS 单行注释
        line = re.sub(r'//.*$', '', line)

        # 跳过 console.log/error/warn 开发者日志
        line = re.sub(r'console\.(log|error|warn|info|debug)\([^)]*\)', '', line)

        # 跳过 CSS 注释块
        if '/*' in line and '*/' not in line:
            in_css_comment = True
        if '*/' in line:
            in_css_comment = False
            continue
        if in_css_comment:
            continue
        line = re.sub(r'/\*.*?\*/', '', line)

        # 移除已翻译的部分
        line_cleaned = re.sub(r"_\(['\"][^'\"]*['\"](\s*,\s*[^)]+)?\)", '', line)

        # 移除 Jinja 变量和控制语句
        line_cleaned = re.sub(r'\{\{[^}]+\}\}', '', line_cleaned)
        line_cleaned = re.sub(r'\{%[^%]+%\}', '', line_cleaned)

        # 移除不需要翻译的 HTML 属性（注意：placeholder 需要翻译，不在此列表中）
        attrs_to_remove = ['class', 'id', 'style', 'href', 'src', 'onclick', 'onchange',
                          'data-[a-z-]+', 'name', 'value', 'type']
        for attr in attrs_to_remove:
            line_cleaned = re.sub(rf'{attr}="[^"]*"', '', line_cleaned)
            line_cleaned = re.sub(rf"{attr}='[^']*'", '', line_cleaned)

        # 找出剩余的中文文本
        chinese_pattern = r'[\u4e00-\u9fff][^\u4e00-\u9fff<>{}\'\"]*[\u4e00-\u9fff]+|[\u4e00-\u9fff]{2,}'
        chinese_matches = re.findall(chinese_pattern, line_cleaned)

        for match in chinese_matches:
            match = match.strip()
            if len(match) < 2:
                continue

            # 跳过纯数字+中文单位
            if re.match(r'^[\d.]+[万元个条天年月日时分秒]$', match):
                continue

            # 判断类型
            if match in STATUS_VALUES:
                results['badge_mapping'].append({
                    'line': line_num,
                    'text': match,
                    'context': original_line.strip()[:100]
                })
            else:
                results['missing_marker'].append({
                    'line': line_num,
                    'text': match,
                    'context': original_line.strip()[:100]
                })

    return results


def print_file_results(filepath, results, show_context=True):
    """打印单个文件的检查结果"""
    rel_path = filepath.replace('app/templates/', '')

    total_issues = (len(results['missing_marker']) +
                   len(results['missing_translation']) +
                   len(results['badge_mapping']))

    if total_issues == 0:
        print(f"\n✅ {rel_path} - 无问题")
        return 0

    print(f"\n{'='*70}")
    print(f"📄 {rel_path}")
    print(f"{'='*70}")

    # 1. 缺少翻译标记
    if results['missing_marker']:
        print(f"\n🔴 缺少翻译标记 ({len(results['missing_marker'])} 处)")
        print("   需要用 _('...') 包裹这些文本：")
        for item in results['missing_marker']:
            print(f"   行 {item['line']:4d}: \"{item['text']}\"")
            if show_context:
                print(f"            → {item['context'][:80]}")

    # 2. 缺少翻译条目
    if results['missing_translation']:
        print(f"\n🟡 缺少翻译条目 ({len(results['missing_translation'])} 处)")
        print("   已标记但 messages.po 中没有对应英文翻译：")
        for item in results['missing_translation']:
            print(f"   行 {item['line']:4d}: \"{item['text']}\"")

    # 3. 徽章映射
    if results['badge_mapping']:
        print(f"\n🔵 徽章/状态值 ({len(results['badge_mapping'])} 处)")
        print("   检查是否有对应的样式映射配置：")
        unique_values = {}
        for item in results['badge_mapping']:
            if item['text'] not in unique_values:
                unique_values[item['text']] = []
            unique_values[item['text']].append(item['line'])
        for text, lines in sorted(unique_values.items()):
            print(f"   - \"{text}\" (行 {', '.join(map(str, lines[:3]))}{'...' if len(lines) > 3 else ''})")

    return total_issues


def interactive_mode(templates, existing_translations):
    """交互式逐页检查模式"""
    print("\n" + "="*70)
    print("📋 交互式翻译检查模式")
    print("="*70)
    print(f"共 {len(templates)} 个页面待检查\n")
    print("命令说明：")
    print("  [Enter] - 检查下一个页面")
    print("  [s]     - 跳过当前页面")
    print("  [q]     - 退出检查")
    print("  [f]     - 标记当前页面为已修复")
    print("-"*70)

    fixed_files = []
    skipped_files = []
    files_with_issues = []

    for i, template in enumerate(templates):
        rel_path = template.replace('app/templates/', '')
        print(f"\n[{i+1}/{len(templates)}] 检查: {rel_path}")

        results = analyze_template(template, existing_translations)
        total_issues = (len(results['missing_marker']) +
                       len(results['missing_translation']) +
                       len(results['badge_mapping']))

        if total_issues == 0:
            print("  ✅ 无问题，自动跳过")
            continue

        files_with_issues.append(rel_path)
        print_file_results(template, results, show_context=True)

        while True:
            try:
                cmd = input("\n按 [Enter] 继续, [s] 跳过, [f] 标记已修复, [q] 退出: ").strip().lower()
            except EOFError:
                cmd = 'q'

            if cmd == '':
                break
            elif cmd == 's':
                skipped_files.append(rel_path)
                break
            elif cmd == 'f':
                fixed_files.append(rel_path)
                print(f"  ✓ 已标记 {rel_path} 为已修复")
                break
            elif cmd == 'q':
                print("\n" + "="*70)
                print("📊 检查总结")
                print("="*70)
                print(f"已检查: {i+1}/{len(templates)}")
                print(f"有问题: {len(files_with_issues)}")
                print(f"已修复: {len(fixed_files)}")
                print(f"已跳过: {len(skipped_files)}")
                return
            else:
                print("  无效命令，请重新输入")

    print("\n" + "="*70)
    print("📊 检查完成")
    print("="*70)
    print(f"总页面数: {len(templates)}")
    print(f"有问题数: {len(files_with_issues)}")
    print(f"已修复数: {len(fixed_files)}")
    print(f"已跳过数: {len(skipped_files)}")


def main():
    parser = argparse.ArgumentParser(description='检查模板中的翻译问题')
    parser.add_argument('--file', '-f', type=str, help='只检查指定文件')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互式逐页检查')
    parser.add_argument('--all', '-a', action='store_true', help='检查所有模板（默认只检查页面）')
    parser.add_argument('--no-context', action='store_true', help='不显示上下文')
    args = parser.parse_args()

    # 加载现有翻译
    existing_translations = load_existing_translations()
    print(f"已加载 {len(existing_translations)} 条现有翻译\n")

    # 确定要检查的文件
    if args.file:
        templates = [args.file]
    elif args.all:
        templates = glob.glob('app/templates/**/*.html', recursive=True)
    else:
        templates = []
        for pattern in ['tw_list.html', 'tw_*_detail.html', 'tw_view.html', 'tw_center.html']:
            templates.extend(glob.glob(f'app/templates/**/{pattern}', recursive=True))

    templates = sorted(templates)

    if args.interactive:
        interactive_mode(templates, existing_translations)
        return 0

    # 批量检查模式
    total_issues = 0
    for template in templates:
        results = analyze_template(template, existing_translations)
        issues = print_file_results(template, results, show_context=not args.no_context)
        total_issues += issues

    print("\n" + "="*70)
    print(f"📊 总计: {total_issues} 处问题")
    print("="*70)

    return 1 if total_issues > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
