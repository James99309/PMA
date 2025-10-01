# 测试脚本归档

**归档时间**: 2025-09-30
**脚本数量**: 137个
**归档原因**: 历史测试脚本（test_*.py）

---

## 📋 归档说明

此目录包含所有历史的 `test_*.py` 测试脚本。这些脚本用于测试各种功能和API，现已归档保存。

---

## 🧪 归档内容分类

### 测试脚本类型

- **单元测试** - 测试单个函数或方法
- **集成测试** - 测试模块间的交互
- **API测试** - 测试API端点和响应
- **功能测试** - 测试完整的业务流程
- **数据测试** - 测试数据完整性和一致性
- **性能测试** - 测试系统性能

### 测试覆盖范围

归档的测试涵盖以下模块：
- 审批流程 (approval)
- 用户权限 (permissions)
- 项目管理 (project)
- 批价管理 (quotation)
- 客户管理 (customer)
- 报销管理 (expense)
- 库存管理 (inventory)
- 其他业务模块

---

## 🔍 如何使用归档测试

### 参考价值

1. **测试思路** - 学习如何设计测试用例
2. **业务理解** - 通过测试了解业务逻辑
3. **代码示例** - 查看API调用和数据处理示例
4. **回归测试** - 需要时恢复测试用例

### 恢复测试脚本

如果需要重新运行某个测试：

```bash
# 复制到活跃测试目录
cp test_specific_feature.py /Users/nijie/Documents/PMA/tests/

# 或复制到临时目录
cp test_specific_feature.py /Users/nijie/Documents/PMA/scripts/temp/

# 从项目根目录运行
cd /Users/nijie/Documents/PMA
python tests/test_specific_feature.py
```

### 创建新测试

不建议直接使用旧测试脚本，而是参考其思路创建新测试：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新测试脚本模板
参考旧测试逻辑，但使用最新的代码结构
"""
import sys
import os

# 路径修正
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
import unittest

class TestNewFeature(unittest.TestCase):
    """测试新功能"""

    def setUp(self):
        """测试前准备"""
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        """测试后清理"""
        db.session.rollback()
        self.app_context.pop()

    def test_feature(self):
        """测试具体功能"""
        # 测试代码...
        pass

if __name__ == '__main__':
    unittest.main()
```

---

## 🏗️ 推荐：建立正式测试框架

归档这些脚本后，建议：

### 1. 使用pytest框架

```bash
# 安装pytest
pip install pytest pytest-flask

# 创建测试目录结构
tests/
  ├── conftest.py          # pytest配置
  ├── unit/               # 单元测试
  ├── integration/        # 集成测试
  ├── functional/         # 功能测试
  └── fixtures/           # 测试数据
```

### 2. 编写标准测试

```python
# tests/unit/test_approval_model.py
import pytest
from app.models.approval import ApprovalInstance

def test_create_approval_instance():
    """测试创建审批实例"""
    # 使用pytest fixtures和assertions
    pass

def test_approval_workflow():
    """测试审批工作流"""
    pass
```

### 3. CI/CD集成

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest tests/
```

---

## ⚠️ 注意事项

### 归档测试的局限性

1. **代码变更** - 测试可能基于旧版本代码，直接运行可能失败
2. **数据依赖** - 某些测试依赖特定的测试数据
3. **环境配置** - 可能需要特定的环境变量或配置
4. **数据库状态** - 某些测试假设特定的数据库状态

### 运行前检查

- [ ] 确认代码和模型没有重大变更
- [ ] 检查测试依赖的数据是否存在
- [ ] 确认测试不会修改生产数据
- [ ] 使用测试数据库运行

---

## 📊 测试覆盖度

### 归档前的测试统计（估算）

- 审批流程测试：约30个
- 权限系统测试：约20个
- 业务模块测试：约50个
- API接口测试：约20个
- 数据处理测试：约17个

### 建议的测试覆盖目标

建立新测试框架后，目标覆盖率：
- 核心业务逻辑：>80%
- API端点：>70%
- 工具函数：>60%

---

## 🗑️ 清理建议

### 何时可以删除

测试脚本的保留价值相对较高，建议：

- ⏳ 至少保留1年
- ✅ 新测试框架建立并覆盖相同功能后可删除
- ✅ 相关功能已完全重构或废弃后可删除
- ✅ 确认有完整备份后可删除

### 保留理由

- 历史测试逻辑有参考价值
- 业务需求可能会回滚
- 测试用例是业务逻辑的文档
- 回归测试可能需要

---

## 📦 完整备份

归档测试包含在以下备份中：

```bash
# 完整项目备份
/Users/nijie/Documents/PMA_full_backup_before_cleanup_20250930_223146.tar.gz

# 仅脚本备份
/Users/nijie/Documents/PMA_scripts_backup_20250930_230205.tar.gz
```

---

## 📚 相关文档

- [CLAUDE-SCRIPTS.md](../../CLAUDE-SCRIPTS.md) - 脚本创建与管理规范
- [SCRIPTS_ORGANIZATION_REPORT.md](../../SCRIPTS_ORGANIZATION_REPORT.md) - 脚本整理报告
- [pytest文档](https://docs.pytest.org/) - pytest测试框架

---

**维护人**: Claude AI 助手
**创建日期**: 2025-09-30
**下次审查**: 2026-09-30（建议1年后审查）