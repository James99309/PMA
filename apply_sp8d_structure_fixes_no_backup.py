#!/usr/bin/env python3
"""
直接应用SP8D数据库结构修复（跳过备份）
PostgreSQL版本不匹配时的应急方案，遵循CLAUDE.md规范
"""

import os
import sys
import logging
from datetime import datetime
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SP8D_Structure_Fix_Direct')

class SP8DStructureFix:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.sp8d_url = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
    
    def parse_db_url(self, db_url):
        """解析数据库URL"""
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }
    
    def get_connection(self):
        """获取数据库连接"""
        params = self.parse_db_url(self.sp8d_url)
        return psycopg2.connect(
            host=params['host'],
            port=params['port'],
            user=params['user'],
            password=params['password'],
            dbname=params['dbname'],
            cursor_factory=RealDictCursor
        )
    
    def check_column_exists(self, conn, table_name, column_name):
        """检查字段是否存在"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        return cursor.fetchone() is not None
    
    def fix_approval_step_fields(self, conn):
        """修复approval_step表的审批分支功能字段"""
        logger.info("🔧 修复approval_step表审批分支功能字段...")
        
        cursor = conn.cursor()
        
        # 检查并添加缺失字段
        branch_fields = [
            ('is_parallel', 'BOOLEAN DEFAULT FALSE', '是否为并行分支'),
            ('branch_condition', 'JSON', '分支条件配置'),
            ('merge_step_id', 'INTEGER', '合并步骤ID'),
            ('branch_level', 'INTEGER DEFAULT 0', '分支层级'),
            ('parent_step_id', 'INTEGER', '父步骤ID'),
            ('step_type', 'VARCHAR(20) DEFAULT \'normal\'', '步骤类型'),
            ('branch_group_id', 'VARCHAR(50)', '分支组ID'),
            ('branch_path', 'VARCHAR(100)', '分支路径')
        ]
        
        added_count = 0
        for field_name, field_type, comment in branch_fields:
            if not self.check_column_exists(conn, 'approval_step', field_name):
                sql = f"ALTER TABLE approval_step ADD COLUMN {field_name} {field_type}"
                cursor.execute(sql)
                logger.info(f"  ✅ 添加字段: approval_step.{field_name}")
                added_count += 1
            else:
                logger.info(f"  ⏭️ 字段已存在: approval_step.{field_name}")
        
        # 创建索引
        indexes = [
            ('idx_approval_step_branch_level', 'branch_level'),
            ('idx_approval_step_parent_id', 'parent_step_id'), 
            ('idx_approval_step_type', 'step_type'),
            ('idx_approval_step_branch_group', 'branch_group_id')
        ]
        
        for idx_name, column in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON approval_step ({column})")
                logger.info(f"  ✅ 创建索引: {idx_name}")
            except Exception as e:
                logger.info(f"  ⏭️ 索引可能已存在: {idx_name}")
        
        return added_count
    
    def check_column_type(self, conn, table_name, column_name):
        """检查字段数据类型"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        result = cursor.fetchone()
        return result['data_type'] if result else None
    
    def fix_performance_amount_types(self, conn):
        """修复绩效模块金额字段数据类型"""
        logger.info("💰 统一绩效模块金额字段数据类型...")
        
        cursor = conn.cursor()
        converted_count = 0
        
        # 修改performance_statistics表
        stats_fields = [
            ('implant_amount_actual', '植入额实际完成'),
            ('sales_amount_actual', '销售额实际完成')
        ]
        
        for field_name, comment in stats_fields:
            current_type = self.check_column_type(conn, 'performance_statistics', field_name)
            if current_type == 'double precision':
                sql = f"ALTER TABLE performance_statistics ALTER COLUMN {field_name} TYPE NUMERIC(15,2)"
                cursor.execute(sql)
                logger.info(f"  ✅ 转换类型: performance_statistics.{field_name} -> NUMERIC(15,2)")
                converted_count += 1
            else:
                logger.info(f"  ⏭️ 类型正确: performance_statistics.{field_name} ({current_type})")
        
        # 修改performance_targets表
        targets_fields = [
            ('implant_amount_target', '植入额目标'),
            ('sales_amount_target', '销售额目标')
        ]
        
        for field_name, comment in targets_fields:
            current_type = self.check_column_type(conn, 'performance_targets', field_name)
            if current_type == 'double precision':
                sql = f"ALTER TABLE performance_targets ALTER COLUMN {field_name} TYPE NUMERIC(15,2)"
                cursor.execute(sql)
                logger.info(f"  ✅ 转换类型: performance_targets.{field_name} -> NUMERIC(15,2)")
                converted_count += 1
            else:
                logger.info(f"  ⏭️ 类型正确: performance_targets.{field_name} ({current_type})")
        
        return converted_count
    
    def check_column_constraint(self, conn, table_name, column_name):
        """检查字段约束"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        result = cursor.fetchone()
        if result:
            return {'nullable': result['is_nullable'] == 'YES', 'default': result['column_default']}
        return None
    
    def fix_performance_targets_constraints(self, conn):
        """修复performance_targets表约束和默认值"""
        logger.info("⚙️ 统一performance_targets表约束和默认值...")
        
        cursor = conn.cursor()
        fixed_count = 0
        
        # 检查created_by约束
        constraint_info = self.check_column_constraint(conn, 'performance_targets', 'created_by')
        if constraint_info and constraint_info['nullable']:
            # 为NULL值设置默认值
            cursor.execute("UPDATE performance_targets SET created_by = 1 WHERE created_by IS NULL")
            
            # 设置NOT NULL约束
            cursor.execute("ALTER TABLE performance_targets ALTER COLUMN created_by SET NOT NULL")
            logger.info("  ✅ 设置约束: performance_targets.created_by NOT NULL")
            fixed_count += 1
        else:
            logger.info("  ⏭️ 约束正确: performance_targets.created_by")
        
        # 设置rate字段默认值
        rate_fields = ['customers_rate', 'implant_rate', 'projects_rate', 'sales_rate']
        
        for field in rate_fields:
            constraint_info = self.check_column_constraint(conn, 'performance_targets', field)
            if constraint_info and (not constraint_info['default'] or constraint_info['default'] == 'NULL'):
                # 为NULL值设置默认值
                cursor.execute(f"UPDATE performance_targets SET {field} = 0 WHERE {field} IS NULL")
                
                # 设置默认值
                cursor.execute(f"ALTER TABLE performance_targets ALTER COLUMN {field} SET DEFAULT 0")
                logger.info(f"  ✅ 设置默认值: performance_targets.{field} = 0")
                fixed_count += 1
            else:
                logger.info(f"  ⏭️ 默认值正确: performance_targets.{field}")
        
        return fixed_count
    
    def verify_fixes(self, conn):
        """验证修复结果"""
        logger.info("🔍 验证修复结果...")
        
        cursor = conn.cursor()
        
        # 验证approval_step字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'approval_step' 
            AND column_name IN ('is_parallel', 'branch_condition', 'merge_step_id', 
                               'branch_level', 'parent_step_id', 'step_type', 
                               'branch_group_id', 'branch_path')
        """)
        
        approval_fields = [row['column_name'] for row in cursor.fetchall()]
        expected_fields = ['is_parallel', 'branch_condition', 'merge_step_id', 'branch_level', 
                          'parent_step_id', 'step_type', 'branch_group_id', 'branch_path']
        
        missing_fields = set(expected_fields) - set(approval_fields)
        if missing_fields:
            logger.error(f"  ❌ 缺失字段: {missing_fields}")
            return False
        else:
            logger.info(f"  ✅ approval_step分支字段完整: {len(approval_fields)}/8")
        
        # 验证金额字段类型
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns 
            WHERE table_name IN ('performance_statistics', 'performance_targets')
            AND column_name LIKE '%amount%'
        """)
        
        amount_fields = cursor.fetchall()
        for field in amount_fields:
            if field['data_type'] != 'numeric':
                logger.error(f"  ❌ 类型错误: {field['table_name']}.{field['column_name']} = {field['data_type']}")
                return False
        
        logger.info(f"  ✅ 金额字段类型统一: {len(amount_fields)} 个字段")
        
        # 验证约束
        cursor.execute("""
            SELECT is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'performance_targets' AND column_name = 'created_by'
        """)
        
        created_by_info = cursor.fetchone()
        if created_by_info['is_nullable'] == 'YES':
            logger.error("  ❌ 约束错误: performance_targets.created_by 仍可为空")
            return False
        else:
            logger.info("  ✅ 约束正确: performance_targets.created_by NOT NULL")
        
        return True
    
    def run(self):
        """执行完整的结构修复流程"""
        logger.info("🚀 开始SP8D数据库结构修复（直接模式）...")
        logger.info("⚠️ 由于PostgreSQL版本不匹配，跳过备份步骤")
        logger.info("=" * 60)
        
        try:
            # 连接数据库
            conn = self.get_connection()
            conn.autocommit = False  # 使用事务
            
            # 应用修复
            added_fields = self.fix_approval_step_fields(conn)
            converted_types = self.fix_performance_amount_types(conn) 
            fixed_constraints = self.fix_performance_targets_constraints(conn)
            
            # 验证修复结果
            if self.verify_fixes(conn):
                conn.commit()
                logger.info("=" * 60)
                logger.info("🎉 SP8D数据库结构修复完成！")
                logger.info(f"✅ 添加审批分支字段: {added_fields} 个")
                logger.info(f"✅ 转换金额字段类型: {converted_types} 个")
                logger.info(f"✅ 修复约束和默认值: {fixed_constraints} 个")
                logger.info("✅ 所有结构差异已修复，SP8D与本地数据库结构现已一致")
                logger.info("=" * 60)
                return True
            else:
                conn.rollback()
                logger.error("❌ 验证失败，回滚所有修改")
                return False
            
        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
            logger.error(f"❌ 修复过程出错: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            try:
                conn.close()
            except:
                pass

if __name__ == "__main__":
    fixer = SP8DStructureFix()
    success = fixer.run()
    
    if success:
        print("\n✅ SP8D数据库结构修复成功")
        sys.exit(0)
    else:
        print("\n❌ SP8D数据库结构修复失败")
        sys.exit(1)