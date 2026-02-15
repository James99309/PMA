# PMA 个人文件管理系统 - 设计文档

> **分支**: `feature/file-manager`
> **创建日期**: 2026-02-14
> **状态**: 设计阶段

---

## 1. 需求概述

为 PMA 系统的每个员工提供个人文件存储空间，通过 PMA 统一入口管理，利用现有 NAS WebDAV 基础设施。

### 核心需求

| 需求 | 说明 |
|------|------|
| 个人文件空间 | 每个员工有独立的文件管理区域，支持文件夹分层 |
| 团队共享 | 支持按人、按部门分享文件/文件夹 |
| 公司公共文件库 | 全员可查看的公司公共文档区，由专人管理 |
| 文件去重 | 相同文件只在 NAS 上存储一份，通过引用管理 |
| 存储配额 | 默认每人 10GB，管理员可调整 |

### 不包含的范围

- 不改动现有模块的附件系统（任务附件、发票、产品图片继续用各自存储路径）
- 不包含日志、任务等业务场景的文件上传（那些保持现有逻辑）
- 第一期不做现有附件迁移到文件库

---

## 2. 系统架构

```
┌──────────────────────────────────────────────────────┐
│                      用户界面层                        │
│                                                        │
│  📁 我的文件          📤 共享给我         🏢 公司文件库   │
│  - 文件夹管理         - 别人分享给我的     - 公司公共文档  │
│  - 10GB 配额         - 按人/按部门        - 专人管理     │
│  - 上传/下载/删除     - 只读访问          - 全员可查看    │
│                                                        │
├──────────────────────────────────────────────────────┤
│                      引用管理层                        │
│                                                        │
│  UserFileRef   ← 个人文件引用（指向文件库 + 所在文件夹）  │
│  FileShare     ← 分享关系（按人/按部门/全公司）          │
│  UserFolder    ← 文件夹树形结构                        │
│                                                        │
├──────────────────────────────────────────────────────┤
│                    文件库层（去重）                      │
│                                                        │
│  FileLibrary   ← SHA256 内容寻址，相同文件只存一份       │
│                                                        │
├──────────────────────────────────────────────────────┤
│                     物理存储层                          │
│                                                        │
│  NAS WebDAV: /pma-files/file_library/{hash前2位}/{hash}│
│  现有模块不动: /pma-files/invoices/, products/, etc.    │
│                                                        │
└──────────────────────────────────────────────────────┘
```

### 关键设计决策

1. **物理去重与逻辑隔离分离**：底层 FileLibrary 按 SHA256 去重，用户看到的个人空间只显示自己主动添加的文件，日志/任务等碎片附件不会污染个人空间
2. **现有模块不改动**：任务附件、发票、产品图片继续用各自的存储桶和路径，不做迁移
3. **新增 `file_library` 存储桶**：个人文件/共享文件统一走新桶，与现有桶隔离

---

## 3. 数据模型

### 3.1 FileLibrary（文件库 - 物理文件去重层）

存储实际物理文件的元信息，一个文件内容只有一条记录。

```python
class FileLibrary(db.Model):
    __tablename__ = 'file_library'

    id = db.Column(db.Integer, primary_key=True)

    # 内容寻址
    sha256_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    file_size = db.Column(db.BigInteger, nullable=False)          # 字节

    # 物理存储
    storage_path = db.Column(db.String(500), nullable=False)       # NAS 路径
    mime_type = db.Column(db.String(100))                          # MIME 类型
    original_extension = db.Column(db.String(20))                  # 原始扩展名

    # 引用计数
    ref_count = db.Column(db.Integer, default=1, nullable=False)

    # 元数据
    created_at = db.Column(db.DateTime, default=get_local_time)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 索引
    __table_args__ = (
        db.Index('ix_file_library_hash', 'sha256_hash'),
    )
```

**NAS 存储路径规则**：
```
/pma-files/file_library/{SYSTEM_ID}/{hash前2位}/{sha256_hash}.{ext}

示例：
/pma-files/file_library/DEV-PMA/a3/a3f5b2c8...d4e1.pdf
```

### 3.2 UserFolder（用户文件夹）

```python
class UserFolder(db.Model):
    __tablename__ = 'user_folders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    name = db.Column(db.String(255), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('user_folders.id'), nullable=True)  # null = 根目录

    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=get_local_time)
    updated_at = db.Column(db.DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = db.Column(db.Boolean, default=False)

    # 关系
    parent = db.relationship('UserFolder', remote_side=[id], backref='children')
    files = db.relationship('UserFileRef', backref='folder', lazy='dynamic')

    # 约束：同一用户同一父目录下文件夹名唯一
    __table_args__ = (
        db.UniqueConstraint('user_id', 'parent_id', 'name', name='uq_user_folder_name'),
        db.Index('ix_user_folders_user_parent', 'user_id', 'parent_id'),
    )
```

**文件夹深度限制**：最多 3 层（根目录 → 一级 → 二级 → 三级），在应用层校验。

### 3.3 UserFileRef（用户文件引用）

用户个人空间中的文件条目，指向 FileLibrary。

```python
class UserFileRef(db.Model):
    __tablename__ = 'user_file_refs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # 指向文件库
    file_library_id = db.Column(db.Integer, db.ForeignKey('file_library.id'), nullable=False)

    # 文件夹归属
    folder_id = db.Column(db.Integer, db.ForeignKey('user_folders.id'), nullable=True)  # null = 根目录

    # 显示信息（用户可自定义，不影响底层文件）
    display_name = db.Column(db.String(255), nullable=False)       # 显示文件名
    description = db.Column(db.Text, nullable=True)                 # 备注

    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=get_local_time)
    is_deleted = db.Column(db.Boolean, default=False)

    # 关系
    file = db.relationship('FileLibrary', backref='refs')

    __table_args__ = (
        db.Index('ix_user_file_refs_user_folder', 'user_id', 'folder_id'),
    )
```

### 3.4 FileShare（文件分享）

```python
class FileShare(db.Model):
    __tablename__ = 'file_shares'

    id = db.Column(db.Integer, primary_key=True)

    # 分享来源
    shared_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 分享内容（文件或文件夹，二选一）
    file_ref_id = db.Column(db.Integer, db.ForeignKey('user_file_refs.id'), nullable=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('user_folders.id'), nullable=True)

    # 分享目标（三选一）
    share_type = db.Column(db.String(20), nullable=False)          # 'user' / 'department' / 'company'
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    target_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    target_company_name = db.Column(db.String(100), nullable=True)  # PMA 用 company_name 文本字段

    # 权限
    permission = db.Column(db.String(20), default='read')          # 'read' / 'write'

    created_at = db.Column(db.DateTime, default=get_local_time)
    expires_at = db.Column(db.DateTime, nullable=True)             # 可选过期时间
    is_deleted = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.Index('ix_file_shares_target_user', 'target_user_id'),
        db.Index('ix_file_shares_target_dept', 'target_department_id'),
        db.CheckConstraint(
            '(file_ref_id IS NOT NULL AND folder_id IS NULL) OR '
            '(file_ref_id IS NULL AND folder_id IS NOT NULL)',
            name='ck_file_shares_one_target'
        ),
    )
```

### 3.5 CompanyFile（公司公共文件）

公司公共文件库，独立管理，不走个人空间。

```python
class CompanyFile(db.Model):
    __tablename__ = 'company_files'

    id = db.Column(db.Integer, primary_key=True)

    # 指向文件库
    file_library_id = db.Column(db.Integer, db.ForeignKey('file_library.id'), nullable=False)

    # 分类管理
    category = db.Column(db.String(50), nullable=False)            # 'template' / 'policy' / 'reference' / 'other'
    display_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # 归属
    company_name = db.Column(db.String(100), nullable=False)       # 对应用户的 company_name

    # 管理
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)               # 置顶

    created_at = db.Column(db.DateTime, default=get_local_time)
    updated_at = db.Column(db.DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.Index('ix_company_files_company', 'company_name', 'category'),
    )
```

### 3.6 User 模型扩展

在现有 User 模型中添加配额字段：

```python
# 新增字段
storage_quota = db.Column(db.BigInteger, default=10737418240)      # 默认 10GB (bytes)
storage_used = db.Column(db.BigInteger, default=0)                 # 已用空间 (bytes)
```

---

## 4. NAS 存储结构

```
/pma-files/
├── file_library/                    # 新增：内容寻址文件库
│   └── {SYSTEM_ID}/
│       ├── a3/
│       │   ├── a3f5b2...d4e1.pdf
│       │   └── a3c8e1...b2f5.jpg
│       ├── b7/
│       │   └── b7d2a1...e8c3.docx
│       └── ...
│
├── invoices/                        # 不动：发票附件
├── products/                        # 不动：产品文件
├── rd_products/                     # 不动：研发产品
├── meetings/                        # 不动：会议录音
└── tasks/                           # 不动：任务附件
```

**去重流程**：
1. 用户上传文件 → 计算 SHA256
2. 查询 FileLibrary 是否已存在该 hash
3. 已存在 → 直接创建 UserFileRef 引用，`ref_count += 1`，不重复上传
4. 不存在 → 上传到 NAS `file_library/{SYSTEM_ID}/{hash[:2]}/{hash}.{ext}`，创建 FileLibrary + UserFileRef

---

## 5. API 设计

### 5.1 文件夹 API

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/files/folders` | 获取当前用户文件夹树 |
| POST | `/api/files/folders` | 创建文件夹 |
| PUT | `/api/files/folders/<id>` | 重命名/移动文件夹 |
| DELETE | `/api/files/folders/<id>` | 删除文件夹（软删除，内含文件移到根目录） |

### 5.2 文件 API

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/files/list?folder_id=` | 获取文件夹下的文件列表 |
| POST | `/api/files/upload` | 上传文件（含 SHA256 去重） |
| PUT | `/api/files/<id>` | 修改文件显示名/备注/移动到其他文件夹 |
| DELETE | `/api/files/<id>` | 删除文件引用（移入回收站） |
| GET | `/api/files/<id>/download` | 下载文件 |
| GET | `/api/files/<id>/preview` | 预览文件（图片/PDF） |
| GET | `/api/files/quota` | 查询配额使用情况 |

### 5.3 分享 API

| 方法 | 路由 | 说明 |
|------|------|------|
| POST | `/api/files/share` | 分享文件/文件夹给用户或部门 |
| GET | `/api/files/shared-with-me` | 获取别人分享给我的文件 |
| GET | `/api/files/my-shares` | 获取我分享出去的列表 |
| DELETE | `/api/files/share/<id>` | 取消分享 |

### 5.4 公司文件库 API

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/files/company` | 获取公司公共文件列表 |
| POST | `/api/files/company/upload` | 上传公司文件（需管理权限） |
| PUT | `/api/files/company/<id>` | 修改公司文件信息（需管理权限） |
| DELETE | `/api/files/company/<id>` | 删除公司文件（需管理权限） |

### 5.5 回收站 API

| 方法 | 路由 | 说明 |
|------|------|------|
| GET | `/api/files/trash` | 获取回收站文件列表 |
| POST | `/api/files/trash/<id>/restore` | 恢复文件 |
| DELETE | `/api/files/trash/<id>` | 永久删除 |
| DELETE | `/api/files/trash/empty` | 清空回收站 |

---

## 6. 页面设计

### 6.1 文件管理主页面

路由：`/files`
模板：`app/templates/files/tw_file_manager.html`

```
┌──────────────────────────────────────────────────────────┐
│  文件管理                               已用 1.2GB / 10GB │
│                                          ████░░░░░░ 12%  │
├──────────┬───────────────────────────────────────────────┤
│ 侧边栏    │  📁 全部文件  >  合同文档        [新建文件夹] [上传] │
│          │ ──────────────────────────────────────────── │
│ 📁 全部文件│  ☐  名称           大小     修改时间    操作    │
│ 📁 合同文档│  ☐  📁 子文件夹A     -       02-14     ···    │
│ 📁 技术资料│  ☐  📄 合同.pdf     2.3MB   02-13     ···    │
│ 📁 客户报价│  ☐  📄 报价单.xlsx  1.1MB   02-12     ···    │
│          │  ☐  🖼️ 产品图.png   800KB   02-10     ···    │
│ ──────── │                                               │
│ 📤 共享给我│  共 4 个项目，已用 4.2MB                        │
│ 🏢 公司文件│                                               │
│ 🗑️ 回收站 │                                               │
│          │                                               │
│ ──────── │                                               │
│ ⚙️ 设置   │                                               │
└──────────┴───────────────────────────────────────────────┘
```

### 6.2 操作交互

| 操作 | 交互方式 |
|------|---------|
| 上传文件 | 点击上传按钮或拖拽到文件区域 |
| 新建文件夹 | 弹出输入框输入名称 |
| 重命名 | 点击名称直接编辑（inline edit） |
| 移动 | 拖拽到侧边栏文件夹，或右键菜单选择"移动到" |
| 删除 | 右键菜单或工具栏删除按钮，移入回收站 |
| 分享 | 右键菜单"分享"，弹出用户/部门选择器（复用现有树状选择器） |
| 预览 | 点击文件名，图片/PDF 直接预览，其他类型触发下载 |
| 下载 | 右键菜单或操作列下载按钮 |
| 批量操作 | 勾选多个文件后，工具栏显示批量移动/删除/下载 |

### 6.3 共享给我视图

```
┌─────────────────────────────────────────────────────┐
│  共享给我                                             │
│ ─────────────────────────────────────────────────── │
│  名称             分享者      类型      时间          │
│  📁 Q1 报价资料    张三       部门分享   02-13        │
│  📄 技术规格.pdf   李四       个人分享   02-12        │
│  📄 合同模板.docx  王五       个人分享   02-10        │
└─────────────────────────────────────────────────────┘
```

### 6.4 公司文件库视图

```
┌─────────────────────────────────────────────────────┐
│  公司文件库                      [上传] (仅管理员可见)  │
│ ─────────────────────────────────────────────────── │
│  📌 模板文件                                         │
│     📄 报价单模板 v3.docx      上传者: 管理员  01-15  │
│     📄 合同模板.docx           上传者: 管理员  01-10  │
│                                                     │
│  📋 公司制度                                         │
│     📄 考勤制度 2026.pdf       上传者: HR     01-05  │
│     📄 报销规范.pdf            上传者: 财务   12-20  │
│                                                     │
│  📚 参考资料                                         │
│     📄 产品手册 v5.pdf         上传者: 技术   02-01  │
└─────────────────────────────────────────────────────┘
```

---

## 7. 权限设计

### 7.1 个人文件

| 角色 | 权限 |
|------|------|
| 文件所有者 | 完全控制（上传、下载、删除、分享、管理文件夹） |
| 被分享者（read） | 只读（查看、下载） |
| 被分享者（write） | 读写（查看、下载、上传到分享文件夹） |
| 管理员 | 可查看所有用户的配额使用情况，可调整配额上限 |

### 7.2 公司文件库

| 角色 | 权限 |
|------|------|
| 管理员 (admin) | 上传、编辑、删除、管理分类 |
| 指定管理员 | 通过权限配置，授予特定用户公司文件管理权限 |
| 普通员工 | 只读（查看、下载） |

### 7.3 配额管理

| 操作 | 说明 |
|------|------|
| 上传文件 | 检查 `storage_used + file_size <= storage_quota`，超出拒绝 |
| 删除文件引用 | 移入回收站，**不释放配额**（文件仍占空间） |
| 永久删除/清空回收站 | 如果 `ref_count` 降为 0，删除物理文件，释放配额 |
| 去重上传 | 文件库已存在相同 hash，仅创建引用，**不增加配额占用**（物理文件共享） |

**配额计算规则**：按用户 UserFileRef 关联的 FileLibrary.file_size 求和（去重后）。即如果同一个文件在你的不同文件夹各有一个引用，只计算一次空间。

---

## 8. 分享机制详细设计

### 8.1 分享类型

```python
# 分享给个人
FileShare(
    shared_by=current_user.id,
    file_ref_id=123,
    share_type='user',
    target_user_id=456,
    permission='read'
)

# 分享给部门
FileShare(
    shared_by=current_user.id,
    folder_id=789,
    share_type='department',
    target_department_id=10,
    permission='read'
)

# 分享给全公司
FileShare(
    shared_by=current_user.id,
    file_ref_id=123,
    share_type='company',
    target_company_name='上海XX公司',
    permission='read'
)
```

### 8.2 分享 UI 交互

复用 PMA 现有的树状用户选择器组件（`SharingService.get_shareable_users_tree()`），在分享弹窗中：

1. 选择分享对象：人员树（按公司 → 部门 → 人员展开）或部门列表
2. 选择权限：只读 / 可编辑
3. 可选设置过期时间
4. 确认分享

### 8.3 "保存到我的文件"

未来扩展：在任务附件、日志等位置添加"保存到我的文件"按钮：
- 计算附件的 SHA256
- 在 FileLibrary 中查找（去重）
- 创建 UserFileRef 到用户选择的文件夹
- 不重复上传物理文件

---

## 9. 文件上传流程

```
用户选择文件
    │
    ▼
前端计算 SHA256 (Web Crypto API)
    │
    ▼
POST /api/files/check-hash  ──── hash 已存在 ────→ 直接创建 UserFileRef
    │                                                （秒传，不上传文件）
    │ hash 不存在
    ▼
检查配额是否足够
    │
    │ 配额不足 → 返回错误提示
    │
    ▼
POST /api/files/upload (multipart/form-data)
    │
    ▼
后端接收文件 → 验证 SHA256 → 存入 NAS
    │
    ▼
创建 FileLibrary + UserFileRef
    │
    ▼
更新 User.storage_used
    │
    ▼
返回成功
```

---

## 10. 技术选型

| 技术点 | 选择 | 原因 |
|--------|------|------|
| 前端框架 | Alpine.js + Tailwind | 与 PMA 现有技术栈一致 |
| 文件上传组件 | 扩展现有 `file-upload-component.js` | 复用已有代码 |
| SHA256 计算 | 前端: Web Crypto API, 后端: hashlib | 双重验证 |
| 存储 | NAS WebDAV (SmartStorageManager) | 复用现有基础设施 |
| 拖拽排序 | SortableJS (已引入) | 文件夹/文件拖拽排序和移动 |
| 用户选择器 | 现有 SharingService 树状组件 | 复用分享功能 |

---

## 11. 分阶段实施计划

### Phase 1：个人文件空间（核心功能）

**预计工作量**：主要开发内容

1. 数据库模型创建（FileLibrary, UserFolder, UserFileRef）+ 迁移
2. User 模型添加 storage_quota / storage_used 字段
3. 文件上传服务（SHA256 去重 + NAS 存储）
4. 文件夹 CRUD API
5. 文件 CRUD API（上传、下载、预览、删除）
6. 配额检查和管理
7. 回收站功能
8. 前端文件管理页面（侧边栏 + 文件列表 + 上传 + 文件夹管理）
9. 导航入口（tw_layout 侧边栏添加"文件管理"）

### Phase 2：分享功能

1. FileShare 模型 + 迁移
2. 分享 API（创建、查看、取消）
3. "共享给我"视图
4. 分享弹窗 UI（复用树状用户选择器）
5. 分享权限校验

### Phase 3：公司公共文件库

1. CompanyFile 模型 + 迁移
2. 公司文件 CRUD API
3. 公司文件管理权限配置
4. 公司文件库 UI（分类展示 + 管理界面）

### Phase 4：扩展集成（可选）

1. "保存到我的文件"按钮（任务附件、日志等场景）
2. 文件搜索（按文件名、标签搜索）
3. 管理员配额管理面板
4. 文件版本管理（同名文件多版本）

---

## 12. 文件组织

### 新增文件清单

```
app/
├── models/
│   └── file_manager.py              # FileLibrary, UserFolder, UserFileRef, FileShare, CompanyFile
├── services/
│   └── file_manager_service.py      # 文件上传/去重/配额管理业务逻辑
├── views/
│   └── file_manager.py              # API 路由
├── templates/
│   └── files/
│       └── tw_file_manager.html     # 文件管理主页面
├── static/
│   └── js/
│       └── file-manager.js          # 文件管理前端逻辑
```

### 修改文件清单

```
app/
├── models/
│   └── user.py                      # 添加 storage_quota, storage_used 字段
├── __init__.py                      # 注册 file_manager blueprint
├── templates/
│   └── components/
│       └── tw_layout.html           # 侧边栏添加"文件管理"入口
├── utils/
│   └── smart_storage_manager.py     # 添加 'file_library' 存储桶映射
```

---

## 13. 安全考虑

| 安全项 | 措施 |
|--------|------|
| 文件类型限制 | 白名单：图片、PDF、Office 文档、压缩包，禁止可执行文件 |
| 文件大小限制 | 单文件最大 50MB（可配置） |
| 路径遍历 | 存储路径使用 hash，不使用用户输入的文件名 |
| 权限校验 | 每次文件访问校验 owner_id 或 share 关系 |
| CSRF | 所有 POST/PUT/DELETE 接口验证 CSRF token |
| 配额绕过 | 后端强制校验配额，不信任前端 |

---

## 14. 回收站机制

| 规则 | 说明 |
|------|------|
| 删除文件 | `UserFileRef.is_deleted = True`，文件进入回收站 |
| 删除文件夹 | 文件夹及内部所有文件标记 `is_deleted = True` |
| 恢复 | 重置 `is_deleted = False`，恢复到原文件夹（如原文件夹已删则恢复到根目录） |
| 自动清理 | 30 天后自动永久删除回收站中的文件 |
| 永久删除 | `FileLibrary.ref_count -= 1`，如降为 0 则删除 NAS 物理文件 |
| 配额释放 | 仅在永久删除时释放配额 |
