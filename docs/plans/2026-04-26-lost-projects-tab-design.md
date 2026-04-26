# 流失项目标签设计

**日期**：2026-04-26
**模块**：市场情报库（prospect）
**目的**：在市场情报库中新增"流失项目"标签，把销售手中已流失但未签约的项目暴露给其他销售/代理商，鼓励申请承接，同时不暴露原负责人的核心商业资源。

---

## 1. 需求来源

- 销售手中有项目长期无进展（120+ 天无活动），但仍占着归属，其他销售看不到
- 团队希望让这些"沉睡资源"被同事或代理商发现并接手
- 同时要保护：客户联系方式、报价、跟进记录等敏感数据不能泄露给非负责人

---

## 2. 范围与定义

### 2.1 流失项目过滤条件

实时查询 `projects` 表：

```python
Project.query.filter(
    Project.is_deleted == False,
    Project.activity_status == 'churned',         # 活跃度=流失
    Project.stage != '签约',                       # 阶段非签约（不在 FROZEN_STAGES）
)
```

**注意**：`activity_status` 由 `app/utils/activity_tracker.py` 统一计算。本次会修改该计算逻辑（见 §3）。

### 2.2 活跃度计算逻辑修改（关键）

修改 `calculate_project_activity()`，增加两条优先规则：

```python
def calculate_project_activity(project):
    # 规则 1：终态项目永远 frozen（最高优先级，已存在）
    if project.stage in FROZEN_STAGES:  # 含 '签约', '竣工' 等
        return 'frozen', f'项目已{stage_label}，活跃度已冻结', project.last_activity_date

    # 规则 2【新增】：负责人离职 / 无负责人 → churned
    if not project.owner_id:
        return 'churned', '无负责人', project.last_activity_date
    if project.owner and not project.owner.is_active:
        return 'churned', '负责人已离职', project.last_activity_date

    # 规则 3：原有 6 级时间规则（活跃/正常/待跟进/休眠/流失）
    ...
```

**触发时机（双保险）**：
1. **实时**：admin 在 `/admin/users` 把某用户 `is_active=False` 时，hook 同步更新该用户名下所有非 frozen 项目的 `activity_status`
2. **定时**：现有 `scheduled_tasks.py` 的项目活跃度批处理任务自然覆盖

**反向恢复**：用户重新激活后，下一次活跃度计算自动按真实活动天数重算（无需特殊代码）。

---

## 3. 数据模型变更

### 3.1 ProspectProject 新增字段

```python
# app/models/prospect_project.py
class ProspectProject(db.Model):
    ...
    link_type = Column(String(20), nullable=False, server_default='converted')
    # 'converted': 原用法（市场情报线索 → 转化为正式项目）
    # 'research':  新用法（从已存在项目反向调研，存放 AI 补全数据）
```

**Migration**：
- 新增 `link_type` 列，默认 `'converted'`，已有数据全部回填 `'converted'`（保持兼容）
- 流失项目 AI 调研补全时，新建 ProspectProject 记录，写 `link_type='research'`，`converted_project_id` 指向源 Project

### 3.2 流失项目申请表（新表）

```python
# app/models/prospect_claim_request.py
class ProspectClaimRequest(db.Model):
    __tablename__ = 'prospect_claim_requests'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    reason = Column(Text, nullable=False)         # 申请人填写的理由
    status = Column(String(20), default='pending', nullable=False)
    # pending / handled (负责人手动处理后由系统不区分，状态保留待将来扩展)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('project_id', 'applicant_id', name='uq_claim_project_applicant'),
    )
```

**唯一约束的语义**：同一申请人对同一项目只能申请一次（永久去重）。如果业务后续需要"过期重申"，再扩展 status 即可。

### 3.3 复用现有 Message 模型

申请提交时同步创建一条 Message：

```python
Message(
    recipient_id=project.owner_id,
    sender_id=current_user.id,
    message_type='prospect_claim_request',
    title=f'{current_user.real_name} 申请参与流失项目《{project.project_name}》',
    content=reason,
    related_object_type='project',
    related_object_id=project.id,
    extra_data={'claim_request_id': claim_request.id}
)
```

待办列表（现有 Message 收件箱）会自动渲染。

---

## 4. 路由与视图

### 4.1 标签页

**入口**：`app/templates/prospect/tw_list.html` 顶部增加 Tab 切换器
- Tab 1：**市场情报**（默认，现有列表）—— 过滤 `link_type='converted' AND converted_project_id IS NULL`
- Tab 2：**流失项目**（新增）

**实现**：
- 同一路由 `/prospect/`，URL 加 query `?tab=lost`
- 后端在 `app/views/prospect.py::list_view` 根据 `tab` 参数走不同查询分支

### 4.2 流失项目详情页

**新路由**：`GET /prospect/lost/<int:project_id>`
**模板**：`app/templates/prospect/tw_lost_detail.html`

**展示分区**：

| 分区 | 内容 | 谁能看 |
|---|---|---|
| 顶部 | 项目名、阶段、行业、地区、城市、投资规模、流失原因、申领人姓名+角色 | 所有可见用户 |
| 项目描述 | description（来自 Project 或调研补全） | 所有可见用户 |
| 项目进展 | progress（仅 AI 调研后存在） | 所有可见用户 |
| 关联方公司层 | 公司名、类型、地址、官网、业务范围、备注 | 所有可见用户 |
| 关联方联系人 | 姓名、电话、邮件、部门 | 仅 owner+共享+admin |
| 客户/报价/批价/跟进 | （锁图标占位） | 仅 owner+共享+admin |

**操作按钮**：

| 按钮 | 显示条件 |
|---|---|
| **申请参与** | 当前用户 ≠ owner、≠ 共享用户、≠ admin |
| **AI 调研补全** | 当前用户 = owner / 共享用户 / 部门上级 / admin（即 `can_view_project(user, project)` 通过） |
| **撤销申请** | 当前用户已提交过申请且未被处理 |

---

## 5. 申请参与流程（极简版）

```
[流失项目详情页]
        ↓ 点击 "申请参与" 按钮
[弹窗: 输入申请理由（必填，≥10字）]
        ↓ 提交
[后端]
  - 校验：用户有项目模块权限
  - 校验：(project_id, applicant_id) 唯一约束
  - 创建 ProspectClaimRequest
  - 创建 Message → recipient = Project.owner_id
        ↓ 待办列表推送
[原负责人 owner]
  - 在待办列表看到通知（含申请人姓名+理由）
  - 点击跳转到 Project 正式详情页
  - 线下决定：
      • 同意 → 在项目页用现有"转移负责人"或"添加共享"功能操作
      • 不同意 → 直接忽略待办（可选回复消息）
```

**关键说明**：
- 系统不做自动转移、不做审批按钮
- 负责人完全在现有项目页面里手动操作
- 通知 = 单纯的"待办提醒"

**代理商类申领人**：
Project.owner_id 始终是系统内 User（即使项目实际由代理商主导，owner 通常填内部销售对接人）。通知一律发给 owner_id。
若 owner_id 为空（无负责人项目），消息发给所有 admin（兜底）。

---

## 6. AI 调研补全

### 6.1 触发权限

仅以下用户能在流失项目详情页点 "AI 调研补全"：
- Project.owner_id 本人
- Project.shared_with_users 中的用户
- 通过 Affiliation 上下级关系拥有该项目权限的部门上级
- 拥有 `project.view` system 级权限的管理员

技术上：调用 `can_view_project(current_user, project)` 通过即可（即"现有项目权限系统判定能看到该项目的人"）。

### 6.2 流程

```
[详情页] "AI 调研补全" 按钮
        ↓ 点击
[后端 /prospect/lost/<project_id>/ai_research]
  - 校验权限
  - 检查是否已存在 prospect_projects.converted_project_id == project_id
                        AND link_type == 'research'
      • 有 → 取该记录，准备增量更新
      • 无 → 新建一条 ProspectProject(link_type='research', converted_project_id=project_id)
  - 调用 app/services/ai_research_service 调研：
      入参：project.project_name, project.region, customer_name (脱敏)
      出参：description / progress / stakeholders（公司层）
  - 写回到 prospect_project 记录
        ↓
[流失详情页刷新展示]
```

**关键约束**：AI 调研结果**只写到 prospect_projects 表**，**不修改 projects 表**任何字段。

---

## 7. 权限矩阵（汇总）

| 操作 | admin | owner | shared_with | 部门上级 | 其他销售/代理商 | 普通员工 |
|---|---|---|---|---|---|---|
| 看到"流失项目"标签 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 列表查看基本信息 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 进入公开详情页 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 看关联方公司层 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 看关联方联系人 | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 看客户/报价/跟进 | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 触发 AI 调研补全 | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 申请参与（发待办） | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

"普通员工"指无 `project.view` 或 `customer.view` 权限的人。
"其他销售/代理商"指有项目模块权限但不在该项目权限范围内的用户。

---

## 8. 列表页字段

**所有可见用户都能看到的列**：

| 列 | 内容 |
|---|---|
| 项目名称 | 文字（可点击进详情） |
| 阶段 | 徽章 |
| 行业 | 文字，空值显示"未分类" |
| 地区 | 文字 |
| 投资规模 | 文字 |
| 关联方 | 类型聚合统计，如"设计院 1·总包 1"（只统计数量，不显示企业名） |
| 申领人 | 姓名 + 角色标签（销售 / 代理商） |
| 活跃度 | "流失" 红色徽章 + reason tooltip（120 天无活动 / 负责人已离职 / 无负责人） |

**筛选项**：地区、行业（含"未分类"选项）、阶段、流失原因。

---

## 9. 实施顺序（建议）

1. **后端基础**
   - migration: ProspectProject 加 `link_type`，新表 ProspectClaimRequest
   - 修改 `activity_tracker.py` 加离职 / 无负责人规则
   - admin 用户停用钩子触发活跃度更新
   - 单测覆盖

2. **后端 API**
   - 列表接口（支持 tab=lost）
   - 流失详情接口（区分敏感字段）
   - 申请参与 POST 接口
   - AI 调研补全 POST 接口

3. **前端**
   - tw_list.html 加 Tab 切换器
   - tw_lost_detail.html 公开详情页
   - 申请参与弹窗
   - 待办列表渲染 `prospect_claim_request` 类型消息

4. **联调**
   - 权限矩阵全场景测试
   - i18n（中英文）
   - 部署

---

## 10. 未决事项 / 后续可扩展

- 申请被忽略后，长期未处理的待办是否需要兜底（admin 介入）—— 当前不做
- 申请理由的最少字数 / 字数上限 —— 设 10~500 字
- 流失项目能否被批量"申请参与" —— 当前一次一个
- 是否记录"申请被同意/拒绝"的最终结果 —— 当前不记录，只记申请发出，后续如要数据分析再扩展 status

---

## 11. 文件清单（实施时需要触动的）

**新增**：
- `migrations/versions/<hash>_add_link_type_and_claim_request.py`
- `app/models/prospect_claim_request.py`
- `app/templates/prospect/tw_lost_detail.html`
- `app/templates/prospect/_lost_list_tab.html` (Tab 内容片段)
- `tests/test_prospect_lost_projects.py`

**修改**：
- `app/models/prospect_project.py` (加 link_type)
- `app/models/__init__.py` (注册新模型)
- `app/utils/activity_tracker.py` (加离职/无负责人规则)
- `app/views/prospect.py` (Tab 路由 + 流失详情 + 申请 API + AI 调研 API)
- `app/views/admin.py` (用户停用钩子)
- `app/templates/prospect/tw_list.html` (Tab 切换器)
- `app/templates/messages/_inbox.html` 或类似 (新消息类型渲染)
- `app/translations/*/messages.po` (新文案 i18n)

---

**最后更新**：2026-04-26
**负责人**：（待定）
**关联**：[2026-04-26-prospect-project-intelligence.md](./2026-04-26-prospect-project-intelligence.md)
