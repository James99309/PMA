#!/usr/bin/env python3
"""
OVS数据库迁移脚本 V2.0
基于重新设计的核心基础类

使用方法:
python3 ovs_migration_v2.py

新特性:
- 真正的逐步迁移执行
- 智能合并迁移检测和处理
- 完整的数据库状态验证
- 详细的迁移路径规划
- 全面的错误处理和恢复机制
"""

import sys
import os
from database_migration_core_v2 import DatabaseMigrationCoreV2, MigrationReport

class OVSMigrationV2(DatabaseMigrationCoreV2):
    """OVS数据库迁移工具 V2.0"""
    
    def __init__(self):
        super().__init__("OVS")
        
        # OVS数据库连接配置
        self.ovs_url = "postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
        
        self.logger.info("🔧 OVS数据库迁移工具 V2.0 已初始化")
        
    def get_database_url(self) -> str:
        """返回OVS数据库连接URL"""
        return self.ovs_url

def main():
    """主函数"""
    print("🚀 开始OVS数据库迁移 V2.0...")
    print("✨ 新特性:")
    print("   • 真正的逐步迁移执行")
    print("   • 智能合并迁移处理")
    print("   • 完整的数据库验证")
    print("   • 详细的迁移规划")
    print("⚠️  禁用合并迁移，确保数据库结构完整性")
    print()
    
    try:
        # 创建迁移器
        migrator = OVSMigrationV2()
        
        # 执行完整迁移流程
        report = migrator.run_complete_migration()
        
        # 输出详细报告
        summary = migrator.generate_migration_summary(report)
        print(summary)
        
        if report.success:
            print("\n✅ OVS数据库迁移 V2.0 成功完成")
            print("🔍 所有迁移步骤已验证")
            
            # 输出状态信息
            status = migrator.get_migration_status()
            print(f"📊 当前状态:")
            print(f"   数据库版本: {status['current_revision'][:12] if status['current_revision'] else 'None'}...")
            print(f"   本地头版本: {status['local_head_revision'][:12] if status['local_head_revision'] else 'None'}...")
            print(f"   需要迁移: {'否' if not status['needs_migration'] else '是'}")
            
            sys.exit(0)
        else:
            print("\n❌ OVS数据库迁移 V2.0 失败")
            print("💾 请检查备份文件以进行恢复")
            
            # 输出失败详情
            if report.error_message:
                print(f"错误信息: {report.error_message}")
                
            if report.backup_path:
                print(f"备份文件: {report.backup_path}")
                
            # 输出失败的执行步骤
            failed_executions = [r for r in report.execution_results if not r.success]
            if failed_executions:
                print(f"\n失败的迁移步骤:")
                for result in failed_executions:
                    print(f"   • {result.migration_id[:12]}...: {result.message}")
                    
            # 输出失败的验证步骤
            failed_validations = [r for r in report.validation_results if not r.passed]
            if failed_validations:
                print(f"\n失败的验证步骤:")
                for result in failed_validations:
                    print(f"   • {result.category}.{result.check_name}: {result.message}")
            
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断迁移过程")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 迁移过程发生异常: {e}")
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()