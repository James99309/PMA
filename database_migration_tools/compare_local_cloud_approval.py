#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比本地和云端审批相关表结构差异
分析为什么本地正常但云端报错
"""

import psycopg2
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('本地云端对比')

class LocalCloudComparison:
    def __init__(self):
        self.local_db_url = "postgresql://nijie@localhost:5432/pma_local"
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
    
    def connect_db(self, db_url):
        params = self.parse_db_url(db_url)
        return psycopg2.connect(**params)
    
    def get_approval_record_constraints(self, db_url, db_name):
        """获取approval_record表的约束信息"""
        logger.info(f"🔍 检查{db_name}数据库 approval_record 表约束...")
        
        conn = self.connect_db(db_url)
        cursor = conn.cursor()
        
        # 检查step_id字段约束
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
        
        # 检查所有约束
        cursor.execute("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'public' AND table_name = 'approval_record'
        """)
        constraints = cursor.fetchall()
        
        # 检查外键约束详情
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
        """)
        fk_constraints = cursor.fetchall()
        
        conn.close()
        
        return {
            'step_id_info': step_id_info,
            'constraints': constraints,
            'foreign_keys': fk_constraints
        }
    
    def get_approval_data_sample(self, db_url, db_name):
        """获取审批相关数据样本"""
        logger.info(f"🔍 检查{db_name}数据库审批数据...")
        
        conn = self.connect_db(db_url)
        cursor = conn.cursor()
        
        # 检查approval_record中是否有NULL的step_id
        cursor.execute("""
            SELECT COUNT(*) as total_records,
                   COUNT(step_id) as non_null_step_id,
                   COUNT(*) - COUNT(step_id) as null_step_id
            FROM approval_record
        """)
        record_stats = cursor.fetchone()
        
        # 检查最近的审批记录
        cursor.execute("""
            SELECT id, instance_id, step_id, approver_id, action, timestamp
            FROM approval_record
            ORDER BY timestamp DESC
            LIMIT 5
        """)
        recent_records = cursor.fetchall()
        
        # 检查approval_instance和approval_step的关联
        cursor.execute("""
            SELECT 
                ai.id as instance_id,
                ai.current_step,
                ai.process_id,
                ast.id as step_id,
                ast.step_order,
                ast.step_name
            FROM approval_instance ai
            LEFT JOIN approval_step ast ON ai.process_id = ast.process_id 
                AND ai.current_step = ast.step_order
            WHERE ai.id <= 10
            ORDER BY ai.id
        """)
        instance_step_mapping = cursor.fetchall()
        
        conn.close()
        
        return {
            'record_stats': record_stats,
            'recent_records': recent_records,
            'instance_step_mapping': instance_step_mapping
        }
    
    def compare_databases(self):
        """对比本地和云端数据库"""
        logger.info("🚀 开始对比本地和云端数据库差异...")
        
        try:
            # 获取本地数据库信息
            logger.info("\n" + "="*50)
            logger.info("📋 本地数据库分析")
            logger.info("="*50)
            
            local_constraints = self.get_approval_record_constraints(self.local_db_url, "本地")
            local_data = self.get_approval_data_sample(self.local_db_url, "本地")
            
            # 获取云端数据库信息
            logger.info("\n" + "="*50)
            logger.info("📋 云端数据库分析")
            logger.info("="*50)
            
            cloud_constraints = self.get_approval_record_constraints(self.cloud_db_url, "云端")
            cloud_data = self.get_approval_data_sample(self.cloud_db_url, "云端")
            
            # 对比约束差异
            logger.info("\n" + "="*50)
            logger.info("🔍 约束对比分析")
            logger.info("="*50)
            
            self.compare_constraints(local_constraints, cloud_constraints)
            
            # 对比数据差异
            logger.info("\n" + "="*50)
            logger.info("📊 数据对比分析")
            logger.info("="*50)
            
            self.compare_data(local_data, cloud_data)
            
            # 问题分析
            logger.info("\n" + "="*50)
            logger.info("🚨 问题根因分析")
            logger.info("="*50)
            
            self.analyze_root_cause(local_constraints, cloud_constraints, local_data, cloud_data)
            
        except Exception as e:
            logger.error(f"❌ 对比过程中出错: {str(e)}")
    
    def compare_constraints(self, local_constraints, cloud_constraints):
        """对比约束差异"""
        local_step_id = local_constraints['step_id_info']
        cloud_step_id = cloud_constraints['step_id_info']
        
        logger.info("🔍 step_id字段约束对比:")
        logger.info(f"本地数据库:")
        if local_step_id:
            logger.info(f"  - 是否可空: {local_step_id[1]}")
            logger.info(f"  - 数据类型: {local_step_id[3]}")
            logger.info(f"  - 默认值: {local_step_id[2]}")
        else:
            logger.warning("  - ❌ 未找到step_id字段")
            
        logger.info(f"云端数据库:")
        if cloud_step_id:
            logger.info(f"  - 是否可空: {cloud_step_id[1]}")
            logger.info(f"  - 数据类型: {cloud_step_id[3]}")
            logger.info(f"  - 默认值: {cloud_step_id[2]}")
        else:
            logger.warning("  - ❌ 未找到step_id字段")
        
        # 对比是否有差异
        if local_step_id and cloud_step_id:
            if local_step_id[1] != cloud_step_id[1]:
                logger.warning(f"⚠️ 发现差异: 本地可空性={local_step_id[1]}, 云端可空性={cloud_step_id[1]}")
            else:
                logger.info("✅ step_id字段约束一致")
        
        # 对比外键约束
        local_fks = {fk[1]: fk for fk in local_constraints['foreign_keys']}
        cloud_fks = {fk[1]: fk for fk in cloud_constraints['foreign_keys']}
        
        logger.info("\n🔗 外键约束对比:")
        for col in ['step_id']:
            if col in local_fks and col in cloud_fks:
                local_fk = local_fks[col]
                cloud_fk = cloud_fks[col]
                if local_fk[2:] == cloud_fk[2:]:  # 比较引用表和字段
                    logger.info(f"✅ {col}外键约束一致: {local_fk[2]}.{local_fk[3]}")
                else:
                    logger.warning(f"⚠️ {col}外键约束不同: 本地={local_fk[2]}.{local_fk[3]}, 云端={cloud_fk[2]}.{cloud_fk[3]}")
            elif col in local_fks:
                logger.warning(f"⚠️ {col}外键约束仅存在于本地")
            elif col in cloud_fks:
                logger.warning(f"⚠️ {col}外键约束仅存在于云端")
    
    def compare_data(self, local_data, cloud_data):
        """对比数据差异"""
        local_stats = local_data['record_stats']
        cloud_stats = cloud_data['record_stats']
        
        logger.info("📊 approval_record表数据统计:")
        logger.info(f"本地数据库:")
        logger.info(f"  - 总记录数: {local_stats[0]}")
        logger.info(f"  - step_id非空记录: {local_stats[1]}")
        logger.info(f"  - step_id为空记录: {local_stats[2]}")
        
        logger.info(f"云端数据库:")
        logger.info(f"  - 总记录数: {cloud_stats[0]}")
        logger.info(f"  - step_id非空记录: {cloud_stats[1]}")
        logger.info(f"  - step_id为空记录: {cloud_stats[2]}")
        
        # 关键发现
        if local_stats[2] > 0 and cloud_stats[2] == 0:
            logger.warning("⚠️ 关键发现: 本地有NULL step_id记录，但云端没有")
        elif local_stats[2] == 0 and cloud_stats[2] > 0:
            logger.warning("⚠️ 关键发现: 云端有NULL step_id记录，但本地没有")
        elif local_stats[2] > 0 and cloud_stats[2] > 0:
            logger.info("📋 两边都有NULL step_id记录")
        else:
            logger.info("✅ 两边都没有NULL step_id记录")
        
        # 对比instance-step映射
        logger.info("\n🔗 审批实例-步骤映射对比:")
        logger.info("本地数据库前5个实例:")
        for mapping in local_data['instance_step_mapping'][:5]:
            step_status = "有效" if mapping[3] is not None else "❌无效"
            logger.info(f"  - 实例{mapping[0]}: 当前步骤{mapping[1]} -> 步骤ID{mapping[3]} ({step_status})")
        
        logger.info("云端数据库前5个实例:")
        for mapping in cloud_data['instance_step_mapping'][:5]:
            step_status = "有效" if mapping[3] is not None else "❌无效"
            logger.info(f"  - 实例{mapping[0]}: 当前步骤{mapping[1]} -> 步骤ID{mapping[3]} ({step_status})")
    
    def analyze_root_cause(self, local_constraints, cloud_constraints, local_data, cloud_data):
        """分析问题根因"""
        local_step_id = local_constraints['step_id_info']
        cloud_step_id = cloud_constraints['step_id_info']
        local_stats = local_data['record_stats']
        cloud_stats = cloud_data['record_stats']
        
        logger.info("🚨 问题根因分析:")
        
        # 1. 约束差异分析
        if local_step_id and cloud_step_id:
            if local_step_id[1] == 'YES' and cloud_step_id[1] == 'NO':
                logger.error("❌ 根因1: 约束不一致")
                logger.error("   本地数据库允许step_id为NULL，但云端数据库不允许")
                logger.error("   这是数据库结构同步问题!")
                return
            elif local_step_id[1] == 'NO' and cloud_step_id[1] == 'NO':
                logger.info("✅ 约束一致: 两边都不允许step_id为NULL")
            else:
                logger.warning("⚠️ 约束配置需要检查")
        
        # 2. 数据差异分析
        if local_stats[2] > 0:
            logger.warning("⚠️ 本地数据库有NULL step_id记录，但能正常运行")
            logger.warning("   可能原因: 本地代码版本不同，或者本地约束被禁用")
        
        # 3. 最终结论
        logger.info("\n🎯 最终结论:")
        if local_step_id and cloud_step_id and local_step_id[1] != cloud_step_id[1]:
            logger.error("💥 主要原因: 数据库约束不一致")
            logger.error("   - 在数据库结构同步时，约束设置不同")
            logger.error("   - 需要统一约束设置或修复代码逻辑")
        else:
            logger.error("💥 主要原因: 代码逻辑问题")
            logger.error("   - 相同的代码在不同环境表现不同")
            logger.error("   - 可能的原因:")
            logger.error("     1. 环境配置不同")
            logger.error("     2. 数据状态不同") 
            logger.error("     3. 代码版本不同")
            logger.error("     4. 依赖库版本不同")

if __name__ == "__main__":
    comparator = LocalCloudComparison()
    comparator.compare_databases()