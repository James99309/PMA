// PMA Chat · 位置消息气泡(对话流中的地图卡 + 点开后的导航全屏)
const LOC = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#C2BBB3',
  divider: 'rgba(0,0,0,0.06)', dividerStrong: 'rgba(0,0,0,0.10)',
  accent: '#D97757', accentSoft: '#F4E4D8', accentBg: 'rgba(217,119,87,0.08)',
  blue: '#4D82E0',
  serif: '"Tiempos Headline","Source Serif Pro","Noto Serif SC",Georgia,serif',
  sans: '-apple-system,"SF Pro Text","PingFang SC",system-ui,sans-serif',
  mono: 'ui-monospace,"SF Mono",monospace',
};

function LOCStatusPad() { return <div style={{ height: 54 }}/>; }
function LOCNav({ title, sub }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', padding: '6px 16px 10px', gap: 10,
      borderBottom: `1px solid ${LOC.divider}`, background: LOC.bg }}>
      <span style={{ fontSize: 22, color: LOC.ink2, padding: '0 4px' }}>‹</span>
      <div style={{ flex: 1, textAlign: 'center', minWidth: 0 }}>
        <div style={{ fontFamily: LOC.serif, fontSize: 16, fontWeight: 500 }}>{title}</div>
        {sub && <div style={{ fontSize: 11, color: LOC.ink3, marginTop: 1 }}>{sub}</div>}
      </div>
      <div style={{ width: 24, fontSize: 18, color: LOC.ink3 }}>···</div>
    </div>
  );
}
function LOCDay({ label }) {
  return (
    <div style={{ textAlign: 'center', padding: '14px 0 8px' }}>
      <span style={{ fontSize: 11, color: LOC.ink3, fontFamily: LOC.serif, fontStyle: 'italic' }}>{label}</span>
    </div>
  );
}

// 复用的 mini map svg(在气泡内 / 全屏顶都用)— 紧凑版
function MiniMap({ width = 252, height = 132, pinX = '50%', pinY = '52%' }) {
  return (
    <div style={{ position: 'relative', width, height, background: '#E8E4DC', overflow: 'hidden' }}>
      <svg width="100%" height="100%" viewBox="0 0 260 140" preserveAspectRatio="xMidYMid slice">
        <rect x="0" y="0" width="260" height="140" fill="#E8E4DC"/>
        {/* 主干道 */}
        <path d="M-10 50 L270 80" stroke="#fff" strokeWidth="9"/>
        <path d="M120 -10 L150 150" stroke="#fff" strokeWidth="7"/>
        {/* 次干道 */}
        <path d="M-10 110 L270 122" stroke="#F1ECE3" strokeWidth="4"/>
        <path d="M30 -10 L42 150" stroke="#F1ECE3" strokeWidth="4"/>
        <path d="M210 -10 L222 150" stroke="#F1ECE3" strokeWidth="4"/>
        {/* 街区 */}
        <rect x="60" y="14" width="40" height="36" fill="#DCD5C5" rx="1.5"/>
        <rect x="170" y="14" width="40" height="36" fill="#DCD5C5" rx="1.5"/>
        <rect x="50" y="118" width="50" height="22" fill="#DCD5C5" rx="1.5"/>
        <rect x="165" y="118" width="50" height="22" fill="#DCD5C5" rx="1.5"/>
        {/* 公园 */}
        <path d="M155 84 L240 84 L240 116 L155 116 Z" fill="#D4DDC8" rx="1.5"/>
      </svg>

      {/* pin 居中 */}
      <div style={{ position: 'absolute', left: pinX, top: pinY, transform: 'translate(-50%, -100%)',
        filter: 'drop-shadow(0 3px 4px rgba(0,0,0,0.22))' }}>
        <svg width="22" height="28" viewBox="0 0 32 40">
          <path d="M16 38 C 16 38, 4 22, 4 14 A 12 12 0 1 1 28 14 C 28 22, 16 38, 16 38 Z" fill={LOC.accent}/>
          <circle cx="16" cy="14" r="5" fill="#fff"/>
        </svg>
      </div>
    </div>
  );
}

// ═══ 1) 位置消息气泡(项目群,有发送 + 接收) ════════════════════════
function ChatLocationBubbles() {
  return (
    <div style={{ background: LOC.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: LOC.sans }}>
      <LOCStatusPad/>
      <LOCNav title="深圳半导体工厂扩产" sub="5 人 · 招标中"/>

      <div style={{ flex: 1, overflow: 'auto', padding: '6px 0 12px' }}>
        <LOCDay label="今天"/>

        {/* 普通消息(铺底) */}
        <div style={{ padding: '6px 14px', display: 'flex', gap: 8 }}>
          <div style={{ width: 30, height: 30, borderRadius: 15, background: LOC.accentSoft, color: LOC.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: LOC.serif, fontSize: 13, fontWeight: 600, flexShrink: 0 }}>陈</div>
          <div style={{ maxWidth: 280 }}>
            <div style={{ fontSize: 11, color: LOC.ink3, marginBottom: 3, marginLeft: 2 }}>陈刚 · 14:02</div>
            <div style={{ background: LOC.card, border: `1px solid ${LOC.divider}`, padding: '9px 13px',
              borderRadius: 14, fontFamily: LOC.serif, fontSize: 14.5, lineHeight: 1.5, color: LOC.ink }}>
              我已经到工地了,把现场位置发给你们。
            </div>
          </div>
        </div>

        {/* 接收态位置卡 */}
        <div style={{ padding: '6px 14px', display: 'flex', gap: 8, alignItems: 'flex-start' }}>
          <div style={{ width: 30, height: 30, borderRadius: 15, background: LOC.accentSoft, color: LOC.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: LOC.serif, fontSize: 13, fontWeight: 600, flexShrink: 0 }}>陈</div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: 11, color: LOC.ink3, marginBottom: 3, marginLeft: 2 }}>陈刚 · 14:02</div>
            {/* 卡片本体 */}
            <div style={{
              width: 252,
              background: LOC.card, border: `1px solid ${LOC.divider}`,
              borderRadius: 14, overflow: 'hidden',
              boxShadow: '0 1px 2px rgba(0,0,0,0.03)',
            }}>
              <MiniMap/>
              <div style={{ padding: '10px 12px 12px' }}>
                <div style={{ fontFamily: LOC.serif, fontSize: 14, fontWeight: 600, color: LOC.ink,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  深铁阅洺境花园(售楼处)
                </div>
                <div style={{ fontSize: 11.5, color: LOC.ink3, marginTop: 3,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  深圳市龙岗区宝龙街道站前路3号
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 发送态位置卡(自己发的)*/}
        <div style={{ padding: '6px 14px', display: 'flex', flexDirection: 'row-reverse', gap: 8, alignItems: 'flex-start' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <div style={{
              width: 252,
              background: LOC.ink, color: '#fff',
              borderRadius: 14, overflow: 'hidden',
              boxShadow: '0 1px 2px rgba(0,0,0,0.06)',
            }}>
              <MiniMap pinX="50%" pinY="48%"/>
              <div style={{ padding: '10px 12px 12px' }}>
                <div style={{ fontFamily: LOC.serif, fontSize: 14, fontWeight: 600,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  阅洺境工地临时办公楼
                </div>
                <div style={{ fontSize: 11.5, opacity: 0.7, marginTop: 3,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  站前路3号工地北侧
                </div>
              </div>
            </div>
            <div style={{ fontSize: 11, color: LOC.ink3, marginTop: 3, marginRight: 2 }}>14:05 · 已读</div>
          </div>
        </div>

        {/* 后续追问 */}
        <div style={{ padding: '6px 14px', display: 'flex', gap: 8 }}>
          <div style={{ width: 30, height: 30, borderRadius: 15, background: LOC.accentSoft, color: LOC.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: LOC.serif, fontSize: 13, fontWeight: 600, flexShrink: 0 }}>李</div>
          <div style={{ maxWidth: 280 }}>
            <div style={{ fontSize: 11, color: LOC.ink3, marginBottom: 3, marginLeft: 2 }}>李明 · 14:08</div>
            <div style={{ background: LOC.card, border: `1px solid ${LOC.divider}`, padding: '9px 13px',
              borderRadius: 14, fontFamily: LOC.serif, fontSize: 14.5, lineHeight: 1.5, color: LOC.ink }}>
              收到,我开车 30 分钟到。
            </div>
          </div>
        </div>
      </div>

      {/* 输入栏 */}
      <div style={{ borderTop: `1px solid ${LOC.divider}`, background: LOC.bg,
        padding: '8px 12px 24px', display: 'flex', alignItems: 'flex-end', gap: 8 }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: LOC.card, border: `1px solid ${LOC.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: LOC.ink2, fontWeight: 300 }}>+</span>
        <div style={{ flex: 1, background: LOC.card, borderRadius: 20, border: `1px solid ${LOC.dividerStrong}`,
          padding: '9px 14px', fontFamily: LOC.serif, fontSize: 14, color: LOC.ink3, fontStyle: 'italic',
          minHeight: 36, display: 'flex', alignItems: 'center' }}>说点什么…</div>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: LOC.card, border: `1px solid ${LOC.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="6" y="2" width="4" height="8" rx="2" stroke={LOC.ink2} strokeWidth="1.4"/>
            <path d="M3.5 8a4.5 4.5 0 009 0M8 12.5V14" stroke={LOC.ink2} strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
        </span>
      </div>
    </div>
  );
}

// ═══ 2) 点开位置卡 — 全屏地图 + 导航 ═══════════════════════════════
function LocationDetail() {
  return (
    <div style={{ background: LOC.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: LOC.sans, position: 'relative' }}>
      <LOCStatusPad/>
      <div style={{ padding: '6px 16px 10px', display: 'flex', alignItems: 'center', gap: 10,
        background: LOC.bg, borderBottom: `1px solid ${LOC.divider}` }}>
        <span style={{ fontSize: 22, color: LOC.ink2, padding: '0 4px' }}>‹</span>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontFamily: LOC.serif, fontSize: 16, fontWeight: 500 }}>位置详情</div>
        </div>
        <span style={{ fontSize: 13, color: LOC.ink2 }}>分享</span>
      </div>

      {/* 大地图 */}
      <div style={{ position: 'relative', flex: 1, background: '#E8E4DC', overflow: 'hidden' }}>
        <svg width="100%" height="100%" viewBox="0 0 430 600" preserveAspectRatio="xMidYMid slice">
          <rect x="0" y="0" width="430" height="600" fill="#E8E4DC"/>
          {/* 主干道 */}
          <path d="M-20 220 L450 280" stroke="#fff" strokeWidth="14"/>
          <path d="M-20 220 L450 280" stroke="#D6D0C2" strokeWidth="14" strokeDasharray="2 6" strokeOpacity="0.5"/>
          <path d="M180 -20 L240 620" stroke="#fff" strokeWidth="11"/>
          {/* 次干道 */}
          <path d="M-20 420 L450 450" stroke="#F1ECE3" strokeWidth="6"/>
          <path d="M50 -20 L80 620" stroke="#F1ECE3" strokeWidth="6"/>
          <path d="M340 -20 L370 620" stroke="#F1ECE3" strokeWidth="6"/>
          <path d="M-20 100 L450 130" stroke="#F1ECE3" strokeWidth="5"/>
          {/* 街区 */}
          <rect x="100" y="40" width="60" height="50" fill="#DCD5C5" rx="2"/>
          <rect x="260" y="40" width="60" height="50" fill="#DCD5C5" rx="2"/>
          <rect x="80" y="320" width="80" height="90" fill="#DCD5C5" rx="2"/>
          <rect x="270" y="320" width="80" height="90" fill="#DCD5C5" rx="2"/>
          <rect x="80" y="480" width="80" height="120" fill="#DCD5C5" rx="2"/>
          {/* 公园 */}
          <path d="M250 460 L390 460 L390 540 L250 540 Z" fill="#D4DDC8"/>
          <text x="320" y="505" textAnchor="middle" fill="#8a9277" fontSize="11" fontFamily="serif" fontStyle="italic">龙岗公园</text>
          <text x="380" y="266" fill="#aaa" fontSize="10" fontStyle="italic">龙岗大道</text>
          <text x="195" y="190" fill="#aaa" fontSize="10" fontStyle="italic" transform="rotate(-89 195 190)">站前路</text>
        </svg>

        {/* 中心 pin */}
        <div style={{ position: 'absolute', left: '50%', top: '46%', transform: 'translate(-50%, -100%)',
          filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.22))' }}>
          <svg width="34" height="42" viewBox="0 0 32 40">
            <path d="M16 38 C 16 38, 4 22, 4 14 A 12 12 0 1 1 28 14 C 28 22, 16 38, 16 38 Z" fill={LOC.accent}/>
            <circle cx="16" cy="14" r="5" fill="#fff"/>
          </svg>
        </div>

        {/* 我的位置(蓝点) */}
        <div style={{ position: 'absolute', left: '38%', top: '70%' }}>
          <span style={{ width: 14, height: 14, borderRadius: 7, background: LOC.blue,
            border: '2px solid #fff', display: 'block',
            boxShadow: '0 0 0 6px rgba(77,130,224,0.18)' }}/>
        </div>

        {/* 浮动按钮 — 我的位置 */}
        <span style={{
          position: 'absolute', right: 14, top: 14,
          width: 38, height: 38, borderRadius: 19,
          background: LOC.card, border: `1px solid ${LOC.divider}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
        }}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="3.5" stroke={LOC.accent} strokeWidth="1.6"/>
            <circle cx="9" cy="9" r="1.5" fill={LOC.accent}/>
            <path d="M9 1v2.5M9 14.5V17M1 9h2.5M14.5 9H17" stroke={LOC.accent} strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
        </span>
      </div>

      {/* 底部 sheet */}
      <div style={{ background: LOC.card, borderRadius: '20px 20px 0 0', padding: '14px 18px 28px',
        boxShadow: '0 -8px 24px rgba(0,0,0,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 10 }}>
          <div style={{ width: 36, height: 4, background: LOC.dividerStrong, borderRadius: 2 }}/>
        </div>
        <div style={{ fontFamily: LOC.serif, fontSize: 18, fontWeight: 600, color: LOC.ink }}>
          深铁阅洺境花园(售楼处)
        </div>
        <div style={{ fontSize: 12.5, color: LOC.ink3, marginTop: 4 }}>
          深圳市龙岗区宝龙街道站前路3号
        </div>
        <div style={{ fontSize: 11, color: LOC.ink3, marginTop: 8, display: 'flex', gap: 10 }}>
          <span><span style={{ color: LOC.accent, fontWeight: 600 }}>2.4</span> 公里</span>
          <span>·</span>
          <span>开车 8 分钟</span>
          <span>·</span>
          <span>步行 28 分钟</span>
        </div>

        {/* 操作按钮 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginTop: 14 }}>
          <span style={{
            background: LOC.accent, color: '#fff', textAlign: 'center', padding: '11px 0',
            borderRadius: 12, fontSize: 14, fontWeight: 600,
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M2 8l12-6-3 14-3-6-6-2z" fill="#fff"/>
            </svg>
            导航
          </span>
          <span style={{
            background: LOC.card, border: `1px solid ${LOC.dividerStrong}`,
            color: LOC.ink, textAlign: 'center', padding: '11px 0',
            borderRadius: 12, fontSize: 13, fontWeight: 500,
          }}>
            高德
          </span>
          <span style={{
            background: LOC.card, border: `1px solid ${LOC.dividerStrong}`,
            color: LOC.ink, textAlign: 'center', padding: '11px 0',
            borderRadius: 12, fontSize: 13, fontWeight: 500,
          }}>
            百度
          </span>
        </div>

        {/* 复制 / 收藏 */}
        <div style={{ marginTop: 10, display: 'flex', gap: 10, justifyContent: 'center', fontSize: 12, color: LOC.ink3 }}>
          <span>复制地址</span>
          <span>·</span>
          <span>添加到收藏</span>
          <span>·</span>
          <span>关联到项目</span>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ChatLocationBubbles, LocationDetail });
