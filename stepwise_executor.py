#!/usr/bin/env python3
"""
逐步迁移执行器
负责逐步执行迁移并验证每个步骤的结果

核心功能：
1. 执行单个迁移到指定版本
2. 验证每个迁移步骤的结果
3. 支持失败时的回滚操作
4. 记录详细的执行日志
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse

class MigrationExecutionResult:
    """迁移执行结果"""
    def __init__(self, success: bool, migration_id: str, message: str = "", 
                 execution_time: float = 0.0, output: str = "", error: str = ""):
        self.success = success
        self.migration_id = migration_id
        self.message = message
        self.execution_time = execution_time
        self.output = output
        self.error = error
        self.timestamp = datetime.now()
        
    def __str__(self):
        status = "✅ 成功" if self.success else "❌ 失败"
        return f"{status} {self.migration_id[:8]}... ({self.execution_time:.2f}s)"

class DatabaseSnapshot:
    """数据库状态快照"""
    def __init__(self, revision: str, table_count: int, tables: List[str], 
                 constraints: Dict[str, int], indexes: Dict[str, int]):
        self.revision = revision
        self.table_count = table_count
        self.tables = tables
        self.constraints = constraints
        self.indexes = indexes
        self.timestamp = datetime.now()

class StepwiseMigrationExecutor:
    """逐步迁移执行器"""
    
    def __init__(self, database_url: str, database_name: str):
        self.database_url = database_url
        self.database_name = database_name
        self.logger = logging.getLogger(f'{database_name}StepwiseExecutor')
        
        # 执行历史
        self.execution_history: List[MigrationExecutionResult] = []
        self.snapshots: Dict[str, DatabaseSnapshot] = {}
        
        # 当前状态
        self.current_revision = None
        self.last_successful_revision = None
        
    def get_current_revision(self) -> Optional[str]:
        """获取当前数据库版本"""
        # 首先尝试直接数据库查询
        try:
            import psycopg2
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # 检查alembic_version表是否存在
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                );
            """)
            
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                self.logger.warning("alembic_version表不存在，数据库可能未初始化")
                cursor.close()
                conn.close()
                return None
                
            # 获取当前版本
            cursor.execute("SELECT version_num FROM alembic_version;")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                revision = result[0]
                self.current_revision = revision
                self.logger.info(f"📊 当前数据库版本: {revision[:12]}...")
                return revision
            else:
                self.logger.warning("alembic_version表为空")
                return None
                
        except Exception as e:
            self.logger.error(f"直接数据库查询失败: {e}")
            
        # 如果直接查询失败，尝试Alembic命令
        try:
            env = os.environ.copy()
            env['DATABASE_URL'] = self.database_url
            # 更新PATH以使用PostgreSQL 17
            env['PATH'] = '/opt/homebrew/opt/postgresql@17/bin:' + env.get('PATH', '')
            
            # 使用独立的alembic配置
            result = subprocess.run(['alembic', '-c', 'alembic_standalone.ini', 'current'], 
                                  capture_output=True, text=True, 
                                  check=True, env=env, timeout=30,
                                  cwd=os.getcwd())
            
            revision = result.stdout.strip()
            self.current_revision = revision
            self.logger.info(f"📊 当前数据库版本: {revision[:12]}...")
            return revision
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Alembic获取当前版本失败: {e}")
            if e.stderr:
                self.logger.error(f"错误输出: {e.stderr}")
            return None
        except subprocess.TimeoutExpired:
            self.logger.error("Alembic获取当前版本超时")
            return None
    
    def execute_single_migration(self, migration_id: str, timeout: int = 300) -> MigrationExecutionResult:
        """执行单个迁移到指定版本"""
        self.logger.info(f"🚀 执行迁移: {migration_id[:8]}...")
        
        start_time = time.time()
        
        try:
            env = os.environ.copy()
            env['DATABASE_URL'] = self.database_url
            # 更新PATH以使用PostgreSQL 17
            env['PATH'] = '/opt/homebrew/opt/postgresql@17/bin:' + env.get('PATH', '')
            
            # 使用独立的alembic配置
            cmd = ['alembic', '-c', 'alembic_standalone.ini', 'upgrade', migration_id]
            self.logger.debug(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, env=env, capture_output=True, 
                                  text=True, check=True, timeout=timeout,
                                  cwd=os.getcwd())
            
            execution_time = time.time() - start_time
            
            # 创建成功结果
            exec_result = MigrationExecutionResult(
                success=True,
                migration_id=migration_id,
                message=f"迁移成功执行",
                execution_time=execution_time,
                output=result.stdout,
                error=result.stderr
            )
            
            self.execution_history.append(exec_result)
            self.last_successful_revision = migration_id
            
            self.logger.info(f"✅ 迁移成功: {migration_id[:8]}... ({execution_time:.2f}s)")
            if result.stdout:
                self.logger.debug(f"输出: {result.stdout}")
            
            return exec_result
            
        except subprocess.CalledProcessError as e:
            execution_time = time.time() - start_time
            
            error_message = f"迁移执行失败: {e}"
            exec_result = MigrationExecutionResult(
                success=False,
                migration_id=migration_id,
                message=error_message,
                execution_time=execution_time,
                output=e.stdout if e.stdout else "",
                error=e.stderr if e.stderr else ""
            )
            
            self.execution_history.append(exec_result)
            
            self.logger.error(f"❌ 迁移失败: {migration_id[:8]}... ({execution_time:.2f}s)")
            self.logger.error(f"错误: {e}")
            if e.stdout:
                self.logger.error(f"标准输出: {e.stdout}")
            if e.stderr:
                self.logger.error(f"错误输出: {e.stderr}")
            
            return exec_result
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            
            error_message = f"迁移执行超时 (>{timeout}s)"
            exec_result = MigrationExecutionResult(
                success=False,
                migration_id=migration_id,
                message=error_message,
                execution_time=execution_time
            )
            
            self.execution_history.append(exec_result)
            self.logger.error(f"⏰ 迁移超时: {migration_id[:8]}... ({execution_time:.2f}s)")
            
            return exec_result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            error_message = f"迁移执行异常: {e}"
            exec_result = MigrationExecutionResult(
                success=False,
                migration_id=migration_id,
                message=error_message,
                execution_time=execution_time
            )
            
            self.execution_history.append(exec_result)
            self.logger.error(f"💥 迁移异常: {migration_id[:8]}... - {e}")
            
            return exec_result
    
    def verify_migration_result(self, expected_revision: str) -> bool:
        """验证迁移结果是否正确"""
        self.logger.info(f"🔍 验证迁移结果: {expected_revision[:8]}...")
        
        # 1. 检查当前数据库版本
        current = self.get_current_revision()
        if current != expected_revision:
            self.logger.error(f"❌ 版本不匹配: 预期 {expected_revision[:8]}..., 实际 {current[:8] if current else 'None'}...")
            return False
        
        # 2. 检查数据库连接是否正常
        if not self._test_database_connection():
            self.logger.error("❌ 数据库连接测试失败")
            return False
        
        # 3. 创建状态快照
        snapshot = self._create_database_snapshot(expected_revision)
        if snapshot:
            self.snapshots[expected_revision] = snapshot
            self.logger.debug(f"📸 状态快照: {snapshot.table_count} 个表")
        
        self.logger.info(f"✅ 迁移验证通过: {expected_revision[:8]}...")
        return True
    
    def execute_migration_chain(self, migration_path: List[str]) -> Tuple[bool, List[MigrationExecutionResult]]:
        """执行完整的迁移链"""
        self.logger.info(f"🔗 开始执行迁移链 ({len(migration_path)} 步)")
        
        if not migration_path:
            self.logger.info("✅ 没有需要执行的迁移")
            return True, []
        
        results = []
        successful_steps = 0
        
        # 记录起始状态
        initial_revision = self.get_current_revision()
        self.logger.info(f"起始版本: {initial_revision[:8] if initial_revision else 'None'}...")
        
        for i, migration_id in enumerate(migration_path, 1):
            self.logger.info(f"\n--- 步骤 {i}/{len(migration_path)} ---")
            
            # 执行前快照
            pre_execution_revision = self.get_current_revision()
            
            # 执行迁移
            result = self.execute_single_migration(migration_id)
            results.append(result)
            
            if not result.success:
                self.logger.error(f"💥 步骤 {i} 失败，停止执行")
                break
            
            # 验证结果
            if not self.verify_migration_result(migration_id):
                self.logger.error(f"🚨 步骤 {i} 验证失败，停止执行")
                # 创建失败结果记录
                verify_result = MigrationExecutionResult(
                    success=False,
                    migration_id=migration_id,
                    message="迁移验证失败"
                )
                results.append(verify_result)
                break
            
            successful_steps += 1
            self.logger.info(f"✅ 步骤 {i} 完成并验证通过")
        
        # 执行总结
        total_steps = len(migration_path)
        success = successful_steps == total_steps
        
        self.logger.info(f"\n{'='*60}")
        if success:
            self.logger.info(f"🎉 迁移链执行完成: {successful_steps}/{total_steps} 步成功")
        else:
            self.logger.error(f"💥 迁移链执行失败: {successful_steps}/{total_steps} 步成功")
            
        self._log_execution_summary()
        
        return success, results
    
    def rollback_to_revision(self, target_revision: str) -> bool:
        """回滚到指定版本"""
        self.logger.warning(f"🔄 尝试回滚到版本: {target_revision[:8]}...")
        
        try:
            env = os.environ.copy()
            env['DATABASE_URL'] = self.database_url
            
            cmd = ['flask', 'db', 'downgrade', target_revision]
            result = subprocess.run(cmd, env=env, capture_output=True, 
                                  text=True, check=True, timeout=300)
            
            # 验证回滚结果
            current = self.get_current_revision()
            if current == target_revision:
                self.logger.info(f"✅ 回滚成功: {target_revision[:8]}...")
                return True
            else:
                self.logger.error(f"❌ 回滚验证失败: 预期 {target_revision[:8]}..., 实际 {current[:8] if current else 'None'}...")
                return False
                
        except Exception as e:
            self.logger.error(f"💥 回滚失败: {e}")
            return False
    
    def _test_database_connection(self) -> bool:
        """测试数据库连接"""
        try:
            env = os.environ.copy()
            env['DATABASE_URL'] = self.database_url
            
            # 简单的SQL查询测试连接
            result = subprocess.run(['flask', 'db', 'current'], 
                                  capture_output=True, text=True, 
                                  check=True, env=env, timeout=10)
            return True
            
        except Exception as e:
            self.logger.debug(f"数据库连接测试失败: {e}")
            return False
    
    def _create_database_snapshot(self, revision: str) -> Optional[DatabaseSnapshot]:
        """创建数据库状态快照"""
        try:
            # 这里可以实现更详细的数据库状态检查
            # 目前返回基本快照
            return DatabaseSnapshot(
                revision=revision,
                table_count=0,  # 可以通过SQL查询获取
                tables=[],      # 可以查询所有表名
                constraints={}, # 可以查询约束信息
                indexes={}      # 可以查询索引信息
            )
        except Exception as e:
            self.logger.debug(f"创建快照失败: {e}")
            return None
    
    def get_execution_summary(self) -> Dict:
        """获取执行摘要"""
        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        failed = total - successful
        
        total_time = sum(r.execution_time for r in self.execution_history)
        
        return {
            'total_steps': total,
            'successful_steps': successful,
            'failed_steps': failed,
            'total_execution_time': total_time,
            'current_revision': self.current_revision,
            'last_successful_revision': self.last_successful_revision,
            'snapshots_count': len(self.snapshots)
        }
    
    def _log_execution_summary(self):
        """记录执行摘要"""
        summary = self.get_execution_summary()
        
        self.logger.info("📊 执行摘要:")
        self.logger.info(f"   总步骤数: {summary['total_steps']}")
        self.logger.info(f"   成功步骤: {summary['successful_steps']}")
        self.logger.info(f"   失败步骤: {summary['failed_steps']}")
        self.logger.info(f"   总执行时间: {summary['total_execution_time']:.2f}s")
        self.logger.info(f"   当前版本: {summary['current_revision'][:8] if summary['current_revision'] else 'None'}...")
        
        if summary['failed_steps'] > 0:
            self.logger.error("💥 存在失败步骤，请检查日志")
            for result in self.execution_history:
                if not result.success:
                    self.logger.error(f"   ❌ {result.migration_id[:8]}...: {result.message}")
    
    def get_failed_migrations(self) -> List[MigrationExecutionResult]:
        """获取所有失败的迁移"""
        return [r for r in self.execution_history if not r.success]
    
    def clear_history(self):
        """清空执行历史"""
        self.execution_history.clear()
        self.snapshots.clear()
        self.logger.info("🧹 执行历史已清空")