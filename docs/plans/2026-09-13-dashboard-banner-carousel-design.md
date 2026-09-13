# 仪表盘顶部通知横幅（轮播）设计

2026-09-13

## 背景

仪表盘顶部原来只有一条写死的通栏：「公司官网预览　请点击跳转」，文案硬编码在
`at_dashboard.html` 里，改一个字要改 `.po` + 重编译 + 发版。需求是让它能滚动多条通知，
比如新上线的培训标准。

## 关键发现：不新建通知系统

系统里已有完整的公告能力 —— `announcements` + `announcement_reads` + 管理 UI
`/announcement/list`（发布/目标用户/已读跟踪），接在消息中心上。但 CN 生产只有
1 条公告，还是 2026-02 的，建好了基本没人用。

所以本次不造新表，把横幅做成**公告系统的一个展示出口**。

## 决策

| 问题 | 结论 | 理由 |
|---|---|---|
| 通知来源 | 复用公告系统 | 白拿目标用户/已读跟踪/消息中心联动 |
| 什么进横幅 | 所有已发布公告 | 见下「那个勾选框为什么被撤掉」 |
| 什么时候消失 | 撤回为草稿 | 不做"已读即消失"——横幅是常驻展示位 |
| 条数 | `BANNER_LIMIT = 5` | 没有已读淘汰，不限条数会越攒越多 |
| 定时发布 | 撤掉该字段 | 见下「顺手拆掉的 `scheduled_time`」 |
| 形式 | 淡入淡出轮播，6s | 跑马灯读到一半跑掉，手机端与无障碍都差 |
| 正文怎么看 | 悬停原地下拉展开 | 不占额外版面；点击仍是跳转，两种意图不冲突 |
| 告知 vs 链接 | `banner_link` 空 = 纯告知 | 「本周六维护」点进消息中心看同一句话，是白跑一趟 |
| 官网那条 | 也入库 | 见下 |

## 那个勾选框为什么被撤掉

第一版按"管理员控制哪条上首页"加了 `show_on_banner` 勾选框。它连着坑了两次：用户发布
公告后来问"为什么没出现在 banner 上"，两次都是没勾。

问题在于这个开关表达的信息量约等于零 —— 公告本来就有目标用户、有发布/撤回，"已发布
且发给我的公告"和"该让我看见的通知"是同一件事；再叠一个开关，只是给每次发布多加一个
必须记得的步骤，忘了就静默失效（没有任何提示告诉你差了一勾）。

现在的规则没有第三种状态：**发布即上横幅，撤回即下架**。相应地，「撤回」这个动作必须
存在且好按 —— 见下。

## 顺手拆掉的 `scheduled_time`

公告表里原有一列 `scheduled_time`，表单上叫「定时发布」。查下来它**全仓库只写不读**：
没有任何 cron / APScheduler / 启动钩子会去扫它，`api_publish` 也从不看它。也就是说
填了"明天 9:00"，点发布的那一刻就已经发出去了 —— 是个会骗人的控件。

两台生产核对过都是 0 行填过值（CN 1 条公告、SG 1 条公告，`scheduled_time` 均为 NULL），
不存在数据丢失，所以直接在本次迁移里 `DROP COLUMN`，而不是留着当死列。

真要做定时发布，得先有一个跑得住的调度器；那是另一件事，不该靠一个没人执行的时间戳
假装已经有了。

## 发布后必须能改、能撤

原 `api_update` 见 `is_readonly` 直接拒绝整个请求，于是一条公告一旦发布就彻底冻住：
错别字改不了，挂上首页也撤不下来，唯一出路是删公告（连带消息中心记录一起没）。

现在分两档：

- **标题 / 正文 / 类型 / 横幅跳转地址** —— 已发布也能改。这几项不影响
  `announcement_reads` 与目标名单的对应关系。
- **发布范围（`target_users`）** —— 锁死。加人会缺已读记录、减人会留孤儿行。要改先
  「撤回」为草稿。

`api_recall` 把状态退回 `draft`，并**清空该公告的 `announcement_reads`** —— 该表有
`UNIQUE(announcement_id, user_id)`，重新发布时 `api_publish` 会为每个目标用户插一条，
不清就撞唯一约束。代价是已读状态归零、重新发布后大家会再收到一次未读提醒，弹窗里
写明了。

## 官网预览那条为什么也入库

一开始想留作代码内置项，理由是链接按 `IS_OVS` 运行时算、显示与否取决于本机有没有那份
140M 快照。但第一条理由站不住：**CN/SG 数据库本来就独立，公告本来就各发各的**，
两台各建一条（CN 存 `/website-preview/cn/`、SG 存 `/website-preview/en/`）即可。

第二条理由还在，代价是 `Announcement.banner_items()` 里一处 3 行体检：指向
`/website-preview/` 的条目渲染前查一次资产在不在，没有就跳过（否则点进去 404）。
换来的是模板里彻底没有 `{% if website_preview_available %}` 分支、管理端一个列表
看全首页横幅上挂了什么、文案随时可改。

## 跳转地址只收相对路径

`banner_link` 只接受 `/` 开头的站内路径，或 `https://` 外链。**不收内网 IP，也不收公网域名**：

- 用户从内网、Tailscale、Cloudflare 公网域名进来的都有，相对路径自动跟随当前来源；
  写死绝对地址会把内网用户踢到公网绕一圈
- CN 是 `pma.jamesgpone.win`、SG 是 `sg-pma.jamesgpone.win`，写死任一个另一台必错
- 域名和 IP 在这个项目里会变（CN NAS 从 `.107` 漂到 `.124` 那次，WebDAV 老附件全 404
  四天才发现）。公告是长期沉淀的数据，绑死地址等于埋同类地雷

校验在 `views._normalize_banner_link()`：这是管理员自由输入直接进 `<a href>` 的值，
不挡 `javascript:` / `data:` / `//evil.com` 就是个 XSS 与开放重定向口子。

## 实现

```
migrations/versions/announcement_banner_20260913.py   +banner_link  -scheduled_time(幂等)
app/models/announcement.py       banner_link + banner_items()
app/views/announcement.py        _normalize_banner_link() / _users_tree_with_self() / api_recall()
app/views/main.py                仪表盘视图传 banner_items
app/templates/main/at_dashboard.html          轮播容器 + CSS + JS
app/templates/announcement/partials/_announcement_modal_fields.html   横幅地址输入 + 锁定说明
app/templates/announcement/tw_list.html       表单读写 + 编辑/撤回按钮 + 字段锁
app/templates/components/tw_user_selector_modal.html   修保存卡死(见下)
```

## 悬停展开正文

悬停 180ms 后，当前条的 `content` 以浮层形式从横幅下沿展开（`position:absolute; top:100%`），
**不挤占版面** —— 若改成把页面推下去，鼠标一划过顶栏整页就跳一下，还会甩掉光标。
面板本身在 `<a>` 里，所以在面板上点击照常跳转，不需要额外的"查看详情"按钮；移开即收起。
键盘 focus 同样展开（悬停交互对键盘用户不可达）。

180ms 延迟是必要的：顶栏是鼠标高频经过的地方，不延迟的话划过去就闪一下面板。

`content` 与 `title` 相同时不渲染面板 —— 短通知常把两者写成同一句，展开看到重复的
一行反而像 bug。

**一个被抓到的 bug**：圆点的点击处理原本是 `show(n); stop(); start();`，而点圆点必然
是在悬停状态下做的，`start()` 会把定时器重启 —— 人还没看完就被切走，与"移上去就不滚动"
矛盾。加 `held` 计数，悬停/聚焦期间 `start()` 直接 no-op。

## 三个退化情形

- 只有 1 条 → 不轮播、不出圆点、`position:static`，行高 27px，与改造前像素一致
- 一条都没有 → 整条不渲染
- `prefers-reduced-motion` → 不自动播，圆点仍可手动切

## 踩到的坑

`at-theme.css:108` 有全局 `body.at-page button { background:none; padding:0 }`，
把圆点的背景和热区 padding 全压掉了 —— 未选中的点直接不可见。样式必须带
`body.at-page` 前缀才压得过（同文件 183/204 行也是为这个坑加的前缀）。

同文件 124 行 `a { color: inherit }` 更隐蔽：带链接的条目渲染成 `<a>`、纯告知条目渲染成
`<div>`，于是同一条横幅里一半字发白、一半发黑。加前缀时**必须整组一起加** —— 只给基础
规则加前缀会让 `body.at-page .dash-banner-item`(0,2,1) 压过 `.dash-banner-item.is-active`
(0,2,0)，结果是整条横幅空白。

## 途中修掉的一个陈年 bug

发布范围的用户选择弹窗点「确定」后永远转圈 —— `saveSelection()` 里 `this.saving = false`
写在 `await` 之后的正常路径上，一抛异常就再也复位不了。自 2026-03-03 起存在，同时影响
公告发布对象、工作日历协助人、归属关系配置三处（共用
`components/tw_user_selector_modal.html`）。改成 `finally` 复位。

同一处还有两个问题：重新打开弹窗时旧选择不回填（代码用的是 Alpine **v2** 的 `el.__x`
API，本项目是 v3，要 `Alpine.$data(el)`）；以及 `get_shareable_users()` 带
`User.id != current_user.id`，导致作者永远无法把公告发给自己 —— 在公告这一处用
`_users_tree_with_self()` 把本人补回选择树（没有去动共享模块的 `sharing.py`）。

同一类坑还中了第二次：`at-theme.css:124` 的 `body.at-page a { color: inherit }`
特异性 (0,1,1) 压过裸类名 (0,1,0)，于是**有链接的条目（`<a>`）字色被继承成深色、
纯告知的条目（`<div>`）还是白色** —— 同一条带子上两种字色。

而加前缀时又犯了反向错误：`body.at-page .dash-banner-item`（0,2,1）反超了
`.dash-banner-item.is-active`（0,2,0），`opacity:0` 把所有条目盖成空白。
**提特异性必须整组一起提**，只提基础规则会把状态类压死。

## 面板配色

面板与横幅同色同字色（白字压橘底），展开后看着是同一块延伸下来。底色用
`color-mix(in srgb, var(--accent) 65%, var(--bg-page))` —— 混 `--bg-page` 而不是
混 `transparent`：渲染出的颜色和横幅 hover 态一致，但**不透明**。半透明会把下面的
卡片透出来，长段正文压在卡片纹理上没法读。
