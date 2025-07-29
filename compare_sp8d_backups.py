#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较两次sp8d数据库备份的差异
"""

import os
import sys
import psycopg2
import logging
import subprocess
import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('备份比较工具')

class BackupComparator:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 云端数据库连接信息
        self.cloud_db_url = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
        
        # 备份文件路径
        self.backup_dir = os.path.join(os.getcwd(), 'cloud_db_backups')
        self.latest_backup_info = os.path.join(self.backup_dir, 'backup_info_20250729_235941.md')
        self.previous_backup_info = os.path.join(self.backup_dir, 'cloud_sp8d_backup_info_20250728_181337.md')
        
    def get_current_table_stats(self):
        """获取当前数据库表统计"""
        logger.info("连接云端数据库获取当前数据统计...")
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.cloud_db_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                dbname=parsed.path.lstrip('/')
            )
            cursor = conn.cursor()
            
            # 获取表行数统计
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            table_stats = {}
            total_rows = 0
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    table_stats[table_name] = count
                    total_rows += count
                except Exception as e:
                    logger.warning(f"无法获取表 {table_name} 的行数: {e}")
                    table_stats[table_name] = 0
            
            cursor.close()
            conn.close()
            
            return table_stats, total_rows
            
        except Exception as e:
            logger.error(f"获取当前数据统计失败: {str(e)}")
            return {}, 0
    
    def parse_backup_info(self, info_file):
        """解析备份信息文件中的表统计"""
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            table_stats = {}
            total_rows = 0
            
            # 查找表统计部分
            lines = content.split('\n')
            in_table_section = False
            
            for line in lines:
                if '| 表名 | 当前行数 |' in line or '| 表名 | 行数 |' in line:
                    in_table_section = True
                    continue
                
                if in_table_section and '|' in line and not line.startswith('|---'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:
                        table_name = parts[1]
                        if table_name and table_name != '表名' and not table_name.startswith('**'):
                            try:
                                row_count = int(parts[2].replace(',', ''))
                                table_stats[table_name] = row_count
                                total_rows += row_count
                            except ValueError:
                                continue
                        elif '**总计**' in table_name:
                            break
                            
            return table_stats, total_rows
            
        except Exception as e:
            logger.error(f"解析备份信息文件失败: {str(e)}")
            return {}, 0
    
    def compare_backups(self):
        """比较两次备份的差异"""
        logger.info("🔍 开始比较sp8d数据库备份...")
        
        # 获取当前数据统计（最新备份）
        logger.info("📊 获取最新备份数据统计...")
        current_stats, current_total = self.parse_backup_info(self.latest_backup_info)
        
        if not current_stats:
            logger.error("无法获取最新备份统计数据")
            return False
        
        logger.info(f"最新备份 (2025-07-29): 总行数 {current_total:,}")
        
        # 从云端直接获取当前实时数据进行验证
        logger.info("🔄 获取云端实时数据进行验证...")
        live_stats, live_total = self.get_current_table_stats()
        
        if live_stats:
            logger.info(f"云端实时数据: 总行数 {live_total:,}")
            
            # 检查备份是否最新
            if current_total == live_total:
                logger.info("✅ 备份数据与云端实时数据一致")
            else:
                logger.warning(f"⚠️  备份数据可能不是最新的，差异: {live_total - current_total} 行")
        
        # 比较文件大小差异
        backup_files = [
            ('最新备份 (2025-07-29)', '/Users/nijie/Documents/PMA/cloud_db_backups/pma_db_sp8d_backup_20250729_235941.sql'),
            ('前次备份 (2025-07-28)', '/Users/nijie/Documents/PMA/cloud_db_backups/cloud_sp8d_backup_20250728_181337.sql'),
            ('7月14日备份', '/Users/nijie/Documents/PMA/cloud_db_backups/pma_db_sp8d_backup_20250714_074549.sql')
        ]
        
        logger.info("\n📁 备份文件大小对比:")
        file_sizes = {}
        for name, filepath in backup_files:
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                size_mb = size / (1024 * 1024)
                file_sizes[name] = size
                logger.info(f"  {name}: {size_mb:.2f} MB ({size:,} bytes)")
            else:
                logger.warning(f"  {name}: 文件不存在")
        
        # 计算增长
        if len(file_sizes) >= 2:
            sizes_list = list(file_sizes.values())
            latest_size = sizes_list[0]
            previous_size = sizes_list[1] if len(sizes_list) > 1 else sizes_list[0]
            
            growth = latest_size - previous_size
            growth_percent = (growth / previous_size) * 100 if previous_size > 0 else 0
            
            logger.info(f"\n📈 数据增长分析:")
            logger.info(f"  文件大小增长: {growth / (1024*1024):.2f} MB ({growth_percent:+.1f}%)")
            
            if current_total and live_total:
                logger.info(f"  数据行数: {current_total:,} 行")
                if live_total != current_total:
                    logger.info(f"  最新行数: {live_total:,} 行")
        
        # 显示主要表的数据量
        logger.info(f"\n📊 主要表数据统计 (最新备份):")
        sorted_tables = sorted(current_stats.items(), key=lambda x: x[1], reverse=True)
        
        for table_name, row_count in sorted_tables[:10]:  # 显示前10个最大的表
            logger.info(f"  {table_name}: {row_count:,} 行")
        
        return True

if __name__ == "__main__":
    comparator = BackupComparator()
    success = comparator.compare_backups()
    
    if success:
        logger.info("🎯 备份比较完成!")
    else:
        logger.error("💥 备份比较失败!")