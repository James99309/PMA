# 仪表盘顶部通知横幅（轮播）设计

2026-09-13

## 背景

仪表盘顶部原来只有一条写死的通栏：「公司官网预览　请点击跳转」，文案硬编码在
`at_dashboard.html` 里，改一个字要改 `.po` + 重编译 + 发版。需求是让它能滚动多条通知，
比如新上线的培训标准。

## 关键发现：不新建通知系统

系统里已有完整的公告能力 —— `announcements` + `announcement_reads` + 管理 UI
`/announcement/list`（发布/定时/目标用户/已读跟踪），接在消息中心上。但 CN 生产只有
1 条公告，还是 2026-02 的，建好了基本没人用。

所以本次不造新表，把横幅做成**公告系统的一个展示出口**。

## 决策

| 问题 | 结论 | 理由 |
|---|---|---|
| 通知来源 | 复用公告系统 | 白拿定时发布/目标用户/消息中心联动 |
| 什么进横幅 | 公告加 `show_on_banner` 开关 | 管理员控制，不是所有公告都该上首页 |
| 什么时候消失 | 管理员取消勾选 | 不做"已读即消失"——横幅是常驻展示位 |
| 条数 | `BANNER_LIMIT = 5` | 没有已读淘汰，不限条数会越攒越多 |
| 形式 | 淡入淡出轮播，6s | 跑马灯读到一半跑掉，手机端与无障碍都差 |
| 正文怎么看 | 悬停原地下拉展开 | 不占额外版面；点击仍是跳转，两种意图不冲突 |
| 告知 vs 链接 | `banner_link` 空 = 纯告知 | 「本周六维护」点进消息中心看同一句话，是白跑一趟 |
| 官网那条 | 也入库 | 见下 |

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
migrations/versions/announcement_banner_20260913.py   加 2 列(幂等 IF NOT EXISTS)
app/models/announcement.py       show_on_banner / banner_link + banner_items()
app/views/announcement.py        _normalize_banner_link() + create/update 接字段
app/views/main.py                仪表盘视图传 banner_items
app/templates/main/at_dashboard.html          轮播容器 + CSS + JS
app/templates/announcement/partials/_announcement_modal_fields.html   两个表单控件
app/templates/announcement/tw_list.html       表单读写接上
```

**已发布公告也能改横幅两项** —— 原 `api_update` 对 `is_readonly` 直接拒绝，那样一条
已发布公告挂上首页后就再也撤不下来，只能删公告（连带消息中心记录一起没）。

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
