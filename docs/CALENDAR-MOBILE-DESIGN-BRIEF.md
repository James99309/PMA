# 日历 / 工作日志 模块移动端设计简报 (for Claude Design)

> 和 `TASK-MOBILE-DESIGN-BRIEF.md` 同一套流程:把这份 + 你已有的 Claude Design jsx 包
> + web 日历页截图,丢给 Claude Design,产出 **`calendar-screens.jsx`**(与现有 App + 刚出的
> Task 设计同一体系)。本份已尽量自包含。

---

## 0. 设计交付要求(给 Claude Design 的指令)

产出 **`calendar-screens.jsx`**,覆盖移动端屏幕,**严格沿用 §1 设计系统**(和
Projects/Expense/Task 一致,不要另起视觉):

1. **Calendar / Agenda** —— 顶部日期条(周滚动)+ 选中日的工作项列表;月视图用小弹层切日
2. **Day Detail** —— 某天:工作项列表(状态/类型色)+ 当天「日报」卡(摘要/工时/质量分)
3. **WorkItem Create / Edit** —— 标题 + 工作类型(31 类分组选择器)+ 起止/全天 + 工时 + 关联 + 附件
4. **Daily Log Submit** —— 日报:自动摘要 + 补充说明 + 提交;提交后只读质量分 + 改进建议
5. **Sheets** —— 工作类型分组选择器、完成/取消工作项、(只读)钉钉同步标记

**硬约束**:目标区新加坡 → **全英文 UI**;沿用 §1 token;移动优先(web 的月历拖拽、
FullCalendar、周报分析等砍/缓,见 §4);输出设计稿(jsx mock),能 1:1 映射到 Vue。

---

## 1. 设计系统(必须沿用 · 与 Task 同一 token)

```
背景 #F7F5F2  卡片 #FFFFFF
ink #1A1A1A / ink2 #3A3A3A / ink3 #7A7570 / ink4 #B5AEA3
accent(橙) #D97757  soft #FAEEE5
blue #3A6FB7 soft #E5EBF4  green #2F7A4F soft #E9F1EB
warn #C77B22 soft #F9F1E6  red #B5453A soft #F4E4E1  purple #7B5BAC soft #EEE6F5
divider #EBE6DD / soft #F2EEE6
衬线 hero/标题 Source Serif(oldstyle 数字)· 正文 SF Pro/system sans
sheet 阴影 0 -10px 30px rgba(0,0,0,.18)
```
布局惯例同 Task brief:54px 状态栏占位 + 环境条;Nav(‹返回 / 标题 / 右动作);衬线 hero;
Section 白卡分组;底部 sheet(圆角20、遮罩 rgba(0,0,0,.32)、拖拽条36×4);**底部 5 tab 不动**,
入口建议同 Task —— 放「我的/Me」页一张 hero 卡(或与 Task 合并成「工作」入口,**请你给方案**)。

---

## 2. 数据模型真相(后端已存在 · `app/models/worklog.py`)

**WorkItem(日历工作项)**:
- `title`、`description`、`planned_date`(索引,所属日)、`end_date`(可跨天)、`is_all_day`
- `start_time` / `end_time`(非全天时可选)、`estimated_hours`、`actual_hours`
- `work_type` —— **31 个类型,分 6 组**:通用(meeting/internal_training/other)、行销
  (customer_visit/presales_support/business_negotiation/customer_maintenance)、市场
  (video_production/material_design/social_media_operation/channel_activity/brand_event)、
  服务(onsite_maintenance/service_response/technical_support/troubleshooting)、行政
  (admin_affairs/office_management/asset_management)、+ 人事/财务/产品等。每类型有
  颜色(TYPE_COLORS)和 label(TYPE_LABELS,后端已 i18n,移动端**取后端 label 别自己枚举**)
- `status`:`planned` / `completed` / `cancelled`
- `owner_id`、`shared_with_users`、`attachments`(JSON)、`dingtalk_event_id`(钉钉日历同步)

**WorkLog(日报/周报)**:
- `log_date`(索引)、`log_type`:`daily` / `weekly`
- `summary`(系统自动生成)、`additional_notes`(用户补充)、`total_hours`(自动算)
- `status`:`draft` / `submitted`;**唯一约束:每人每天每类型一条**
- `mentioned_users`(@)、`mentioned_projects`(#)、`quality_score`(自动算)、`quality_issues`(JSON)
- `work_items` 一对多(WorkItem.worklog_id)

**工时算法(后端,移动端只显示结果)**:排除跨天/全天项 → 合并重叠区间 → 扣午休
12:00–13:00 → 上限 8h/天;无具体时间则 0。

**质量分(后端规则,移动端只读展示分数+issues+建议)**:基础10 + 条目数≤15 + 质量≤25 +
多样性≤15 + 及时性≤10 + 系统活跃≤15 + 互动;issues 如 few_items/no_customer/short_desc/
late_submit 等。**无模板/无配置**(和 Task brief 一样,不是动态表单)。

---

## 3. 屏幕与状态(英文标签)

- **Calendar(Agenda)**:顶部周日期条(可左右滑/点月图标弹月选择),选中日下方列当天
  WorkItems(状态点 + 类型色 chip + 起止时间/全天 + 时长 + 关联);空态 "No work items"。
  顶部 + 新建。节假日(holidays API)弱标记。
- **Day Detail / 当天日报**:当天工作项 + 一张「Daily Log」卡(总工时、质量分徽章、状态
  draft/submitted、提交按钮);已提交显示分数 + 改进建议折叠。
- **WorkItem Create/Edit**:标题、工作类型(**31 类分组选择器** sheet,参考 Task 的
  AssigneePicker 分组样式)、全天开关 / 起止时间、预计/实际工时、关联(项目/客户可选)、
  描述、附件(复用 Expense 附件交互)。
- **Daily Log Submit**:展示自动 summary(只读)+ additional notes 输入 + @人/#项目 +
  提交;提交后质量分(大数字 + 等级 + issues→建议清单,只读)。
- **Sheets**:工作类型分组选择、完成/取消工作项确认、(只读)钉钉同步来源标记。

状态色用 §1:planned=ink3、completed=green、cancelled=ink4;类型用 TYPE_COLORS。

---

## 4. 移动端取舍(让 Claude Design "重新评估" web)

| Web 现有 | 移动端建议 |
|---|---|
| FullCalendar 月历 + 拖拽改期 | **砍**。改 **Agenda**:周日期条 + 当日列表;月用小弹层跳日,不做拖拽 |
| 周报 + 跨人分析仪表 | P1 缓;先做**日报**(daily)闭环 |
| 31 类型平铺大网格 | 分组选择器 sheet(6 组折叠/分段),不一屏全列 |
| 钉钉同步管理 | 只**只读显示**同步来的项加个来源标记,不建同步/解绑 UI |
| 质量分配置/规则编辑 | 不存在配置;只读展示分数+issues+建议 |
| 富附件管理 | 复用 Expense 简单附件缩略 |

核心高频:**看某天 → 加/改工作项 → 当天提交日报 → 看质量分**。

---

## 5. 当前 web UX 参照(让它看现状再决定)

后端 `app/views/worklog.py`:`/calendar` 页(月/日历 + 工作项 CRUD + 当天日报面板 +
节假日着色 + 钉钉同步);API:`/api/items`(增删改查/complete/cancel/附件)、
`/api/daily/<date>`(取/改/提交/标记已读/删 日报)、`/api/holidays/<year>`。
**建议你对 web 日历页截图(月视图 / 某天工作项+日报面板 / 新建工作项 / 提交日报后质量分)
3-5 张给 Claude Design** —— 比读文字准。

`app/api/v1/daily_report.py` 已在移动端,但那是 **AI 日报分析**层(score/团队洞察),
**不是** WorkItem/日历/日报 CRUD —— 移动端要新建 `mobile_worklog.py`。

## 6. 还要随这份给 Claude Design 的

1. 你的 Claude Design jsx 包(customer-screens / task-* 等)—— 同体系扩展、和 Task 视觉连贯
2. web 日历页 3-5 张截图(§5)
3. (可选)现有 Vue 参照:`ProjectListView.vue`(列表)、`ExpenseEditView.vue`(多字段表单+附件)、
   刚出的 `task-list.jsx`(分段/行卡风格,日历的工作项行卡应与之呼应)

> 权限模型(给实现用,非设计):WorkItem/WorkLog 用 `get_viewable_data` + Affiliation
> 上级看下属(同 expense/customer);移动端 `mobile_worklog.py` 照此设计。
