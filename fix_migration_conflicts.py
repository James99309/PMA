#!/usr/bin/env python3
"""
修复迁移冲突脚本
处理SP8D数据库中缺失索引导致的迁移失败问题
"""

import os
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FixMigration')

def fix_migration_file():
    """修复有问题的迁移文件，添加安全的索引删除逻辑"""
    
    migration_file = "/Users/nijie/Documents/PMA/migrations/versions/d1c70d1043d7_add_expense_and_department_tables.py"
    
    logger.info(f"修复迁移文件: {migration_file}")
    
    # 读取原文件
    with open(migration_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到有问题的索引删除操作
    problematic_drops = [
        "batch_op.drop_index('idx_dictionaries_company_email', postgresql_where=\"((type)::text = 'company'::text)\")",
        "batch_op.drop_index('idx_dictionaries_company_logo', postgresql_where='(logo_content IS NOT NULL)')",
        "batch_op.drop_index('idx_dictionaries_company_phone', postgresql_where=\"((type)::text = 'company'::text)\")"
    ]
    
    # 替换为安全的删除操作
    safe_drop_template = """        # 安全删除索引（如果存在）
        try:
            {original_drop}
        except Exception as e:
            # 索引不存在时忽略错误
            pass"""
    
    for drop_line in problematic_drops:
        safe_drop = safe_drop_template.format(original_drop=drop_line)
        content = content.replace(f"        {drop_line}", safe_drop)
    
    # 写回文件
    with open(migration_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info("✅ 迁移文件修复完成")
    return True

def main():
    """主函数"""
    try:
        fix_migration_file()
        logger.info("🎉 迁移冲突修复完成！")
        return True
    except Exception as e:
        logger.error(f"❌ 修复失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)