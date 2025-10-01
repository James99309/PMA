#!/usr/bin/env python3
"""
完整的数据库迁移测试套件
验证所有新组件的功能和集成

测试范围：
1. 迁移文件解析器功能测试
2. 逐步执行器功能测试
3. 数据库验证器功能测试
4. 核心基础类集成测试
5. SP8D和OVS迁移脚本测试
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from migration_parser import MigrationParser, MigrationInfo
    from stepwise_executor import StepwiseMigrationExecutor, MigrationExecutionResult
    from database_validator import DatabaseValidator, ValidationResult
    from database_migration_core_v2 import DatabaseMigrationCoreV2, MigrationPlan, MigrationReport
    from sp8d_migration_v2 import SP8DMigrationV2
    from ovs_migration_v2 import OVSMigrationV2
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

class TestMigrationParser(unittest.TestCase):
    """测试迁移文件解析器"""
    
    def setUp(self):
        self.migrations_dir = "/tmp/test_migrations"
        # 创建模拟迁移目录
        os.makedirs(f"{self.migrations_dir}/versions", exist_ok=True)
        
    def test_parser_initialization(self):
        """测试解析器初始化"""
        parser = MigrationParser(self.migrations_dir)
        self.assertEqual(parser.migrations_dir, self.migrations_dir)
        self.assertIsInstance(parser.migrations, dict)
        
    def test_migration_info_creation(self):
        """测试迁移信息结构"""
        info = MigrationInfo("/path/test.py", "abc123", "def456", "test.py")
        self.assertEqual(info.revision, "abc123")
        self.assertEqual(info.down_revision, "def456")
        self.assertFalse(info.is_merge)
        
        # 测试合并迁移
        merge_info = MigrationInfo("/path/merge.py", "merge123", ("abc", "def"), "merge.py")
        self.assertTrue(merge_info.is_merge)

class TestStepwiseExecutor(unittest.TestCase):
    """测试逐步执行器"""
    
    def setUp(self):
        self.database_url = "postgresql://test:test@localhost:5432/test"
        self.executor = StepwiseMigrationExecutor(self.database_url, "TestDB")
        
    def test_executor_initialization(self):
        """测试执行器初始化"""
        self.assertEqual(self.executor.database_url, self.database_url)
        self.assertEqual(self.executor.database_name, "TestDB")
        self.assertEqual(len(self.executor.execution_history), 0)
        
    def test_execution_result_creation(self):
        """测试执行结果结构"""
        result = MigrationExecutionResult(True, "abc123", "测试成功", 1.5)
        self.assertTrue(result.success)
        self.assertEqual(result.migration_id, "abc123")
        self.assertEqual(result.execution_time, 1.5)
        
    @patch('subprocess.run')
    def test_get_current_revision(self, mock_subprocess):
        """测试获取当前版本"""
        mock_subprocess.return_value = Mock(stdout="abc123def456", returncode=0)
        
        revision = self.executor.get_current_revision()
        self.assertEqual(revision, "abc123def456")
        
        # 测试失败情况
        mock_subprocess.side_effect = Exception("连接失败")
        revision = self.executor.get_current_revision()
        self.assertIsNone(revision)

class TestDatabaseValidator(unittest.TestCase):
    """测试数据库验证器"""
    
    def setUp(self):
        self.database_url = "postgresql://test:test@localhost:5432/test"
        self.validator = DatabaseValidator(self.database_url, "TestDB")
        
    def test_validator_initialization(self):
        """测试验证器初始化"""
        self.assertEqual(self.validator.database_url, self.database_url)
        self.assertEqual(self.validator.database_name, "TestDB")
        self.assertEqual(len(self.validator.validation_results), 0)
        
    def test_validation_result_creation(self):
        """测试验证结果结构"""
        result = ValidationResult("schema", "table_check", True, "所有表存在")
        self.assertEqual(result.category, "schema")
        self.assertEqual(result.check_name, "table_check")
        self.assertTrue(result.passed)

class TestDatabaseMigrationCore(unittest.TestCase):
    """测试核心基础类"""
    
    def setUp(self):
        # 创建测试用的核心类实现
        class TestMigrationCore(DatabaseMigrationCoreV2):
            def get_database_url(self):
                return "postgresql://test:test@localhost:5432/test"
                
        self.core = TestMigrationCore("TestDB")
        
    def test_core_initialization(self):
        """测试核心类初始化"""
        self.assertEqual(self.core.database_name, "TestDB")
        self.assertIsNotNone(self.core.logger)
        self.assertIsNone(self.core.parser)  # 延迟初始化
        
    def test_migration_plan_creation(self):
        """测试迁移计划创建"""
        plan = MigrationPlan("start", "target", ["step1", "step2"], ["step1"])
        self.assertEqual(plan.start_revision, "start")
        self.assertEqual(plan.target_revision, "target")
        self.assertEqual(plan.total_steps, 1)
        
    def test_migration_report_creation(self):
        """测试迁移报告创建"""
        report = MigrationReport()
        self.assertFalse(report.success)
        self.assertIsNone(report.end_time)
        
        report.mark_completed(True)
        self.assertTrue(report.success)
        self.assertIsNotNone(report.end_time)

class TestSP8DMigration(unittest.TestCase):
    """测试SP8D迁移脚本"""
    
    def test_sp8d_initialization(self):
        """测试SP8D迁移器初始化"""
        migrator = SP8DMigrationV2()
        self.assertEqual(migrator.database_name, "SP8D")
        self.assertTrue(migrator.get_database_url().startswith("postgresql://"))
        self.assertIn("iqcyimnjtnmomvfuwjzw", migrator.get_database_url())

class TestOVSMigration(unittest.TestCase):
    """测试OVS迁移脚本"""
    
    def test_ovs_initialization(self):
        """测试OVS迁移器初始化"""
        migrator = OVSMigrationV2()
        self.assertEqual(migrator.database_name, "OVS")
        self.assertTrue(migrator.get_database_url().startswith("postgresql://"))
        self.assertIn("pqzviljbpfoqvyfulakl", migrator.get_database_url())

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_component_integration(self):
        """测试组件集成"""
        # 创建测试用的核心类
        class TestMigrationCore(DatabaseMigrationCoreV2):
            def get_database_url(self):
                return "postgresql://test:test@localhost:5432/test"
                
        core = TestMigrationCore("TestDB")
        
        # 测试组件初始化
        core.initialize_components()
        
        self.assertIsNotNone(core.parser)
        self.assertIsNotNone(core.executor)
        self.assertIsNotNone(core.validator)
        
        # 测试组件类型
        self.assertIsInstance(core.parser, MigrationParser)
        self.assertIsInstance(core.executor, StepwiseMigrationExecutor)
        self.assertIsInstance(core.validator, DatabaseValidator)

def run_comprehensive_test():
    """运行综合测试"""
    print("🧪 开始数据库迁移系统综合测试")
    print("=" * 60)
    
    # 测试套件
    test_suites = [
        ("迁移文件解析器", TestMigrationParser),
        ("逐步执行器", TestStepwiseExecutor),
        ("数据库验证器", TestDatabaseValidator),
        ("核心基础类", TestDatabaseMigrationCore),
        ("SP8D迁移脚本", TestSP8DMigration),
        ("OVS迁移脚本", TestOVSMigration),
        ("集成测试", TestIntegration),
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_suites = []
    
    for suite_name, test_class in test_suites:
        print(f"\n🔬 测试 {suite_name}...")
        
        # 创建测试套件
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
        
        # 运行测试
        result = runner.run(suite)
        
        suite_total = result.testsRun
        suite_failed = len(result.failures) + len(result.errors)
        suite_passed = suite_total - suite_failed
        
        total_tests += suite_total
        passed_tests += suite_passed
        
        if suite_failed == 0:
            print(f"✅ {suite_name}: {suite_passed}/{suite_total} 测试通过")
        else:
            print(f"❌ {suite_name}: {suite_passed}/{suite_total} 测试通过")
            failed_suites.append(suite_name)
            
            # 显示失败详情
            if result.failures:
                for test, traceback in result.failures:
                    tb_lines = traceback.split('\n')
                    error_msg = tb_lines[-2] if len(tb_lines) > 1 else traceback
                    print(f"   失败: {test} - {error_msg}")
            if result.errors:
                for test, traceback in result.errors:
                    tb_lines = traceback.split('\n')
                    error_msg = tb_lines[-2] if len(tb_lines) > 1 else traceback
                    print(f"   错误: {test} - {error_msg}")
    
    # 测试摘要
    print("\n" + "=" * 60)
    print("📊 测试摘要")
    print("=" * 60)
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"成功率: {success_rate:.1f}%")
    
    if failed_suites:
        print(f"\n❌ 失败的测试套件: {', '.join(failed_suites)}")
    else:
        print("\n🎉 所有测试套件通过！")
    
    return success_rate == 100.0

def test_file_structure():
    """测试文件结构完整性"""
    print("\n📁 检查文件结构...")
    
    required_files = [
        'migration_parser.py',
        'stepwise_executor.py', 
        'database_validator.py',
        'database_migration_core_v2.py',
        'sp8d_migration_v2.py',
        'ovs_migration_v2.py'
    ]
    
    missing_files = []
    for filename in required_files:
        if not os.path.exists(filename):
            missing_files.append(filename)
    
    if missing_files:
        print(f"❌ 缺失文件: {', '.join(missing_files)}")
        return False
    else:
        print("✅ 所有必需文件存在")
        return True

def test_basic_imports():
    """测试基本导入"""
    print("\n📦 测试模块导入...")
    
    try:
        # 测试所有核心模块导入
        import migration_parser
        import stepwise_executor
        import database_validator
        import database_migration_core_v2
        import sp8d_migration_v2
        import ovs_migration_v2
        
        print("✅ 所有模块导入成功")
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 数据库迁移系统 V2.0 测试套件")
    print("=" * 60)
    
    # 基础测试
    tests_passed = 0
    total_basic_tests = 2
    
    if test_file_structure():
        tests_passed += 1
        
    if test_basic_imports():
        tests_passed += 1
    
    if tests_passed < total_basic_tests:
        print(f"\n❌ 基础测试失败 ({tests_passed}/{total_basic_tests})，跳过综合测试")
        return False
    
    # 综合测试
    success = run_comprehensive_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！数据库迁移系统 V2.0 准备就绪")
        print("\n🔧 使用说明:")
        print("   SP8D数据库迁移: python3 sp8d_migration_v2.py")
        print("   OVS数据库迁移:  python3 ovs_migration_v2.py")
        print("\n✨ V2.0 新特性:")
        print("   • 真正的逐步迁移执行")
        print("   • 智能合并迁移检测")
        print("   • 完整的数据库验证")
        print("   • 详细的迁移规划")
    else:
        print("❌ 部分测试失败，请检查上述错误")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)