# Task 模块移动端设计简报 (for Claude Design)

> 用途:把这份 + 你已有的 Claude Design jsx 包(`customer-screens.jsx / unified-lists.jsx /
> new-form-screens.jsx / filter-screens.jsx / chat-screens.jsx / screens.jsx`)+ web 任务页
> 截图,一起丢给 Claude Design,产出 **`task-screens.jsx`**(与现有 App 同一设计系统)。
> 这份本身已尽量自包含:无 jsx 包也能用,只是给了 jsx 包保真度更高。

---

## 0. 设计交付要求(给 Claude Design 的指令)

产出 **`task-screens.jsx`**,覆盖以下移动端屏幕,**严格沿用下方 §1 设计系统**(和现有
Projects/Expense/Customers 屏幕视觉一致,不要另起一套):

1. **Task List** —— 顶部分段 tab(5 个,见 §3),每行卡片;FAB 新建
2. **Task Detail** —— hero 标题 + 状态/优先级 + 分区(详情/子任务/评论/附件/审批)
3. **Task Create / Edit** —— 表单(同 ProjectEdit/ExpenseEdit 的字段卡片风格)
4. **Quick Status Change** —— 底部 sheet(开始/暂停/完成/取消)
5. **Comment / Reply** —— 详情内时间轴 + 输入

**硬约束**:
- 目标区是新加坡,**全英文 UI**(文案用英文,见 §3 给的英文标签)。不要出现中文。
- 移动优先:web 上重的(里程碑多人并行审批 UI、子任务拖拽排序、甘特/看板/日历切换)
  **砍掉或极简**(见 §4)。先覆盖高频:看列表→看详情→快速改状态→评论→新建。
- 输出是设计稿(jsx mock),不是生产代码;但 token/间距/组件形态要能 1:1 映射到现有 Vue。

---

## 1. 设计系统(必须沿用 · token 真实值)

App 是单一 token 源,沿用即可。色板/字体:

```
背景        bg #F7F5F2        卡片 card #FFFFFF
文字        ink #1A1A1A  ink2 #3A3A3A  ink3 #7A7570  ink4 #B5AEA3/#C2BBB3
主色(橙)   accent #D97757   accent-soft #F4E4D8 / #FAEEE5
状态色      green #2F7A4F(soft #E9F1EB)  warn #C77B22(soft #F9F1E6)
            red #B5453A(soft #F4E4E1)    blue #3A6FB7(soft #E5EBF4)
分隔线      divider #EBE6DD / rgba(0,0,0,.06)
字体        衬线 hero/标题: Source Serif 4(数字用 oldstyle-nums, class .font-serif .oldstyle)
            正文/控件: SF Pro / system sans
阴影        sheet: 0 -10px 30px rgba(0,0,0,.18)   FAB: 0 10px 24px rgba(26,26,26,.22)
```

**布局/组件惯例**(和 ProjectDetail/ExpenseList/ReceiptConfirm 一致):
- 顶部 **54px status pad**;其上一条浅色「Browsing · 区域 DB」环境条(已有,设计不用画)。
- **Nav**:左「‹ 返回标签」,中标题,右动作(详情页右上是 **Edit** 文字,不是 ···)。
- **Hero**:大号衬线标题(oldstyle 数字),下方一行 ink3 副信息(负责人 · 关联 · 日期)。
- **Section 卡片**:浅色大写 section 标签(letter-spacing) + 白卡分组,行间 divider-soft。
- **底部 sheet**:圆角 20px 顶,半透明遮罩 rgba(0,0,0,.32),拖拽条 36×4;选择/确认类操作都走 sheet。
- **FAB / 主操作**:accent 实心圆/胶囊;次操作描边白底。
- **底部 Tab Bar**:现有 5 个 Projects / Customers / Expense / Chat / Me。**Task 放哪需你给方案**
  (建议:替换或新增一个 tab;或并入某处)——在设计里给出导航位置建议。
- 状态/优先级用**小圆点 + 文字**或 soft 底色 chip(参考 Expense 状态徽章:color + bg soft)。
- 空状态:居中 ink3 小字(如 "No tasks")。日期相对化(Today / Yesterday / This week)。

---

## 2. 数据模型真相(后端已存在,设计要覆盖这些)

**Task**(`app/models/task.py`)字段:
- 核心:`title`、`description`
- 人:`creator`(创建人)、`assignee`(负责人)、`shared_with_users`(共享可见多人)、
  `task_reviewers`(多人审核,各自 status/comment)
- 状态机 `status`:`pending`(待开始)→ `in_progress`(进行中)→ `paused`(已暂停,带原因)
  → `pending_review`(待审核)→ `completed`(已完成);另有取消
- `priority`:`urgent` / `high` / `normal` / `low`
- 日期:`start_date`、`due_date`、`completed_at`、`calendar_date`
- 关联(均可选):`project`、`customer`、`quotation`
- `task_type`:general / product_dev / custom

**SubTask**(子任务/节点):title、status、`is_milestone`、`milestone_criteria`、
`milestone_status`、`milestone_reviewers`(里程碑可多人并行确认)

**TaskReply**:评论;并自动生成变更日志(`reply_type='update'`,如"状态 X→Y")

**TaskAttachment**:文件(图片/文档),走 NAS 存储

**通知**:指派→通知 assignee+shared;完成→通知 creator;暂停→通知 reviewers

---

## 3. List 的 5 个 tab + 列表行(英文标签)

顶部分段:**My Tasks / Created by Me / Shared / To Review / All**
(对应 web 的 我的/我创建/共享给我/待我审/全部)

每行卡片建议元素:状态点 · **Title** · 优先级标记(urgent/high 用 warn/red) ·
负责人 · 截止日(逾期红) · 关联项目/客户(若有,弱化) · 右侧相对日期。
排序:按 due_date / priority / updated;状态筛选(pending/in_progress/paused/pending_review/completed)。

详情页 Section 建议:**Detail**(负责人/创建人/优先级/起止日/关联项目客户)、
**Subtasks**(列表,milestone 标记)、**Comments**(时间轴,系统变更日志混排)、
**Attachments**、**Review**(审核人及其状态,若该任务进入 review)。

---

## 4. 移动端取舍(让 Claude Design "重新评估" web UX)

| Web 现有 | 移动端建议 |
|---|---|
| 列表/看板/甘特/日历多视图切换 | **只保留列表**(分段 tab + 筛选 sheet);日历/分析后期 |
| 里程碑多人并行审批的复杂面板 | 极简:详情里列审核人+状态;审批动作走底部 sheet 单步;并行 UI 后期 |
| 子任务拖拽排序、层级树 | 平铺子任务列表 + 勾选完成 + 加子任务;不做拖拽 |
| 富文本/大附件管理 | 评论纯文本 + 简单附件缩略;复用 Expense 的附件交互 |
| 一屏塞满筛选/批量操作 | 筛选收进底部 sheet;批量操作移动端先不做 |
| 创建表单字段很多 | 必填精简(标题/负责人/优先级/截止/关联),其余进"更多"折叠 |

核心高频路径必须顺:**列表→详情→快速改状态(开始/暂停/完成)→评论→新建**。

---

## 5. 当前 web UX 参照(让它看现状再决定)

web 任务页:`app/templates/task/tw_task_management.html`(Tailwind,单页含 列表 +
新建/编辑模态 + 子任务 + 里程碑 + 附件 + 评论;有 我的/我创建/共享/待我审/全部 分段、
优先级、截止、负责人、审核人)。**建议你对 web 任务的「列表 / 详情(或编辑模态) /
新建」截 3-5 张图一并给 Claude Design**——它对图的"重新评估"比读这段文字准得多。

---

## 6. 还要随这份一起给 Claude Design 的(提保真度)

1. 你已有的 **Claude Design jsx 设计包**(customer-screens.jsx 等)——让它在同体系扩展,
   而不是只看 token 值猜视觉。
2. **web 任务页 3-5 张截图**(§5)——"重新评估"的依据。
3. (可选)现有 Vue 视图作"已落地形态"参照:
   `mobile-app/src/views/projects/ProjectListView.vue`(列表+分段+筛选)、
   `ProjectDetailView.vue`(hero+Section+右上 Edit+底部 sheet)、
   `expense/ExpenseEditView.vue`(多字段表单卡片)。

> 单给本 MD 也能产出可用设计;给齐 1+2 后,产出会和现有 App 几乎无缝。
