#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
排查云端审批流程数据库问题
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('审批问题排查')

class ApprovalDebugger:
    def __init__(self):
        self.cloud_db_url = "postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs"
        
    def parse_db_url(self, db_url):
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }
    
    def connect_db(self):
        params = self.parse_db_url(self.cloud_db_url)
        return psycopg2.connect(**params)
    
    def check_approval_tables_structure(self):
        """检查审批相关表的结构"""
        logger.info("🔍 检查审批相关表结构...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        tables_to_check = ['approval_instance', 'approval_step', 'approval_record']
        
        for table in tables_to_check:
            logger.info(f"\n📋 表: {table}")
            
            # 检查表结构
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table,))
            
            columns = cursor.fetchall()
            logger.info(f"字段结构:")
            for col in columns:
                nullable = "可空" if col[2] == 'YES' else "不可空"
                default = f", 默认值: {col[3]}" if col[3] else ""
                logger.info(f"  - {col[0]}: {col[1]} ({nullable}{default})")
            
            # 检查约束
            cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            
            constraints = cursor.fetchall()
            if constraints:
                logger.info(f"约束:")
                for constraint in constraints:
                    logger.info(f"  - {constraint[0]}: {constraint[1]}")
        
        conn.close()
    
    def check_approval_instance_6(self):
        """检查审批实例6的详细信息"""
        logger.info("\n🔍 检查审批实例 ID=6 的详细信息...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查审批实例
        cursor.execute("""
            SELECT id, object_id, process_id, status, started_at, current_step
            FROM approval_instance 
            WHERE id = 6
        """)
        
        instance = cursor.fetchone()
        if instance:
            logger.info(f"📄 审批实例信息:")
            logger.info(f"  - ID: {instance[0]}")
            logger.info(f"  - 对象ID: {instance[1]}")
            logger.info(f"  - 流程ID: {instance[2]}")
            logger.info(f"  - 状态: {instance[3]}")
            logger.info(f"  - 开始时间: {instance[4]}")
            logger.info(f"  - 当前步骤: {instance[5]}")
            
            process_id = instance[2]
            current_step = instance[5]
        else:
            logger.error("❌ 未找到审批实例 ID=6")
            conn.close()
            return
        
        # 检查审批步骤
        if process_id:
            cursor.execute("""
                SELECT id, process_id, step_order, step_name, approver_user_id, approver_type
                FROM approval_step 
                WHERE process_id = %s
                ORDER BY step_order
            """, (process_id,))
            
            steps = cursor.fetchall()
            logger.info(f"\n📋 审批步骤 (流程ID: {process_id}):")
            for step in steps:
                current_marker = " <-- 当前步骤" if step[1] == current_step else ""
                logger.info(f"  - 步骤ID: {step[0]}, 顺序: {step[2]}, 名称: {step[3]}, 审批人ID: {step[4]}, 类型: {step[5]}{current_marker}")
        
        # 检查已有的审批记录
        cursor.execute("""
            SELECT id, instance_id, step_id, approver_id, action, comment, timestamp
            FROM approval_record 
            WHERE instance_id = 6
            ORDER BY timestamp
        """)
        
        records = cursor.fetchall()
        logger.info(f"\n📝 现有审批记录:")
        if records:
            for record in records:
                logger.info(f"  - 记录ID: {record[0]}, 步骤ID: {record[2]}, 审批人: {record[3]}, 操作: {record[4]}, 时间: {record[6]}")
        else:
            logger.info("  - 暂无审批记录")
        
        conn.close()
    
    def check_approval_workflow_logic(self):
        """检查审批工作流逻辑"""
        logger.info("\n🔍 检查审批工作流逻辑...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查是否有孤立的审批实例（没有对应步骤）
        cursor.execute("""
            SELECT ai.id, ai.process_id, ai.current_step, ast.id as step_exists
            FROM approval_instance ai
            LEFT JOIN approval_step ast ON ai.current_step = ast.step_order AND ai.process_id = ast.process_id
            WHERE ai.current_step IS NOT NULL
            AND ast.id IS NULL
        """)
        
        orphaned_instances = cursor.fetchall()
        if orphaned_instances:
            logger.warning("⚠️ 发现孤立的审批实例（current_step指向不存在的步骤）:")
            for instance in orphaned_instances:
                logger.warning(f"  - 实例ID: {instance[0]}, 流程ID: {instance[1]}, 当前步骤: {instance[2]}")
        
        # 检查是否有steps但没有对应process的情况  
        cursor.execute("""
            SELECT ast.id, ast.process_id, apt.id as process_exists
            FROM approval_step ast
            LEFT JOIN approval_process_template apt ON ast.process_id = apt.id
            WHERE apt.id IS NULL
        """)
        
        orphaned_steps = cursor.fetchall()
        if orphaned_steps:
            logger.warning("⚠️ 发现孤立的审批步骤（process_id指向不存在的流程）:")
            for step in orphaned_steps:
                logger.warning(f"  - 步骤ID: {step[0]}, 流程ID: {step[1]}")
        
        conn.close()
    
    def check_step_id_null_constraint(self):
        """检查step_id字段的约束设置"""
        logger.info("\n🔍 检查approval_record表step_id字段约束...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查字段约束
        cursor.execute("""
            SELECT 
                column_name,
                is_nullable,
                column_default,
                data_type
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'approval_record' 
            AND column_name = 'step_id'
        """)
        
        step_id_info = cursor.fetchone()
        if step_id_info:
            logger.info(f"📋 step_id字段信息:")
            logger.info(f"  - 字段名: {step_id_info[0]}")
            logger.info(f"  - 是否可空: {step_id_info[1]}")
            logger.info(f"  - 默认值: {step_id_info[2]}")
            logger.info(f"  - 数据类型: {step_id_info[3]}")
            
            if step_id_info[1] == 'NO':
                logger.warning("⚠️ step_id字段设置为NOT NULL，但代码尝试插入NULL值")
        
        # 检查外键约束
        cursor.execute("""
            SELECT 
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name as foreign_table_name,
                ccu.column_name as foreign_column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_schema = 'public' 
            AND tc.table_name = 'approval_record'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND kcu.column_name = 'step_id'
        """)
        
        fk_info = cursor.fetchone()
        if fk_info:
            logger.info(f"🔗 外键约束:")
            logger.info(f"  - 约束名: {fk_info[0]}")
            logger.info(f"  - 引用表: {fk_info[2]}")
            logger.info(f"  - 引用字段: {fk_info[3]}")
        
        conn.close()
    
    def check_recent_approval_failures(self):
        """检查最近的审批相关错误"""
        logger.info("\n🔍 检查最近的审批记录插入情况...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # 检查最近的审批记录
        cursor.execute("""
            SELECT 
                ar.id,
                ar.instance_id,
                ar.step_id,
                ar.approver_id,
                ar.action,
                ar.timestamp,
                ai.process_id,
                ai.current_step
            FROM approval_record ar
            JOIN approval_instance ai ON ar.instance_id = ai.id
            ORDER BY ar.timestamp DESC
            LIMIT 10
        """)
        
        recent_records = cursor.fetchall()
        logger.info(f"📝 最近10条审批记录:")
        for record in recent_records:
            step_status = "NULL" if record[2] is None else str(record[2])
            logger.info(f"  - 记录ID: {record[0]}, 实例: {record[1]}, 步骤ID: {step_status}, 审批人: {record[3]}, 操作: {record[4]}, 时间: {record[5]}")
        
        # 检查是否有step_id为NULL的记录
        cursor.execute("""
            SELECT COUNT(*) 
            FROM approval_record 
            WHERE step_id IS NULL
        """)
        
        null_step_count = cursor.fetchone()[0]
        if null_step_count > 0:
            logger.warning(f"⚠️ 发现 {null_step_count} 条step_id为NULL的审批记录")
        
        conn.close()
    
    def run_diagnosis(self):
        """运行完整的问题诊断"""
        logger.info("🚀 开始审批流程问题诊断...")
        
        try:
            self.check_approval_tables_structure()
            self.check_approval_instance_6()
            self.check_step_id_null_constraint()
            self.check_approval_workflow_logic()
            self.check_recent_approval_failures()
            
            logger.info("\n✅ 诊断完成!")
            
        except Exception as e:
            logger.error(f"❌ 诊断过程中出错: {str(e)}")

if __name__ == "__main__":
    debugger = ApprovalDebugger()
    debugger.run_diagnosis()