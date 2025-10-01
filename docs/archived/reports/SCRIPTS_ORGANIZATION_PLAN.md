# PMA 根目录脚本整理方案

**生成时间**: 2025-09-30
**当前状态**: 根目录有 **658个Python脚本**，总大小 **6.3 MB**

---

## 📊 脚本分析总结

### 按类型统计

| 类型 | 数量 | 占比 | 说明 | 建议 |
|-----|------|------|------|------|
| **test_*** | **201** | 31% | 测试脚本 | 归档到 `tests/archived/` |
| **check_*** | **73** | 11% | 检查脚本 | 归档到 `scripts/checks/archived/` |
| **fix_*** | **68** | 10% | 修复脚本 | 归档到 `scripts/fixes/archived/` |
| **debug_*** | **40** | 6% | 调试脚本 | 归档到 `scripts/debug/archived/` |
| **update_*** | **16** | 2% | 更新脚本 | 归档到 `scripts/updates/archived/` |
| **sync_*** | **15** | 2% | 同步脚本 | 归档到 `scripts/sync/archived/` |
| **create_*** | **15** | 2% | 创建脚本 | 评估后归档或保留 |
| **analyze_*** | **11** | 2% | 分析脚本 | 归档到 `scripts/analysis/` |
| **verify_*** | **11** | 2% | 验证脚本 | 归档到 `scripts/verification/` |
| **import_*** | **10** | 2% | 导入脚本 | 归档到 `scripts/import/` |
| **migrate_*** | **8** | 1% | 迁移脚本 | 归档到 `scripts/migration/` |
| **add_*** | **7** | 1% | 添加字段脚本 | 归档到 `scripts/schema_changes/` |
| **apply_*** | **5** | 1% | 应用脚本 | 评估后归档 |
| **compare_*** | **4** | 1% | 比对脚本 | 归档到 `scripts/comparison/` |
| **restore_*** | **4** | 1% | 恢复脚本 | 归档到 `scripts/backup_restore/` |
| **clean_*** | **4** | 1% | 清理脚本 | 保留常用，其他归档 |
| **extract_*** | **3** | 0.5% | 提取脚本 | 归档 |
| **monitor_*** | **2** | 0.3% | 监控脚本 | 评估是否保留 |
| **backup_*** | **2** | 0.3% | 备份脚本 | **保留核心备份脚本** |
| **generate_*** | **2** | 0.3% | 生成脚本 | 评估后归档 |
| **reset_*** | **2** | 0.3% | 重置脚本 | 归档 |
| **其他** | **155** | 24% | 混合类型 | 逐个评估 |
| **总计** | **658** | 100% | - | - |

### 按时间统计

| 时间范围 | 数量 | 占比 | 建议 |
|---------|------|------|------|
| **90天以上未修改** | **332** | 50% | 可直接归档 |
| **30-90天未修改** | **322** | 49% | 评估后归档 |
| **最近30天修改** | **3** | 1% | 保留或归档到活跃目录 |

### 大文件脚本（>40KB）

| 文件名 | 大小 | 用途 | 建议 |
|--------|------|------|------|
| quotation_backup.py | 152K | 批价单备份 | 归档到 `scripts/backup_restore/` |
| quotation_backup_20250721_024607.py | 152K | 批价单备份（旧版本） | 可删除 |
| update_app_config.py | 64K | 应用配置更新 | 归档 |
| import_to_render_ordered.py | 56K | Render导入 | 归档到 `scripts/deployment/` |
| import_data_to_render.py | 52K | Render数据导入 | 归档到 `scripts/deployment/` |
| run_fix.py | 52K | 运行修复 | 归档 |
| cloud_models.py | 44K | 云端模型 | 归档到 `scripts/models/` |
| local_models.py | 44K | 本地模型 | 归档到 `scripts/models/` |

---

## 🎯 推荐的目录结构

```
PMA/
├── scripts/                          # 工具脚本目录（新建）
│   ├── active/                       # 活跃使用的脚本
│   │   ├── backup_cloud_pma_db.py   # SP8D数据库备份（保留）
│   │   ├── simple_ovs_backup.py     # OVS数据库备份（保留）
│   │   ├── standard_migration_upgrade.py  # 标准迁移升级（保留）
│   │   └── standard_migration_upgrade_ovs.py  # OVS迁移升级（保留）
│   │
│   ├── archived/                     # 归档脚本（按日期组织）
│   │   ├── 2025-Q1/                 # 2025年第一季度
│   │   ├── 2025-Q2/                 # 2025年第二季度
│   │   └── 2025-Q3/                 # 2025年第三季度
│   │
│   ├── backup_restore/              # 备份和恢复脚本
│   │   ├── quotation_backup.py
│   │   └── restore_*.py
│   │
│   ├── checks/                      # 检查脚本
│   │   └── archived/                # 历史检查脚本
│   │       └── check_*.py
│   │
│   ├── debug/                       # 调试脚本
│   │   └── archived/
│   │       └── debug_*.py
│   │
│   ├── fixes/                       # 修复脚本
│   │   └── archived/
│   │       └── fix_*.py
│   │
│   ├── migration/                   # 数据迁移脚本
│   │   ├── migrate_*.py
│   │   └── import_*.py
│   │
│   ├── deployment/                  # 部署相关脚本
│   │   ├── import_to_render*.py
│   │   └── sync_to_*.py
│   │
│   ├── schema_changes/              # 数据库结构变更脚本
│   │   ├── add_*.py
│   │   └── alter_*.py
│   │
│   ├── analysis/                    # 分析脚本
│   │   └── analyze_*.py
│   │
│   ├── sync/                        # 同步脚本
│   │   └── sync_*.py
│   │
│   ├── verification/                # 验证脚本
│   │   └── verify_*.py
│   │
│   ├── comparison/                  # 对比脚本
│   │   └── compare_*.py
│   │
│   ├── models/                      # 模型脚本
│   │   ├── cloud_models.py
│   │   └── local_models.py
│   │
│   └── tools/                       # 通用工具脚本
│       ├── config_*.py
│       └── version_*.py
│
├── tests/                           # 测试脚本目录
│   ├── archived/                    # 历史测试脚本
│   │   └── test_*.py (201个)
│   └── active/                      # 活跃测试（如果有）
│
├── run.py                           # 应用启动（保留）
├── config.py                        # 配置文件（保留）
├── wsgi.py                          # WSGI入口（保留）
├── babel.cfg                        # Babel配置（保留）
└── 其他核心文件...
```

---

## 📋 详细整理计划

### 🔥 阶段1: 核心脚本识别（保留在根目录或scripts/active/）

**必须保留的核心脚本**（共6个）:
- ✅ `run.py` - 应用启动脚本
- ✅ `config.py` - 配置文件
- ✅ `wsgi.py` - WSGI生产环境入口
- ✅ `babel.cfg` - 国际化配置
- ✅ `backup_cloud_pma_db.py` - SP8D数据库备份工具
- ✅ `simple_ovs_backup.py` - OVS数据库备份工具

**建议移到scripts/active/**（活跃工具）:
- `standard_migration_upgrade.py` - SP8D迁移升级工具
- `standard_migration_upgrade_ovs.py` - OVS迁移升级工具
- `fix_migration_conflicts.py` - 迁移冲突修复工具

**总计保留**: 9个核心/活跃脚本

---

### 🗂️ 阶段2: 批量归档（按时间和类型）

#### 2.1 测试脚本归档 → `tests/archived/`
**数量**: 201个 `test_*.py`
**空间**: ≈2 MB
**建议**:
- 全部移到 `tests/archived/`
- 如有pytest测试套件，保留在 `tests/` 根目录

```bash
mkdir -p tests/archived
mv test_*.py tests/archived/
```

#### 2.2 调试脚本归档 → `scripts/debug/archived/`
**数量**: 40个 `debug_*.py`
**空间**: ≈400 KB
**建议**: 全部归档，这些都是一次性调试脚本

```bash
mkdir -p scripts/debug/archived
mv debug_*.py scripts/debug/archived/
```

#### 2.3 检查脚本归档 → `scripts/checks/archived/`
**数量**: 73个 `check_*.py`
**空间**: ≈700 KB
**建议**: 全部归档

```bash
mkdir -p scripts/checks/archived
mv check_*.py scripts/checks/archived/
```

#### 2.4 修复脚本归档 → `scripts/fixes/archived/`
**数量**: 68个 `fix_*.py`
**空间**: ≈800 KB
**建议**: 保留 `fix_migration_conflicts.py`，其他全部归档

```bash
mkdir -p scripts/fixes/archived
mv fix_*.py scripts/fixes/archived/
mv scripts/fixes/archived/fix_migration_conflicts.py scripts/active/
```

#### 2.5 分析脚本归档 → `scripts/analysis/`
**数量**: 11个 `analyze_*.py`
**空间**: ≈200 KB

```bash
mkdir -p scripts/analysis
mv analyze_*.py scripts/analysis/
```

#### 2.6 验证脚本归档 → `scripts/verification/`
**数量**: 11个 `verify_*.py`
**空间**: ≈300 KB

```bash
mkdir -p scripts/verification
mv verify_*.py scripts/verification/
```

#### 2.7 迁移导入脚本归档 → `scripts/migration/`
**数量**: 18个 (`migrate_*.py` + `import_*.py`)
**空间**: ≈600 KB

```bash
mkdir -p scripts/migration
mv migrate_*.py import_*.py scripts/migration/
```

#### 2.8 同步脚本归档 → `scripts/sync/`
**数量**: 15个 `sync_*.py`
**空间**: ≈400 KB

```bash
mkdir -p scripts/sync
mv sync_*.py scripts/sync/
```

#### 2.9 部署脚本归档 → `scripts/deployment/`
**相关脚本**:
- `import_to_render*.py`
- `render_*.py`
- `apply_schema_on_render.py`
- `cloud_deployment_verification.py`

```bash
mkdir -p scripts/deployment
mv *render*.py scripts/deployment/
mv apply_schema_on_render.py scripts/deployment/
mv cloud_deployment_verification.py scripts/deployment/
```

#### 2.10 数据库结构变更脚本 → `scripts/schema_changes/`
**数量**: 7个 `add_*.py` + `alter_*.py`

```bash
mkdir -p scripts/schema_changes
mv add_*.py alter_*.py scripts/schema_changes/
```

#### 2.11 备份恢复脚本 → `scripts/backup_restore/`
**相关脚本**:
- `quotation_backup*.py`
- `restore_*.py`
- `backup_storage_solution.py`

```bash
mkdir -p scripts/backup_restore
mv quotation_backup*.py restore_*.py backup_storage_solution.py scripts/backup_restore/
```

#### 2.12 模型脚本 → `scripts/models/`
**相关脚本**:
- `cloud_models.py`
- `local_models.py`

```bash
mkdir -p scripts/models
mv cloud_models.py local_models.py scripts/models/
```

#### 2.13 对比脚本 → `scripts/comparison/`
**数量**: 4个 `compare_*.py`

```bash
mkdir -p scripts/comparison
mv compare_*.py scripts/comparison/
```

---

### 🧹 阶段3: 特殊处理

#### 3.1 重复版本脚本（可删除）
- `quotation_backup_20250721_024607.py` - 删除旧版本，保留 `quotation_backup.py`
- 任何带日期后缀的重复脚本

#### 3.2 90天以上未修改且无明确用途的脚本
**数量**: 约150个
**建议**: 移到 `scripts/archived/2025-Q1/` 或 `scripts/archived/2025-Q2/`

```bash
mkdir -p scripts/archived/2025-Q2
find . -maxdepth 1 -name "*.py" -mtime +90 -exec mv {} scripts/archived/2025-Q2/ \;
```

#### 3.3 配置和工具脚本
**保留或移到scripts/tools/**:
- `config_*.py` → `scripts/tools/`
- `version_*.py` → `scripts/tools/`
- `activate_admin.py` → `scripts/tools/`

---

## 📊 整理后效果预估

### 根目录清理效果

| 项目 | 整理前 | 整理后 | 减少 |
|-----|--------|--------|------|
| **Python脚本数量** | 658个 | **9个** | **649个 (99%)** |
| **根目录文件总数** | 1300+ | ≈50个 | **1250+ (96%)** |
| **根目录可读性** | ⭐ | ⭐⭐⭐⭐⭐ | 显著提升 |

### 整理后根目录结构

```
PMA/
├── run.py                    # 应用启动
├── config.py                 # 配置文件
├── wsgi.py                   # WSGI入口
├── babel.cfg                 # Babel配置
├── backup_cloud_pma_db.py    # SP8D备份工具
├── simple_ovs_backup.py      # OVS备份工具
├── requirements.txt          # 依赖
├── .env*                     # 环境变量
├── CLAUDE*.md               # 项目规则文档
├── app/                      # 应用代码
├── migrations/               # 数据库迁移
├── venv/                     # 虚拟环境
├── scripts/                  # 工具脚本（新建，649个文件）
├── tests/                    # 测试脚本（新建，201个文件）
└── 其他核心文件...
```

---

## 🚀 执行建议

### 方式1: 手动执行（推荐，安全）

**优点**:
- 完全可控
- 可随时中断
- 可逐个检查

**步骤**:
1. 创建目录结构
2. 逐类别移动文件
3. 每步验证
4. 测试应用启动

### 方式2: 自动脚本执行

**优点**:
- 快速高效
- 批量处理

**风险**:
- 可能误移重要脚本
- 需要事前备份

**建议**:
- 先备份整个项目
- 使用我提供的自动化脚本
- 执行后验证

---

## 📝 自动化脚本

我可以为你生成一个自动化整理脚本 `organize_scripts.py`，它会：

1. ✅ 创建所有必需的目录结构
2. ✅ 按规则移动脚本到对应目录
3. ✅ 保留核心脚本在根目录
4. ✅ 生成移动日志
5. ✅ 支持回滚操作

**是否需要生成自动化脚本？**

---

## ⚠️ 注意事项

### 整理前必做

1. **完整备份** - 再次备份整个项目
2. **测试应用** - 确保当前应用正常运行
3. **查看依赖** - 检查是否有其他脚本引用这些文件

### 整理时注意

1. **不要移动正在使用的脚本**
2. **核心工具脚本单独处理**
3. **分阶段执行，每阶段后测试**

### 整理后验证

1. **应用启动测试** - `python run.py`
2. **备份工具测试** - 运行备份脚本
3. **迁移工具测试** - 测试迁移升级脚本
4. **检查导入错误** - 查看是否有脚本相互引用

---

## 📌 总结

### 核心收益

- ✅ 根目录从 **658个脚本** 减少到 **9个核心脚本**
- ✅ 清理 **99%的临时脚本**
- ✅ 建立规范的脚本组织结构
- ✅ 显著提升项目可维护性

### 预计耗时

- **手动整理**: 2-3小时
- **自动脚本**: 5-10分钟（含验证）

### 风险评估

- **风险等级**: 🟢 低（有备份机制）
- **回滚难度**: 🟢 简单（可直接恢复备份）
- **影响范围**: 🟡 中（仅影响脚本组织，不影响应用运行）

---

**建议**: 采用自动脚本方式，先在测试环境验证，确认无误后再在生产环境执行。

**下一步**: 是否需要我生成自动化整理脚本？