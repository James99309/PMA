#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查云端数据库大小和邮件备份可行性分析
"""

import psycopg2
import subprocess
import os
import gzip
import tempfile
from urllib.parse import urlparse
from config import CLOUD_DB_URL
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSizeAnalyzer:
    """数据库大小分析器"""
    
    def __init__(self):
        self.db_config = self._parse_database_url(CLOUD_DB_URL)
        
    def _parse_database_url(self, database_url):
        """解析数据库URL"""
        parsed = urlparse(database_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'username': parsed.username,
            'password': parsed.password,
            'database': parsed.path.strip('/')
        }
    
    def get_database_size_info(self):
        """获取数据库大小信息"""
        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password']
            )
            
            with conn.cursor() as cursor:
                # 获取数据库总大小
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size,
                           pg_database_size(current_database()) as db_size_bytes
                """)
                db_size_pretty, db_size_bytes = cursor.fetchone()
                
                # 获取各表的大小
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                        pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)
                
                table_sizes = cursor.fetchall()
                
                # 获取记录数统计
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                
                record_counts = {}
                total_records = 0
                
                for table_name in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        record_counts[table_name] = count
                        total_records += count
                    except Exception as e:
                        record_counts[table_name] = f"Error: {str(e)}"
            
            conn.close()
            
            return {
                'db_size_pretty': db_size_pretty,
                'db_size_bytes': db_size_bytes,
                'db_size_mb': db_size_bytes / (1024 * 1024),
                'table_sizes': table_sizes,
                'record_counts': record_counts,
                'total_records': total_records
            }
            
        except Exception as e:
            logger.error(f"获取数据库大小信息失败: {str(e)}")
            return None
    
    def create_test_backup(self):
        """创建测试备份以评估实际大小"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            # 创建临时备份文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                backup_path = temp_file.name
            
            logger.info("创建测试备份...")
            
            # 构建pg_dump命令
            cmd = [
                'pg_dump',
                '--host', self.db_config['host'],
                '--port', str(self.db_config['port']),
                '--username', self.db_config['username'],
                '--no-password',
                '--format', 'plain',
                '--clean',
                '--create',
                '--encoding', 'UTF8',
                self.db_config['database']
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            # 执行备份
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)
            
            if result.returncode != 0:
                logger.error(f"备份创建失败: {result.stderr}")
                return None
            
            # 获取原始备份文件大小
            original_size = os.path.getsize(backup_path)
            
            # 创建压缩版本
            compressed_path = backup_path + '.gz'
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            compressed_size = os.path.getsize(compressed_path)
            
            # 清理临时文件
            os.remove(backup_path)
            os.remove(compressed_path)
            
            return {
                'original_size_bytes': original_size,
                'original_size_mb': original_size / (1024 * 1024),
                'compressed_size_bytes': compressed_size,
                'compressed_size_mb': compressed_size / (1024 * 1024),
                'compression_ratio': compressed_size / original_size if original_size > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"创建测试备份失败: {str(e)}")
            return None
    
    def analyze_email_backup_feasibility(self, db_info, backup_info):
        """分析邮件备份可行性"""
        
        # 邮件附件大小限制
        email_limits = {
            'gmail': 25,      # Gmail: 25MB
            'outlook': 20,    # Outlook: 20MB
            'yahoo': 25,      # Yahoo: 25MB
            'general': 20     # 一般邮件服务器: 20MB
        }
        
        analysis = {
            'database_size_mb': db_info['db_size_mb'],
            'backup_original_mb': backup_info['original_size_mb'] if backup_info else 0,
            'backup_compressed_mb': backup_info['compressed_size_mb'] if backup_info else 0,
            'compression_ratio': backup_info['compression_ratio'] if backup_info else 0,
            'email_feasible': {},
            'recommendations': []
        }
        
        if backup_info:
            compressed_size_mb = backup_info['compressed_size_mb']
            
            # 检查各邮件服务的可行性
            for service, limit in email_limits.items():
                analysis['email_feasible'][service] = {
                    'limit_mb': limit,
                    'feasible': compressed_size_mb <= limit,
                    'size_ratio': compressed_size_mb / limit
                }
            
            # 生成建议
            if compressed_size_mb <= 20:
                analysis['recommendations'].append("✅ 邮件备份完全可行，所有主流邮件服务都支持")
            elif compressed_size_mb <= 25:
                analysis['recommendations'].append("⚠️ 邮件备份基本可行，但需要选择支持25MB的邮件服务（如Gmail）")
            else:
                analysis['recommendations'].append("❌ 邮件备份不可行，需要考虑其他方案")
                analysis['recommendations'].append("💡 建议使用云存储（AWS S3、阿里云OSS）或GitHub私有仓库")
        
        return analysis
    
    def generate_backup_strategy_report(self, db_info, backup_info, analysis):
        """生成备份策略报告"""
        
        report = f"""
# 📊 PMA数据库备份策略分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🗄️ 数据库规模分析

### 总体规模
- **数据库大小**: {db_info['db_size_pretty']} ({db_info['db_size_mb']:.2f} MB)
- **总记录数**: {db_info['total_records']:,} 条
- **表数量**: {len(db_info['table_sizes'])} 个

### 主要数据表大小
"""
        
        # 添加表大小信息
        for schema, table, size, size_bytes, table_size, index_size in db_info['table_sizes'][:10]:
            record_count = db_info['record_counts'].get(table, 'N/A')
            report += f"- **{table}**: {size} ({record_count:,} 条记录)\n"
        
        if backup_info:
            report += f"""
## 📦 备份文件大小分析

### 备份文件规格
- **原始SQL文件**: {backup_info['original_size_mb']:.2f} MB
- **压缩后大小**: {backup_info['compressed_size_mb']:.2f} MB
- **压缩比**: {backup_info['compression_ratio']:.1%}

## 📧 邮件备份可行性分析

### 各邮件服务支持情况
"""
            
            for service, info in analysis['email_feasible'].items():
                status = "✅ 支持" if info['feasible'] else "❌ 超限"
                report += f"- **{service.title()}** (限制{info['limit_mb']}MB): {status} (占用{info['size_ratio']:.1%})\n"
            
            report += f"""
### 📋 备份策略建议

"""
            for recommendation in analysis['recommendations']:
                report += f"{recommendation}\n"
        
        report += f"""
## ⏰ 邮件备份发送逻辑

### 当前配置
- **备份时间**: 每天凌晨 00:00 (可配置)
- **增量备份**: 每6小时执行一次
- **邮件发送**: 备份完成后立即发送
- **接收邮箱**: James.ni@evertacsolutions.com, james98980566@gmail.com

### 发送流程
1. **创建备份**: 使用pg_dump生成SQL文件
2. **文件压缩**: 使用gzip压缩减少大小
3. **大小检查**: 验证是否超过邮件附件限制
4. **邮件发送**: 通过SMTP发送到指定邮箱
5. **本地清理**: 删除临时备份文件

### 时间安排优化建议
- **完整备份**: 凌晨2:00 (避开业务高峰)
- **增量备份**: 每8小时 (减少频率)
- **邮件发送**: 仅完整备份发送邮件
- **本地保留**: 保留最近3天的备份文件

## 🔄 备份方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 📧 邮件备份 | 简单可靠、自动发送 | 大小限制、依赖邮件服务 | 小型数据库(<20MB) |
| 📁 GitHub备份 | 版本控制、免费 | 需要配置、100MB限制 | 中型数据库(<100MB) |
| ☁️ 云存储备份 | 无大小限制、高可靠 | 需要付费、配置复杂 | 大型数据库(>100MB) |
| 💾 本地备份 | 速度快、无限制 | 容易丢失、需要手动管理 | 开发测试环境 |

## 💡 最终建议

基于当前数据库规模分析，推荐采用**混合备份策略**：

1. **主要方案**: {"邮件备份" if backup_info and backup_info['compressed_size_mb'] <= 20 else "GitHub备份"}
2. **备用方案**: 云存储备份（长期归档）
3. **应急方案**: 手动下载备份

这样可以确保数据安全的同时，兼顾成本和便利性。
"""
        
        return report

def main():
    """主函数"""
    print("🔍 开始分析云端数据库大小和邮件备份可行性...")
    print("=" * 60)
    
    analyzer = DatabaseSizeAnalyzer()
    
    # 1. 获取数据库大小信息
    print("📊 获取数据库大小信息...")
    db_info = analyzer.get_database_size_info()
    
    if not db_info:
        print("❌ 无法获取数据库信息")
        return
    
    print(f"✅ 数据库大小: {db_info['db_size_pretty']} ({db_info['db_size_mb']:.2f} MB)")
    print(f"📋 总记录数: {db_info['total_records']:,} 条")
    
    # 2. 创建测试备份
    print("\n📦 创建测试备份评估实际大小...")
    backup_info = analyzer.create_test_backup()
    
    if backup_info:
        print(f"✅ 原始备份: {backup_info['original_size_mb']:.2f} MB")
        print(f"✅ 压缩备份: {backup_info['compressed_size_mb']:.2f} MB")
        print(f"📊 压缩比: {backup_info['compression_ratio']:.1%}")
    else:
        print("❌ 无法创建测试备份")
    
    # 3. 分析邮件备份可行性
    print("\n📧 分析邮件备份可行性...")
    analysis = analyzer.analyze_email_backup_feasibility(db_info, backup_info)
    
    if backup_info:
        compressed_size = backup_info['compressed_size_mb']
        if compressed_size <= 20:
            print("✅ 邮件备份完全可行！")
        elif compressed_size <= 25:
            print("⚠️ 邮件备份基本可行，需要选择合适的邮件服务")
        else:
            print("❌ 邮件备份不可行，建议使用其他方案")
    
    # 4. 生成详细报告
    print("\n📄 生成详细分析报告...")
    report = analyzer.generate_backup_strategy_report(db_info, backup_info, analysis)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"DATABASE_BACKUP_ANALYSIS_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已生成: {report_file}")
    
    # 5. 显示关键结论
    print("\n🎯 关键结论:")
    for recommendation in analysis['recommendations']:
        print(f"  {recommendation}")

if __name__ == "__main__":
    main() 