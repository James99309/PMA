// PMA · 工作日历 — base tokens + mock 数据
// 沿用 A 方向 + Task 同套 token

const CAL = {
  bg: '#F7F5F2', card: '#FFFFFF',
  ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#B5AEA3',
  divider: '#EBE6DD', dividerSoft: '#F2EEE6',
  accent: '#D97757', accentSoft: '#FAEEE5',
  blue: '#3A6FB7', blueSoft: '#E5EBF4', blueDeep: '#1A4A8C',
  green: '#2F7A4F', greenSoft: '#E9F1EB',
  warn: '#C77B22', warnSoft: '#F9F1E6',
  red: '#B5453A', redSoft: '#F4E4E1',
  purple: '#7B5BAC', purpleSoft: '#EEE6F5',
  teal: '#1F8478', tealSoft: '#DEEFEB',
  pink: '#C46B91', pinkSoft: '#F6E1EB',
  serif: '"Tiempos Headline", "Source Serif Pro", "Noto Serif SC", Georgia, serif',
  sans: '"PingFang SC", -apple-system, "Helvetica Neue", sans-serif',
  mono: '"SF Mono", "JetBrains Mono", monospace',
};
const STATUS_PAD_CAL = 54;
function CALStatusPad() { return <div style={{ height: STATUS_PAD_CAL }}/>; }

// 工作类型 — 31 类 / 6 组(取后端 label,这里 mock 中文)
const CAL_TYPE_GROUPS = [
  { id: 'general', label: '通用', types: [
    { id: 'meeting',  label: '会议',     color: CAL.blue,   bg: CAL.blueSoft },
    { id: 'training', label: '内部培训', color: CAL.purple, bg: CAL.purpleSoft },
    { id: 'other',    label: '其他',     color: CAL.ink3,   bg: CAL.dividerSoft },
  ]},
  { id: 'sales', label: '行销', types: [
    { id: 'customer_visit',   label: '客户拜访', color: CAL.accent, bg: CAL.accentSoft },
    { id: 'presales',         label: '售前支持', color: CAL.teal,   bg: CAL.tealSoft },
    { id: 'negotiation',      label: '商务洽谈', color: CAL.warn,   bg: CAL.warnSoft },
    { id: 'maintenance',      label: '客户维护', color: CAL.pink,   bg: CAL.pinkSoft },
  ]},
  { id: 'market', label: '市场', types: [
    { id: 'video',     label: '视频制作', color: CAL.purple, bg: CAL.purpleSoft },
    { id: 'design',    label: '物料设计', color: CAL.pink,   bg: CAL.pinkSoft },
    { id: 'social',    label: '社媒运营', color: CAL.blue,   bg: CAL.blueSoft },
    { id: 'channel',   label: '渠道活动', color: CAL.warn,   bg: CAL.warnSoft },
    { id: 'event',     label: '品牌活动', color: CAL.accent, bg: CAL.accentSoft },
  ]},
  { id: 'service', label: '服务', types: [
    { id: 'onsite',    label: '现场维护', color: CAL.teal,   bg: CAL.tealSoft },
    { id: 'response',  label: '服务响应', color: CAL.green,  bg: CAL.greenSoft },
    { id: 'tech',      label: '技术支持', color: CAL.blue,   bg: CAL.blueSoft },
    { id: 'trouble',   label: '故障排查', color: CAL.red,    bg: CAL.redSoft },
  ]},
  { id: 'admin', label: '行政', types: [
    { id: 'admin',     label: '行政事务', color: CAL.ink3,   bg: CAL.dividerSoft },
    { id: 'office',    label: '办公管理', color: CAL.ink3,   bg: CAL.dividerSoft },
    { id: 'asset',     label: '资产管理', color: CAL.ink3,   bg: CAL.dividerSoft },
  ]},
  { id: 'others', label: '人事 / 财务 / 产品', types: [
    { id: 'hr',        label: '人事',     color: CAL.purple, bg: CAL.purpleSoft },
    { id: 'finance',   label: '财务',     color: CAL.green,  bg: CAL.greenSoft },
    { id: 'product',   label: '产品',     color: CAL.accent, bg: CAL.accentSoft },
  ]},
];
function calType(id) {
  for (const g of CAL_TYPE_GROUPS) {
    const t = g.types.find(x => x.id === id);
    if (t) return t;
  }
  return { label: id, color: CAL.ink3, bg: CAL.dividerSoft };
}

// 当前周(5/11–5/17) — 选中今天 5/14
const CAL_WEEK = [
  { d: 11, w: '周一', date: '2026/05/11', items: 2 },
  { d: 12, w: '周二', date: '2026/05/12', items: 4 },
  { d: 13, w: '周三', date: '2026/05/13', items: 3 },
  { d: 14, w: '周四', date: '2026/05/14', items: 5, today: true, sel: true },
  { d: 15, w: '周五', date: '2026/05/15', items: 2 },
  { d: 16, w: '周六', date: '2026/05/16', items: 0, weekend: true },
  { d: 17, w: '周日', date: '2026/05/17', items: 1, weekend: true, holiday: '端午' },
];

// 今日工作项
const CAL_ITEMS_TODAY = [
  { id: 'W1', type: 'meeting',         title: '与技术、产品团队会议',
    sub: '推进新加坡节点 MCP 部署', start: '09:00', end: '10:00', hours: 1.0,
    project: '新加坡 MCP', dingtalk: true },
  { id: 'W2', type: 'customer_visit',  title: '拜访上海地方枢纽业主',
    sub: '需求确认 + 现场勘查', start: '10:30', end: '12:30', hours: 2.0,
    customer: '上海宝山节能科技' },
  { id: 'W3', type: 'tech',            title: '新加坡节点 MCP 部署',
    sub: '远程协助配置 + 联调', start: '14:00', end: '17:00', hours: 3.0,
    project: '新加坡 MCP' },
  { id: 'W4', type: 'meeting',         title: '财务/人事/技术/产品 4 部门月会',
    sub: '月度复盘 + Q3 规划', start: '17:00', end: '18:00', hours: 1.0 },
  { id: 'W5', type: 'admin',           title: '通知人事部门:政策需走知会',
    sub: '邮件 + 同步飞书群', allDay: false, start: '18:00', end: '18:30', hours: 0.5,
    status: 'completed' },
];

// 日报状态
const CAL_DAILY_LOG = {
  date: '2026-05-14',
  status: 'draft',                  // draft / submitted
  totalHours: 7.5,
  itemCount: 5,
  summary: '今日完成 1 次客户拜访、3 项技术对接会议、1 项跨部门月会;主要推进新加坡 MCP 部署。',
  notes: '',
  qualityScore: null,                // submitted 后才有
  issues: [],
};
const CAL_DAILY_LOG_SUBMITTED = {
  ...CAL_DAILY_LOG,
  status: 'submitted',
  notes: '客户拜访期间发现现场配电柜与图纸不符,已记录到项目跟进。',
  qualityScore: 87,
  grade: '良好',
  issues: [
    { code: 'no_quotation', label: '未关联报价单', tone: 'warn',
      tip: '建议补充关联,便于销售复盘' },
    { code: 'short_admin',  label: '行政类描述过短', tone: 'info',
      tip: '加 1–2 句沟通对象更利于团队检索' },
  ],
};

function cfmt(n) { return n.toFixed(1).replace(/\.0$/, ''); }
