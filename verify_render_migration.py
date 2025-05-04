#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库迁移验证脚本
用于验证本地数据库和Render数据库的结构和数据是否一致

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('verify_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('验证迁移')

# 数据库连接信息
LOCAL_DB_URI = os.environ.get('LOCAL_DB_URI', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
RENDER_DB_URI = os.environ.get('RENDER_DB_URI', 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d')

def create_db_engine(db_uri):
    """创建数据库引擎"""
    try:
        engine = create_engine(db_uri)
        logger.info(f"成功创建数据库引擎")
        return engine
    except Exception as e:
        logger.error(f"创建数据库引擎失败: {e}")
        return None

def get_table_names(engine):
    """获取数据库中的所有表名"""
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        return table_names
    except Exception as e:
        logger.error(f"获取表名失败: {e}")
        return []

def get_table_row_count(engine, table_name):
    """获取表中的行数"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    except Exception as e:
        logger.error(f"获取表 {table_name} 行数失败: {e}")
        return 0

def get_table_columns(engine, table_name):
    """获取表的列信息"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return {col['name']: col['type'] for col in columns}
    except Exception as e:
        logger.error(f"获取表 {table_name} 列信息失败: {e}")
        return {}

def compare_tables(local_engine, render_engine):
    """比较两个数据库的表结构和数据量"""
    
    # 获取两个数据库的表名
    local_tables = get_table_names(local_engine)
    render_tables = get_table_names(render_engine)
    
    logger.info(f"本地数据库有 {len(local_tables)} 张表")
    logger.info(f"Render数据库有 {len(render_tables)} 张表")
    
    # 检查表名的差异
    missing_tables = set(local_tables) - set(render_tables)
    extra_tables = set(render_tables) - set(local_tables)
    
    if missing_tables:
        logger.warning(f"Render数据库缺少以下表: {', '.join(missing_tables)}")
    if extra_tables:
        logger.warning(f"Render数据库额外包含以下表: {', '.join(extra_tables)}")
    
    # 比较共有表的结构和数据量
    common_tables = set(local_tables).intersection(set(render_tables))
    
    results = []
    for table_name in sorted(common_tables):
        local_count = get_table_row_count(local_engine, table_name)
        render_count = get_table_row_count(render_engine, table_name)
        
        # 获取表结构
        local_columns = get_table_columns(local_engine, table_name)
        render_columns = get_table_columns(render_engine, table_name)
        
        # 检查列的差异
        missing_cols = set(local_columns.keys()) - set(render_columns.keys())
        extra_cols = set(render_columns.keys()) - set(local_columns.keys())
        
        # 检查列类型的差异
        type_diff_cols = []
        for col in set(local_columns.keys()).intersection(set(render_columns.keys())):
            if str(local_columns[col]) != str(render_columns[col]):
                type_diff_cols.append(col)
        
        status = "一致" if local_count == render_count and not missing_cols and not extra_cols and not type_diff_cols else "不一致"
        row_status = "✅" if local_count == render_count else "❌"
        structure_status = "✅" if not missing_cols and not extra_cols and not type_diff_cols else "❌"
        
        results.append({
            "表名": table_name,
            "本地行数": local_count,
            "Render行数": render_count,
            "行数一致": row_status,
            "结构一致": structure_status,
            "缺少列": ", ".join(missing_cols) if missing_cols else "",
            "多余列": ", ".join(extra_cols) if extra_cols else "",
            "类型不同的列": ", ".join(type_diff_cols) if type_diff_cols else "",
            "状态": status
        })
        
        logger.info(f"表 {table_name}: 本地 {local_count} 行, Render {render_count} 行, 状态: {status}")
        
        if missing_cols:
            logger.warning(f"表 {table_name} 在Render中缺少以下列: {', '.join(missing_cols)}")
        if extra_cols:
            logger.warning(f"表 {table_name} 在Render中多出以下列: {', '.join(extra_cols)}")
        if type_diff_cols:
            logger.warning(f"表 {table_name} 中以下列的类型不同: {', '.join(type_diff_cols)}")
    
    # 生成报告
    report_df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"migration_verification_report_{timestamp}.csv"
    report_df.to_csv(report_file, index=False)
    logger.info(f"验证报告已保存到 {report_file}")
    
    # 返回总体结果
    all_matched = all(r["状态"] == "一致" for r in results)
    
    return {
        "tables_compared": len(common_tables),
        "missing_tables": list(missing_tables),
        "extra_tables": list(extra_tables),
        "all_matched": all_matched,
        "details": results
    }

def verify_critical_data(local_engine, render_engine):
    """验证关键数据的一致性"""
    critical_tables = ["users", "permissions", "companies", "projects", "quotations"]
    
    for table_name in critical_tables:
        try:
            # 验证ID范围一致
            with local_engine.connect() as local_conn, render_engine.connect() as render_conn:
                local_min_id = local_conn.execute(text(f"SELECT MIN(id) FROM {table_name}")).scalar() or 0
                local_max_id = local_conn.execute(text(f"SELECT MAX(id) FROM {table_name}")).scalar() or 0
                
                render_min_id = render_conn.execute(text(f"SELECT MIN(id) FROM {table_name}")).scalar() or 0
                render_max_id = render_conn.execute(text(f"SELECT MAX(id) FROM {table_name}")).scalar() or 0
                
                if local_min_id != render_min_id or local_max_id != render_max_id:
                    logger.warning(f"表 {table_name} ID范围不一致: 本地({local_min_id}-{local_max_id}), Render({render_min_id}-{render_max_id})")
                else:
                    logger.info(f"表 {table_name} ID范围一致: ({local_min_id}-{local_max_id})")
                
                # 验证某些记录的内容一致
                if local_max_id > 0:
                    sample_id = max(1, local_max_id // 2)  # 取中间的一条记录进行验证
                    
                    # 获取列名
                    inspector = inspect(local_engine)
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    columns_str = ", ".join(columns)
                    
                    local_record = local_conn.execute(text(f"SELECT {columns_str} FROM {table_name} WHERE id = {sample_id}")).fetchone()
                    render_record = render_conn.execute(text(f"SELECT {columns_str} FROM {table_name} WHERE id = {sample_id}")).fetchone()
                    
                    if not local_record or not render_record:
                        logger.warning(f"表 {table_name} ID={sample_id} 的记录在一个或两个数据库中不存在")
                    elif local_record != render_record:
                        logger.warning(f"表 {table_name} ID={sample_id} 的记录内容不一致")
                    else:
                        logger.info(f"表 {table_name} ID={sample_id} 的记录内容一致")
        except Exception as e:
            logger.error(f"验证表 {table_name} 关键数据失败: {e}")

def main():
    """主函数"""
    logger.info("开始验证数据库迁移结果...")
    
    # 创建数据库引擎
    local_engine = create_db_engine(LOCAL_DB_URI)
    render_engine = create_db_engine(RENDER_DB_URI)
    
    if not local_engine or not render_engine:
        logger.error("无法创建数据库引擎，验证终止")
        return False
    
    # 比较表结构和数据量
    comparison_result = compare_tables(local_engine, render_engine)
    
    # 验证关键数据
    verify_critical_data(local_engine, render_engine)
    
    # 输出总结
    matched_tables = sum(1 for r in comparison_result["details"] if r["状态"] == "一致")
    total_tables = comparison_result["tables_compared"]
    
    logger.info(f"验证结果摘要: {matched_tables}/{total_tables} 个表完全一致")
    
    if comparison_result["missing_tables"]:
        logger.warning(f"Render数据库缺少 {len(comparison_result['missing_tables'])} 个表")
    
    if comparison_result["extra_tables"]:
        logger.warning(f"Render数据库多出 {len(comparison_result['extra_tables'])} 个表")
    
    if comparison_result["all_matched"]:
        logger.info("✅ 验证通过! 所有表的结构和数据量都一致")
        return True
    else:
        logger.warning("❌ 验证未通过! 某些表的结构或数据量不一致")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
# -*- coding: utf-8 -*-
"""
Render数据库迁移验证脚本
用于验证本地数据库和Render数据库的结构和数据是否一致

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('verify_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('验证迁移')

# 数据库连接信息
LOCAL_DB_URI = os.environ.get('LOCAL_DB_URI', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
RENDER_DB_URI = os.environ.get('RENDER_DB_URI', 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d')

def create_db_engine(db_uri):
    """创建数据库引擎"""
    try:
        engine = create_engine(db_uri)
        logger.info(f"成功创建数据库引擎")
        return engine
    except Exception as e:
        logger.error(f"创建数据库引擎失败: {e}")
        return None

def get_table_names(engine):
    """获取数据库中的所有表名"""
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        return table_names
    except Exception as e:
        logger.error(f"获取表名失败: {e}")
        return []

def get_table_row_count(engine, table_name):
    """获取表中的行数"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    except Exception as e:
        logger.error(f"获取表 {table_name} 行数失败: {e}")
        return 0

def get_table_columns(engine, table_name):
    """获取表的列信息"""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return {col['name']: col['type'] for col in columns}
    except Exception as e:
        logger.error(f"获取表 {table_name} 列信息失败: {e}")
        return {}

def compare_tables(local_engine, render_engine):
    """比较两个数据库的表结构和数据量"""
    
    # 获取两个数据库的表名
    local_tables = get_table_names(local_engine)
    render_tables = get_table_names(render_engine)
    
    logger.info(f"本地数据库有 {len(local_tables)} 张表")
    logger.info(f"Render数据库有 {len(render_tables)} 张表")
    
    # 检查表名的差异
    missing_tables = set(local_tables) - set(render_tables)
    extra_tables = set(render_tables) - set(local_tables)
    
    if missing_tables:
        logger.warning(f"Render数据库缺少以下表: {', '.join(missing_tables)}")
    if extra_tables:
        logger.warning(f"Render数据库额外包含以下表: {', '.join(extra_tables)}")
    
    # 比较共有表的结构和数据量
    common_tables = set(local_tables).intersection(set(render_tables))
    
    results = []
    for table_name in sorted(common_tables):
        local_count = get_table_row_count(local_engine, table_name)
        render_count = get_table_row_count(render_engine, table_name)
        
        # 获取表结构
        local_columns = get_table_columns(local_engine, table_name)
        render_columns = get_table_columns(render_engine, table_name)
        
        # 检查列的差异
        missing_cols = set(local_columns.keys()) - set(render_columns.keys())
        extra_cols = set(render_columns.keys()) - set(local_columns.keys())
        
        # 检查列类型的差异
        type_diff_cols = []
        for col in set(local_columns.keys()).intersection(set(render_columns.keys())):
            if str(local_columns[col]) != str(render_columns[col]):
                type_diff_cols.append(col)
        
        status = "一致" if local_count == render_count and not missing_cols and not extra_cols and not type_diff_cols else "不一致"
        row_status = "✅" if local_count == render_count else "❌"
        structure_status = "✅" if not missing_cols and not extra_cols and not type_diff_cols else "❌"
        
        results.append({
            "表名": table_name,
            "本地行数": local_count,
            "Render行数": render_count,
            "行数一致": row_status,
            "结构一致": structure_status,
            "缺少列": ", ".join(missing_cols) if missing_cols else "",
            "多余列": ", ".join(extra_cols) if extra_cols else "",
            "类型不同的列": ", ".join(type_diff_cols) if type_diff_cols else "",
            "状态": status
        })
        
        logger.info(f"表 {table_name}: 本地 {local_count} 行, Render {render_count} 行, 状态: {status}")
        
        if missing_cols:
            logger.warning(f"表 {table_name} 在Render中缺少以下列: {', '.join(missing_cols)}")
        if extra_cols:
            logger.warning(f"表 {table_name} 在Render中多出以下列: {', '.join(extra_cols)}")
        if type_diff_cols:
            logger.warning(f"表 {table_name} 中以下列的类型不同: {', '.join(type_diff_cols)}")
    
    # 生成报告
    report_df = pd.DataFrame(results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"migration_verification_report_{timestamp}.csv"
    report_df.to_csv(report_file, index=False)
    logger.info(f"验证报告已保存到 {report_file}")
    
    # 返回总体结果
    all_matched = all(r["状态"] == "一致" for r in results)
    
    return {
        "tables_compared": len(common_tables),
        "missing_tables": list(missing_tables),
        "extra_tables": list(extra_tables),
        "all_matched": all_matched,
        "details": results
    }

def verify_critical_data(local_engine, render_engine):
    """验证关键数据的一致性"""
    critical_tables = ["users", "permissions", "companies", "projects", "quotations"]
    
    for table_name in critical_tables:
        try:
            # 验证ID范围一致
            with local_engine.connect() as local_conn, render_engine.connect() as render_conn:
                local_min_id = local_conn.execute(text(f"SELECT MIN(id) FROM {table_name}")).scalar() or 0
                local_max_id = local_conn.execute(text(f"SELECT MAX(id) FROM {table_name}")).scalar() or 0
                
                render_min_id = render_conn.execute(text(f"SELECT MIN(id) FROM {table_name}")).scalar() or 0
                render_max_id = render_conn.execute(text(f"SELECT MAX(id) FROM {table_name}")).scalar() or 0
                
                if local_min_id != render_min_id or local_max_id != render_max_id:
                    logger.warning(f"表 {table_name} ID范围不一致: 本地({local_min_id}-{local_max_id}), Render({render_min_id}-{render_max_id})")
                else:
                    logger.info(f"表 {table_name} ID范围一致: ({local_min_id}-{local_max_id})")
                
                # 验证某些记录的内容一致
                if local_max_id > 0:
                    sample_id = max(1, local_max_id // 2)  # 取中间的一条记录进行验证
                    
                    # 获取列名
                    inspector = inspect(local_engine)
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    columns_str = ", ".join(columns)
                    
                    local_record = local_conn.execute(text(f"SELECT {columns_str} FROM {table_name} WHERE id = {sample_id}")).fetchone()
                    render_record = render_conn.execute(text(f"SELECT {columns_str} FROM {table_name} WHERE id = {sample_id}")).fetchone()
                    
                    if not local_record or not render_record:
                        logger.warning(f"表 {table_name} ID={sample_id} 的记录在一个或两个数据库中不存在")
                    elif local_record != render_record:
                        logger.warning(f"表 {table_name} ID={sample_id} 的记录内容不一致")
                    else:
                        logger.info(f"表 {table_name} ID={sample_id} 的记录内容一致")
        except Exception as e:
            logger.error(f"验证表 {table_name} 关键数据失败: {e}")

def main():
    """主函数"""
    logger.info("开始验证数据库迁移结果...")
    
    # 创建数据库引擎
    local_engine = create_db_engine(LOCAL_DB_URI)
    render_engine = create_db_engine(RENDER_DB_URI)
    
    if not local_engine or not render_engine:
        logger.error("无法创建数据库引擎，验证终止")
        return False
    
    # 比较表结构和数据量
    comparison_result = compare_tables(local_engine, render_engine)
    
    # 验证关键数据
    verify_critical_data(local_engine, render_engine)
    
    # 输出总结
    matched_tables = sum(1 for r in comparison_result["details"] if r["状态"] == "一致")
    total_tables = comparison_result["tables_compared"]
    
    logger.info(f"验证结果摘要: {matched_tables}/{total_tables} 个表完全一致")
    
    if comparison_result["missing_tables"]:
        logger.warning(f"Render数据库缺少 {len(comparison_result['missing_tables'])} 个表")
    
    if comparison_result["extra_tables"]:
        logger.warning(f"Render数据库多出 {len(comparison_result['extra_tables'])} 个表")
    
    if comparison_result["all_matched"]:
        logger.info("✅ 验证通过! 所有表的结构和数据量都一致")
        return True
    else:
        logger.warning("❌ 验证未通过! 某些表的结构或数据量不一致")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 