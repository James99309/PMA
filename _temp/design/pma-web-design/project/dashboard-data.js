/* ─────────────────────────────────────────────────────────────
   PMA · 仪表盘 · Mock 数据
   ───────────────────────────────────────────────────────────── */

window.DASH = (() => {

  /* ── 我的待办 ─────────────────────────────────────────────── */
  const todos = [
    { id: "T1", type: "approval", typeLabel: "待审批", tone: "warn",
      title: "张三 · 出差报销 ¥1,820.50",
      meta: "EXP-2026-0512 · 3 项明细",
      who: "张三",
      when: "1天前",
      route: "approval/EXP-2026-0512",
      urgent: false },
    { id: "T2", type: "approval", typeLabel: "待审批", tone: "warn",
      title: "采购订单 PO-2026-0103 终审",
      meta: "供应商：广州英沃 · ¥48,600.00",
      who: "王采",
      when: "2小时前",
      route: "approval/PO-2026-0103",
      urgent: true },
    { id: "T3", type: "approval", typeLabel: "待审批", tone: "warn",
      title: "项目立项 · 苏州 MO 酒店项目",
      meta: "预算 ¥320,000",
      who: "孙杰",
      when: "3天前",
      route: "approval/PRJ-026",
      urgent: true },
    { id: "T4", type: "quotation", typeLabel: "待确认报价", tone: "info",
      title: "QU-2026-0521 · 中石化广西北海",
      meta: "等待 SM 二次确认 · ¥1,129,938.00",
      who: "孙杰",
      when: "4小时前",
      route: "quotation/QU-2026-0521" },
    { id: "T5", type: "mention", typeLabel: "@我的", tone: "accent",
      title: "李四 在 PO-2026-0099 回复了你",
      meta: "「这批等到货之后再拆…」",
      who: "李四",
      when: "30分钟前",
      route: "po/PO-2026-0099" },
    { id: "T6", type: "action", typeLabel: "超期 Action", tone: "danger",
      title: "广州宇洪科技 · 35 天未沟通",
      meta: "客户：广州宇洪 · 上次：4-19 电话",
      who: "—",
      when: "—",
      route: "customer/YH-018" },
    { id: "T7", type: "action", typeLabel: "超期 Action", tone: "danger",
      title: "知识城智能汽车 · 42 天未沟通",
      meta: "客户：知识城 · 上次：4-12 邮件",
      who: "—",
      when: "—",
      route: "customer/ZSC-002" },
    { id: "T8", type: "task", typeLabel: "超期任务", tone: "danger",
      title: "整理 Q2 销售复盘材料",
      meta: "应完成于 05-20 (已超期 4 天)",
      who: "我",
      when: "—",
      route: "task/901" },
  ];

  /* ── 我的 KPI ──────────────────────────────────────────────── */
  const kpis = {
    salesGoal:    { label: "本季销售目标",  value: 1620000, target: 2400000, unit: "¥" },
    quoteWin:     { label: "报价转化率",    value: 60,      target: 100,     unit: "%" },
    activeCust:   { label: "活跃客户",      value: 12,      target: 15,      unit: " 户" },
    budget:       { label: "年度费用预算",  value: 415020,  target: 1783930, unit: "¥" },
  };
  const todayStats = {
    newCust:   2,
    newQuote:  5,
    newAction: 18,
    newOrder:  3,
  };

  /* ── 销售漏斗 (5 段) ──────────────────────────────────────── */
  const funnel = [
    { stage: "报价",   count: 32, amount: 3_240_000 },
    { stage: "已确认", count: 24, amount: 2_410_000 },
    { stage: "批价",   count: 18, amount: 1_820_000 },
    { stage: "SO",     count: 12, amount: 1_140_000 },
    { stage: "已出货", count: 8,  amount:   810_000 },
  ];
  const funnelConversion = 25;  // %
  const funnelYoY = 12;         // +12% 同比

  /* ── 我的项目 (进行中) ────────────────────────────────────── */
  const projects = [
    { id: "P1", name: "中石化广西北海炼化装置防爆区域 5G", stage: "标中",   stageT: "success", progress: 56, dueIn: 3, dueRed: true },
    { id: "P2", name: "上海豫园南里二期",                  stage: "实施",   stageT: "info",    progress: 56, dueIn: 12 },
    { id: "P3", name: "苏州文华东方 MO 酒店项目",           stage: "立项",   stageT: "neutral", progress: 14, dueIn: 28 },
    { id: "P4", name: "福建亚升集团总部大楼",               stage: "植入",   stageT: "accent",  progress: 28, dueIn: 18 },
    { id: "P5", name: "济南起步区综合医疗中心",             stage: "标中",   stageT: "success", progress: 56, dueIn: 5,  dueRed: true },
    { id: "P6", name: "广州粤芯半导体四期",                 stage: "报价",   stageT: "warn",    progress: 22, dueIn: 21 },
  ];
  const projectCounts = { active: 8, dueSoon: 2 };

  /* ── 我的报价 (按状态) ────────────────────────────────────── */
  const quotes = [
    { id: "QU-2026-0521", title: "中石化广西北海", amount: 1_129_938.00, status: "待确认",  tone: "warn",    urgent: true,  expireIn: 2 },
    { id: "QU-2026-0501", title: "上海瑞康通信",   amount:   302_273.00, status: "待回复",  tone: "info",    urgent: false, expireIn: 5 },
    { id: "QU-2026-0498", title: "科思创聚合物",   amount:    20_123.06, status: "草稿",    tone: "neutral", urgent: false },
    { id: "QU-2026-0496", title: "上海瑞康通信",   amount:   124_047.20, status: "即将到期", tone: "danger",  urgent: true,  expireIn: 1 },
    { id: "QU-2026-0492", title: "苏州文华东方",   amount:   149_459.00, status: "已成交",  tone: "success" },
  ];
  const quoteCounts = { draft: 3, awaitConfirm: 5, awaitReply: 2, expiring: 1, wonThisMonth: 12 };

  /* ── 我的报销 (年度 + 月度折线 + 最近) ──────────────────────── */
  const expense = {
    yearTotal:   45_318.72,
    yearTotalLast: 38_900.00,
    monthly: [3200, 5180, 4220, 6510, 7800, 4910, 3120, 2480, 1450, 980, 4670, 0],
    months:  ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
    recent: [
      { id: "EXP-0512", title: "招待费 · 中石化广州",   amount: 1820.50, status: "待审批",  tone: "warn"    },
      { id: "EXP-0511", title: "出差 · 杭州博览会",     amount:  716.23, status: "已通过",  tone: "success" },
      { id: "EXP-0510", title: "招待费 · 福建亚升",     amount:  303.30, status: "已通过",  tone: "success" },
    ],
  };

  /* ── 工作记录流 ─────────────────────────────────────────────── */
  const worklog = [
    { id: "W1", who: "孙杰", customer: "茂名佳胜科技",  project: "中石化广西北海",
      time: "2小时前", date: "2026-05-22",
      text: "中石化广西北海炼化装置防爆区域 5G 及无线对讲信号增强项目,今日完成第二次现场勘查,与业主确认了天线安装点位 17 处。",
      replies: 3, mentioned: true },
    { id: "W2", who: "孙杰", customer: "广州宇洪科技",  project: "广州粤芯半导体",
      time: "4小时前", date: "2026-05-22",
      text: "广州粤芯半导体四期新建项目,配合广州宇洪对接中标集成商,今日提交了一稿系统设计方案。",
      replies: 1 },
    { id: "W3", who: "康国", customer: "—",            project: "深圳湾超级总部",
      time: "今天 10:32", date: "2026-05-22",
      text: "深湾发展朱总下午在 C 塔项目部,拜访了朱总并对跟三家集成商的方案做了横向对比,客户倾向方案 B。",
      replies: 0 },
    { id: "W4", who: "康国", customer: "—",            project: "深圳湾超级总部",
      time: "昨天 17:55", date: "2026-05-21",
      text: "C 塔项目部见成本郑杰及设计,跟郑杰沟通了两种方案的取舍,郑杰倾向预算可控的方案 A。",
      replies: 2 },
    { id: "W5", who: "方玲", customer: "科思创聚合物",   project: "科思创 C506 区",
      time: "昨天 14:21", date: "2026-05-21",
      text: "506 区域未做信号覆盖,工程师出具初步方案,根据方案做物料估算并向甲方汇报。",
      replies: 0 },
    { id: "W6", who: "方玲", customer: "中芯南方集成",   project: "—",
      time: "昨天 09:08", date: "2026-05-21",
      text: "中芯南方维修检测维修跟进,检测告知设备正常,与产线负责人确认下次保养窗口。",
      replies: 4, mentioned: true },
  ];

  /* ── 风险提醒 (条件性条) ──────────────────────────────────── */
  const alerts = [
    { kind: "approval", text: "5 单审批超 3 天未处理", to: "approval?stale=1" },
    { kind: "quote",    text: "3 张报价即将到期",       to: "quote?expiring=1" },
    { kind: "stock",    text: "2 个 SN 库存低于安全水位", to: "inventory?low=1" },
  ];

  /* ── 全局搜索结果 (mock) ──────────────────────────────────── */
  const searchSuggest = {
    "客户":   [{label: "广州宇洪科技有限公司", sub: "YH-018"}, {label: "茂名佳胜科技",     sub: "JS-031"}, {label: "中石化广西北海", sub: "ZSH-007"}],
    "项目":   [{label: "中石化广西北海炼化装置防爆区域 5G", sub: "PRJ-019"}, {label: "上海豫园南里二期", sub: "PRJ-016"}],
    "报价":   [{label: "QU-2026-0521 · 中石化广西北海", sub: "¥1,129,938"}, {label: "QU-2026-0501 · 上海瑞康", sub: "¥302,273"}],
    "SN":     [{label: "ETC-2403-00187", sub: "Cisco WS-C3850"}],
    "产品":   [{label: "5G 防爆 CPE · EBC-500S", sub: "EBC"}],
  };

  /* ── 当前用户 / 角色 ───────────────────────────────────────── */
  const currentUser = {
    name: "张伟",
    title: "采购经理",
    role: "admin",
  };

  return {
    todos, kpis, todayStats, funnel, funnelConversion, funnelYoY,
    projects, projectCounts, quotes, quoteCounts,
    expense, worklog, alerts, searchSuggest, currentUser,
  };
})();
