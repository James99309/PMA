#!/usr/bin/env python3
"""
数据库验证器
负责验证数据库状态、完整性检查和迁移结果验证

核心功能：
1. 验证数据库schema是否符合预期版本
2. 检查数据完整性和约束
3. 验证迁移后的数据库结构
4. 提供详细的验证报告
"""

import os
import sys
import subprocess
import logging
import psycopg2
from typing import Dict, List, Set, Optional, Tuple, Any
from urllib.parse import urlparse
from datetime import datetime

class ValidationResult:
    """验证结果"""
    def __init__(self, category: str, check_name: str, passed: bool, 
                 message: str = "", details: Dict = None):
        self.category = category
        self.check_name = check_name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
        
    def __str__(self):
        status = "✅" if self.passed else "❌"
        return f"{status} {self.category}.{self.check_name}: {self.message}"

class DatabaseInfo:
    """数据库信息结构"""
    def __init__(self):
        self.version: Optional[str] = None
        self.table_count: int = 0
        self.tables: Set[str] = set()
        self.columns: Dict[str, List[str]] = {}
        self.indexes: Dict[str, List[str]] = {}
        self.constraints: Dict[str, List[str]] = {}
        self.foreign_keys: List[Dict] = []
        self.sequences: List[str] = []

class DatabaseValidator:
    """数据库验证器"""
    
    def __init__(self, database_url: str, database_name: str):
        self.database_url = database_url
        self.database_name = database_name
        self.logger = logging.getLogger(f'{database_name}DatabaseValidator')
        
        # 解析数据库连接信息
        self.parsed_url = urlparse(database_url)
        
        # 验证结果
        self.validation_results: List[ValidationResult] = []
        self.current_db_info: Optional[DatabaseInfo] = None
        
    def validate_migration_version(self, expected_version: str) -> ValidationResult:
        """验证迁移版本是否正确"""
        self.logger.info(f"🔍 验证迁移版本: {expected_version[:8]}...")
        
        try:
            # 方法1: 使用flask db current
            current_version = self._get_flask_db_current()
            
            if current_version == expected_version:
                result = ValidationResult(
                    category="version",
                    check_name="migration_version",
                    passed=True,
                    message=f"版本匹配: {expected_version[:8]}..."
                )
            else:
                result = ValidationResult(
                    category="version", 
                    check_name="migration_version",
                    passed=False,
                    message=f"版本不匹配: 期望 {expected_version[:8]}..., 实际 {current_version[:8] if current_version else 'None'}...",
                    details={
                        'expected': expected_version,
                        'actual': current_version
                    }
                )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            result = ValidationResult(
                category="version",
                check_name="migration_version", 
                passed=False,
                message=f"版本检查失败: {e}"
            )
            self.validation_results.append(result)
            return result
    
    def validate_database_connection(self) -> ValidationResult:
        """验证数据库连接"""
        self.logger.info("🔗 验证数据库连接...")
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # 简单查询测试连接
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            result = ValidationResult(
                category="connection",
                check_name="basic_connection",
                passed=True,
                message="数据库连接正常",
                details={'db_version': db_version}
            )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            result = ValidationResult(
                category="connection",
                check_name="basic_connection",
                passed=False,
                message=f"连接失败: {e}"
            )
            self.validation_results.append(result)
            return result
    
    def validate_alembic_version_table(self) -> ValidationResult:
        """验证alembic_version表是否存在且正确"""
        self.logger.info("📋 验证alembic_version表...")
        
        try:
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
                result = ValidationResult(
                    category="schema",
                    check_name="alembic_version_table",
                    passed=False,
                    message="alembic_version表不存在"
                )
            else:
                # 检查表结构和数据
                cursor.execute("SELECT version_num FROM alembic_version;")
                versions = cursor.fetchall()
                
                if len(versions) == 1:
                    current_version = versions[0][0]
                    result = ValidationResult(
                        category="schema",
                        check_name="alembic_version_table",
                        passed=True,
                        message=f"alembic_version表正常: {current_version[:8]}...",
                        details={'current_version': current_version}
                    )
                else:
                    result = ValidationResult(
                        category="schema",
                        check_name="alembic_version_table",
                        passed=False,
                        message=f"alembic_version表数据异常: {len(versions)} 条记录"
                    )
            
            cursor.close()
            conn.close()
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            result = ValidationResult(
                category="schema",
                check_name="alembic_version_table",
                passed=False,
                message=f"检查alembic_version表失败: {e}"
            )
            self.validation_results.append(result)
            return result
    
    def collect_database_info(self) -> DatabaseInfo:
        """收集数据库信息"""
        self.logger.info("📊 收集数据库信息...")
        
        db_info = DatabaseInfo()
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # 获取版本信息
            try:
                cursor.execute("SELECT version_num FROM alembic_version;")
                db_info.version = cursor.fetchone()[0]
            except:
                pass
            
            # 获取表信息
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            db_info.tables = {table[0] for table in tables}
            db_info.table_count = len(db_info.tables)
            
            # 获取每个表的列信息
            for table_name in db_info.tables:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cursor.fetchall()
                db_info.columns[table_name] = [
                    f"{col[0]} ({col[1]}, {'NULL' if col[2] == 'YES' else 'NOT NULL'})"
                    for col in columns
                ]
            
            # 获取索引信息
            cursor.execute("""
                SELECT schemaname, tablename, indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            
            indexes = cursor.fetchall()
            for schema, table, index in indexes:
                if table not in db_info.indexes:
                    db_info.indexes[table] = []
                db_info.indexes[table].append(index)
            
            # 获取外键约束信息
            cursor.execute("""
                SELECT
                    tc.table_name, 
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema='public';
            """)
            
            fkeys = cursor.fetchall()
            db_info.foreign_keys = [
                {
                    'table': fk[0],
                    'column': fk[1], 
                    'ref_table': fk[2],
                    'ref_column': fk[3]
                }
                for fk in fkeys
            ]
            
            cursor.close()
            conn.close()
            
            self.current_db_info = db_info
            self.logger.info(f"✅ 数据库信息收集完成: {db_info.table_count} 个表")
            
            return db_info
            
        except Exception as e:
            self.logger.error(f"❌ 收集数据库信息失败: {e}")
            return db_info
    
    def validate_data_integrity(self) -> List[ValidationResult]:
        """验证数据完整性"""
        self.logger.info("🔍 验证数据完整性...")
        
        results = []
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            if not self.current_db_info:
                self.collect_database_info()
            
            # 检查外键约束
            for fk in self.current_db_info.foreign_keys:
                try:
                    # 检查是否有违反外键约束的数据
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM {fk['table']} t1
                        LEFT JOIN {fk['ref_table']} t2 ON t1.{fk['column']} = t2.{fk['ref_column']}
                        WHERE t1.{fk['column']} IS NOT NULL AND t2.{fk['ref_column']} IS NULL;
                    """)
                    
                    violation_count = cursor.fetchone()[0]
                    
                    if violation_count == 0:
                        result = ValidationResult(
                            category="integrity",
                            check_name=f"foreign_key_{fk['table']}_{fk['column']}",
                            passed=True,
                            message=f"外键约束正常: {fk['table']}.{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}"
                        )
                    else:
                        result = ValidationResult(
                            category="integrity",
                            check_name=f"foreign_key_{fk['table']}_{fk['column']}",
                            passed=False,
                            message=f"外键约束违规: {violation_count} 条记录",
                            details=fk
                        )
                    
                    results.append(result)
                    
                except Exception as e:
                    result = ValidationResult(
                        category="integrity",
                        check_name=f"foreign_key_{fk['table']}_{fk['column']}",
                        passed=False,
                        message=f"外键检查失败: {e}"
                    )
                    results.append(result)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            result = ValidationResult(
                category="integrity", 
                check_name="data_integrity_check",
                passed=False,
                message=f"数据完整性检查失败: {e}"
            )
            results.append(result)
        
        self.validation_results.extend(results)
        self.logger.info(f"✅ 数据完整性检查完成: {len(results)} 项检查")
        
        return results
    
    def validate_critical_tables(self, required_tables: List[str]) -> ValidationResult:
        """验证关键表是否存在"""
        self.logger.info(f"📋 验证关键表 ({len(required_tables)} 个)...")
        
        if not self.current_db_info:
            self.collect_database_info()
        
        missing_tables = []
        for table in required_tables:
            if table not in self.current_db_info.tables:
                missing_tables.append(table)
        
        if not missing_tables:
            result = ValidationResult(
                category="schema",
                check_name="critical_tables",
                passed=True,
                message=f"所有关键表存在: {len(required_tables)} 个"
            )
        else:
            result = ValidationResult(
                category="schema",
                check_name="critical_tables", 
                passed=False,
                message=f"缺失关键表: {', '.join(missing_tables)}",
                details={'missing_tables': missing_tables}
            )
        
        self.validation_results.append(result)
        return result
    
    def run_full_validation(self, expected_version: str, 
                          required_tables: List[str] = None) -> Dict[str, Any]:
        """执行完整验证"""
        self.logger.info("🔍 开始完整数据库验证...")
        
        # 清空之前的结果
        self.validation_results.clear()
        
        # 1. 连接验证
        self.validate_database_connection()
        
        # 2. alembic_version表验证
        self.validate_alembic_version_table()
        
        # 3. 版本验证
        self.validate_migration_version(expected_version)
        
        # 4. 收集数据库信息
        self.collect_database_info()
        
        # 5. 关键表验证
        if required_tables:
            self.validate_critical_tables(required_tables)
        
        # 6. 数据完整性验证
        self.validate_data_integrity()
        
        # 生成验证报告
        report = self._generate_validation_report()
        
        return report
    
    def _get_flask_db_current(self) -> Optional[str]:
        """使用Flask命令获取当前版本"""
        try:
            env = os.environ.copy()
            env['DATABASE_URL'] = self.database_url
            
            result = subprocess.run(['flask', 'db', 'current'],
                                  capture_output=True, text=True,
                                  check=True, env=env, timeout=30)
            
            return result.stdout.strip()
            
        except Exception as e:
            self.logger.debug(f"Flask DB当前版本获取失败: {e}")
            return None
    
    def _generate_validation_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        total_checks = len(self.validation_results)
        passed_checks = sum(1 for r in self.validation_results if r.passed)
        failed_checks = total_checks - passed_checks
        
        # 按类别分组
        categories = {}
        for result in self.validation_results:
            category = result.category
            if category not in categories:
                categories[category] = {'passed': 0, 'failed': 0, 'results': []}
            
            if result.passed:
                categories[category]['passed'] += 1
            else:
                categories[category]['failed'] += 1
            categories[category]['results'].append(result)
        
        report = {
            'timestamp': datetime.now(),
            'database_name': self.database_name,
            'database_url_host': self.parsed_url.hostname,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'success_rate': (passed_checks / total_checks * 100) if total_checks > 0 else 0,
            'categories': categories,
            'database_info': {
                'version': self.current_db_info.version if self.current_db_info else None,
                'table_count': self.current_db_info.table_count if self.current_db_info else 0,
                'foreign_keys_count': len(self.current_db_info.foreign_keys) if self.current_db_info else 0
            }
        }
        
        # 记录报告摘要
        self.logger.info(f"📊 验证报告摘要:")
        self.logger.info(f"   总检查项: {total_checks}")
        self.logger.info(f"   通过: {passed_checks}")
        self.logger.info(f"   失败: {failed_checks}")
        self.logger.info(f"   成功率: {report['success_rate']:.1f}%")
        
        if failed_checks > 0:
            self.logger.warning("❌ 验证失败项目:")
            for result in self.validation_results:
                if not result.passed:
                    self.logger.warning(f"   • {result}")
        
        return report
    
    def get_failed_validations(self) -> List[ValidationResult]:
        """获取所有失败的验证"""
        return [r for r in self.validation_results if not r.passed]