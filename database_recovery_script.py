#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库恢复脚本
1. 备份当前云端数据
2. 恢复本地备份到云端
3. 验证数据一致性
"""

import psycopg2
import subprocess
import os
import re
from urllib.parse import urlparse
from config import CLOUD_DB_URL
from datetime import datetime

class DatabaseRecovery:
    def __init__(self):
        self.backup_file = './cloud_backup_20250613_151838.sql'
        self.recovery_backup_file = None
        self.parsed_url = urlparse(CLOUD_DB_URL)
        self.recovery_log = []
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.recovery_log.append(log_entry)
    
    def create_recovery_backup(self):
        """创建恢复前的安全备份"""
        self.log("🔒 创建恢复前安全备份...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recovery_backup_file = f"pre_recovery_backup_{timestamp}.sql"
        
        try:
            # 构建pg_dump命令
            cmd = [
                'pg_dump',
                '--host', self.parsed_url.hostname,
                '--port', str(self.parsed_url.port or 5432),
                '--username', self.parsed_url.username,
                '--dbname', self.parsed_url.path.strip('/'),
                '--no-password',
                '--verbose',
                '--file', self.recovery_backup_file
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = self.parsed_url.password
            
            # 执行备份
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                file_size = os.path.getsize(self.recovery_backup_file) / 1024 / 1024
                self.log(f"✅ 安全备份创建成功: {self.recovery_backup_file} ({file_size:.2f} MB)")
                return True
            else:
                self.log(f"❌ 安全备份失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.log(f"❌ 安全备份异常: {str(e)}")
            return False
    
    def get_table_counts_before(self):
        """获取恢复前的表记录数"""
        self.log("📊 获取恢复前数据统计...")
        
        try:
            conn = psycopg2.connect(
                host=self.parsed_url.hostname,
                port=self.parsed_url.port or 5432,
                database=self.parsed_url.path.strip('/'),
                user=self.parsed_url.username,
                password=self.parsed_url.password
            )
            
            counts_before = {}
            
            with conn.cursor() as cursor:
                # 获取所有表名
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                
                # 获取每个表的记录数
                for table_name in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        counts_before[table_name] = count
                    except Exception as e:
                        counts_before[table_name] = f"Error: {str(e)}"
            
            conn.close()
            
            total_before = sum(count for count in counts_before.values() if isinstance(count, int))
            self.log(f"📋 恢复前统计: {len(counts_before)} 个表, {total_before:,} 条记录")
            
            return counts_before
            
        except Exception as e:
            self.log(f"❌ 获取恢复前统计失败: {str(e)}")
            return {}
    
    def restore_database(self):
        """恢复数据库"""
        self.log("🔄 开始数据库恢复...")
        
        if not os.path.exists(self.backup_file):
            self.log(f"❌ 备份文件不存在: {self.backup_file}")
            return False
        
        try:
            # 构建psql命令
            cmd = [
                'psql',
                '--host', self.parsed_url.hostname,
                '--port', str(self.parsed_url.port or 5432),
                '--username', self.parsed_url.username,
                '--dbname', self.parsed_url.path.strip('/'),
                '--no-password',
                '--file', self.backup_file
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = self.parsed_url.password
            
            self.log(f"📁 恢复文件: {self.backup_file}")
            file_size = os.path.getsize(self.backup_file) / 1024 / 1024
            self.log(f"📊 文件大小: {file_size:.2f} MB")
            
            # 执行恢复
            self.log("⏳ 正在执行恢复操作...")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ 数据库恢复成功")
                return True
            else:
                # 检查是否是警告而非错误
                if "ERROR" in result.stderr:
                    self.log(f"❌ 数据库恢复失败: {result.stderr}")
                    return False
                else:
                    self.log(f"⚠️ 数据库恢复完成，有警告: {result.stderr}")
                    return True
                
        except Exception as e:
            self.log(f"❌ 数据库恢复异常: {str(e)}")
            return False
    
    def get_table_counts_after(self):
        """获取恢复后的表记录数"""
        self.log("📊 获取恢复后数据统计...")
        
        try:
            conn = psycopg2.connect(
                host=self.parsed_url.hostname,
                port=self.parsed_url.port or 5432,
                database=self.parsed_url.path.strip('/'),
                user=self.parsed_url.username,
                password=self.parsed_url.password
            )
            
            counts_after = {}
            
            with conn.cursor() as cursor:
                # 获取所有表名
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                
                # 获取每个表的记录数
                for table_name in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        counts_after[table_name] = count
                    except Exception as e:
                        counts_after[table_name] = f"Error: {str(e)}"
            
            conn.close()
            
            total_after = sum(count for count in counts_after.values() if isinstance(count, int))
            self.log(f"📋 恢复后统计: {len(counts_after)} 个表, {total_after:,} 条记录")
            
            return counts_after
            
        except Exception as e:
            self.log(f"❌ 获取恢复后统计失败: {str(e)}")
            return {}
    
    def verify_critical_data(self):
        """验证关键数据"""
        self.log("🔍 验证关键业务数据...")
        
        critical_tables = [
            'quotation_details', 'quotations', 'projects', 'companies', 
            'contacts', 'products', 'users'
        ]
        
        verification_results = {}
        
        try:
            conn = psycopg2.connect(
                host=self.parsed_url.hostname,
                port=self.parsed_url.port or 5432,
                database=self.parsed_url.path.strip('/'),
                user=self.parsed_url.username,
                password=self.parsed_url.password
            )
            
            with conn.cursor() as cursor:
                for table_name in critical_tables:
                    try:
                        # 获取记录数
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        
                        # 获取ID范围
                        cursor.execute(f"SELECT MIN(id), MAX(id) FROM {table_name}")
                        min_id, max_id = cursor.fetchone()
                        
                        # 获取最新记录时间
                        cursor.execute(f"""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name = '{table_name}' 
                            AND column_name IN ('created_at', 'updated_at')
                            LIMIT 1
                        """)
                        
                        time_column = cursor.fetchone()
                        latest_time = None
                        
                        if time_column:
                            cursor.execute(f"SELECT MAX({time_column[0]}) FROM {table_name}")
                            latest_time = cursor.fetchone()[0]
                        
                        verification_results[table_name] = {
                            'count': count,
                            'min_id': min_id,
                            'max_id': max_id,
                            'latest_time': latest_time,
                            'status': 'success'
                        }
                        
                        self.log(f"   ✅ {table_name}: {count:,} 条记录 (ID: {min_id}-{max_id})")
                        
                    except Exception as e:
                        verification_results[table_name] = {
                            'error': str(e),
                            'status': 'error'
                        }
                        self.log(f"   ❌ {table_name}: 验证失败 - {str(e)}")
            
            conn.close()
            
        except Exception as e:
            self.log(f"❌ 关键数据验证失败: {str(e)}")
        
        return verification_results
    
    def compare_with_backup_file(self):
        """与备份文件进行对比"""
        self.log("📄 与备份文件进行数据对比...")
        
        try:
            # 解析备份文件
            with open(self.backup_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取备份文件中的表数据统计
            copy_pattern = r'COPY public\.(\w+).*?FROM stdin;(.*?)\\\.'
            copy_matches = re.findall(copy_pattern, content, re.DOTALL | re.IGNORECASE)
            
            backup_counts = {}
            for table_name, data_section in copy_matches:
                lines = [line.strip() for line in data_section.split('\n') if line.strip()]
                backup_counts[table_name] = len(lines)
            
            # 获取当前云端数据统计
            current_counts = self.get_table_counts_after()
            
            # 对比结果
            comparison_results = {}
            
            all_tables = set(backup_counts.keys()) | set(current_counts.keys())
            
            for table_name in sorted(all_tables):
                backup_count = backup_counts.get(table_name, 0)
                current_count = current_counts.get(table_name, 0)
                
                if isinstance(current_count, str):  # 错误情况
                    current_count = 0
                
                difference = current_count - backup_count
                
                comparison_results[table_name] = {
                    'backup_count': backup_count,
                    'current_count': current_count,
                    'difference': difference,
                    'match': difference == 0
                }
            
            # 统计匹配情况
            total_matches = sum(1 for result in comparison_results.values() if result['match'])
            total_tables = len(comparison_results)
            
            self.log(f"📊 对比结果: {total_matches}/{total_tables} 个表完全匹配")
            
            return comparison_results
            
        except Exception as e:
            self.log(f"❌ 备份文件对比失败: {str(e)}")
            return {}
    
    def generate_recovery_report(self, counts_before, counts_after, verification_results, comparison_results):
        """生成恢复报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"DATABASE_RECOVERY_REPORT_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 数据库恢复报告\n\n")
            f.write(f"**恢复时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**备份文件**: {self.backup_file}\n")
            f.write(f"**安全备份**: {self.recovery_backup_file}\n\n")
            
            # 恢复概要
            f.write("## 📊 恢复概要\n\n")
            
            total_before = sum(count for count in counts_before.values() if isinstance(count, int))
            total_after = sum(count for count in counts_after.values() if isinstance(count, int))
            
            f.write("| 统计项 | 恢复前 | 恢复后 | 变化 |\n")
            f.write("|--------|--------|--------|------|\n")
            f.write(f"| 表数量 | {len(counts_before)} | {len(counts_after)} | {len(counts_after) - len(counts_before):+d} |\n")
            f.write(f"| 总记录数 | {total_before:,} | {total_after:,} | {total_after - total_before:+,} |\n\n")
            
            # 关键业务表验证
            f.write("## 🎯 关键业务表验证\n\n")
            f.write("| 表名 | 记录数 | ID范围 | 最新时间 | 状态 |\n")
            f.write("|------|--------|--------|----------|------|\n")
            
            for table_name, result in verification_results.items():
                if result['status'] == 'success':
                    id_range = f"{result['min_id']}-{result['max_id']}" if result['min_id'] and result['max_id'] else "N/A"
                    latest_time = str(result['latest_time'])[:19] if result['latest_time'] else "N/A"
                    f.write(f"| {table_name} | {result['count']:,} | {id_range} | {latest_time} | ✅ 成功 |\n")
                else:
                    f.write(f"| {table_name} | - | - | - | ❌ 失败 |\n")
            
            # 数据一致性对比
            f.write("\n## 🔍 数据一致性对比\n\n")
            f.write("| 表名 | 备份文件 | 恢复后 | 差异 | 状态 |\n")
            f.write("|------|----------|--------|------|------|\n")
            
            matches = 0
            for table_name, result in sorted(comparison_results.items()):
                status = "✅ 匹配" if result['match'] else "⚠️ 差异"
                if result['match']:
                    matches += 1
                
                f.write(f"| {table_name} | {result['backup_count']:,} | {result['current_count']:,} | "
                       f"{result['difference']:+,} | {status} |\n")
            
            f.write(f"\n**匹配率**: {matches}/{len(comparison_results)} ({matches/len(comparison_results)*100:.1f}%)\n")
            
            # 恢复日志
            f.write("\n## 📋 恢复日志\n\n")
            f.write("```\n")
            for log_entry in self.recovery_log:
                f.write(f"{log_entry}\n")
            f.write("```\n")
            
            # 建议
            f.write("\n## 💡 建议\n\n")
            
            if matches == len(comparison_results):
                f.write("✅ **恢复成功**: 所有表数据完全匹配，恢复操作成功完成。\n\n")
            else:
                f.write("⚠️ **需要关注**: 部分表存在数据差异，建议进一步检查。\n\n")
            
            f.write("### 后续措施\n")
            f.write("1. 验证关键业务功能是否正常\n")
            f.write("2. 建立定期备份机制\n")
            f.write("3. 实施数据监控告警\n")
            f.write("4. 考虑平台迁移计划\n")
        
        self.log(f"📄 恢复报告已生成: {report_file}")
        return report_file
    
    def run_recovery(self):
        """执行完整的恢复流程"""
        self.log("=" * 80)
        self.log("🚀 开始数据库恢复流程")
        self.log("=" * 80)
        
        # 1. 创建安全备份
        if not self.create_recovery_backup():
            self.log("❌ 安全备份失败，终止恢复流程")
            return False
        
        # 2. 获取恢复前统计
        counts_before = self.get_table_counts_before()
        
        # 3. 执行恢复
        if not self.restore_database():
            self.log("❌ 数据库恢复失败")
            return False
        
        # 4. 获取恢复后统计
        counts_after = self.get_table_counts_after()
        
        # 5. 验证关键数据
        verification_results = self.verify_critical_data()
        
        # 6. 与备份文件对比
        comparison_results = self.compare_with_backup_file()
        
        # 7. 生成报告
        report_file = self.generate_recovery_report(
            counts_before, counts_after, verification_results, comparison_results
        )
        
        self.log("=" * 80)
        self.log("✅ 数据库恢复流程完成")
        self.log("=" * 80)
        
        return True

def main():
    """主函数"""
    recovery = DatabaseRecovery()
    
    # 确认操作
    print("⚠️ 警告: 即将执行数据库恢复操作")
    print(f"📁 备份文件: {recovery.backup_file}")
    print(f"🎯 目标数据库: {recovery.parsed_url.hostname}")
    print("\n此操作将:")
    print("1. 创建当前数据库的安全备份")
    print("2. 使用本地备份文件恢复云端数据库")
    print("3. 验证恢复后的数据一致性")
    
    confirm = input("\n确认执行恢复操作? (输入 'YES' 确认): ")
    
    if confirm == 'YES':
        success = recovery.run_recovery()
        if success:
            print("\n🎉 恢复操作成功完成!")
        else:
            print("\n❌ 恢复操作失败!")
    else:
        print("❌ 恢复操作已取消")

if __name__ == "__main__":
    main()