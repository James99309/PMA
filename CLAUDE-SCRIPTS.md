# PMA 项目脚本创建与管理规范

**文档版本**: 1.0.0
**最后更新**: 2025-09-30
**适用对象**: Claude AI 助手、开发人员

---

## 📚 概述

本文档规定了PMA项目中所有Python脚本的创建、存放、命名和管理规范。遵循这些规范可以保持项目根目录整洁，提高代码可维护性。

---

## 📁 目录结构规范

### 标准目录结构

```
PMA/
├── *.py                      # 仅保留核心启动和配置脚本
│   ├── run.py               # 应用启动脚本（必需）
│   ├── config.py            # 配置文件（必需）
│   ├── wsgi.py              # WSGI生产环境入口（必需）
│   └── babel.cfg            # 国际化配置（必需）
│
├── scripts/                  # 工具脚本目录
│   ├── active/              # 活跃的工具脚本
│   │   ├── backup_cloud_pma_db.py          # SP8D数据库备份
│   │   ├── simple_ovs_backup.py            # OVS数据库备份
│   │   ├── standard_migration_upgrade.py   # 数据库迁移升级
│   │   └── fix_migration_conflicts.py      # 迁移冲突修复
│   │
│   ├── temp/                # 临时脚本（测试完即删除）
│   │   ├── debug_*.py      # 调试脚本
│   │   ├── check_*.py      # 检查脚本
│   │   └── fix_*.py        # 临时修复脚本
│   │
│   ├── tools/               # 通用工具脚本
│   │   ├── analysis/       # 数据分析脚本
│   │   ├── migration/      # 数据迁移脚本
│   │   ├── deployment/     # 部署相关脚本
│   │   └── maintenance/    # 维护脚本
│   │
│   └── archived/            # 归档的历史脚本
│       ├── 2025-Q1/        # 按季度归档
│       ├── 2025-Q2/
│       └── 2025-Q3/
│
└── tests/                    # 测试脚本目录
    ├── active/              # 活跃的测试脚本
    └── archived/            # 归档的测试脚本
```

---

## 🔧 Claude AI 脚本创建规范

### 核心原则

**Claude AI 在创建新脚本时必须遵循以下原则：**

1. ❌ **禁止在项目根目录创建临时脚本**（除非是核心工具）
2. ✅ **所有临时脚本放入 `scripts/temp/` 目录**
3. ✅ **测试脚本放入 `tests/` 目录**
4. ✅ **所有脚本必须包含路径修正代码**
5. ✅ **脚本完成任务后必须询问用户是保留还是删除**

### 脚本存放位置决策树

```
创建新脚本时，按照以下流程决定存放位置：

是测试脚本 (test_*.py)？
├─ 是 → tests/
└─ 否 → 继续

是临时调试脚本 (debug_*.py, check_*.py)？
├─ 是 → scripts/temp/
└─ 否 → 继续

是一次性修复脚本 (fix_*.py)？
├─ 是 → scripts/temp/
└─ 否 → 继续

是可复用的工具脚本？
├─ 是 → scripts/tools/ (选择合适的子目录)
└─ 否 → scripts/temp/

是核心备份/迁移工具？
├─ 是 → scripts/active/
└─ 否 → scripts/temp/
```

### 具体规则

#### 1. 测试脚本 (`test_*.py`)
**存放位置**: `tests/`

```python
# tests/test_approval_flow.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审批流程测试脚本
测试审批创建、提交、审批、拒绝等完整流程
"""
import sys
import os

# 路径修正：从tests/目录访问项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.approval import ApprovalInstance

def test_approval_flow():
    """测试审批流程"""
    app = create_app()
    with app.app_context():
        # 测试代码...
        pass

if __name__ == '__main__':
    test_approval_flow()
```

#### 2. 调试脚本 (`debug_*.py`)
**存放位置**: `scripts/temp/`

```python
# scripts/temp/debug_user_permissions.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户权限调试脚本
临时脚本，用于调试特定用户的权限问题
完成调试后删除
"""
import sys
import os

# 路径修正：从scripts/temp/访问项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.user import User

def debug_user_permissions(username):
    """调试用户权限"""
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"用户: {user.username}")
            print(f"角色: {user.role}")
            # 调试代码...

if __name__ == '__main__':
    debug_user_permissions('test_user')
```

**重要**：调试完成后，Claude必须询问：
```
🗑️ 调试已完成。此脚本是临时调试脚本，是否删除？
- 输入 'y' 删除
- 输入 'n' 保留（将说明保留原因）
```

#### 3. 检查脚本 (`check_*.py`)
**存放位置**: `scripts/temp/`（一次性）或 `scripts/tools/maintenance/`（可复用）

```python
# scripts/temp/check_data_integrity.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据完整性检查脚本
临时检查特定问题
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app, db

def check_data_integrity():
    """检查数据完整性"""
    app = create_app()
    with app.app_context():
        # 检查代码...
        pass

if __name__ == '__main__':
    check_data_integrity()
```

#### 4. 修复脚本 (`fix_*.py`)
**存放位置**: `scripts/temp/`（一次性）或 `scripts/tools/maintenance/`（可复用）

```python
# scripts/temp/fix_approval_status.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审批状态修复脚本
修复特定审批实例的状态问题
一次性脚本，修复后删除
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app, db

def fix_approval_status():
    """修复审批状态"""
    app = create_app()
    with app.app_context():
        # 修复代码...
        db.session.commit()
        print("✅ 修复完成")

if __name__ == '__main__':
    fix_approval_status()
```

#### 5. 数据分析脚本 (`analyze_*.py`)
**存放位置**: `scripts/tools/analysis/`

```python
# scripts/tools/analysis/analyze_user_activity.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户活跃度分析脚本
分析用户登录和操作活跃度
可复用的分析工具
"""
import sys
import os

# 从scripts/tools/analysis/访问项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
sys.path.insert(0, project_root)

from app import create_app, db
from datetime import datetime, timedelta

def analyze_user_activity(days=30):
    """分析最近N天的用户活跃度"""
    app = create_app()
    with app.app_context():
        # 分析代码...
        pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='用户活跃度分析')
    parser.add_argument('--days', type=int, default=30, help='分析天数')
    args = parser.parse_args()

    analyze_user_activity(args.days)
```

#### 6. 迁移脚本 (`migrate_*.py`, `import_*.py`)
**存放位置**: `scripts/tools/migration/`

```python
# scripts/tools/migration/migrate_old_data.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旧数据迁移脚本
从旧系统迁移数据到新系统
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
sys.path.insert(0, project_root)

from app import create_app, db

def migrate_old_data():
    """迁移旧数据"""
    app = create_app()
    with app.app_context():
        # 迁移代码...
        pass

if __name__ == '__main__':
    migrate_old_data()
```

---

## 📝 标准脚本模板

### 通用脚本模板

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能简述

详细说明：
- 脚本用途
- 使用场景
- 注意事项

创建时间: YYYY-MM-DD
创建原因: [简述为何创建此脚本]
使用频率: [一次性/周期性/按需]
"""
import sys
import os

# ==================== 路径修正代码（必需） ====================
# 根据脚本所在位置，自动计算项目根目录

def get_project_root():
    """
    获取项目根目录
    支持从任何子目录运行脚本
    """
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)

    # 根据脚本位置确定项目根目录
    # 如果在 scripts/temp/ → 向上3级
    # 如果在 scripts/tools/xxx/ → 向上3-4级
    # 如果在 tests/ → 向上1级

    # 通用方法：向上查找包含 app/ 目录的路径
    current = script_dir
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)

    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)
# ============================================================

from app import create_app, db
# 其他导入...

def main():
    """主函数"""
    app = create_app()
    with app.app_context():
        # 脚本主要逻辑...
        pass

if __name__ == '__main__':
    main()
```

### 带参数的脚本模板

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本功能简述

使用方法:
    python script_name.py --param1 value1 --param2 value2

参数说明:
    --param1: 参数1说明
    --param2: 参数2说明
"""
import sys
import os
import argparse

# 路径修正（使用上面的get_project_root函数）
def get_project_root():
    # ... (同上)
    pass

project_root = get_project_root()
sys.path.insert(0, project_root)

from app import create_app, db

def main(param1, param2):
    """主函数"""
    app = create_app()
    with app.app_context():
        print(f"参数1: {param1}")
        print(f"参数2: {param2}")
        # 脚本逻辑...

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='脚本功能说明')
    parser.add_argument('--param1', required=True, help='参数1说明')
    parser.add_argument('--param2', default='default_value', help='参数2说明')

    args = parser.parse_args()
    main(args.param1, args.param2)
```

---

## 🏷️ 脚本命名规范

### 命名原则

1. **使用小写字母和下划线** - `script_name.py`
2. **名称要有描述性** - 一看就知道功能
3. **使用统一前缀** - 便于分类和识别

### 标准前缀

| 前缀 | 用途 | 示例 | 存放位置 |
|-----|------|------|---------|
| `test_` | 测试脚本 | `test_approval_flow.py` | `tests/` |
| `debug_` | 调试脚本 | `debug_user_permissions.py` | `scripts/temp/` |
| `check_` | 检查脚本 | `check_data_integrity.py` | `scripts/temp/` 或 `scripts/tools/maintenance/` |
| `fix_` | 修复脚本 | `fix_approval_status.py` | `scripts/temp/` 或 `scripts/tools/maintenance/` |
| `analyze_` | 分析脚本 | `analyze_user_activity.py` | `scripts/tools/analysis/` |
| `migrate_` | 迁移脚本 | `migrate_old_data.py` | `scripts/tools/migration/` |
| `import_` | 导入脚本 | `import_users_from_csv.py` | `scripts/tools/migration/` |
| `export_` | 导出脚本 | `export_reports.py` | `scripts/tools/data/` |
| `sync_` | 同步脚本 | `sync_databases.py` | `scripts/tools/maintenance/` |
| `backup_` | 备份脚本 | `backup_cloud_pma_db.py` | `scripts/active/` |
| `restore_` | 恢复脚本 | `restore_database.py` | `scripts/active/` |

### 命名示例

**✅ 好的命名**:
- `test_approval_flow.py` - 清晰表达是测试审批流程
- `debug_gxh_permissions.py` - 明确是调试gxh用户权限
- `migrate_old_quotations.py` - 明确是迁移旧批价单数据
- `analyze_monthly_sales.py` - 明确是分析月度销售数据

**❌ 不好的命名**:
- `script1.py` - 无意义
- `temp.py` - 太模糊
- `fix.py` - 不知道修复什么
- `test.py` - 不知道测试什么

---

## 🔄 脚本生命周期管理

### 脚本完成后的处理流程

```
脚本任务完成
    ↓
是一次性脚本？
    ├─ 是 → 询问用户是否删除
    │         ├─ 删除 → 从文件系统移除
    │         └─ 保留 → 移到 scripts/archived/当前季度/
    │
    └─ 否 → 是否有复用价值？
              ├─ 有 → 移到 scripts/tools/对应分类/
              │        并添加文档说明
              │
              └─ 无 → 移到 scripts/archived/当前季度/
```

### Claude AI 的询问模板

**一次性脚本完成后**:
```
✅ 脚本任务已完成

此脚本是一次性调试/修复脚本，建议删除。

选项：
1. 删除脚本（推荐） - 任务已完成，不再需要
2. 归档保存 - 移到 scripts/archived/2025-Q3/
3. 保留使用 - 移到 scripts/tools/对应目录/ （需说明复用场景）

请选择：[1/2/3]
```

**可复用脚本完成后**:
```
✅ 脚本创建完成

此脚本具有复用价值，建议：
- 移到 scripts/tools/analysis/ 目录
- 添加使用说明和示例

是否立即移动并整理？[y/n]
```

---

## 📊 脚本创建统计与审查

### 定期审查机制

**每季度执行一次脚本审查**：

```bash
# 1. 统计各目录脚本数量
find scripts/temp -name "*.py" | wc -l
find scripts/tools -name "*.py" | wc -l
find tests -name "*.py" | wc -l

# 2. 查找长期未使用的脚本（90天以上）
find scripts/temp -name "*.py" -mtime +90

# 3. 归档旧脚本
find scripts/temp -name "*.py" -mtime +90 -exec mv {} scripts/archived/$(date +%Y-Q%q)/ \;

# 4. 清理空目录
find scripts/temp -type d -empty -delete
```

### 脚本审查清单

- [ ] `scripts/temp/` 目录是否有超过30天的脚本？
- [ ] 临时脚本是否都添加了说明和创建原因？
- [ ] 有复用价值的脚本是否移到了 `scripts/tools/`？
- [ ] 归档的脚本是否有README说明？
- [ ] 根目录是否有新增的临时脚本？

---

## 🚨 禁止事项

### ❌ 严格禁止

1. **禁止在根目录创建临时脚本**
   - ❌ 不允许：`/Users/nijie/Documents/PMA/debug_something.py`
   - ✅ 正确：`/Users/nijie/Documents/PMA/scripts/temp/debug_something.py`

2. **禁止创建无意义命名的脚本**
   - ❌ 不允许：`script1.py`, `temp.py`, `test.py`, `fix.py`
   - ✅ 正确：`debug_user_login_issue.py`, `fix_approval_status_bug.py`

3. **禁止不添加路径修正代码**
   - ❌ 不允许：直接 `from app import ...` 而不修正路径
   - ✅ 正确：先调用 `get_project_root()` 并添加到 `sys.path`

4. **禁止创建脚本后不询问处理方式**
   - ❌ 不允许：脚本完成任务后就不管了
   - ✅ 正确：询问用户是删除、归档还是保留

### ⚠️ 谨慎处理

1. **谨慎在根目录创建新的核心脚本**
   - 只有确实是核心工具才能放根目录
   - 需要明确说明为何是核心脚本

2. **谨慎修改现有脚本的存放位置**
   - 如果脚本已经被其他地方引用，移动前需要检查

---

## 📋 快速参考

### Claude AI 创建脚本时的决策表

| 场景 | 存放位置 | 命名 | 完成后处理 |
|-----|---------|------|-----------|
| 测试某个功能 | `tests/` | `test_功能.py` | 集成到测试套件或删除 |
| 调试特定问题 | `scripts/temp/` | `debug_问题.py` | **删除**（推荐） |
| 检查数据一致性 | `scripts/temp/` | `check_数据.py` | 删除或移到tools |
| 修复一次性bug | `scripts/temp/` | `fix_bug描述.py` | **删除**（推荐） |
| 分析业务数据 | `scripts/tools/analysis/` | `analyze_内容.py` | 保留并文档化 |
| 数据迁移 | `scripts/tools/migration/` | `migrate_数据.py` | 归档到archived |
| 备份工具 | `scripts/active/` | `backup_目标.py` | **保留**（核心工具） |

### 常见问题

**Q: 如何判断脚本是否应该删除？**
A: 如果脚本名称以 `debug_`, `check_`, `fix_` 开头，且是针对特定问题的，通常应该删除。

**Q: 脚本放在 scripts/temp/ 和 scripts/tools/ 有什么区别？**
A:
- `scripts/temp/` - 临时脚本，用完就删除或归档
- `scripts/tools/` - 有复用价值的工具脚本，长期保留

**Q: 如何恢复已删除的脚本？**
A:
1. 从归档目录恢复：`scripts/archived/YYYY-Qx/`
2. 从备份恢复：`/Users/nijie/Documents/PMA_scripts_backup_*.tar.gz`

**Q: 创建脚本时如何确定路径修正代码？**
A: 使用提供的 `get_project_root()` 函数，它会自动向上查找包含 `app/` 和 `run.py` 的目录。

---

## 📌 总结

### 核心要点

1. ✅ **临时脚本放 `scripts/temp/`，不要放根目录**
2. ✅ **所有脚本必须包含路径修正代码**
3. ✅ **使用有意义的命名和标准前缀**
4. ✅ **完成任务后询问用户处理方式**
5. ✅ **定期清理和归档旧脚本**

### 记住这个流程

```
创建脚本 → 选择正确位置 → 使用标准模板 → 完成任务 → 询问处理 → 删除/归档/保留
```

---

**文档维护**: 本规范应根据项目发展持续更新
**反馈渠道**: 如有改进建议，请在项目会议中提出

**相关文档**:
- [CLAUDE.md](./CLAUDE.md) - 项目核心规则
- [SCRIPTS_ORGANIZATION_PLAN.md](./SCRIPTS_ORGANIZATION_PLAN.md) - 脚本整理方案
- [SCRIPTS_ORGANIZATION_REPORT.md](./SCRIPTS_ORGANIZATION_REPORT.md) - 脚本整理报告