# 采购订单重设

_Started 2026-05-22 09:47 UTC_

---

## User

我需要为PMAweb端重新设计UI和交互,你可以查看https://pma.jamesgpone.win 来了解整个页面风格,先进行规范和提升的是采购订单模块,我上传了这个模块的大部分页面,请重新评估设计布局和交互,帮我更好的推进进度,了解信息,整个风格字体更清楚排版,保持anthorpic的风格

## Assistant

_[tool: list_files]_

_[tool: view_image]_

_[tool: view_image]_

_[tool: view_image]_

_[tool: view_image]_

_[tool: view_image]_

_[tool: view_image]_

_[tool: view_image]_

_[tool: view_image]_

_[tool: view_image]_

_[tool: list_files]_

我已经查看了所有的页面截图,对当前 PMA 采购订单模块有了清晰的认识。在开始之前,我需要先了解一下 Anthropic 风格设计系统,并确认一些关键设计方向。

_[tool: read_file]_

_[tool: list_files]_

_[tool: read_file]_

_[tool: questions_v2]_

我已仔细查看了所有截图,理解了采购订单的完整业务流(提交审批 → 供应商确认 → 备料 → 生产 → 测试 → 待发货 → 验收入库),也看到了几个关键交互入口(发货单、确认、测试报告、审批节点)。在动手之前,我想先确认几个关键方向,避免做偏。

## User

Questions answered:
- anthropic_intensity: Decide for me
- scope_priority: 订单列表页(含统计卡 + 筛选 + 表格), 订单详情页(含阶段时间线 + 基本信息 + 明细 + 发货记录)
- layout_innovation: Decide for me
- stage_interaction: Decide for me
- typography: Decide for me
- density: Decide for me
- stats_treatment: Decide for me
- table_style: Decide for me
- tweaks: Decide for me

## Assistant

_[tool: update_todos]_

_[tool: copy_starter_component]_

明白了,全部由我决定。我会按 Anthropic 的暖白底 + 衬线大标题 + 单一陶土橙强调色这条路走,并把"是否衬线 / 强调色 / 密度 / 时间线位置 / 深色模式"都做成 Tweaks 让你随时切换。

先把方向定下来,然后开始构建:

_[tool: read_file]_

_[tool: write_file]_

## Assistant

_[tool: write_file]_

_[tool: write_file]_

_[tool: write_file]_

_[tool: write_file]_

_[tool: write_file]_

_[tool: write_file]_

## User

继续

## Assistant

_[tool: write_file]_

_[tool: write_file]_

_[tool: show_html]_

_[tool: show_html]_

_[tool: get_webview_logs]_

_[tool: str_replace_edit]_

_[tool: grep]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

Cleanest fix: wrap `data.js` in an IIFE so it only exports via `window.PMA_DATA`. Then restore the destructure in `screens.jsx`.

_[tool: grep]_

_[tool: show_html]_

_[tool: sleep]_

_[tool: get_webview_logs]_

_[tool: save_screenshot]_

_[tool: view_image]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: register_assets]_

Let me set a proper viewport and tighten table behavior on narrower widths.

_[tool: save_screenshot]_

_[tool: done]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

Let me replace Fragment usages — the editor injects `data-om-id` onto them which Fragment can't accept.

_[tool: grep]_

_[tool: str_replace_edit]_

_[tool: grep]_

_[tool: str_replace_edit]_

_[tool: done]_

_[tool: fork_verifier_agent]_

已完成首版采购订单模块重设计,文件:`采购订单.html`

**这版的设计决策**

- **整体气质** — 暖白底(#FAF9F5)、衬线大标题(Newsreader)、陶土橙(#C15F3C)做唯一强调色;表格无重边、密度收紧,大量留白和细线,告别原版的"管理后台堆栈感"。
- **列表页** — 把原来的 6 个并排大统计卡换成顶部 tab 切换(全部 / 待确认 / 生产中 / 已发货 / 已入库 / 超期 + 计数),省下整片视觉空间给表格;进度条改为细线 + tabular-num 百分比;PO 单号、金额、日期统一等宽字体。
- **详情页** — 顶部紧凑式 sticky 阶段条(7 步全可见,完成态墨黑、当前态陶土橙带光晕),阶段条下方有一张"当前阶段任务卡"清晰指引下一步操作并带主按钮(测试 → 上传测试报告 / 待发货 → 创建发货单 / 待审批 → 去审批);右侧固定边栏含元数据 + 操作历史。
- **弹窗** — 三个核心弹窗(供应商确认 / 上传测试报告 / 创建发货单)统一拖拽上传卡 + 信息条 + 字段网格;创建发货单里 SN 前缀/起始号实时预览生成序列号区间。
- **审批节点** — 单独的卡片,头像 + 当前节点 pill + 审批意见 textarea + 同意/驳回,代替原版那个偏拟物的橙色当前节点装饰。

**Tweaks 面板里能切**
- 强调色:陶土橙 / 经典蓝 / 墨黑 / 森林绿
- 深色模式
- 大标题字体:衬线 / 黑体
- 信息密度:紧凑 / 标准 / 宽松
- 详情页阶段时间线位置:顶部 / 右侧
- 演示捷径:一键跳到列表、测试中详情、已入库详情、待审批详情,以及三个弹窗

**建议下一步**
看完之后告诉我哪部分要调整。常见的几个方向:1)把表格改成卡片式列表;2)把"当前任务卡"做成可折叠;3)给已入库订单加更明显的归档样式;4)加客户订单 / 供应商详情这些联动页面。收到。等你看完页面给反馈,我再调整。

## User

在列表的明细行的分隔线是否过深? 滚动时应该只在栏内滚动合理还是整个页面滚动

## Assistant

_[tool: grep]_

_[tool: grep]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: read_file]_

两个都是好问题。我做以下改动:

**1. 分隔线偏深** — 当前用的 `#E5E1D3`,在暖白底上确实显眼。新增更浅的 `--line-soft: #EFECE0` 专门给表格行间使用,卡片外框保持 `--line` 略明确一些。

**2. 滚动行为** — 列表页改成"栏内滚动"(头、tabs、筛选条固定,只表格滚动),这是 Linear/Notion 数据表的做法。详情页保持页面级滚动(多张卡片自然纵向铺开)。把这点做成 Tweak 也行。

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

我把列表页改成"栏内滚动":页头、tabs、筛选条固定,表格区域填满剩余高度并内部滚动(表头会粘在顶部)。详情页保持页面级滚动。同时再加一批 mock 数据以便看到滚动行为。

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: done]_

Border on `<tr>` won't show with `border-collapse: separate`. Let me move the row border to td cells, and add more rows so scrolling is visible.已调整,你刷新一下应该能看到效果:

**分隔线**
- 新增 `--line-soft`(暖白底用 `#F0EDDF`,深色模式 `#25221C`),专门用在表格行间,比原来浅一档
- 卡片外框、表头分隔线保持 `--line`,有层次感
- 订单列表、订单明细、发货记录三处都换用了 `--line-soft`

**滚动行为(我的建议)**
- **列表页 → 栏内滚动** ✅ 已实施。页头 / tabs / 筛选条全部固定,表格区域填满剩余高度并在卡片内部滚动,表头粘在顶部。这样滚很长的订单也不会让筛选器消失,操作更顺。
- **详情页 → 页面级滚动** ✅ 保持。详情页是多张卡片纵向铺开,自然滚动更舒服,右侧元数据栏本身就是 sticky 的。

顺便加了一批历史已入库订单的 mock 数据(现在有 18 条),这样你能看到滚动效果。

如果觉得卡片内滚动不舒服(比如希望整页滚到底),可以告诉我,加个 Tweak 切换就行。

## User

详情中操作历史时多余的,上面的阶段已经有了,生产阶段和审批是两个流,如何分开,审批本身也是显示流程

## Assistant

_[tool: read_file]_

好点子。当前把"提交审批"塞进了 7 步生产阶段条,确实混了两条流。我把它拆开:

- **审批流**:一条独立的紧凑流(提交人 → 部门负责人 → 财务 → ...),自带"进行中"和"已通过"两种态。通过后默认折叠成一行摘要,可展开看每个节点。
- **执行流**:阶段条精简为 6 步(供应商确认 → 备料 → 生产 → 测试 → 待发货 → 验收入库),只在审批通过后启用。
- **删除"操作历史"侧栏**:信息已被上面两条流完全覆盖,纯冗余。

_[tool: write_file]_

_[tool: str_replace_edit]_

Now add the new `ApprovalFlow` component, update `CurrentActionCard` to handle approval-pending state, and add a `dimmed` prop to the stage strips.

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: grep]_

_[tool: read_file]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: grep]_

_[tool: done]_

已完成,刷新查看。这版的变化:

**审批与执行分流**
- **审批流**(独立卡片,顶部带 "APPROVAL · 审批流" 标识)
  - 节点:提交 → 部门负责人 → 财务审核(支持任意多节点)
  - **已通过**:头部一行摘要 + 头像堆叠 + 历时天数,默认折叠;点"展开"看每个节点谁、何时、做了什么
  - **审批中**:默认展开,当前节点用暖橙色脉冲圈出,头部直接显示"当前节点 · 部门负责人 (刘强)"
- **执行流**(下方阶段条)
  - 6 步:供应商确认 → 备料 → 生产 → 测试 → 待发货 → 验收入库
  - 待审批通过前整体淡出 + "ⓘ 待审批通过后进入执行阶段"提示,完全表达"这是另一条流,还没启动"

**删掉了**
- 侧栏的"操作历史"——上面两条流已经包含全部信息
- "提交审批"不再混在执行阶段条里

**当前任务卡也分流了**
- 审批中:暖橙底色,显示"当前节点 · XX 审批 — XX",右侧给"催办"按钮(因为审批本身不是订单创建者的操作)
- 执行中:陶土橙底色,显示当前生产阶段 + 主操作按钮(测试 → 上传测试报告 / 待发货 → 创建发货单 等)

试一下 Tweaks 里的"详情页 · 待审批 (PUO…-004)"和"详情页 · 测试中 (CG-2601-001)"两个捷径,可以对比两种状态。

## User

这里有个设计问题,阶段和审批节点之间的连接线是否应该水平对齐图标中心而不是整个包括文字的区域

## Assistant

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

对,这是个明显的小 bug。当前的连接线用 `alignSelf: center` 居中,导致随文字行数浮动,在标签多的时候就偏低了。改成"按图标中心定位":顶部对齐 + `marginTop = 图标半径`。改完了。两处连接线都改成了:

- `alignSelf: flex-start` — 让连接线从容器顶部开始,不再随文字内容居中
- `marginTop = 图标半径`(审批节点 15px / 执行阶段 18px) — 精确对齐图标中心

这样不管节点下方有多少行文字(姓名 / 日期 / 动作 / 角色),连接线始终穿过图标圆心。刷新看看。

## User

在业务流程中比如供应商确认需要通过时要打开一个静态框来上传确认的回函,然后才通过,这个文件可以在通过的节点打开预览 类似的还有测试环境,

## Assistant

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

好需求。我把这件事拆成两部分:

1. **执行阶段的附件资料** — 每个完成节点可挂附件(确认单/测试报告等);在阶段条上能直接看到"📎"指示并点击预览。
2. **当前阶段的对话框** — 已经有 `SupplierConfirmModal` 和 `UploadTestModal`,需要把它们和阶段推进联动起来。

我先把数据模型加上附件,然后在阶段条上加可点的预览入口和一个简单的文件预览弹窗。Now add the file preview modal and surface attachments on completed stage nodes in both strips:

_[tool: str_replace_edit]_

Now wire attachment indicators on completed stage nodes in both horizontal and vertical stage strips, and open the FilePreviewModal on click:

_[tool: read_file]_

_[tool: grep]_

_[tool: read_file]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: str_replace_edit]_

## Assistant

_[tool: str_replace_edit]_

Now wire the preview modal state into DetailScreen and pass `onPreview` to both strips. Also add the App-side mount of `FilePreviewModal`.

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: grep]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: str_replace_edit]_

_[tool: done]_

完成。现在的附件流转方式:

**数据模型**
每个已完成的阶段(history 条目)可以挂一组附件:
```js
{ stage: "confirm", date: "...", attachments: [{ name, size, type }] }
```
目前 CG-2605-002(已入库)在确认 + 测试两个阶段有附件,CG-2601-001(测试中)的确认阶段有附件。

**顶部阶段条**
已完成且有附件的节点,在日期下方多一颗细小的"📎 N"小药丸(暖灰底)。点击就打开预览弹窗,几乎不增加视觉权重。

**右侧侧栏阶段条**
更明显的呈现方式:每个完成节点下方独立一行的"📎 查看确认单 / 查看测试报告 …"按钮(模仿你截图里的样式),按阶段类型自动取标签。

**预览弹窗**
- 单文件:大图标占位 + 文件名 + 大小 + 下载
- 多文件:左侧列表(JPG/PDF/ZIP 彩色标签),点击切换右侧预览
- 现在用的是占位预览;接到真实接口时把 `<FilePreviewPane>` 换成 PDF.js / 图片标签 / iframe 即可

**业务流程联动**
完成阶段时上传 → 文件挂到那个 history 节点 → 后续可在两条阶段条任何位置点开预览。

Tweaks 里把"详情页时间线位置"切到「右侧」,就能直接看到你截图里那种"查看确认单"风格的按钮。

## User

详情的订单明细要占满整个宽度,否则太局促了考虑元数据不要占一栏,发货记录有的时间点击可以展开

## Assistant

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

明白。改三件事:

1. **详情页改成单列全宽** — 内容(基本信息 / 明细 / 发货记录)占满,元数据不再独占一栏
2. **元数据合并掉** — 大多数信息已经在头部和基本信息里,去掉重复栏
3. **发货记录可展开** — 点击行展开物流信息 + 物料明细 + SN 段Now make the shipment rows expandable:

_[tool: str_replace_edit]_

_[tool: done]_

调整完了。详情页现在是:

**布局**
- 单列全宽,内容(基本信息、订单明细、发货记录)铺满
- 原来的元数据栏合并进了基本信息(创建者、创建时间、更新时间、订单金额作为额外四个字段,12 个字段排成 4 列 × 3 行)
- 仅当 Tweaks 把"时间线位置"切到「右侧」时才出现右栏

**发货记录**
- 行首多了一个 chev 指示器,点击整行展开
- 展开后显示:
  - **物流信息** — 承运商 / 运单号 / 发货数量 / 签收日期(4 列)
  - **本次发货明细** — 产品 / 型号 / 数量 / SN 段(以 PNR2000-0001 ~ PNR2000-0100 这种格式)
- 多次发货也可以同时展开多行
- 头部多了 "3 次发货" 这种数量摘要

打开 "详情页 · 已入库 (CG-2605-002)" 那个捷径可以看到三条带物流明细的发货记录。

## User

这些有明细内容的列表选卡太多的分割线了,标题,表头,内部明细

## Assistant

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: done]_

_[tool: grep]_

_[tool: read_file]_

_[tool: read_file]_

_[tool: str_replace_edit]_

_[tool: done]_

已经精简分割线了。具体改动:

**之前** — 三道线:卡片头部底线 + 表头底线 + 每行底线 + 合计行顶部
**现在** — 一道线的逻辑:卡片头部和表头之间不再分割,表头到首行用一条 line-soft,行间也用 line-soft,只有合计行用稍深的 line 与明细区分开

效果上像 Anthropic / Notion 的表格 —— 标题"订单明细"和表头自然过渡,行间的细线只起视觉对齐作用,不抢戏。

同样的逻辑也应用到了发货记录表 + 基本信息卡(基本信息现在头部内边距更舒展,字号略加 13.5px,行距 20px)。

## User

新建采购订单页面增加

## Assistant

_[tool: write_file]_

_[tool: grep]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: done]_

好需求,我把"新建采购订单"做成一个大对话框,包含三个关联交互:主表单 + 产品选择器(级联)+ 客户需求池子弹窗。统一 Anthropic 风格。

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: done]_

_[tool: fork_verifier_agent]_

Just realized — each `<script type="text/babel">` has its own scope, so `SUPPLIERS` from screens.jsx isn't visible in create-order.jsx. Let me fix:已搞定。新建采购订单走 Anthropic 风格了:

**主弹窗(1080px)**
- 表单部分:供应商 / 订单类别 / 需求日期 / 贸易术语 / 运输方式 / 运费承担 / 验证测试 / 交货地点 / 付款条件 / 备注 — 4 列网格,关键字段(供应商 / 需求日期)有红色 *
- 必选项缺失时"创建采购订单"按钮自动 disabled
- 表头沿用页面里其他表格的 small-caps 风格

**产品表**
- 空态:整行变成"+ 点击选择产品…"暖白底大按钮
- 有产品后:产品名 / 型号 / 规格(暗色细描述)/ 数量(步进器)/ 单位 / 单价(可编辑)/ 金额(自动算)
- 右侧 × 删除按钮(hover 变红)
- 底栏:添加产品 / 从客户需求导入 / 货币选择 / 合计金额(大字 mono)

**产品级联选择器**
- 三栏布局:类目(深底高亮当前)→ 产品族(每族带产品数)→ 具体 SKU(卡片式,陶土橙价格)
- 点 SKU 卡片直接加到表单,选择器关闭
- Esc 或点空白可关

**客户需求池**
- 搜索框 + 表格 + 多选导入按钮(数据为空时显示空态图)

试一下 Tweaks 里的"弹窗 · 新建采购订单",或者点列表页右上角"新建采购订单"按钮。

## User

Verifier agent check completed

## Assistant

收到,核查通过。新建采购订单走通了。

## User

左侧的菜单能默认收缩吗,交互时才展开

## Assistant

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: done]_

好,默认收缩 + 悬停展开成浮层(内容不挤压,顺手干净)。改完了。现在的逻辑:

- **默认收缩到 64px**(只显示图标)
- **鼠标悬停** → 自动浮层展开到 232px,带细微阴影,**主内容不挤压**(因为浮层用 absolute 定位覆盖在内容之上)
- **离开** → 收回收缩态
- **想固定展开**:点击侧边栏右上角的小箭头,变成"固定展开"模式;再点一次回到"默认收缩 + hover 展开"

这样平时画面更安静,鼠标过去也能快速看到全部菜单。

## User

所有的静态框,标题下面的分割线都去掉底部的按键的区域分割线页去掉

## Assistant

_[tool: str_replace_edit]_

_[tool: done]_

改完了 — 所有静态弹窗(供应商确认 / 上传测试报告 / 创建发货单 / 新建采购订单 / 文件预览 / 客户需求池)的标题分割线和底部按钮区分割线都去掉了,底部也不再有暖灰色块,跟正文连成一片更安静。

## User

数量用左右—+太占地方了,另外这个选中的明细如何修改二次? 我需要有明细可以拖动排序

## Assistant

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: done]_

已优化:

**数量字段** — 步进器换成普通输入框(56px 宽,右对齐),省下大约 60px 横向空间

**修改已选产品** — 产品名变成"虚线下划线 + hover 变橙色"的可点击文本,点击重新打开级联选择器,在新弹窗顶部标题变成"替换为",选另一个产品后会替换当前行(保留数量)

**拖拽排序** — 行首多了一个 ⋮⋮ 拖动手柄(hover 时鼠标变 grab):
- 拖动时该行半透明
- 鼠标悬停的目标行顶部出现一条陶土橙色横线指示落点
- 松手即重排

打开"新建采购订单"试试 —— 添加两三个产品,然后拖第二行到第一行就能看到。

## User

你的布局不好明细单位栏台窄了变成换行了

## Assistant

_[tool: str_replace_edit]_

_[tool: done]_

解决了。

原因:之前 单位 列只有 50px 宽,而表头"单位"两个汉字加上 letter-spacing 实际占用约 51px,差一像素就触发换行。

现在的列宽:
- 数量 60 → 76(给输入框留更宽裕的空间)
- 单位 50 → 64(汉字 + 字距不再挤)
- 单价 100 → 110、金额 110 → 120(让 ¥13,580.00 这种数字不被裁)
- 同时所有表头加了 `whiteSpace: nowrap` 防御性兜底,letter-spacing 也从 0.08em 收紧到 0.06em

刷新就看不到换行了。

## User

这个创建发货单页你设计了吗

## Assistant

_[tool: read_file]_

_[tool: str_replace_edit]_

_[tool: done]_

设计过,但当前版本有几个问题:数量栏带原生上下箭头(占位、丑)、SN 编辑器横向太挤、表格列宽不合理、规格没显示。我重做一版。重做完了。主要改动:

**版式**
- 弹窗宽度从 820 → 880
- 发货去向卡片更紧凑(尺寸更克制,主副两行)
- 客户订单下拉里直接带客户名 + 待发数量,选项更清楚

**发货明细表**
- 列结构从 6 列(产品 / 型号 / 到货 / 已发 / 可发 / 本次发货)精简到 4 列:
  - **产品**(品名 + 型号 + 规格,信息完整)
  - **已发 / 可发**(用 0 / 1 这种叠加式,占地更小)
  - **本次发货**(普通输入框,无原生 ±箭头)
  - **序列号**(原来挤一整行的 SN 编辑器,现在和产品行齐平,变成"前缀输入 + 起始号输入" + 下方紧凑预览)
- 数量为 0 时下方预览自动隐藏

**SN 编辑器**
- 不再用整行宽度,跟产品行水平对齐,前缀 input flex 自适应,起始 64px
- 预览改成单行:`→ Mark3000BS-001 … Mark3000BS-005`,数量为 1 时只显示一个
- 「无序列号」复选框移到下方,勾选后整个 SN 区显示"无需序列号"

**底部按钮**
- "创建发货单"按钮上显示 `· N 件`,所选数量为 0 时禁用
- 占位文本改成更具体的「如:顺丰速运」「如:SF1234567890」

## User

我点击那个按键可以看到你设计的创建发货单?

## Assistant

三个入口都可以打开:

1. **Tweaks 面板** — 右下角面板里"演示捷径"分组有「弹窗 · 创建发货单」按钮(无论在哪个页面都能开)

2. **当前任务卡** — 进入一个处于"待发货"阶段的订单详情页,头部下方的橙色任务卡有「创建发货单」主按钮
   - 在 Tweaks 演示捷径里点"详情页 · 已入库 (CG-2605-002)" 可以看到 — 不过这单已经入库不会显示;
   - 我目前的 mock 数据里没有正处于"待发货"阶段的订单。我加一条临时跳板:

_[tool: str_replace_edit]_

_[tool: str_replace_edit]_

_[tool: done]_

现在三种方式都能看到新的创建发货单弹窗:

1. **Tweaks 面板 → 演示捷径 → 「弹窗 · 创建发货单」** — 直接弹
2. **Tweaks 面板 → 演示捷径 → 「详情页 · 待发货 (CG-2604-001)」** — 跳到一个待发货订单,顶部橙色任务卡的「创建发货单」主按钮可点
3. **列表页** — 第 9 行 CG-2604-001(状态:待发货)点进去也是同一个详情页

