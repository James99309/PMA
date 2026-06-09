// PMA · Work Calendar (EN) — base tokens + mock data
const CALEN = {
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
  serif: '"Tiempos Headline", "Source Serif Pro", Georgia, serif',
  sans: '-apple-system, "SF Pro Text", "Helvetica Neue", sans-serif',
  mono: '"SF Mono", "JetBrains Mono", monospace',
};
const STATUS_PAD_CALEN = 54;
function CALENStatusPad() { return <div style={{ height: STATUS_PAD_CALEN }}/>; }

const CALEN_TYPE_GROUPS = [
  { id: 'general', label: 'General', types: [
    { id: 'meeting',  label: 'Meeting',  color: CALEN.blue,   bg: CALEN.blueSoft },
    { id: 'training', label: 'Training', color: CALEN.purple, bg: CALEN.purpleSoft },
    { id: 'other',    label: 'Other',    color: CALEN.ink3,   bg: CALEN.dividerSoft },
  ]},
  { id: 'sales', label: 'Sales', types: [
    { id: 'visit',   label: 'Customer Visit', color: CALEN.accent, bg: CALEN.accentSoft },
    { id: 'presale', label: 'Presales',       color: CALEN.teal,   bg: CALEN.tealSoft },
    { id: 'nego',    label: 'Negotiation',    color: CALEN.warn,   bg: CALEN.warnSoft },
    { id: 'maint',   label: 'Account Mgmt',   color: CALEN.pink,   bg: CALEN.pinkSoft },
  ]},
  { id: 'market', label: 'Marketing', types: [
    { id: 'video',   label: 'Video',     color: CALEN.purple, bg: CALEN.purpleSoft },
    { id: 'design',  label: 'Design',    color: CALEN.pink,   bg: CALEN.pinkSoft },
    { id: 'social',  label: 'Social',    color: CALEN.blue,   bg: CALEN.blueSoft },
    { id: 'channel', label: 'Channel',   color: CALEN.warn,   bg: CALEN.warnSoft },
    { id: 'event',   label: 'Event',     color: CALEN.accent, bg: CALEN.accentSoft },
  ]},
  { id: 'service', label: 'Service', types: [
    { id: 'onsite',  label: 'On-site',   color: CALEN.teal,   bg: CALEN.tealSoft },
    { id: 'resp',    label: 'Response',  color: CALEN.green,  bg: CALEN.greenSoft },
    { id: 'tech',    label: 'Tech Support', color: CALEN.blue, bg: CALEN.blueSoft },
    { id: 'trouble', label: 'Troubleshoot', color: CALEN.red,  bg: CALEN.redSoft },
  ]},
  { id: 'admin', label: 'Admin', types: [
    { id: 'admin',   label: 'Admin Affairs', color: CALEN.ink3, bg: CALEN.dividerSoft },
    { id: 'office',  label: 'Office Mgmt',   color: CALEN.ink3, bg: CALEN.dividerSoft },
    { id: 'asset',   label: 'Asset Mgmt',    color: CALEN.ink3, bg: CALEN.dividerSoft },
  ]},
  { id: 'others', label: 'HR / Finance / Product', types: [
    { id: 'hr',      label: 'HR',       color: CALEN.purple, bg: CALEN.purpleSoft },
    { id: 'finance', label: 'Finance',  color: CALEN.green,  bg: CALEN.greenSoft },
    { id: 'product', label: 'Product',  color: CALEN.accent, bg: CALEN.accentSoft },
  ]},
];
function calTypeEN(id) {
  for (const g of CALEN_TYPE_GROUPS) {
    const t = g.types.find(x => x.id === id);
    if (t) return t;
  }
  return { label: id, color: CALEN.ink3, bg: CALEN.dividerSoft };
}

const CALEN_WEEK = [
  { d: 11, w: 'Mon', items: 2 },
  { d: 12, w: 'Tue', items: 4 },
  { d: 13, w: 'Wed', items: 3 },
  { d: 14, w: 'Thu', items: 5, today: true, sel: true },
  { d: 15, w: 'Fri', items: 2 },
  { d: 16, w: 'Sat', items: 0, weekend: true },
  { d: 17, w: 'Sun', items: 1, weekend: true, holiday: 'Vesak' },
];

const CALEN_ITEMS_TODAY = [
  { id: 'W1', type: 'meeting', title: 'Tech & Product Sync',
    sub: 'Push SG MCP node deployment', start: '09:00', end: '10:00', hours: 1.0,
    project: 'SG MCP', dingtalk: true },
  { id: 'W2', type: 'visit', title: 'Visit Shanghai Hub Owner',
    sub: 'Requirements + site survey', start: '10:30', end: '12:30', hours: 2.0,
    customer: 'Shanghai Baoshan Energy Tech' },
  { id: 'W3', type: 'tech', title: 'SG Node MCP Deployment',
    sub: 'Remote config + integration', start: '14:00', end: '17:00', hours: 3.0,
    project: 'SG MCP' },
  { id: 'W4', type: 'meeting', title: 'Finance / HR / Tech / Product Monthly',
    sub: 'Monthly review + Q3 plan', start: '17:00', end: '18:00', hours: 1.0 },
  { id: 'W5', type: 'admin', title: 'Notify HR: policy needs sign-off',
    sub: 'Email + Lark sync', start: '18:00', end: '18:30', hours: 0.5,
    status: 'completed' },
];

const CALEN_DAILY_LOG = {
  date: '2026-05-14', status: 'draft', totalHours: 7.5, itemCount: 5,
  summary: 'Completed 1 customer visit, 3 technical / sync meetings, 1 cross-team monthly. Focus: SG MCP deployment.',
  notes: '', qualityScore: null, issues: [],
};
const CALEN_DAILY_LOG_SUBMITTED = {
  ...CALEN_DAILY_LOG, status: 'submitted',
  notes: 'On the customer visit, found the on-site switchboard differs from drawings. Logged to project follow-up.',
  qualityScore: 87, grade: 'Good',
  issues: [
    { code: 'no_quotation', label: 'No quotation linked', tone: 'warn',
      tip: 'Linking aids sales retrospective' },
    { code: 'short_admin',  label: 'Admin description too brief', tone: 'info',
      tip: 'Add 1–2 lines on whom you talked to' },
  ],
};

function cfmtEN(n) { return n.toFixed(1).replace(/\.0$/, ''); }
