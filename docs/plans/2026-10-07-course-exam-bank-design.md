# 课程考核题库 + 学习伙伴「小源」设计

- 日期：2026-10-07
- 分支：`feat/course-buddy-exam`（worktree `.worktrees/course-buddy-exam`，基于 origin/main 83e7cc63）
- 部署范围：仅 CN NAS（SG 暂不开放）
- 目标用户：销售新人（学员）、admin / HR（题库管理、成绩查看）、销售经理（看直属下属成绩）

## 1. 背景与目标

现状：知识库已有「AI 考核」（`app/services/course_quiz.py`）——每门课出「页数−2」道单选/判断题，
一次性作答，80 分及格；题库缓存在 `course_assets/<key>.quiz.json`；解锁条件是「翻到最后一页」，纯前端判断。

问题：题量太少、无难度区分、生产容器 `/app/app` 只读导致题库无法在线编辑、解锁可被秒翻绕过。

目标：

1. 每门 HTML 课件配一个 **~100 题题库**（选择题为主），每题有可靠的 **难度** 标注；
2. **累积闯关制**：随机抽题、答对按难度加分，**60 分及格、100 分满分**，及格后可继续；
3. **有效阅读时长达标** 后才解锁考核；
4. 考核与课程提问统一收进全 PMA 常驻、可拖动吸附的学习伙伴 **「小源」** 面板；随时关闭、断点续答。

## 2. 不做（YAGNI）

- 视频课程 / PPT 下载课程不纳入考核（沿用 2026-07-29 视频课设计决定：无逐页讲解素材）。
- 不做 SG、不做移动 App、不做旧版 TW 页面。
- 不做答错扣分、不做限时、不做难度自动调整（只提示，管理员确认）。
- 提问对话不入库（仅浏览器 localStorage）。
- 小源只保留一个造型（官网 6 造型里的「小源」），不移植钉钉转人工 / 留资 / 附件。

## 3. 数据模型

### 3.1 `course_quiz_questions`（新表，题库）

| 字段 | 说明 |
|---|---|
| id | PK |
| course_key | 课程 key（索引） |
| qtype | `single` / `multi` / `judge` |
| difficulty | 1 易 / 2 中 / 3 难（当前生效值） |
| ai_difficulty | 复核 AI 独立评出的难度 |
| question / options(JSON) / answer(JSON) / explain | 题干、选项、答案（single=int，multi=int[]，judge=bool）、解析 |
| source_page | 出自课件第几页 |
| status | `active` / `review`（待审）/ `disabled` |
| origin | `ai` / `edited` / `legacy`（由旧 .quiz.json 导入） |
| created_by / updated_at 等 | 审计 |

删题 = `disabled`（软删），保证历史答题记录可追溯。旧 `.quiz.json` 首次访问时导入，`origin=legacy`、难度默认 2。

### 3.2 `course_learning_progress`（新表，每人每课一行，唯一 `(user_id, course_key)`）

| 分组 | 字段 |
|---|---|
| 阅读 | `read_seconds`（有效秒数）、`page_seconds`(JSON `{页号: 秒}`)、`unlocked_at` |
| 考核 | `score`（0–100）、`current_question_id`、`current_option_order`(JSON)、`current_answered`(bool)、`passed_at`、`perfect_at` |
| 其他 | `created_at` / `updated_at` |

### 3.3 复用

- `training_quiz_attempt`：逐题记录（`module_slug='bank'`，与旧版 `'main'` 区分），用于「已答对移出抽题池」、错题间隔、实测正确率。
- `interactive_courses` 新增列 `min_read_seconds`（可空；空=按公式自动计算，非空=管理员覆盖）。

## 4. 计分与抽题

- 答对加分：易 1 / 中 2 / 难 3；答错 0 分不扣；`score` 封顶 100。
- `score ≥ 60` 首次到达记 `passed_at`；到 100 记 `perfect_at`，考核入口消失。
- 抽题池 = 本课 `active` 题 − 本人已答对的题；答错题留池，但距上次答错至少隔 5 题才可再抽。
- 难度加权随机（权重 易:中:难）：
  - score < 30：6:3:1
  - 30 ≤ score < 60：3:5:2
  - score ≥ 60：1:4:5
  - 某档无题时权重自动归零重分配。
- 每题出题时随机打乱选项顺序，顺序存入 `current_option_order`，提交时据此换算回原始下标判分。
- 题库健康检查：`Σ(active 题分值) ≥ 100` 才允许对学员开放，否则题库页告警。默认配比（易 50 / 中 30 / 难 20）理论 170 分。

## 5. 难度保障（三层）

**第 1 层 · 出题标准**

| 难度 | 定义 |
|---|---|
| 易 | 课件单页原话可答，记忆类 |
| 中 | 理解/比较，需联系同一主题 2 个知识点 |
| 难 | 客户场景应用，跨页综合，干扰项似是而非 |

题型约束：判断题只出易/中；多选只出中/难；场景题必为难。
按难度 **分三批** 生成（每批只出一档），批间把已有题干传给 AI 防重复。目标题型配比：单选 ~70 / 多选 ~10 / 判断 ~20。

**第 2 层 · 独立复核**：生成后另起一次调用，**不告知原难度**，让 AI：重评难度；校验唯一正确答案且课件有依据；
检查干扰项是否过假。一致 → `active`；不一致或答案存疑 → `review`（不进抽题池，待管理员确认）。

**第 3 层 · 实测校准**：按每题 **首次作答正确率** 推断实测难度（>85% 易 / 50–85% 中 / <50% 难，<20% 疑似题目有误）。
首次作答人数 ≥10 后在题库页并排显示「标注 vs 实测」，偏差高亮并给建议难度，**管理员一键采纳**；已得分不回溯。

## 6. 阅读解锁（仅 HTML 课件）

- 达标时长 = `Σ max(20s, 该页讲解字数 / 5)` × 70%；`min_read_seconds` 非空时以其为准。
- 同时要求 **每页都打开过**（`page_seconds` 覆盖所有页）。
- 有效计时规则（前端计、服务端校验）：
  - 标签页不可见不计；2 分钟无翻页/指针/键盘活动即停；
  - 单页累计上限 = 该页估算时长 × 3；
  - 每 15 秒上报 `{page, seconds}`；服务端拒绝 `seconds` 超过距上次上报的真实间隔（+2s 容差）的上报。
- 达标即写 `unlocked_at`；之后不再计时上报。

## 7. 出题流程（后台异步）

1. 素材：课件逐页讲解（`_get_course_pages`，带页号）。
2. 三批生成（易/中/难）→ 独立复核 → 题干相似度去重 → 入库。
3. 内容不足允许少于 100 题，但须满足 §4 健康检查。
4. 管理员在题库页点「生成题库」触发；后台线程执行，完成发站内通知。单课约 3–5 分钟。
5. 单题「AI 重出」：保持同难度、同页。补题：只补指定难度。

AI 客户端沿用 `WikiClaudeClient` + 现有 JSON 容错解析（`_extract_json` / `_scan_objects`）；注意推理模型 thinking 块，
取文本走 `first_text()`（见既往 ThinkingBlock 教训）。

## 8. 学习伙伴「小源」

### 8.1 形象与交互（移植官网 `evertac-website/release-template/site/mascot.js`）

- SVG 形象 + 眨眼/呼吸/跳动/说话动画；遵守 `prefers-reduced-motion`。
- **拖动**：鼠标/触屏（pointer events），位移 <6px 视为点击。
- **吸附**：松手按中心点落在左/右半屏贴到左/右边；垂直位置保留并钳制在可视区；吸附时果冻回弹。
- **藏边**：拖出屏幕超过 1/3 → 半身藏在边上（半透明），点击弹回。
- **面板/气泡跟随吸附侧展开**，高度自动避让屏幕边界。
- 位置（side / bottom / tucked）存 localStorage（按设备），resize 自动重算。
- PMA 特有避让：左吸附时贴在 AT 侧栏右缘，侧栏折叠/展开时跟随；课程播放器内最低位置避开底部讲解栏与翻页按钮。

### 8.2 状态反馈（气泡/表情）

| 场景 | 表现 |
|---|---|
| 课程内阅读中 | 偶发气泡「已读 62%，加油」 |
| 闲置 >2 分钟（计时暂停） | 闭眼睡觉，气泡「休息中，翻页叫醒我」 |
| 刚解锁 | 跳一下 +「解锁考核啦，来考考你？」（不自动打开） |
| 考核中 | 头顶小牌 `47/100` |
| 满分 | 戴奖杯，考核标签消失 |
| 课程外、有未满分课 | 每天最多一次「还有 N 门课考核没满分」 |

### 8.3 面板（风格：白底大圆角、大标题、灰色副标题、灰圆关闭钮、浅灰选项块、青色仅作强调）

- 顶部分段控件：**提问 | 考核**。
- **提问**：对话式，调用现有 `/api/wiki/query`（已按权限过滤、带课件页缩略图深链）。
  课程内默认范围=本课（可切全库），课程外=全库。记录存 localStorage，最多 50 条。
- **考核**：
  - 课程内：直接进入本课断点；未解锁时标签显示阅读进度圆环、不可点。
  - 课程外：列出「已解锁未满分」课程及分数，选一门进入。
  - 题卡：难度标签+分值 → 题干 → 选项（单选=竖排选项块；多选=选项块+勾选框，题干后注「（多选）」；
    判断=「正确 | 错误」分段控件）→ 主按钮「提交答案」（未作答置灰）。
  - 提交后：选中项变浅绿/浅红，正确项浅绿；灰字解析；分数跳动 `+2`；按钮变「下一题」；
    跨过 60 / 100 时面板内庆祝条。
- 关闭：✕ / 点遮罩 / Esc / 下拉拖动条；无确认（断点在服务端）。
- 布局：桌面贴小源侧弹出（宽 ~400–440px）；窄屏底部抽屉全宽、最高 90vh 内滚动。暗色模式复用 AT 变量。

### 8.4 挂载

- 新组件：`templates/components/at_course_buddy.html` + `static/js/course-buddy.js` + `static/css/course-buddy.css`。
- 挂载点：`components/at_sidebar.html`（覆盖 27 个 AT 页面）+ 独立页补挂：`knowledge/at_course_player.html`、
  `approval/at_detail.html`、`user/at_person_affiliation.html`、`user/at_person_ai.html`。不挂登录页。
- 个人设置「显示学习伙伴」开关（服务端存，默认开）。
- 课程播放器：移除「开始考核」按钮与「翻到最后一页解锁」逻辑；`at_course_quiz.html` 改为重定向回课程页。
- 播放器通过 `window.CourseBuddy.setCourse({key, pages, currentPage})` 等接口把翻页/活动事件交给小源计时。

## 9. API（均 `@login_required`；判分全在服务端，前端永不拿答案）

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/learning/buddy` | 小源初始化：开关状态、未满分课程列表 |
| GET | `/api/learning/<key>/progress` | 阅读/考核状态 |
| POST | `/api/learning/<key>/read-ping` | 上报 `{page, seconds}` |
| GET | `/api/learning/<key>/exam/current` | 取当前题（无则抽新题，幂等） |
| POST | `/api/learning/<key>/exam/answer` | 提交 → 对错/解析/新分数 |
| POST | `/api/learning/<key>/exam/next` | 推进到下一题 |
| GET/POST… | `/wiki/play/<key>/bank`、`/api/learning/<key>/bank/*` | 题库页与题库 CRUD/生成（admin/HR） |
| GET | `/wiki/learning-report` | 成绩汇总页 |

## 10. 管理端

**题库页** `/wiki/play/<key>/bank`（admin、HR）：统计（总数、难度/题型分布、待审数、理论总分、达标阅读时长可改）；
列表筛选（难度/题型/状态/页）；列显示标注难度、AI 复核难度、实测正确率；单题编辑/停用/AI 重出/采纳建议难度；
批量通过待审、补题。

**成绩汇总** `/wiki/learning-report`：课程 × 学员矩阵（灰=未解锁+阅读%、黄=考核中+分数、绿=及格、金=满分）；
点格看明细（阅读时长、答题数、正确率、反复错题）。权限：admin/HR 全部；销售经理看直属下属（Affiliation 一级）；学员看自己。

## 11. i18n 与规范

- 所有 UI 文本 `_()` / 前端字典，中文 msgid，补 en.po 并编译。
- 新 JS 工具登记 `CLAUDE-JS-TOOLS.md`，组件登记 `CLAUDE-TW-COMPONENTS.md`。
- 不修改受保护通用组件。

## 12. 测试

- 单元（`tests/test_course_exam_*.py`）：加权抽题、封顶、60 及格、答对移出池、错题间隔 5 题、断点幂等
  （同题同选项顺序）、选项乱序判分换算、阅读计时校验（伪造秒数被拒、单页上限、全页覆盖）、
  `public` 接口不泄露答案、权限（学员不能访问题库 API、经理只看下属）。
- E2E：本地 5097 实例（CN 数据）Playwright：阅读解锁 → 打开小源考核 → 中途关闭 → 刷新续答 → 及格 → 满分入口消失；
  拖动吸附左右、藏边、侧栏避让。
- 改模板后跑 `check_all_templates_parse.py`。

## 13. 部署（CN）

- 迁移：新增 2 表 + `interactive_courses.min_read_seconds`。注意 `create_all` 抢建表 → 必要时 `flask db stamp`。
- 上线后管理员逐门课「生成题库」→ 审待审题 → 开放。
- 旧 80 分制记录保留不迁移；新规则下所有人重新累计阅读时长。

## 14. 实施顺序

1. **原型**：小源拖动吸附 + 面板（提问/考核）可点击原型，用户确认外观手感。
2. 数据模型 + 迁移 + 题库导入旧 json。
3. 抽题/计分/断点服务 + API + 单元测试。
4. 阅读计时服务 + 播放器接入。
5. AI 出题三批 + 复核 + 题库管理页。
6. 小源正式组件 + 全站挂载 + 个人开关。
7. 成绩汇总页 + 实测难度校准。
8. i18n、文档登记、E2E、CN 部署。
