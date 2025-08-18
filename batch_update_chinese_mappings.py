#!/usr/bin/env python3
"""
批量更新数据库中的中文映射
补全data_field_config表中缺失的中文字段映射
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text
from app.utils.table_chinese_mapping import get_table_chinese_name, get_all_table_mappings
from app.utils.field_chinese_mapping import get_field_chinese_name, get_all_field_mappings

def batch_update_chinese_mappings():
    """批量更新中文映射"""
    app = create_app()
    
    with app.app_context():
        print("🔧 开始批量更新中文映射")
        print("=" * 60)
        
        # 1. 更新表名映射
        update_table_mappings()
        
        # 2. 更新字段名映射
        update_field_mappings()
        
        # 3. 添加缺失的表配置
        add_missing_table_configs()
        
        # 4. 生成映射覆盖率报告
        generate_mapping_coverage_report()
        
        print("\n🎉 批量更新完成！")

def update_table_mappings():
    """更新表名映射"""
    print("\n📊 1. 更新表名映射...")
    
    try:
        # 获取所有表映射
        table_mappings = get_all_table_mappings()
        
        updated_count = 0
        for table_name, chinese_name in table_mappings.items():
            # 检查表是否存在于配置中
            query = text("""
                SELECT id, display_name 
                FROM data_table_config 
                WHERE table_name = :table_name
            """)
            result = db.session.execute(query, {'table_name': table_name})
            row = result.fetchone()
            
            if row:
                # 如果显示名称是英文，更新为中文
                if not _has_chinese_chars(row.display_name):
                    update_query = text("""
                        UPDATE data_table_config 
                        SET display_name = :chinese_name,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """)
                    db.session.execute(update_query, {
                        'chinese_name': chinese_name,
                        'id': row.id
                    })
                    print(f"   ✓ 更新表名: {table_name} -> {chinese_name}")
                    updated_count += 1
            else:
                # 检查表是否在数据库中存在
                check_table_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                """)
                table_exists = db.session.execute(check_table_query, {'table_name': table_name}).fetchone()
                
                if table_exists:
                    print(f"   📝 表 {table_name} 存在但未配置，建议添加到配置表中")
        
        db.session.commit()
        print(f"   ✓ 成功更新 {updated_count} 个表名映射")
        
    except Exception as e:
        db.session.rollback()
        print(f"   ❌ 更新表名映射失败: {e}")

def update_field_mappings():
    """更新字段名映射"""
    print("\n📋 2. 更新字段名映射...")
    
    try:
        # 获取所有配置的字段
        query = text("""
            SELECT 
                dfc.id,
                dfc.field_name,
                dfc.display_name,
                dtc.table_name
            FROM data_field_config dfc
            JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
            WHERE dtc.is_active = true
            ORDER BY dtc.table_name, dfc.field_name
        """)
        
        result = db.session.execute(query)
        updated_count = 0
        
        for row in result:
            field_id = row.id
            field_name = row.field_name
            current_display_name = row.display_name
            table_name = row.table_name
            
            # 如果当前显示名称是英文，尝试获取中文映射
            if not _has_chinese_chars(current_display_name):
                chinese_name = get_field_chinese_name(field_name)
                
                # 如果找到了不同的中文映射，进行更新
                if chinese_name != field_name and chinese_name != current_display_name:
                    update_query = text("""
                        UPDATE data_field_config 
                        SET display_name = :chinese_name,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """)
                    db.session.execute(update_query, {
                        'chinese_name': chinese_name,
                        'id': field_id
                    })
                    print(f"   ✓ 更新字段: {table_name}.{field_name} -> {chinese_name}")
                    updated_count += 1
        
        db.session.commit()
        print(f"   ✓ 成功更新 {updated_count} 个字段名映射")
        
    except Exception as e:
        db.session.rollback()
        print(f"   ❌ 更新字段名映射失败: {e}")

def add_missing_table_configs():
    """添加缺失的重要表配置"""
    print("\n🔧 3. 添加缺失的重要表配置...")
    
    # 重要的业务表列表
    important_tables = [
        'departments', 'purchase_orders', 'inventory', 'actions',
        'affiliations', 'approval_instance', 'approval_step', 'change_logs'
    ]
    
    try:
        added_count = 0
        for table_name in important_tables:
            # 检查表是否存在于数据库中
            check_table_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            """)
            table_exists = db.session.execute(check_table_query, {'table_name': table_name}).fetchone()
            
            if not table_exists:
                continue
            
            # 检查是否已配置
            config_query = text("""
                SELECT id FROM data_table_config 
                WHERE table_name = :table_name
            """)
            config_exists = db.session.execute(config_query, {'table_name': table_name}).fetchone()
            
            if not config_exists:
                # 添加表配置
                chinese_name = get_table_chinese_name(table_name)
                insert_query = text("""
                    INSERT INTO data_table_config 
                    (table_name, display_name, is_active, created_at)
                    VALUES (:table_name, :display_name, true, CURRENT_TIMESTAMP)
                """)
                db.session.execute(insert_query, {
                    'table_name': table_name,
                    'display_name': chinese_name
                })
                print(f"   ✓ 添加表配置: {table_name} -> {chinese_name}")
                added_count += 1
        
        db.session.commit()
        print(f"   ✓ 成功添加 {added_count} 个表配置")
        
    except Exception as e:
        db.session.rollback()
        print(f"   ❌ 添加表配置失败: {e}")

def generate_mapping_coverage_report():
    """生成映射覆盖率报告"""
    print("\n📊 4. 生成映射覆盖率报告...")
    
    try:
        # 统计表映射覆盖率
        table_stats_query = text("""
            SELECT 
                COUNT(*) as total_tables,
                COUNT(CASE WHEN dtc.table_name IS NOT NULL THEN 1 END) as configured_tables
            FROM (
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE '%_seq'
            ) all_tables
            LEFT JOIN data_table_config dtc ON all_tables.table_name = dtc.table_name
        """)
        
        table_result = db.session.execute(table_stats_query).fetchone()
        
        # 统计字段映射覆盖率
        field_stats_query = text("""
            SELECT 
                dtc.table_name,
                dtc.display_name,
                COUNT(dfc.id) as total_fields,
                COUNT(CASE WHEN dfc.display_name ~ '[一-龟]' THEN 1 END) as chinese_fields,
                COUNT(CASE WHEN dfc.display_name !~ '[一-龟]' THEN 1 END) as english_fields
            FROM data_table_config dtc
            LEFT JOIN data_field_config dfc ON dtc.id = dfc.table_config_id
            WHERE dtc.is_active = true
            GROUP BY dtc.table_name, dtc.display_name
            ORDER BY dtc.table_name
        """)
        
        field_results = db.session.execute(field_stats_query).fetchall()
        
        print(f"\n📊 映射覆盖率报告:")
        print(f"   表配置覆盖率: {table_result.configured_tables}/{table_result.total_tables} " +
              f"({table_result.configured_tables/table_result.total_tables*100:.1f}%)")
        
        print(f"\n📋 各表字段中文化情况:")
        for row in field_results:
            if row.total_fields > 0:
                chinese_rate = row.chinese_fields / row.total_fields * 100
                print(f"   {row.table_name} ({row.display_name}): " +
                      f"{row.chinese_fields}/{row.total_fields} ({chinese_rate:.1f}%)")
        
    except Exception as e:
        print(f"   ❌ 生成报告失败: {e}")

def _has_chinese_chars(text):
    """检查文本是否包含中文字符"""
    if not text:
        return False
    return any('\u4e00' <= char <= '\u9fff' for char in text)

if __name__ == "__main__":
    batch_update_chinese_mappings()