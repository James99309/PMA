#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将现有产品编码字段中的规格名称迁移到规格字典
- 从 ProductCodeField 和 dev_product_specs 提取唯一规格名称
- 交互式确认每个规格的添加
- 自动检测相似规格并提示
- 应用建议的单位映射
"""
import sys
import os
from datetime import datetime
from collections import defaultdict
import difflib
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()

# 加载.env文件
env_file = os.path.join(project_root, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ 错误：未找到DATABASE_URL环境变量")
    sys.exit(1)

# ============================================================================
# 配置部分
# ============================================================================

# 建议的单位映射表
SUGGESTED_UNITS = {
    # 频率类
    '频率': 'MHz',
    '频率范围': 'MHz',
    '频率响应': 'MHz',
    '工作频率': 'MHz',
    '下行频率范围': 'MHz',
    '上行频率范围': 'MHz',
    '收发频率间隔': 'MHz',

    # 功率类
    '功率': 'W',
    '输出功率': 'W',
    '最大输出功率': 'W',
    '功耗': 'W',

    # 增益/衰减类
    '增益': 'dB',
    '上下行增益': 'dB',
    '增益调节范围': 'dB',
    '增益调节步进': 'dB',
    '噪声系数': 'dB',
    '插入损耗': 'dB',
    '隔离度': 'dB',
    '上下行隔离度': 'dB',
    '带内波动': 'dB',

    # 带宽类
    '带宽': 'MHz',
    '工作带宽': 'MHz',
    '通信带宽': 'MHz',

    # 电气参数
    '阻抗': 'Ω',
    '工作电压': 'V',
    '供电': 'V',

    # 物理参数
    '尺寸': 'mm',
    '重量': 'kg',
    '长度': 'm',

    # 温度类
    '工作温度': '℃',
    '存储温度': '℃',

    # 时间类
    '时延': 'μs',

    # 距离类
    '传输距离': 'm',

    # 数量类
    '光口数量': '个',

    # 无单位（描述性）
    '驻波比': None,
    '防护等级': None,
    '接口类型': None,
    '电源类型': None,
    '插头类型': None,
    '安装方式': None,
    '双工功能': None,
    '测试规格': None,
    '防护': None,
}

# 相似规格分组（用于检测和提示）
SIMILAR_GROUPS = [
    ['频率', '频率范围', '工作频率'],
    ['功率', '输出功率', '最大输出功率'],
    ['防护', '防护等级'],
    ['带宽', '工作带宽', '通信带宽'],
    ['工作电压', '供电'],
    ['隔离度', '上下行隔离度'],
    ['增益', '上下行增益'],
]

# ============================================================================
# 工具函数
# ============================================================================

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)

def print_subsection(title):
    """打印子章节标题"""
    print("\n" + "-" * 100)
    print(f"  {title}")
    print("-" * 100)

def find_similar_specs(spec_name, existing_specs):
    """
    查找与给定规格名称相似的现有规格

    Args:
        spec_name: 要检查的规格名称
        existing_specs: 已存在的规格名称列表

    Returns:
        相似规格名称列表
    """
    similar = []

    # 1. 检查预定义的相似组
    for group in SIMILAR_GROUPS:
        if spec_name in group:
            similar.extend([s for s in group if s != spec_name and s in existing_specs])

    # 2. 使用字符串相似度检测
    for existing in existing_specs:
        if existing == spec_name:
            continue
        # 计算相似度
        ratio = difflib.SequenceMatcher(None, spec_name, existing).ratio()
        if ratio > 0.6:  # 相似度阈值
            if existing not in similar:
                similar.append(existing)

    return similar

def get_suggested_unit(spec_name):
    """获取建议的单位"""
    return SUGGESTED_UNITS.get(spec_name, '')

def collect_spec_data(conn):
    """
    收集所有规格字段数据

    Returns:
        dict: {
            'spec_name': {
                'count': 使用次数,
                'sources': ['ProductCodeField', 'dev_product_specs'],
                'field_ids': [字段ID列表] (仅ProductCodeField)
            }
        }
    """
    print_subsection("正在收集规格数据...")

    spec_data = defaultdict(lambda: {
        'count': 0,
        'sources': set(),
        'field_ids': []
    })

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. 从 ProductCodeField 收集
    print("  📊 从 product_code_fields 表收集...")
    cur.execute("""
        SELECT id, name
        FROM product_code_fields
        WHERE field_type = 'spec'
    """)
    code_fields = cur.fetchall()

    for field in code_fields:
        spec_data[field['name']]['count'] += 1
        spec_data[field['name']]['sources'].add('ProductCodeField')
        spec_data[field['name']]['field_ids'].append(field['id'])

    print(f"     找到 {len(code_fields)} 个规格字段定义")

    # 2. 从 dev_product_specs 收集
    print("  📊 从 dev_product_specs 表收集...")
    cur.execute("""
        SELECT
            field_name,
            COUNT(DISTINCT dev_product_id) as usage_count
        FROM dev_product_specs
        WHERE field_name IS NOT NULL AND field_name != ''
        GROUP BY field_name
    """)

    dev_specs = cur.fetchall()
    for row in dev_specs:
        field_name = row['field_name']
        usage_count = row['usage_count']
        spec_data[field_name]['count'] += usage_count
        spec_data[field_name]['sources'].add('dev_product_specs')

    print(f"     找到 {len(dev_specs)} 个唯一规格字段名称")

    cur.close()

    # 转换sources为列表
    for spec_name in spec_data:
        spec_data[spec_name]['sources'] = list(spec_data[spec_name]['sources'])

    return dict(spec_data)

def get_existing_specs(conn):
    """获取规格字典中已存在的规格"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, name, unit, is_active
        FROM specification_dictionary
        ORDER BY name
    """)
    specs = cur.fetchall()
    cur.close()
    return {spec['name']: spec for spec in specs}

def interactive_confirm(spec_name, spec_info, index, total, existing_specs):
    """
    交互式确认单个规格的添加

    Args:
        spec_name: 规格名称
        spec_info: 规格信息字典
        index: 当前索引（1-based）
        total: 总数
        existing_specs: 已存在的规格字典

    Returns:
        tuple: (action, final_name, final_unit)
        - action: 'add', 'skip', 'merge'
        - final_name: 最终使用的规格名称
        - final_unit: 最终使用的单位
    """
    print(f"\n{'='*80}")
    print(f"规格 #{index}/{total} (使用 {spec_info['count']} 次)")
    print(f"{'='*80}")
    print(f"📋 规格名称: {spec_name}")
    print(f"📊 数据来源: {', '.join(spec_info['sources'])}")

    # 获取建议的单位
    suggested_unit = get_suggested_unit(spec_name)
    unit_display = suggested_unit if suggested_unit else '(无单位)'
    print(f"💡 建议单位: {unit_display}")

    # 检查相似规格
    similar = find_similar_specs(spec_name, list(existing_specs.keys()))
    if similar:
        print(f"⚠️  相似规格: 已存在 {', '.join([f'「{s}」' for s in similar])}")

    # 显示选项
    print("\n选项:")
    print("  [a] 添加为新规格")
    if similar:
        print(f"  [m] 合并到已存在的规格（跳过添加）")
    print("  [e] 编辑名称/单位后添加")
    print("  [s] 跳过此规格")
    print("  [q] 退出迁移")

    while True:
        choice = input("\n您的选择: ").strip().lower()

        if choice == 'q':
            print("\n⚠️  用户选择退出迁移")
            sys.exit(0)

        elif choice == 'a':
            return ('add', spec_name, suggested_unit)

        elif choice == 'm' and similar:
            print("\n已有的相似规格:")
            for i, sim_name in enumerate(similar, 1):
                sim_spec = existing_specs[sim_name]
                print(f"  [{i}] {sim_name} (单位: {sim_spec['unit'] or '无'})")

            merge_choice = input("选择要合并到的规格编号 (或按回车取消): ").strip()
            if merge_choice.isdigit() and 1 <= int(merge_choice) <= len(similar):
                target_name = similar[int(merge_choice) - 1]
                print(f"✓ 将跳过「{spec_name}」，使用已存在的「{target_name}」")
                return ('merge', target_name, None)
            else:
                print("取消合并，请重新选择")
                continue

        elif choice == 'e':
            print(f"\n当前规格名称: {spec_name}")
            new_name = input("新的规格名称 (按回车保持不变): ").strip()
            if not new_name:
                new_name = spec_name

            print(f"当前建议单位: {unit_display}")
            new_unit = input("新的单位 (按回车使用建议单位，输入'-'表示无单位): ").strip()
            if not new_unit:
                new_unit = suggested_unit
            elif new_unit == '-':
                new_unit = None

            return ('add', new_name, new_unit)

        elif choice == 's':
            return ('skip', None, None)

        else:
            print("❌ 无效选择，请重新输入")

def add_to_dictionary(conn, spec_name, unit, is_active=True):
    """
    添加规格到字典

    Returns:
        bool: 是否成功添加
    """
    try:
        cur = conn.cursor()

        # 检查是否已存在
        cur.execute(
            "SELECT id FROM specification_dictionary WHERE name = %s",
            (spec_name,)
        )
        if cur.fetchone():
            print(f"  ⚠️  规格「{spec_name}」已存在，跳过")
            cur.close()
            return False

        # 创建新规格
        cur.execute("""
            INSERT INTO specification_dictionary (name, unit, is_active, created_at)
            VALUES (%s, %s, %s, %s)
        """, (spec_name, unit, is_active, datetime.now()))

        conn.commit()
        cur.close()

        print(f"  ✅ 成功添加: {spec_name} (单位: {unit or '无'})")
        return True

    except Exception as e:
        conn.rollback()
        print(f"  ❌ 添加失败: {str(e)}")
        return False

# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    print_section("规格字典迁移工具")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 连接数据库
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print(f"✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        sys.exit(1)

    try:
        # 1. 收集数据
        print_section("第一步：收集现有规格数据")
        spec_data = collect_spec_data(conn)

        # 按使用频率排序
        sorted_specs = sorted(spec_data.items(), key=lambda x: x[1]['count'], reverse=True)

        print(f"\n📊 统计结果:")
        print(f"   - 唯一规格名称: {len(sorted_specs)} 个")
        print(f"   - 总使用次数: {sum(s[1]['count'] for s in sorted_specs)} 次")

        # 2. 获取已存在的规格
        print_section("第二步：检查规格字典现有数据")
        existing_specs = get_existing_specs(conn)
        print(f"\n📖 规格字典中已有 {len(existing_specs)} 个规格:")
        for i, (name, spec) in enumerate(existing_specs.items(), 1):
            status = '[启用]' if spec['is_active'] else '[停用]'
            print(f"   {i:2d}. {name:20s} (单位: {spec['unit'] or '无':10s}) {status}")

        # 3. 筛选需要迁移的规格
        print_section("第三步：筛选待迁移规格")
        to_migrate = []
        already_exists = []

        for spec_name, spec_info in sorted_specs:
            if spec_name in existing_specs:
                already_exists.append(spec_name)
            else:
                to_migrate.append((spec_name, spec_info))

        print(f"\n📋 待迁移规格: {len(to_migrate)} 个")
        print(f"✅ 已在字典中: {len(already_exists)} 个")

        if already_exists:
            print(f"\n已存在的规格: {', '.join(already_exists)}")

        if not to_migrate:
            print("\n✅ 所有规格已在字典中，无需迁移！")
            return

        # 4. 确认是否继续
        print(f"\n准备迁移 {len(to_migrate)} 个规格到字典")
        confirm = input("是否继续？(yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("❌ 用户取消迁移")
            return

        # 5. 交互式迁移
        print_section("第四步：交互式迁移规格")

        stats = {
            'added': [],
            'skipped': [],
            'merged': [],
            'failed': []
        }

        for index, (spec_name, spec_info) in enumerate(to_migrate, 1):
            action, final_name, final_unit = interactive_confirm(
                spec_name,
                spec_info,
                index,
                len(to_migrate),
                existing_specs
            )

            if action == 'add':
                success = add_to_dictionary(conn, final_name, final_unit)
                if success:
                    stats['added'].append((spec_name, final_name, final_unit))
                    # 重新获取existing_specs
                    existing_specs = get_existing_specs(conn)
                else:
                    stats['failed'].append((spec_name, "添加失败"))

            elif action == 'skip':
                stats['skipped'].append((spec_name, "用户跳过"))
                print(f"  ⏭️  跳过: {spec_name}")

            elif action == 'merge':
                stats['merged'].append((spec_name, final_name))
                print(f"  🔗 合并: {spec_name} → {final_name}")

        # 6. 生成报告
        print_section("迁移完成报告")

        print(f"\n✅ 成功添加: {len(stats['added'])} 个")
        for orig_name, final_name, unit in stats['added']:
            if orig_name == final_name:
                print(f"   - {final_name} (单位: {unit or '无'})")
            else:
                print(f"   - {orig_name} → {final_name} (单位: {unit or '无'})")

        if stats['merged']:
            print(f"\n🔗 合并到已有规格: {len(stats['merged'])} 个")
            for orig_name, target_name in stats['merged']:
                print(f"   - {orig_name} → {target_name}")

        if stats['skipped']:
            print(f"\n⏭️  跳过: {len(stats['skipped'])} 个")
            for spec_name, reason in stats['skipped']:
                print(f"   - {spec_name} ({reason})")

        if stats['failed']:
            print(f"\n❌ 失败: {len(stats['failed'])} 个")
            for spec_name, reason in stats['failed']:
                print(f"   - {spec_name} ({reason})")

        # 最终统计
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM specification_dictionary")
        final_count = cur.fetchone()[0]
        cur.close()

        print(f"\n📊 规格字典最终统计:")
        print(f"   - 迁移前: {len(existing_specs)} 个")
        print(f"   - 迁移后: {final_count} 个")
        print(f"   - 新增: {final_count - len(existing_specs)} 个")

        print("\n" + "=" * 100)
        print("✅ 迁移完成！")
        print("=" * 100)

    finally:
        conn.close()
        print("\n✅ 数据库连接已关闭")

if __name__ == '__main__':
    main()
