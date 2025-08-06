#!/usr/bin/env python3
"""拒绝 vs 召回的详细对比分析"""

def compare_reject_vs_recall():
    """对比拒绝和召回的处理逻辑"""
    
    print("🔍 审批拒绝 vs 审批召回 详细对比")
    print("=" * 80)
    
    # 拒绝的处理逻辑
    reject_logic = {
        "触发方式": "审批人在审批过程中点击'拒绝'",
        "触发时机": "审批流程进行中（PENDING状态）",
        "触发权限": "当前步骤的审批人",
        "实例状态": "REJECTED",
        "业务对象状态": "rejected 或 draft",
        "对象锁定": "解锁（可重新编辑）",
        "审批记录": "创建action='reject'的记录",
        "流程结束": "是，审批流程终止",
        "重新发起": "可以重新发起新的审批流程"
    }
    
    # 召回的处理逻辑  
    recall_logic = {
        "触发方式": "发起人主动召回审批",
        "触发时机": "审批流程进行中（PENDING状态）",
        "触发权限": "审批流程的创建者（发起人）",
        "实例状态": "RECALLED",
        "业务对象状态": "draft",
        "对象锁定": "解锁（可重新编辑）",
        "审批记录": "创建action='recall'的记录",
        "流程结束": "是，审批流程终止",
        "重新发起": "可以重新发起新的审批流程"
    }
    
    print("📊 逻辑对比表:")
    print()
    
    # 打印对比表格
    headers = ["特征", "拒绝 (REJECT)", "召回 (RECALL)"]
    print(f"{'特征':<15} | {'拒绝 (REJECT)':<30} | {'召回 (RECALL)':<30}")
    print("-" * 80)
    
    for key in reject_logic.keys():
        reject_val = reject_logic[key]
        recall_val = recall_logic[key]
        print(f"{key:<15} | {reject_val:<30} | {recall_val:<30}")
    
    print("\n" + "=" * 80)
    
    return reject_logic, recall_logic

def analyze_similarities():
    """分析相似之处"""
    
    print("🤝 相似之处:")
    print("=" * 80)
    
    similarities = [
        "✅ 都会终止当前审批流程",
        "✅ 实例状态都变为终止状态（REJECTED/RECALLED）",
        "✅ 都会解锁业务对象，允许重新编辑",
        "✅ 都会更新业务对象状态为可编辑状态",
        "✅ 都允许重新发起新的审批流程",
        "✅ 都会创建操作记录（ApprovalRecord）",
        "✅ 在创建新实例时，都被视为'非活跃'状态",
        "✅ 都会保留完整的历史记录用于审计"
    ]
    
    for similarity in similarities:
        print(similarity)
    
    print("\n" + "=" * 80)

def analyze_differences():
    """分析关键差异"""
    
    print("⚡ 关键差异:")
    print("=" * 80)
    
    print("1️⃣ 权限差异:")
    print("   拒绝: 只有当前步骤的审批人可以操作")
    print("   召回: 只有审批流程的发起人可以操作")
    print()
    
    print("2️⃣ 触发场景差异:")
    print("   拒绝: 审批人认为申请不符合要求，主动拒绝")
    print("   召回: 发起人发现申请有误，需要修改后重新提交")
    print()
    
    print("3️⃣ 业务含义差异:")
    print("   拒绝: 审批失败，申请被正式否决")
    print("   召回: 主动撤回，准备修改后重新申请")
    print()
    
    print("4️⃣ 记录类型差异:")
    print("   拒绝: ApprovalRecord.action = 'reject'")
    print("   召回: ApprovalRecord.action = 'recall'")
    print()
    
    print("5️⃣ 历史追踪差异:")
    print("   拒绝: 显示为'被XX拒绝'")
    print("   召回: 显示为'被发起人召回'")
    
    print("\n" + "=" * 80)

def demonstrate_code_logic():
    """演示代码处理逻辑"""
    
    print("💻 代码处理逻辑:")
    print("=" * 80)
    
    print("📝 拒绝处理代码:")
    print("```python")
    print("if action == ApprovalAction.REJECT:")
    print("    # 1. 更新实例状态")
    print("    instance.status = ApprovalStatus.REJECTED")
    print("    instance.ended_at = datetime.now()")
    print("    ")
    print("    # 2. 创建拒绝记录") 
    print("    record = ApprovalRecord(")
    print("        instance_id=instance.id,")
    print("        action='reject',")
    print("        approver_id=current_approver_id,")
    print("        comment=reject_reason")
    print("    )")
    print("    ")
    print("    # 3. 更新业务对象状态")
    print("    expense.status = 'rejected'  # 或 'draft'")
    print("    expense.is_locked = False")
    print("```")
    print()
    
    print("📝 召回处理代码:")
    print("```python") 
    print("def recall_approval_process(object_type, object_id, user_id):")
    print("    # 1. 权限检查")
    print("    if instance.created_by != user_id:")
    print("        return False, '只有创建者才能召回'")
    print("    ")
    print("    # 2. 更新实例状态")
    print("    instance.status = ApprovalStatus.RECALLED")
    print("    instance.ended_at = datetime.now()")
    print("    ")
    print("    # 3. 更新业务对象状态")
    print("    expense.status = 'draft'")
    print("    expense.is_locked = False")
    print("```")
    
    print("\n" + "=" * 80)

def show_multi_instance_handling():
    """展示多实例处理的一致性"""
    
    print("🔄 多实例处理的一致性:")
    print("=" * 80)
    
    print("📋 创建新实例时的检查逻辑:")
    print("```python")
    print("def can_create_new_instance(object_type, object_id):")
    print("    existing = get_object_approval_instance(object_type, object_id)")
    print("    ")
    print("    # ❌ 阻止创建：活跃状态")
    print("    if existing and existing.status in ['PENDING', 'APPROVED']:")
    print("        return False")
    print("    ")
    print("    # ✅ 允许创建：终止状态（拒绝和召回处理相同）")
    print("    if existing and existing.status in ['REJECTED', 'RECALLED']:")
    print("        return True")
    print("    ")
    print("    return True  # 无现有实例")
    print("```")
    print()
    
    print("🎯 关键点:")
    print("✅ 拒绝和召回在多实例管理上完全一致")
    print("✅ 都被视为'终止状态'，允许创建新实例")
    print("✅ 旧实例都保留用于历史追踪")
    print("✅ 新实例都会成为当前活跃实例")
    
    print("\n" + "=" * 80)

def show_real_world_scenarios():
    """展示实际应用场景"""
    
    print("🌍 实际应用场景:")
    print("=" * 80)
    
    print("📄 场景1：审批拒绝")
    print("时间线:")
    print("09:00 - 员工A提交报销单BX001 → 实例1(PENDING)")
    print("10:00 - 财务B审批，发现发票不合规 → 点击'拒绝'")
    print("10:01 - 实例1状态 → REJECTED，报销单状态 → rejected")
    print("11:00 - 员工A修改报销单，重新提交 → 实例2(PENDING)")
    print("结果: 实例1(REJECTED) + 实例2(PENDING)")
    print()
    
    print("📄 场景2：主动召回")
    print("时间线:")
    print("14:00 - 员工A提交报销单BX002 → 实例1(PENDING)")
    print("15:00 - 员工A发现金额填错，主动召回")
    print("15:01 - 实例1状态 → RECALLED，报销单状态 → draft")
    print("16:00 - 员工A修改金额，重新提交 → 实例2(PENDING)")
    print("结果: 实例1(RECALLED) + 实例2(PENDING)")
    print()
    
    print("🔍 业务含义差异:")
    print("拒绝: '这个申请有问题，不能通过'")
    print("召回: '我要修改这个申请，先撤回'")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print("🧪 审批拒绝 vs 审批召回 完整对比分析")
    print("目标：理解两种终止方式的异同点")
    print("=" * 80)
    
    compare_reject_vs_recall()
    analyze_similarities()
    analyze_differences()
    demonstrate_code_logic()
    show_multi_instance_handling()
    show_real_world_scenarios()
    
    print("🎯 总结:")
    print("1. 拒绝和召回在技术处理上高度相似")
    print("2. 主要差异在于触发权限和业务含义")
    print("3. 多实例管理逻辑完全一致")
    print("4. 都能保证审批流程的完整性和可追溯性")
    print("=" * 80)