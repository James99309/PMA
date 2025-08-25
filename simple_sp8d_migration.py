#!/usr/bin/env python3
"""
简化的SP8D迁移脚本
使用V2.0安全系统，但采用已知的迁移链
"""

import sys
import os
from datetime import datetime
from database_migration_core_v2 import DatabaseMigrationCoreV2, MigrationReport

class SimplifiedSP8DMigrationV2(DatabaseMigrationCoreV2):
    """简化的SP8D数据库迁移工具 V2.0"""
    
    def __init__(self):
        super().__init__("SP8D")
        
        # SP8D数据库连接配置
        self.sp8d_url = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        
        self.logger.info("🔧 简化SP8D数据库迁移工具 V2.0 已初始化")
        
    def get_database_url(self) -> str:
        """返回SP8D数据库连接URL"""
        return self.sp8d_url
        
    def run_known_migration_chain(self) -> MigrationReport:
        """运行已知的迁移链"""
        self.logger.info("=" * 60)
        self.logger.info(f"🚀 开始 {self.database_name} 已知迁移链执行")
        self.logger.info(f"时间戳: {self.timestamp}")
        self.logger.info("=" * 60)
        
        # 创建迁移报告
        report = MigrationReport()
        self.current_report = report
        
        try:
            # 步骤1: 初始化组件
            self.initialize_components()
            
            # 步骤2: 获取当前版本
            current_revision = self.executor.get_current_revision()
            if not current_revision:
                report.mark_completed(False, "无法获取当前数据库版本")
                return report
                
            # 步骤3: 检查是否需要迁移 (期望当前版本为unify_performance_amount_types)
            expected_current = "unify_performance_amount_types"
            if not current_revision.startswith(expected_current[:8]):
                report.mark_completed(False, f"数据库版本不匹配: 期望 {expected_current[:8]}..., 实际 {current_revision[:8]}...")
                return report
                
            # 步骤4: 使用已知的迁移链 (最后一步)
            migration_chain = [
                'unify_performance_targets_constraints'
            ]
            
            self.logger.info(f"📋 执行已知迁移链: {len(migration_chain)} 步")
            for i, step in enumerate(migration_chain, 1):
                self.logger.info(f"   {i}. {step}")
            
            # 步骤5: 跳过本地备份，依赖Supabase PITR
            migration_start_time = datetime.now()
            self.logger.info(f"🕐 迁移开始时间: {migration_start_time.strftime('%Y-%m-%d %H:%M:%S')} (用于PITR恢复)")
            self.logger.info("💾 跳过本地备份，依赖Supabase自动备份和PITR功能")
            self.logger.info("📍 如需回滚，请使用Supabase PITR恢复到上述时间点")
            
            report.backup_path = f"PITR_TIME:{migration_start_time.isoformat()}"
            
            # 步骤6: 逐步执行迁移
            success, execution_results = self.executor.execute_migration_chain(migration_chain)
            report.execution_results = execution_results
            
            if not success:
                report.mark_completed(False, "迁移执行失败")
                self.logger.error("❌ 迁移执行失败")
                self.logger.info("💾 如需恢复，请使用Supabase PITR功能恢复到迁移开始时间点")
                return report
            
            # 步骤7: 验证最终状态
            final_revision = migration_chain[-1]  # unify_performance_targets_constraints
            validation_report = self.validate_final_state(final_revision)
            report.validation_results = self.validator.validation_results
            
            # 检查验证是否通过
            failed_validations = self.validator.get_failed_validations()
            if failed_validations:
                report.mark_completed(False, f"验证失败: {len(failed_validations)} 项检查未通过")
                self.logger.warning(f"⚠️  验证发现 {len(failed_validations)} 个问题")
                return report
            
            # 步骤8: 成功完成
            report.mark_completed(True)
            
            self.logger.info("=" * 60)
            self.logger.info(f"🎉 {self.database_name} 迁移链成功完成！")
            self.logger.info(f"执行时间: {report.duration:.2f}s")
            self.logger.info(f"迁移步骤: {len(migration_chain)}")
            self.logger.info(f"PITR时间点: {report.backup_path}")
            self.logger.info("=" * 60)
            
            return report
            
        except Exception as e:
            self.logger.error(f"💥 迁移流程异常: {e}")
            report.mark_completed(False, f"迁移流程异常: {e}")
            return report

def main():
    """主函数"""
    print("🚀 开始SP8D数据库迁移 V2.0 (简化版)...")
    print("✨ 特性:")
    print("   • 使用已知的安全迁移链")
    print("   • 保持V2.0所有安全特性")
    print("   • 逐步执行和验证")
    print("   • 自动备份和恢复")
    print("⚠️  仅执行预定义的安全迁移路径")
    print()
    
    try:
        # 创建迁移器
        migrator = SimplifiedSP8DMigrationV2()
        
        # 执行已知迁移链
        report = migrator.run_known_migration_chain()
        
        # 输出详细报告
        summary = migrator.generate_migration_summary(report)
        print(summary)
        
        if report.success:
            print("\n✅ SP8D数据库迁移 V2.0 成功完成")
            print("🔍 所有迁移步骤已验证")
            
            # 输出状态信息
            status = migrator.get_migration_status()
            print(f"📊 当前状态:")
            print(f"   数据库版本: {status['current_revision'][:12] if status['current_revision'] else 'None'}...")
            print(f"   需要迁移: {'否' if not status.get('needs_migration', True) else '是'}")
            
            sys.exit(0)
        else:
            print("\n❌ SP8D数据库迁移 V2.0 失败")
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
            if hasattr(report, 'validation_results'):
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