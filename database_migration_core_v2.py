#!/usr/bin/env python3
"""
数据库迁移核心基础类 V2.0
重新设计的完整版本，整合所有迁移组件

核心特性：
1. 真正的逐步迁移执行和验证
2. 智能合并迁移检测和处理
3. 完整的数据库状态验证
4. 详细的迁移路径规划
5. 全面的错误处理和恢复机制
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from urllib.parse import urlparse
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any

# 导入新的组件
from migration_parser import MigrationParser, MigrationInfo
from stepwise_executor import StepwiseMigrationExecutor, MigrationExecutionResult
from database_validator import DatabaseValidator, ValidationResult

class MigrationPlan:
    """迁移计划"""
    def __init__(self, start_revision: str, target_revision: str, 
                 migration_path: List[str], safe_path: List[str]):
        self.start_revision = start_revision
        self.target_revision = target_revision
        self.migration_path = migration_path  # 原始路径
        self.safe_path = safe_path            # 过滤后的安全路径
        self.total_steps = len(safe_path)
        self.created_at = datetime.now()
        
    def __str__(self):
        return f"MigrationPlan({self.start_revision[:8]}... -> {self.target_revision[:8]}..., {self.total_steps} steps)"

class MigrationReport:
    """迁移报告"""
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.success = False
        self.migration_plan: Optional[MigrationPlan] = None
        self.execution_results: List[MigrationExecutionResult] = []
        self.validation_results: List[ValidationResult] = []
        self.error_message = ""
        self.backup_path = ""
        
    def mark_completed(self, success: bool, error_message: str = ""):
        """标记完成"""
        self.end_time = datetime.now()
        self.success = success
        self.error_message = error_message
        
    @property
    def duration(self) -> float:
        """获取执行时间"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

class DatabaseMigrationCoreV2(ABC):
    """数据库迁移核心基础类 V2.0"""
    
    def __init__(self, database_name: str, migrations_dir: str = None):
        self.database_name = database_name
        self.migrations_dir = migrations_dir or os.path.join(os.getcwd(), 'migrations')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 初始化日志
        self.logger = self._setup_logging()
        
        # 初始化组件
        self.parser: Optional[MigrationParser] = None
        self.executor: Optional[StepwiseMigrationExecutor] = None
        self.validator: Optional[DatabaseValidator] = None
        
        # 迁移状态
        self.current_report: Optional[MigrationReport] = None
        
        # 设置环境变量禁用自动合并
        self._setup_migration_environment()
        
    def _setup_logging(self) -> logging.Logger:
        """设置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(f'{self.database_name}MigrationV2')
        
    def _setup_migration_environment(self):
        """设置迁移环境"""
        os.environ['ALEMBIC_CONFIG_FORBID_MULTIPLE_HEADS'] = 'true'
        os.environ['FORCE_STEPWISE_MIGRATION'] = 'true'
        self.logger.info("🚫 已禁用自动合并，强制逐步升级模式")
        
    @abstractmethod
    def get_database_url(self) -> str:
        """获取数据库连接URL - 由子类实现"""
        pass
        
    def initialize_components(self):
        """初始化所有组件"""
        self.logger.info("🔧 初始化迁移组件...")
        
        # 初始化解析器
        self.parser = MigrationParser(self.migrations_dir)
        
        # 初始化执行器
        self.executor = StepwiseMigrationExecutor(
            self.get_database_url(), 
            self.database_name
        )
        
        # 初始化验证器
        self.validator = DatabaseValidator(
            self.get_database_url(),
            self.database_name
        )
        
        self.logger.info("✅ 组件初始化完成")
        
    def analyze_migrations(self) -> Dict[str, MigrationInfo]:
        """分析所有迁移文件"""
        self.logger.info("📂 分析迁移文件...")
        
        if not self.parser:
            self.initialize_components()
            
        migrations = self.parser.parse_all_migrations()
        
        # 输出分析结果
        merge_migrations = self.parser.get_merge_migrations()
        dangerous_merges = self.parser.get_dangerous_merges()
        
        if merge_migrations:
            self.logger.info(f"🔄 发现 {len(merge_migrations)} 个合并迁移")
            
        if dangerous_merges:
            self.logger.warning(f"⚠️  发现 {len(dangerous_merges)} 个危险合并迁移")
            for merge in dangerous_merges:
                self.logger.warning(f"   • {merge.revision[:8]}... - {merge.filename}")
                
        return migrations
        
    def create_migration_plan(self, target_revision: str = None) -> Optional[MigrationPlan]:
        """创建迁移计划"""
        self.logger.info("📋 创建迁移计划...")
        
        if not self.executor:
            self.initialize_components()
            
        # 获取当前版本
        current_revision = self.executor.get_current_revision()
        if not current_revision:
            self.logger.error("❌ 无法获取当前数据库版本")
            return None
            
        # 确定目标版本
        if not target_revision:
            target_revision = self._get_local_head_revision()
            
        if not target_revision:
            self.logger.error("❌ 无法确定目标版本")
            return None
            
        self.logger.info(f"迁移计划: {current_revision[:8]}... -> {target_revision[:8]}...")
        
        # 如果已经是最新版本
        if current_revision == target_revision:
            self.logger.info("✅ 已经是最新版本，无需迁移")
            return MigrationPlan(current_revision, target_revision, [], [])
            
        # 查找迁移路径
        if not self.parser:
            self.analyze_migrations()
            
        migration_path = self.parser.find_migration_path(current_revision, target_revision)
        if not migration_path:
            self.logger.error("❌ 无法找到有效的迁移路径")
            return None
            
        # 过滤安全迁移
        safe_path = self.parser.filter_safe_migrations(migration_path)
        
        plan = MigrationPlan(current_revision, target_revision, migration_path, safe_path)
        
        self.logger.info(f"✅ 迁移计划创建完成: {plan}")
        return plan
        
    def backup_database(self) -> Optional[str]:
        """备份数据库"""
        self.logger.info("💾 开始备份数据库...")
        
        backup_file = f"{self.database_name.lower()}_backup_{self.timestamp}.sql"
        backup_path = os.path.join(os.getcwd(), 'cloud_db_backups', backup_file)
        
        # 确保备份目录存在
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        try:
            parsed = urlparse(self.get_database_url())
            
            # 使用PostgreSQL 17的pg_dump
            pg_dump_path = '/opt/homebrew/opt/postgresql@17/bin/pg_dump'
            if not os.path.exists(pg_dump_path):
                pg_dump_path = 'pg_dump'  # 回退到系统默认
            
            cmd = [
                pg_dump_path,
                '--verbose', '--clean', '--if-exists',
                '--no-owner', '--no-privileges',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '-f', backup_path
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            # 更新PATH以确保使用正确版本的PostgreSQL工具
            env['PATH'] = '/opt/homebrew/opt/postgresql@17/bin:' + env.get('PATH', '')
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True, timeout=300)
            
            backup_size = os.path.getsize(backup_path)
            self.logger.info(f"✅ 备份完成: {backup_path} ({backup_size:,} 字节)")
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"❌ 备份失败: {e}")
            return None
            
    def execute_migration_plan(self, plan: MigrationPlan) -> Tuple[bool, List[MigrationExecutionResult]]:
        """执行迁移计划"""
        self.logger.info(f"⚡ 执行迁移计划: {plan}")
        
        if not self.executor:
            self.initialize_components()
            
        if not plan.safe_path:
            self.logger.info("✅ 没有需要执行的迁移")
            return True, []
            
        # 执行迁移链
        success, results = self.executor.execute_migration_chain(plan.safe_path)
        
        return success, results
        
    def validate_final_state(self, expected_revision: str) -> Dict[str, Any]:
        """验证最终状态"""
        self.logger.info(f"🔍 验证最终状态: {expected_revision[:8]}...")
        
        if not self.validator:
            self.initialize_components()
            
        # 定义关键表（可以根据需要调整）
        critical_tables = [
            'alembic_version', 'users', 'companies', 'projects', 
            'quotations', 'products', 'roles', 'permissions'
        ]
        
        # 运行完整验证
        validation_report = self.validator.run_full_validation(
            expected_version=expected_revision,
            required_tables=critical_tables
        )
        
        return validation_report
        
    def run_complete_migration(self, target_revision: str = None) -> MigrationReport:
        """运行完整迁移流程"""
        self.logger.info("=" * 60)
        self.logger.info(f"🚀 开始 {self.database_name} 数据库完整迁移流程")
        self.logger.info(f"时间戳: {self.timestamp}")
        self.logger.info("=" * 60)
        
        # 创建迁移报告
        report = MigrationReport()
        self.current_report = report
        
        try:
            # 步骤1: 初始化组件
            self.initialize_components()
            
            # 步骤2: 分析迁移文件
            self.analyze_migrations()
            
            # 步骤3: 创建迁移计划
            plan = self.create_migration_plan(target_revision)
            if not plan:
                report.mark_completed(False, "无法创建迁移计划")
                return report
                
            report.migration_plan = plan
            
            # 如果没有需要迁移的步骤
            if not plan.safe_path:
                report.mark_completed(True, "无需迁移")
                self.logger.info("🎉 数据库已是最新版本")
                return report
            
            # 步骤4: 备份数据库
            backup_path = self.backup_database()
            if not backup_path:
                report.mark_completed(False, "数据库备份失败")
                return report
                
            report.backup_path = backup_path
            
            # 步骤5: 执行迁移计划
            success, execution_results = self.execute_migration_plan(plan)
            report.execution_results = execution_results
            
            if not success:
                report.mark_completed(False, "迁移执行失败")
                self.logger.error("❌ 迁移执行失败")
                self.logger.info(f"可以使用备份文件恢复: {backup_path}")
                return report
            
            # 步骤6: 验证最终状态
            validation_report = self.validate_final_state(plan.target_revision)
            report.validation_results = self.validator.validation_results
            
            # 检查验证是否通过
            failed_validations = self.validator.get_failed_validations()
            if failed_validations:
                report.mark_completed(False, f"验证失败: {len(failed_validations)} 项检查未通过")
                self.logger.warning(f"⚠️  验证发现 {len(failed_validations)} 个问题")
                return report
            
            # 步骤7: 成功完成
            report.mark_completed(True)
            
            self.logger.info("=" * 60)
            self.logger.info(f"🎉 {self.database_name} 数据库迁移成功完成！")
            self.logger.info(f"执行时间: {report.duration:.2f}s")
            self.logger.info(f"迁移步骤: {plan.total_steps}")
            self.logger.info(f"备份文件: {backup_path}")
            self.logger.info("=" * 60)
            
            return report
            
        except Exception as e:
            self.logger.error(f"💥 迁移流程异常: {e}")
            report.mark_completed(False, f"迁移流程异常: {e}")
            return report
            
    def _get_local_head_revision(self) -> Optional[str]:
        """获取本地最新版本"""
        # 首先尝试通过解析器获取头版本
        try:
            if not self.parser:
                self.initialize_components()
                
            # 获取所有迁移文件
            migrations = self.parser.migrations
            if not migrations:
                self.logger.warning("⚠️  没有发现迁移文件")
                return None
            
            # 查找没有子依赖的迁移（即头版本）
            heads = []
            for revision, info in migrations.items():
                # 检查是否有其他迁移依赖于此迁移
                is_head = True
                for other_revision, other_info in migrations.items():
                    if other_revision == revision:
                        continue
                    # 检查down_revision
                    if isinstance(other_info.down_revision, str):
                        if other_info.down_revision == revision:
                            is_head = False
                            break
                    elif isinstance(other_info.down_revision, tuple):
                        if revision in other_info.down_revision:
                            is_head = False
                            break
                
                if is_head:
                    heads.append(revision)
            
            if len(heads) == 1:
                self.logger.info(f"📊 本地头版本: {heads[0][:12]}...")
                return heads[0]
            elif len(heads) > 1:
                # 多个头版本，尝试选择最新的（按文件修改时间）
                self.logger.warning(f"⚠️  检测到多个本地迁移头: {[h[:8] for h in heads]}")
                latest_head = max(heads, key=lambda x: migrations[x].file_path_mtime if hasattr(migrations[x], 'file_path_mtime') else 0)
                self.logger.info(f"📊 选择最新头版本: {latest_head[:12]}...")
                return latest_head
            else:
                self.logger.warning("⚠️  没有发现本地迁移头")
                return None
                
        except Exception as e:
            self.logger.error(f"通过解析器获取头版本失败: {e}")
        
        # 如果解析器方法失败，尝试Alembic命令
        try:
            env = os.environ.copy()
            env['DATABASE_URL'] = self.get_database_url()
            
            result = subprocess.run(['alembic', '-c', 'alembic_standalone.ini', 'heads'],
                                  capture_output=True, text=True, 
                                  check=True, timeout=30, env=env,
                                  cwd=os.getcwd())
            
            heads = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            
            if len(heads) == 1:
                self.logger.info(f"📊 本地头版本: {heads[0][:12]}...")
                return heads[0]
            elif len(heads) > 1:
                self.logger.error(f"❌ 检测到多个本地迁移头: {[h[:8] for h in heads]}")
                return None
            else:
                self.logger.warning("⚠️  没有发现本地迁移头")
                return None
                
        except Exception as e:
            self.logger.error(f"Alembic获取本地头版本失败: {e}")
            return None
            
    def get_migration_status(self) -> Dict[str, Any]:
        """获取迁移状态摘要"""
        if not self.executor:
            self.initialize_components()
            
        current_revision = self.executor.get_current_revision()
        local_head = self._get_local_head_revision()
        
        status = {
            'database_name': self.database_name,
            'current_revision': current_revision,
            'local_head_revision': local_head,
            'needs_migration': current_revision != local_head,
            'timestamp': datetime.now()
        }
        
        if self.current_report:
            status['last_migration'] = {
                'success': self.current_report.success,
                'duration': self.current_report.duration,
                'steps': self.current_report.migration_plan.total_steps if self.current_report.migration_plan else 0
            }
            
        return status
        
    def generate_migration_summary(self, report: MigrationReport) -> str:
        """生成迁移摘要报告"""
        summary = []
        summary.append("=" * 60)
        summary.append(f"{self.database_name} 数据库迁移报告")
        summary.append("=" * 60)
        
        # 基本信息
        summary.append(f"开始时间: {report.start_time}")
        summary.append(f"结束时间: {report.end_time}")
        summary.append(f"执行时间: {report.duration:.2f}s")
        summary.append(f"迁移结果: {'✅ 成功' if report.success else '❌ 失败'}")
        
        if report.error_message:
            summary.append(f"错误信息: {report.error_message}")
            
        # 迁移计划
        if report.migration_plan:
            plan = report.migration_plan
            summary.append(f"\n迁移计划:")
            summary.append(f"  起始版本: {plan.start_revision[:12]}...")
            summary.append(f"  目标版本: {plan.target_revision[:12]}...")
            summary.append(f"  迁移步骤: {plan.total_steps}")
            
        # 执行结果
        if report.execution_results:
            successful = sum(1 for r in report.execution_results if r.success)
            failed = len(report.execution_results) - successful
            summary.append(f"\n执行结果:")
            summary.append(f"  总步骤: {len(report.execution_results)}")
            summary.append(f"  成功: {successful}")
            summary.append(f"  失败: {failed}")
            
        # 验证结果
        if report.validation_results:
            passed = sum(1 for r in report.validation_results if r.passed)
            failed = len(report.validation_results) - passed
            summary.append(f"\n验证结果:")
            summary.append(f"  总检查: {len(report.validation_results)}")
            summary.append(f"  通过: {passed}")
            summary.append(f"  失败: {failed}")
            
        # 备份信息
        if report.backup_path:
            summary.append(f"\n备份文件: {report.backup_path}")
            
        summary.append("=" * 60)
        
        return '\n'.join(summary)