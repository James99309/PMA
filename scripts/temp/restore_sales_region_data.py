#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从备份文件恢复销售区域编码数据
- 从最新备份文件中提取origin_location类型的字段选项
- 恢复缺失的销售区域数据到product_code_field_options表
"""
import sys
import os
import re
from datetime import datetime
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

# 备份文件路径
BACKUP_FILE = os.path.join(project_root, 'cloud_db_backups', 'pma_db_sp8d_backup_20251102_152420.sql')

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)

def extract_fields_from_backup():
    """
    从备份文件中提取product_code_fields数据

    Returns:
        list: 字段数据列表
    """
    print("📂 提取product_code_fields数据...")

    if not os.path.exists(BACKUP_FILE):
        print(f"❌ 备份文件不存在: {BACKUP_FILE}")
        return []

    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找COPY product_code_fields部分
    pattern = r'COPY public\.product_code_fields.*?FROM stdin;\n(.*?)\n\\.'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print("❌ 未找到product_code_fields数据")
        return []

    data_section = match.group(1).strip()
    lines = data_section.split('\n')

    fields = []
    for line in lines:
        if not line.strip():
            continue

        # 解析TAB分隔的字段
        parts = line.split('\t')
        if len(parts) < 11:
            continue

        field = {
            'id': int(parts[0]),
            'subcategory_id': int(parts[1]) if parts[1] != '\\N' else None,
            'name': parts[2],
            'code': parts[3],
            'description': parts[4],
            'field_type': parts[5],
            'position': int(parts[6]),
            'max_length': int(parts[7]),
            'is_required': parts[8] == 't',
            'use_in_code': parts[9] == 't',
            'created_at': parts[10],
            'updated_at': parts[11] if len(parts) > 11 else parts[10]
        }

        fields.append(field)

    print(f"   提取到 {len(fields)} 条字段数据")

    return fields

def extract_field_options_from_backup():
    """
    从备份文件中提取product_code_field_options数据

    Returns:
        list: 字段选项数据列表
    """
    print("📂 提取product_code_field_options数据...")

    if not os.path.exists(BACKUP_FILE):
        print(f"❌ 备份文件不存在: {BACKUP_FILE}")
        return []

    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找COPY product_code_field_options部分
    pattern = r'COPY public\.product_code_field_options.*?FROM stdin;(.*?)\\.'
    match = re.search(pattern, content, re.DOTALL)

    if not match:
        print("❌ 未找到product_code_field_options数据")
        return []

    data_section = match.group(1).strip()
    lines = data_section.split('\n')

    field_options = []
    for line in lines:
        if not line.strip():
            continue

        # 解析TAB分隔的字段
        parts = line.split('\t')
        if len(parts) < 9:
            continue

        option = {
            'id': int(parts[0]),
            'field_id': int(parts[1]),
            'value': parts[2],
            'code': parts[3],
            'description': parts[4],
            'is_active': parts[5] == 't',
            'position': int(parts[6]),
            'created_at': parts[7],
            'updated_at': parts[8]
        }

        field_options.append(option)

    print(f"   提取到 {len(field_options)} 条字段选项数据")

    return field_options

def get_origin_location_fields(conn):
    """获取所有origin_location类型的字段ID"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, name, subcategory_id
        FROM product_code_fields
        WHERE field_type = 'origin_location'
        ORDER BY id
    """)
    fields = cur.fetchall()
    cur.close()
    return fields

def get_current_field_options(conn, field_ids):
    """获取当前数据库中的字段选项"""
    if not field_ids:
        return []

    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, field_id, value, code, description
        FROM product_code_field_options
        WHERE field_id = ANY(%s)
        ORDER BY field_id, id
    """, (list(field_ids),))
    options = cur.fetchall()
    cur.close()
    return options

def main(auto_confirm=False):
    """主函数"""
    print_section("销售区域数据恢复工具")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if auto_confirm:
        print("⚙️  自动确认模式已启用")

    # 1. 提取备份数据
    print_section("第一步：从备份文件提取数据")
    print(f"📂 读取备份文件: {BACKUP_FILE}")

    all_fields = extract_fields_from_backup()
    all_field_options = extract_field_options_from_backup()

    if not all_fields and not all_field_options:
        print("❌ 未找到任何数据")
        return

    # 2. 连接数据库
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print(f"\n✅ 数据库连接成功")
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {str(e)}")
        sys.exit(1)

    try:
        # 3. 恢复origin_location字段
        print_section("第二步：恢复销售区域字段定义")

        # 筛选origin_location字段
        origin_fields_backup = [f for f in all_fields if f['field_type'] == 'origin_location']
        print(f"📋 备份中有 {len(origin_fields_backup)} 个销售区域字段:")
        for f in origin_fields_backup:
            print(f"   - ID={f['id']}, name={f['name']}, subcategory_id={f['subcategory_id']}")

        # 检查当前字段
        origin_fields = get_origin_location_fields(conn)
        print(f"\n📖 当前数据库中有 {len(origin_fields)} 个销售区域字段")

        if len(origin_fields) < len(origin_fields_backup):
            print(f"\n需要恢复 {len(origin_fields_backup) - len(origin_fields)} 个字段")

            if auto_confirm:
                confirm = 'yes'
                print("✅ 自动确认：是")
            else:
                confirm = input("是否恢复销售区域字段？(yes/no): ").strip().lower()

            if confirm in ['yes', 'y']:
                cur = conn.cursor()
                for field in origin_fields_backup:
                    # 检查是否已存在
                    cur.execute(
                        "SELECT id FROM product_code_fields WHERE id = %s",
                        (field['id'],)
                    )
                    if cur.fetchone():
                        print(f"   ⏭️  字段ID {field['id']} 已存在，跳过")
                        continue

                    try:
                        cur.execute("""
                            INSERT INTO product_code_fields
                            (id, subcategory_id, name, code, description, field_type, position, max_length, is_required, use_in_code, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            field['id'],
                            field['subcategory_id'],
                            field['name'],
                            field['code'],
                            field['description'],
                            field['field_type'],
                            field['position'],
                            field['max_length'],
                            field['is_required'],
                            field['use_in_code'],
                            field['created_at'],
                            field['updated_at']
                        ))
                        conn.commit()
                        print(f"   ✅ 恢复字段: {field['name']} (ID={field['id']})")
                    except Exception as e:
                        conn.rollback()
                        print(f"   ❌ 失败: {field['name']} - {str(e)}")
                cur.close()

        # 重新获取字段
        origin_fields = get_origin_location_fields(conn)

        if not origin_fields:
            print("❌ 仍然未找到origin_location类型的字段")
            return

        print(f"📋 找到 {len(origin_fields)} 个销售区域字段:")
        for field in origin_fields:
            print(f"   - ID={field['id']}, name={field['name']}, subcategory_id={field['subcategory_id']}")

        origin_field_ids = [f['id'] for f in origin_fields]

        # 4. 筛选出销售区域选项
        print_section("第三步：恢复销售区域选项数据")
        sales_region_options = [
            opt for opt in all_field_options
            if opt['field_id'] in origin_field_ids or '销售区域编码' in opt['description']
        ]

        print(f"📊 从备份中找到 {len(sales_region_options)} 个销售区域选项:")
        for opt in sales_region_options:
            print(f"   - ID={opt['id']}, field_id={opt['field_id']}, value={opt['value']}, code={opt['code']}")

        # 5. 检查当前数据
        print("\n📊 检查当前数据库状态")
        current_options = get_current_field_options(conn, origin_field_ids)

        print(f"📖 当前数据库中有 {len(current_options)} 个销售区域选项")
        if current_options:
            for opt in current_options:
                print(f"   - ID={opt['id']}, field_id={opt['field_id']}, value={opt['value']}, code={opt['code']}")
        else:
            print("   ⚠️  当前数据库中没有销售区域选项数据")

        # 6. 确定需要恢复的数据
        print("\n📋 确定恢复策略")

        current_ids = {opt['id'] for opt in current_options}
        current_field_value_pairs = {(opt['field_id'], opt['value']) for opt in current_options}

        to_restore = []
        duplicates = []

        for opt in sales_region_options:
            # 检查是否已存在相同的field_id+value组合
            if (opt['field_id'], opt['value']) in current_field_value_pairs:
                duplicates.append(opt)
            else:
                to_restore.append(opt)

        print(f"\n📋 需要恢复: {len(to_restore)} 个选项")
        print(f"⏭️  已存在（跳过）: {len(duplicates)} 个选项")

        if to_restore:
            print("\n待恢复的选项:")
            for opt in to_restore:
                print(f"   - ID={opt['id']}, field_id={opt['field_id']}, value={opt['value']}, code={opt['code']}")

        if not to_restore:
            print("\n✅ 所有销售区域选项已存在，无需恢复！")
            return

        # 7. 确认恢复
        if auto_confirm:
            confirm = 'yes'
            print(f"\n✅ 自动确认：恢复 {len(to_restore)} 个选项")
        else:
            confirm = input(f"\n是否恢复这 {len(to_restore)} 个选项？(yes/no): ").strip().lower()

        if confirm not in ['yes', 'y']:
            print("❌ 用户取消恢复")
            return

        # 8. 执行恢复
        print("\n🔧 执行数据恢复")

        cur = conn.cursor()
        restored = 0
        failed = []

        for opt in to_restore:
            try:
                # 检查ID是否冲突
                if opt['id'] in current_ids:
                    # ID冲突，使用下一个可用ID
                    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM product_code_field_options")
                    new_id = cur.fetchone()[0]
                    print(f"   ⚠️  ID {opt['id']} 冲突，使用新ID {new_id}")
                    insert_id = new_id
                else:
                    insert_id = opt['id']

                cur.execute("""
                    INSERT INTO product_code_field_options
                    (id, field_id, value, code, description, is_active, position, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    insert_id,
                    opt['field_id'],
                    opt['value'],
                    opt['code'],
                    opt['description'],
                    opt['is_active'],
                    opt['position'],
                    opt['created_at'],
                    opt['updated_at']
                ))

                conn.commit()
                restored += 1
                print(f"   ✅ 恢复: {opt['value']} (code={opt['code']}, ID={insert_id})")

            except Exception as e:
                conn.rollback()
                failed.append((opt, str(e)))
                print(f"   ❌ 失败: {opt['value']} - {str(e)}")

        cur.close()

        # 9. 生成报告
        print_section("恢复完成报告")
        print(f"\n✅ 成功恢复: {restored} 个选项")
        if failed:
            print(f"❌ 失败: {len(failed)} 个选项")
            for opt, error in failed:
                print(f"   - {opt['value']}: {error}")

        # 10. 验证结果
        print_section("第四步：验证恢复结果")
        final_options = get_current_field_options(conn, origin_field_ids)
        print(f"📊 当前数据库中共有 {len(final_options)} 个销售区域选项")

        for opt in final_options:
            print(f"   - {opt['value']} (code={opt['code']}, field_id={opt['field_id']})")

        print("\n" + "=" * 100)
        print("✅ 恢复完成！")
        print("=" * 100)

    finally:
        conn.close()
        print("\n✅ 数据库连接已关闭")

if __name__ == '__main__':
    import sys
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    main(auto_confirm=auto_confirm)
