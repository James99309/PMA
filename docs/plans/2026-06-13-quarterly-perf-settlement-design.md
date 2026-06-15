# 季度绩效结算审批 + 联动薪资 设计

2026-06-13 确认。把每季度的绩效得分,经 HR 发起、上级与总经理审批后,折算成「绩效薪资」金额写入个人薪资,并锁定该季度的薪资绩效部分。

## 用户确认的决策
- **折算规则**:绩效基数 × 得分%。薪资结构「绩效薪资」(performance_salary)的个人标准金额 = 满分基数;季度结算金额 = 季度绩效基数 × 季度得分 ÷ 100。
- **审批层级**:HR 发起 → 当事人直属上级确认 → 总经理终审(两级)。
- **锁定范围**:只锁该季度的薪资绩效部分(performance_salary 该季度月份只读);其他薪资项、绩效目标/实际值仍可编辑。

## 数据模型(Phase 1)
新表 `performance_settlements`:
- user_id, year, quarter(1-4)
- score(Numeric 季度得分快照)
- base_amount(季度绩效基数快照,元)
- settled_amount(折算金额 = base × score/100,元)
- score_snapshot(JSON:每项 code/name/weight/actual/target/达成率/加权,留痕)
- status(draft / pending / approved / rejected)
- initiated_by(HR), approval_instance_id, settled_at, is_locked
- UNIQUE(user_id, year, quarter)

## 审批流(Phase 2)
- object_type = `perf_settlement`,复用 dealer_apply 同款骨架(get-or-create 模板 + 两步 submitter_designate + resolve)。
- resolve 审批人:
  - 直属上级 = Affiliation(owner_id=当事人).viewer_id,优先 is_department_manager;缺位回退部门经理。
  - 总经理 = role=ceo 在职激活。
- HR 发起 = submitter;两步:① 直属上级 ② 总经理。

## 折算 + 导入(Phase 3,dispatch 回调)
- 季度绩效基数:performance_salary 个人标准金额 × 季度期数(月发×3 / 季发×1 / 年发→季度按 1/4)。
- 通过(APPROVED)→ settled_amount 写入 user_salary_items.performance_salary 的 monthly_amounts[季末月](Q1→3、Q2→6、Q3→9、Q4→12);标记 settlement.is_locked=True、settled_at。
- 驳回/召回 → 解锁,可重新发起。

## 前端(Phase 4)
- 发起入口:个人绩效目标页加「发起季度结算」(选季度,显示当季得分快照预览 → 提交审批)。
- 结算状态展示:绩效页显示各季度结算状态徽章(待审批/已结算/已锁定 + 金额)。
- 薪资页:performance_salary 已结算季度的月份格只读(灰 + 锁标),tooltip「绩效结算已锁定」。

## 阶段交付
1. **P1** 模型 + 迁移(本次)
2. **P2** 审批流 helper(resolve + 模板 + submit)
3. **P3** dispatch 回调(折算 + 写薪资 + 锁定)
4. **P4** 前端(发起入口 + 状态展示 + 薪资锁定)

每阶段本地测试稳定后再进下一阶段;全部完成后统一提交部署。
