# 解决方案经理确认流程简化 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 简化报价单确认徽章系统 — 移除冗余的门控和自动清除逻辑，移除硬编码角色访问，激活报价单创建/修改时对解决方案经理的站内消息通知。

**Architecture:** 减法为主。删除4处代码（硬编码访问、阶段推进检查、签名自动清除、审批后自动pending），替换2处注释代码为实际通知调用。确认徽章的唯一硬门控保留在批价单提交处。

**Tech Stack:** Python/Flask, SQLAlchemy, 现有 Message 模型

---

## 变更总览

| 操作 | 文件 | 说明 |
|------|------|------|
| 删除 | `app/models/user.py:416-423` | 硬编码 solution_manager 查看所有报价单 owner |
| 删除 | `app/views/project.py:2361-2368` | 项目推进签约时的 badge 检查（OR 分支） |
| 删除 | `app/views/project.py:2537-2544` | 同上（第二处重复逻辑） |
| 删除 | `app/models/quotation.py:533-615` | event listener 中签名变化自动清除确认 |
| 删除 | `app/views/quotation.py:3569-3588` | 保存时手动签名检测+清除确认状态 |
| 删除 | `app/helpers/approval_helpers.py:5422` | 审批通过后自动 set_pending |
| 删除 | `app/views/approval.py:1476` | 同上（第二处） |
| 激活 | `app/views/quotation.py:1427-1432` | 创建报价单后通知解决方案经理 |
| 激活 | `app/views/quotation.py:3622-3627` | 修改报价单后通知解决方案经理 |
| 保留 | `app/services/pricing_order_service.py:90` | 批价单提交时要求 confirmed（不改） |
| 保留 | `app/routes/quotation.py` | SM 手动设置/清除 badge API（不改） |

---

### Task 1: 移除硬编码 solution_manager 报价单访问

**Files:**
- Modify: `app/models/user.py:416-423`

**Step 1: 移除硬编码**

删除 `get_viewable_user_ids()` 中 solution_manager 查看所有报价单 owner 的硬编码逻辑。

```python
# 删除这段代码（第416-423行）:
        # 产品经理和解决方案经理可以查看所有报价单所有者的数据
        if self.role in ['product_manager', 'solution_manager']:
            from app.models.quotation import Quotation
            # 获取所有报价单所有者的ID
            owner_ids = db.session.query(Quotation.owner_id).distinct().all()
            for owner_id in owner_ids:
                if owner_id[0] and owner_id[0] not in viewable_ids:
                    viewable_ids.append(owner_id[0])
```

> **注意**: 只删除 `solution_manager` 的部分。`product_manager` 是否保留需确认。如果保守起见，改为只保留 product_manager：
> ```python
>         if self.role in ['product_manager']:
> ```

**Step 2: Commit**

```bash
git commit -m "refactor: remove hardcoded solution_manager quotation access from get_viewable_user_ids"
```

---

### Task 2: 移除项目推进签约时的 badge 检查

**Files:**
- Modify: `app/views/project.py:2361-2368`（第一处）
- Modify: `app/views/project.py:2537-2544`（第二处）

**Step 1: 修改第一处（POST 推进逻辑）**

将 `has_approval` 条件中的 confirmation_badge OR 分支移除，只保留传统审核流程检查：

```python
# 原代码（第2361-2368行）:
            has_approval = (
                (latest_quotation.approval_status and
                 latest_quotation.approval_status != 'pending' and
                 latest_quotation.approval_status != 'rejected' and
                 latest_quotation.approved_stages) or
                (latest_quotation.confirmation_badge_status == 'confirmed')
            )

# 改为:
            has_approval = (
                latest_quotation.approval_status and
                latest_quotation.approval_status != 'pending' and
                latest_quotation.approval_status != 'rejected' and
                latest_quotation.approved_stages
            )
```

**Step 2: 修改第二处（GET 检查逻辑）**

同样的修改应用于第 2537-2544 行。

**Step 3: Commit**

```bash
git commit -m "refactor: remove confirmation badge check from project stage progression"
```

---

### Task 3: 简化 event listener — 移除签名自动清除确认逻辑

**Files:**
- Modify: `app/models/quotation.py:533-615`

**Step 1: 简化 event listener**

保留 `implant_total_amount` 的自动计算，移除 signature 比对和确认状态清除：

```python
# 替换整个 update_quotation_product_signature 函数为:
@event.listens_for(QuotationDetail, 'after_insert')
@event.listens_for(QuotationDetail, 'after_update')
@event.listens_for(QuotationDetail, 'after_delete')
def update_quotation_implant_total(mapper, connection, target):
    """产品明细变化时更新报价单的植入总额合计"""
    try:
        quotation_id = target.quotation_id
        if quotation_id:
            result = connection.execute(text("""
                SELECT COALESCE(SUM(implant_subtotal), 0) as implant_total
                FROM quotation_details
                WHERE quotation_id = :quotation_id
            """), {"quotation_id": quotation_id})

            row = result.fetchone()
            if row:
                connection.execute(text("""
                    UPDATE quotations
                    SET implant_total_amount = :implant_total
                    WHERE id = :quotation_id
                """), {"quotation_id": quotation_id, "implant_total": row[0]})
    except Exception as e:
        print(f"更新植入总额合计时发生错误: {str(e)}")
```

**Step 2: Commit**

```bash
git commit -m "refactor: simplify event listener - keep implant calc, remove signature auto-clear"
```

---

### Task 4: 移除报价单保存时的手动签名检测+清除

**Files:**
- Modify: `app/views/quotation.py:3569-3588`

**Step 1: 删除签名检测和确认清除代码块**

删除第 3569-3588 行的 try 块（签名检测+确认清除），保留其后的植入总额计算（3590-3595）。

```python
# 删除这段（3569-3588）:
            # 在提交前进行签名检测和状态处理
            try:
                # 检测产品明细是否发生变化
                new_product_signature = quotation.calculate_product_signature()
                product_details_changed = old_product_signature != new_product_signature

                # 如果产品明细发生关键变化，手动清除确认状态
                if product_details_changed and quotation.confirmation_badge_status == 'confirmed':
                    quotation.confirmation_badge_status = 'none'
                    quotation.confirmation_badge_color = None
                    quotation.confirmed_by = None
                    quotation.confirmed_at = None
                    current_app.logger.info(f"报价单 {quotation.id} 的产品明细发生关键变化（行数或MN号），已手动清除确认状态")

                # 更新产品签名
                quotation.product_signature = new_product_signature
                current_app.logger.debug(f"产品签名更新: {old_product_signature} -> {new_product_signature}, 变化: {product_details_changed}")

            except Exception as signature_error:
                current_app.logger.error(f"处理产品签名和确认状态时出错: {str(signature_error)}")
```

> **注意**: 检查此函数上方是否有 `old_product_signature = ...` 的赋值行也需一并删除。

**Step 2: Commit**

```bash
git commit -m "refactor: remove manual signature detection and badge clearing from quotation save"
```

---

### Task 5: 移除审批后自动 set_pending_confirmation_badge

**Files:**
- Modify: `app/helpers/approval_helpers.py:5422`
- Modify: `app/views/approval.py:1476`

**Step 1: 删除 approval_helpers.py 中的调用**

删除第 5422 行的 `quotation.set_pending_confirmation_badge()`。需要读取上下文确定是否有 try/except 包裹或条件判断。

**Step 2: 删除 approval.py 中的调用**

删除第 1476 行的 `quotation.set_pending_confirmation_badge()`。

**Step 3: Commit**

```bash
git commit -m "refactor: remove auto-pending badge from approval flow"
```

---

### Task 6: 激活报价单创建/修改通知

**Files:**
- Modify: `app/views/quotation.py:1427-1432`（创建通知）
- Modify: `app/views/quotation.py:3622-3627`（修改通知）

**Step 1: 替换创建通知注释代码**

将第 1427-1432 行的注释替换为实际通知逻辑：

```python
                    # 发送站内消息给厂家的解决方案经理
                    try:
                        from app.models.message import Message
                        from app.models.user import User
                        sm_users = User.query.filter_by(
                            role='solution_manager',
                            company_name=current_user.company_name,
                            is_active=True
                        ).all()
                        for sm in sm_users:
                            if sm.id != current_user.id:
                                msg = Message.create_quotation_created(
                                    sender_id=current_user.id,
                                    recipient_id=sm.id,
                                    quotation=quotation
                                )
                                db.session.add(msg)
                        if sm_users:
                            db.session.commit()
                    except Exception as msg_err:
                        current_app.logger.warning(f"发送报价单创建消息失败: {str(msg_err)}")
```

**Step 2: 替换修改通知注释代码**

将第 3622-3627 行的注释替换为相同逻辑（使用 `create_quotation_updated`）：

```python
                # 发送站内消息给厂家的解决方案经理
                try:
                    from app.models.message import Message
                    from app.models.user import User
                    sm_users = User.query.filter_by(
                        role='solution_manager',
                        company_name=current_user.company_name,
                        is_active=True
                    ).all()
                    for sm in sm_users:
                        if sm.id != current_user.id:
                            msg = Message.create_quotation_updated(
                                sender_id=current_user.id,
                                recipient_id=sm.id,
                                quotation=quotation
                            )
                            db.session.add(msg)
                    if sm_users:
                        db.session.commit()
                except Exception as msg_err:
                    current_app.logger.warning(f"发送报价单修改消息失败: {str(msg_err)}")
```

**Step 3: Commit**

```bash
git commit -m "feat: activate quotation create/update notifications to solution managers"
```

---

### Task 7: 验证 & 回归检查

**Step 1: 确认批价单提交门控未受影响**

读取 `app/services/pricing_order_service.py:86-96`，确认 `confirmation_badge_status != 'confirmed'` 检查完好。

**Step 2: 确认 badge 设置/清除 API 未受影响**

读取 `app/routes/quotation.py:8-70`，确认 set/clear badge 端点完好。

**Step 3: 启动应用验证无导入错误**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 -c "from app import create_app; app = create_app(); print('OK')"
```

**Step 4: Commit 最终状态（如有遗漏修复）**

---

## 不修改的文件（确认保留原样）

| 文件 | 保留内容 |
|------|---------|
| `app/services/pricing_order_service.py:90` | `confirmation_badge_status != 'confirmed'` 检查 |
| `app/routes/quotation.py:8-70` | set/clear badge API |
| `app/models/quotation.py:333-370` | `set_confirmation_badge()`, `clear_confirmation_badge()`, `set_pending_confirmation_badge()` 方法体保留（API 仍可调用） |
| `app/models/message.py:515-588` | `create_quotation_created()`, `create_quotation_updated()` 工厂方法 |

## 后续配置（非代码）

移除硬编码后，需要通过 PMA 后台权限管理给 solution_manager 角色配置：
- `quotation` 模块的 `view` 权限（适当的 permission_level）
- `project` 模块的 `view` 权限（如果需要查看关联项目）
