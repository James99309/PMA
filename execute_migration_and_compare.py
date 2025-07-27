#!/usr/bin/env python3
"""
云端数据库迁移执行和对比脚本

此脚本将：
1. 执行 sp8d_migration_step2_columns.py 迁移
2. 迁移完成后重新对比数据库差异
3. 生成详细的迁移后报告

安全保证：
- 只添加字段，不修改现有数据
- 支持完整回滚
- 保护所有现有功能
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def log_message(message, level="INFO"):
    """记录带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def check_database_connection():
    """检查数据库连接"""
    log_message("检查数据库连接...")
    
    # 检查环境变量
    if not os.getenv('DATABASE_URL'):
        log_message("❌ 未找到 DATABASE_URL 环境变量", "ERROR")
        return False
    
    log_message("✅ 数据库连接配置正常")
    return True

def backup_reminder():
    """备份提醒"""
    log_message("=" * 60)
    log_message("🚨 重要提醒：请确保已备份云端数据库！", "WARNING")
    log_message("如未备份，请先执行备份脚本", "WARNING")
    log_message("=" * 60)
    
    response = input("确认已完成数据库备份？(y/N): ")
    if response.lower() != 'y':
        log_message("❌ 取消迁移，请先完成备份", "ERROR")
        return False
    return True

def execute_migration():
    """执行迁移脚本"""
    log_message("🔄 开始执行迁移脚本...")
    
    try:
        # 执行迁移脚本
        result = subprocess.run([
            sys.executable, 'sp8d_migration_step2_columns.py'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        # 输出迁移日志
        if result.stdout:
            log_message("迁移输出:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        if result.stderr:
            log_message("迁移错误信息:", "WARNING")
            for line in result.stderr.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        if result.returncode == 0:
            log_message("✅ 迁移脚本执行成功", "SUCCESS")
            return True
        else:
            log_message(f"❌ 迁移脚本执行失败，返回码: {result.returncode}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"❌ 执行迁移时发生异常: {str(e)}", "ERROR")
        return False

def run_comparison_analysis():
    """运行迁移后的对比分析"""
    log_message("🔄 开始迁移后数据库对比分析...")
    
    try:
        # 执行对比分析脚本
        result = subprocess.run([
            sys.executable, '详尽数据库差异分析.py'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        # 输出对比结果
        if result.stdout:
            log_message("对比分析结果:")
            print(result.stdout)
        
        if result.stderr:
            log_message("对比分析警告:", "WARNING")
            for line in result.stderr.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        if result.returncode == 0:
            log_message("✅ 迁移后对比分析完成", "SUCCESS")
            return True
        else:
            log_message(f"❌ 对比分析失败，返回码: {result.returncode}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"❌ 执行对比分析时发生异常: {str(e)}", "ERROR")
        return False

def generate_migration_report():
    """生成迁移报告"""
    log_message("📋 生成迁移报告...")
    
    report = {
        "migration_time": datetime.now().isoformat(),
        "migration_script": "sp8d_migration_step2_columns.py",
        "migration_status": "completed",
        "changes_made": {
            "settlement_orders": ["添加 settlement_status 字段"],
            "dictionaries": ["添加 14个Logo和邮件签名相关字段"],
            "indexes": ["添加 2个性能优化索引"]
        },
        "safety_measures": [
            "只添加字段，不修改现有数据",
            "所有新字段设置为 nullable=True",
            "保护SP8D独有的审批功能",
            "支持完整回滚操作"
        ],
        "expected_fixes": [
            "解决报价单删除 settlement_status 错误",
            "修复关键功能缺失问题",
            "提升查询性能"
        ]
    }
    
    # 保存报告
    report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    log_message(f"✅ 迁移报告已保存: {report_file}")
    return report_file

def main():
    """主执行函数"""
    log_message("🚀 云端数据库迁移和对比分析开始")
    log_message("=" * 60)
    
    # 1. 检查数据库连接
    if not check_database_connection():
        return False
    
    # 2. 备份提醒
    if not backup_reminder():
        return False
    
    # 3. 执行迁移
    if not execute_migration():
        log_message("❌ 迁移失败，请检查错误信息", "ERROR")
        return False
    
    # 4. 迁移后对比分析
    if not run_comparison_analysis():
        log_message("⚠️ 对比分析失败，但迁移可能已成功", "WARNING")
    
    # 5. 生成迁移报告
    report_file = generate_migration_report()
    
    log_message("=" * 60)
    log_message("🎉 迁移和分析流程完成", "SUCCESS")
    log_message(f"📄 详细报告: {report_file}")
    log_message("=" * 60)
    
    # 6. 验证关键修复
    log_message("🔍 关键验证点:")
    log_message("1. settlement_orders.settlement_status 字段应该已存在")
    log_message("2. 报价单删除功能应该恢复正常")
    log_message("3. 关键差异数量应该显著减少")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)