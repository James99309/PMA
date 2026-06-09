// PMA Chat — 7 screens × 2 bubble variants
const CB = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#C2BBB3',
  divider: 'rgba(0,0,0,0.06)', dividerStrong: 'rgba(0,0,0,0.10)',
  accent: '#D97757', accentSoft: '#F4E4D8', accentBg: 'rgba(217,119,87,0.08)',
  blue: '#4D82E0', blueSoft: '#E5EDFA',
  green: '#2F7A45',
  serif: '"Tiempos Headline","Source Serif Pro","Noto Serif SC",Georgia,serif',
  sans: '-apple-system,"SF Pro Text","PingFang SC",system-ui,sans-serif',
  mono: 'ui-monospace,"SF Mono",monospace',
};

function StatusPad() { return <div style={{ height: 54 }}/>; }

function ChatNav({ title, sub, back = true, right }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', padding: '6px 16px 10px', gap: 10,
      borderBottom: `1px solid ${CB.divider}`, background: CB.bg,
    }}>
      {back && <span style={{ fontSize: 22, color: CB.ink2, padding: '0 4px' }}>‹</span>}
      <div style={{ flex: 1, textAlign: back ? 'center' : 'left', minWidth: 0 }}>
        <div style={{ fontFamily: CB.serif, fontSize: 16, fontWeight: 500, color: CB.ink,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{title}</div>
        {sub && <div style={{ fontSize: 11, color: CB.ink3, marginTop: 1 }}>{sub}</div>}
      </div>
      {right || <div style={{ width: 24 }}/>}
    </div>
  );
}

// ─── Screen 1: Conversation list ────────────────────────────────────
function ConvList() {
  const items = [
    { kind: 'broadcast', name: '公司广播', last: 'Q2 全员目标已发布', time: '09:21', unread: 0, pinned: true },
    { kind: 'project', name: '深圳半导体工厂扩产', sub: '5 人 · 招标中', last: '陈刚:周三现场勘查没问题', time: '09:18', unread: 3, stage: '招标中', stageColor: CB.accent },
    { kind: 'project', name: '上海某制造厂节能改造', sub: '4 人 · 嵌入', last: '系统:阶段已推进至嵌入', time: '昨天', unread: 0, stage: '嵌入', stageColor: CB.ink3, system: true },
    { kind: 'dm', name: '李明', sub: '产品经理', last: '记得把方案 PDF 发我', time: '昨天', unread: 1 },
    { kind: 'project', name: '杭州光伏电站二期', sub: '6 人 · 招标中', last: '王芳:@张伟 标书需补章程', time: '周二', unread: 0, stage: '招标中', stageColor: CB.accent, mention: true },
    { kind: 'dm', name: '王芳', sub: '商务', last: '语音消息 (00:12)', time: '周一', unread: 0 },
    { kind: 'project', name: '南京数据中心配电', sub: '7 人', last: '已发送:配电方案V3.pdf', time: '04-26', unread: 0 },
  ];
  return (
    <div style={{ background: CB.bg, height: '100%', fontFamily: CB.sans, color: CB.ink, paddingTop: 54 }}>
      <div style={{ padding: '14px 24px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 11, color: CB.ink3, fontWeight: 500, letterSpacing: 1.2, textTransform: 'uppercase' }}>2026 · 5月</div>
          <h1 style={{ fontFamily: CB.serif, fontSize: 32, fontWeight: 500, margin: '4px 0 0', letterSpacing: -0.4 }}>消息</h1>
        </div>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: CB.ink, color: '#fff',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 300 }}>+</span>
      </div>
      <div style={{ padding: '0 24px 12px', display: 'flex', gap: 8 }}>
        {['全部', '未读 4', '@我', '项目'].map((t, i) => (
          <span key={i} style={{ padding: '5px 12px', borderRadius: 999, fontSize: 12, fontWeight: 500,
            background: i === 0 ? CB.ink : 'transparent', color: i === 0 ? '#fff' : CB.ink2,
            border: i === 0 ? 'none' : `1px solid ${CB.dividerStrong}` }}>{t}</span>
        ))}
      </div>
      <div style={{ background: CB.card }}>
        {items.map((it, i) => (
          <div key={i} style={{ padding: '14px 20px', display: 'flex', gap: 12, borderBottom: i === items.length - 1 ? 'none' : `1px solid ${CB.divider}`, alignItems: 'flex-start' }}>
            <Avatar kind={it.kind} name={it.name} system={it.system}/>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontFamily: CB.serif, fontSize: 15, fontWeight: 500, color: CB.ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {it.pinned && <span style={{ color: CB.accent, marginRight: 4 }}>★</span>}{it.name}
                </span>
                <span style={{ fontSize: 11, color: it.unread ? CB.accent : CB.ink3, fontWeight: it.unread ? 600 : 400, whiteSpace: 'nowrap' }}>{it.time}</span>
              </div>
              {it.sub && (
                <div style={{ fontSize: 11, color: CB.ink3, marginTop: 2, display: 'flex', alignItems: 'center', gap: 6 }}>
                  {it.stage && <span style={{ color: it.stageColor, fontWeight: 500 }}>● {it.stage}</span>}
                  {it.stage && <span>·</span>}
                  <span>{it.sub.replace(/^\d+ 人 · [^·]+$/, m => m.split('·')[0].trim())}</span>
                </div>
              )}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                {it.mention && <span style={{ fontSize: 10, color: CB.accent, fontWeight: 600, padding: '1px 5px', borderRadius: 3, background: CB.accentBg }}>@我</span>}
                <span style={{ fontSize: 13, color: it.unread ? CB.ink2 : CB.ink3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, fontStyle: it.system ? 'italic' : 'normal', fontFamily: it.system ? CB.serif : CB.sans }}>
                  {it.last}
                </span>
                {it.unread > 0 && <span style={{ background: CB.accent, color: '#fff', fontSize: 10, fontWeight: 600, padding: '1px 6px', borderRadius: 999, minWidth: 16, textAlign: 'center' }}>{it.unread}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
      <TabBar active="msg"/>
    </div>
  );
}

function Avatar({ kind, name, system }) {
  if (kind === 'broadcast') return (
    <div style={{ width: 42, height: 42, borderRadius: 14, background: CB.ink, color: '#fff',
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
        <path d="M3 7v4M6 5v8M10 3v12M14 6v6" stroke="#fff" strokeWidth="1.6" strokeLinecap="round"/>
      </svg>
    </div>
  );
  if (kind === 'project') return (
    <div style={{ width: 42, height: 42, borderRadius: 14, background: CB.accentSoft, color: CB.accent,
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      fontFamily: CB.serif, fontSize: 16, fontWeight: 600, position: 'relative' }}>
      {name.charAt(0)}
      <span style={{ position: 'absolute', bottom: -2, right: -2, width: 18, height: 18, borderRadius: 9,
        background: CB.card, display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: `0 0 0 2px ${CB.card}` }}>
        <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
          <rect x="1.5" y="2" width="9" height="8" rx="1.5" stroke={CB.ink3} strokeWidth="1.2"/>
          <path d="M4 4.5h4M4 6.5h3" stroke={CB.ink3} strokeWidth="1.2" strokeLinecap="round"/>
        </svg>
      </span>
    </div>
  );
  return (
    <div style={{ width: 42, height: 42, borderRadius: 21, background: CB.blueSoft, color: CB.blue,
      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      fontFamily: CB.serif, fontSize: 15, fontWeight: 600 }}>{name.charAt(0)}</div>
  );
}

function TabBar({ active }) {
  const items = [['项目', 'p'], ['客户', 'c'], ['消息', 'msg'], ['我的', 'me']];
  return (
    <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0,
      background: 'rgba(247,245,242,0.92)', backdropFilter: 'blur(20px)',
      borderTop: `1px solid ${CB.divider}`,
      display: 'flex', justifyContent: 'space-around', padding: '10px 0 30px' }}>
      {items.map(([n, k]) => (
        <div key={k} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 22, height: 22, borderRadius: 4, background: active === k ? CB.ink : 'transparent',
            border: active === k ? 'none' : `1.4px solid ${CB.ink3}`, position: 'relative' }}>
            {k === 'msg' && <span style={{ position: 'absolute', top: -2, right: -2, width: 8, height: 8, borderRadius: 4, background: CB.accent, border: `1.5px solid ${CB.bg}` }}/>}
          </div>
          <span style={{ fontSize: 10, color: active === k ? CB.ink : CB.ink3, fontWeight: active === k ? 600 : 500 }}>{n}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Bubble variants ────────────────────────────────────────────────
// variant A: pure A-direction (no bubbles, indented blocks)
// variant B: WhatsApp-style two-tone bubbles in PMA palette
// variant C: hybrid — bubbles but warm + serif

function MsgBlock({ from, time, text, mine, stage, ref: refBlock, mention, variant = 'B', avatar }) {
  if (variant === 'A') {
    return (
      <div style={{ padding: '12px 24px', borderLeft: mine ? `2px solid ${CB.accent}` : 'none',
        marginLeft: mine ? 60 : 0, marginRight: mine ? 0 : 60, background: 'transparent' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: CB.ink3, fontWeight: 600 }}>{from}</span>
          <span style={{ fontSize: 10, color: CB.ink4, fontVariantNumeric: 'tabular-nums' }}>{time}</span>
        </div>
        <div style={{ fontFamily: CB.serif, fontSize: 15, color: CB.ink, lineHeight: 1.55 }}>{text}</div>
      </div>
    );
  }
  if (variant === 'C') {
    return (
      <div style={{ padding: '6px 16px', display: 'flex', justifyContent: mine ? 'flex-end' : 'flex-start', gap: 8 }}>
        {!mine && avatar && <div style={{ width: 30, height: 30, borderRadius: 15, background: CB.blueSoft, color: CB.blue,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: CB.serif, fontSize: 13, fontWeight: 600, flexShrink: 0, marginTop: 14 }}>{avatar}</div>}
        <div style={{ maxWidth: '76%' }}>
          {!mine && <div style={{ fontSize: 11, color: CB.ink3, marginBottom: 3, marginLeft: 4, fontWeight: 500 }}>{from}</div>}
          <div style={{
            background: mine ? CB.ink : CB.card, color: mine ? '#fff' : CB.ink,
            padding: '10px 14px', borderRadius: 16,
            borderTopLeftRadius: !mine ? 4 : 16, borderTopRightRadius: mine ? 4 : 16,
            fontFamily: CB.serif, fontSize: 15, lineHeight: 1.5,
            border: mine ? 'none' : `1px solid ${CB.divider}`,
          }}>{text}</div>
          <div style={{ fontSize: 10, color: CB.ink4, marginTop: 3, textAlign: mine ? 'right' : 'left', marginRight: 4, marginLeft: 4, fontVariantNumeric: 'tabular-nums' }}>{time}</div>
        </div>
      </div>
    );
  }
  // B — WhatsApp-style
  return (
    <div style={{ padding: '4px 12px', display: 'flex', justifyContent: mine ? 'flex-end' : 'flex-start' }}>
      <div style={{ maxWidth: '78%' }}>
        {!mine && <div style={{ fontSize: 11, color: CB.accent, marginBottom: 2, marginLeft: 12, fontWeight: 600 }}>{from}</div>}
        <div style={{
          background: mine ? '#E8E1D8' : CB.card, color: CB.ink,
          padding: '8px 12px', borderRadius: 12,
          borderTopLeftRadius: !mine ? 2 : 12, borderTopRightRadius: mine ? 2 : 12,
          fontSize: 14.5, lineHeight: 1.45,
          boxShadow: '0 1px 1px rgba(0,0,0,0.05)',
        }}>
          {text}
          <span style={{ fontSize: 10, color: CB.ink3, marginLeft: 8, fontVariantNumeric: 'tabular-nums' }}>{time}</span>
        </div>
      </div>
    </div>
  );
}

function StageBar({ from, to, by }) {
  return (
    <div style={{ padding: '14px 24px', display: 'flex', alignItems: 'center', gap: 14 }}>
      <div style={{ flex: 1, height: 1, background: CB.divider }}/>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: CB.ink2, fontWeight: 600 }}>
          <span>{from}</span>
          <svg width="14" height="8" viewBox="0 0 14 8"><path d="M1 4h11m-3-3l3 3-3 3" stroke={CB.accent} strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
          <span style={{ color: CB.accent }}>{to}</span>
        </div>
        <div style={{ fontSize: 10, color: CB.ink3, fontStyle: 'italic', fontFamily: CB.serif }}>由 {by} · 09:14</div>
      </div>
      <div style={{ flex: 1, height: 1, background: CB.divider }}/>
    </div>
  );
}

function EntityCard({ kind, name, meta, amount, stage, stageColor }) {
  return (
    <div style={{ background: CB.card, border: `1px solid ${CB.dividerStrong}`, borderRadius: 12,
      padding: '10px 12px', margin: '6px 0', maxWidth: 260, display: 'flex', gap: 10 }}>
      <div style={{ width: 32, height: 32, borderRadius: 8, background: CB.accentSoft, color: CB.accent,
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: 14, fontWeight: 600 }}>
        {kind === 'project' ? '⌗' : kind === 'customer' ? '⌂' : '§'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 10, color: CB.ink3, letterSpacing: 0.5, textTransform: 'uppercase', fontWeight: 600 }}>
          {kind === 'project' ? '项目' : kind === 'customer' ? '客户' : '合同'}
        </div>
        <div style={{ fontFamily: CB.serif, fontSize: 13, fontWeight: 500, color: CB.ink, marginTop: 1, lineHeight: 1.3 }}>{name}</div>
        <div style={{ display: 'flex', gap: 8, marginTop: 4, fontSize: 11, color: CB.ink3, alignItems: 'center' }}>
          {stage && <span style={{ color: stageColor, fontWeight: 500 }}>● {stage}</span>}
          {amount && <span style={{ color: CB.ink, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>¥{amount}万</span>}
        </div>
      </div>
    </div>
  );
}

// ─── Screen 2: Project group chat ──────────────────────────────────
function ProjectChat({ variant = 'B' }) {
  return (
    <div style={{ background: CB.bg, height: '100%', fontFamily: CB.sans, color: CB.ink, display: 'flex', flexDirection: 'column' }}>
      <StatusPad/>
      <ChatNav title="深圳半导体工厂扩产" sub="5 人 · 招标中"
        right={<svg width="20" height="20" viewBox="0 0 20 20"><circle cx="10" cy="4" r="1.5" fill={CB.ink2}/><circle cx="10" cy="10" r="1.5" fill={CB.ink2}/><circle cx="10" cy="16" r="1.5" fill={CB.ink2}/></svg>}/>

      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', gap: 2, paddingTop: 8, paddingBottom: 8 }}>
        <DayDivider label="今天"/>
        <MsgBlock variant={variant} avatar="陈" from="陈刚" time="09:08" text="客户那边方案我已经看过初稿,有几处需要调整,稍后发给大家。"/>
        <MsgBlock variant={variant} avatar="李" from="李明" time="09:10" text="@张伟 标书时间紧,这周五前必须出 V2"/>
        <StageBar from="嵌入" to="招标中" by="陈刚"/>
        <MsgBlock variant={variant} avatar="陈" from="陈刚" time="09:14" text={
          <>
            阶段已切换到招标中,关联文件请看
            <EntityCard kind="project" name="深圳半导体工厂扩产" stage="招标中" stageColor={CB.accent} amount="320.00"/>
          </>
        }/>
        <MsgBlock variant={variant} time="09:18" mine text="收到。客户那边我今晚约见一次,问下他们对工期的期望。"/>
      </div>

      <Composer/>
    </div>
  );
}

function DayDivider({ label }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '8px 0' }}>
      <span style={{ fontSize: 10, color: CB.ink3, padding: '4px 12px', borderRadius: 999,
        background: CB.card, border: `1px solid ${CB.divider}`, letterSpacing: 0.5, textTransform: 'uppercase', fontWeight: 600 }}>{label}</span>
    </div>
  );
}

function Composer({ mention, quoting }) {
  return (
    <div>
      {quoting && (
        <div style={{ padding: '10px 16px', background: CB.accentBg, borderTop: `1px solid ${CB.divider}`,
          display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 3, height: 28, background: CB.accent, borderRadius: 2 }}/>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 11, color: CB.accent, fontWeight: 600 }}>引用 · 项目</div>
            <div style={{ fontFamily: CB.serif, fontSize: 13, color: CB.ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>深圳半导体工厂扩产</div>
          </div>
          <span style={{ color: CB.ink3, fontSize: 16 }}>×</span>
        </div>
      )}
      <div style={{ padding: '8px 12px 24px', borderTop: `1px solid ${CB.divider}`, background: CB.bg,
        display: 'flex', alignItems: 'flex-end', gap: 8 }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: CB.card, border: `1px solid ${CB.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: CB.ink2, fontWeight: 300 }}>+</span>
        <div style={{ flex: 1, background: CB.card, borderRadius: 20, border: `1px solid ${CB.dividerStrong}`,
          padding: '9px 14px', fontFamily: CB.serif, fontSize: 14, color: CB.ink3, fontStyle: 'italic',
          display: 'flex', alignItems: 'center', gap: 8, minHeight: 36 }}>
          <span style={{ flex: 1 }}>{mention ? '@' : '说点什么…'}</span>
          <span style={{ fontSize: 11, color: CB.ink4, fontStyle: 'normal', fontFamily: CB.sans }}>@ # 🎤</span>
        </div>
      </div>
    </div>
  );
}

// ─── Screen 3: @ mention picker ────────────────────────────────────
function MentionState() {
  return (
    <div style={{ background: CB.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: CB.sans }}>
      <StatusPad/>
      <ChatNav title="深圳半导体工厂扩产" sub="5 人 · 招标中"/>
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative', paddingTop: 8 }}>
        <div style={{ opacity: 0.45 }}>
          <DayDivider label="今天"/>
          <MsgBlock variant="C" avatar="陈" from="陈刚" time="09:08" text="客户那边方案我已经看过初稿"/>
          <MsgBlock variant="C" avatar="李" from="李明" time="09:10" text="标书这周必须出 V2"/>
        </div>
        {/* mention popover above composer */}
        <div style={{ position: 'absolute', left: 12, right: 12, bottom: 10,
          background: CB.card, borderRadius: 14, border: `1px solid ${CB.divider}`,
          boxShadow: '0 8px 24px rgba(0,0,0,0.10)', overflow: 'hidden' }}>
          <div style={{ padding: '10px 14px 6px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: CB.ink3, letterSpacing: 1, textTransform: 'uppercase' }}>提及成员</div>
            <div style={{ fontSize: 11, color: CB.ink3 }}>5 人</div>
          </div>
          {[['张伟','项目负责人','张',true],['陈刚','商务','陈'],['李明','产品','李'],['王芳','现场','王']].map(([n,r,c,sel],i)=>(
            <div key={i} style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 10, background: sel ? CB.accentBg : 'transparent', borderTop: i === 0 ? `1px solid ${CB.divider}` : 'none' }}>
              <div style={{ width: 30, height: 30, borderRadius: 15, background: CB.accentSoft, color: CB.accent,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: CB.serif, fontSize: 13, fontWeight: 600 }}>{c}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: CB.serif, fontSize: 14, fontWeight: 500 }}>{n}</div>
                <div style={{ fontSize: 11, color: CB.ink3 }}>{r}</div>
              </div>
              {sel && <svg width="14" height="14" viewBox="0 0 14 14"><path d="M3 7l3 3 5-6" stroke={CB.accent} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" fill="none"/></svg>}
            </div>
          ))}
          <div style={{ padding: '10px 14px', borderTop: `1px solid ${CB.divider}`, background: CB.bg,
            display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: CB.ink3 }}>切换:</span>
            <span style={{ fontSize: 11, color: CB.accent, fontWeight: 600 }}>@ 成员</span>
            <span style={{ fontSize: 11, color: CB.ink3 }}>#项目</span>
            <span style={{ fontSize: 11, color: CB.ink3 }}>$客户</span>
            <span style={{ fontSize: 11, color: CB.ink3 }}>§合同</span>
          </div>
        </div>
      </div>
      <div style={{ padding: '8px 12px 24px', borderTop: `1px solid ${CB.divider}`, background: CB.bg,
        display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: CB.card, border: `1px solid ${CB.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: CB.ink2 }}>+</span>
        <div style={{ flex: 1, background: CB.card, borderRadius: 20, border: `1.5px solid ${CB.accent}`,
          padding: '9px 14px', fontFamily: CB.serif, fontSize: 15, color: CB.ink, display: 'flex', alignItems: 'center' }}>
          <span style={{ color: CB.accent, fontWeight: 600 }}>@张</span>
          <span style={{ display: 'inline-block', width: 2, height: 16, background: CB.accent, marginLeft: 1, animation: 'cb 1s infinite' }}/>
          <style>{`@keyframes cb{0%,49%{opacity:1}50%,100%{opacity:0}}`}</style>
        </div>
      </div>
    </div>
  );
}

// ─── Screen 4: Stage advance system "timeline bar" focus ───────────
function StageAdvance() {
  return (
    <div style={{ background: CB.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: CB.sans }}>
      <StatusPad/>
      <ChatNav title="深圳半导体工厂扩产" sub="5 人 · 招标中"/>
      <div style={{ flex: 1, overflow: 'hidden', paddingTop: 8 }}>
        <DayDivider label="今天"/>
        <MsgBlock variant="C" avatar="李" from="李明" time="09:10" text="标书这周必须出 V2"/>

        {/* Big timeline bar */}
        <div style={{ padding: '20px 24px' }}>
          <div style={{ background: CB.card, borderRadius: 16, border: `1px solid ${CB.divider}`,
            padding: '18px 18px 16px', position: 'relative' }}>
            <div style={{ position: 'absolute', top: -8, left: 18, padding: '2px 8px', background: CB.bg,
              fontSize: 10, color: CB.accent, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase' }}>阶段推进</div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginTop: 4 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: CB.ink3, fontWeight: 600, letterSpacing: 0.5, textTransform: 'uppercase' }}>从</div>
                <div style={{ fontFamily: CB.serif, fontSize: 17, fontWeight: 500, color: CB.ink2, marginTop: 2 }}>嵌入</div>
              </div>
              <svg width="32" height="22" viewBox="0 0 32 22"><path d="M2 11h26m-6-6l6 6-6 6" stroke={CB.accent} strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
              <div style={{ flex: 1, textAlign: 'right' }}>
                <div style={{ fontSize: 11, color: CB.accent, fontWeight: 600, letterSpacing: 0.5, textTransform: 'uppercase' }}>到</div>
                <div style={{ fontFamily: CB.serif, fontSize: 17, fontWeight: 500, color: CB.ink, marginTop: 2 }}>招标中</div>
              </div>
            </div>

            <div style={{ height: 1, background: CB.divider, margin: '14px 0' }}/>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 24, height: 24, borderRadius: 12, background: CB.accentSoft, color: CB.accent,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: CB.serif, fontSize: 11, fontWeight: 600 }}>陈</div>
              <div style={{ flex: 1, fontSize: 12, color: CB.ink2 }}>
                <span style={{ fontWeight: 500 }}>陈刚</span>
                <span style={{ color: CB.ink3, fontStyle: 'italic', fontFamily: CB.serif }}> 推进了阶段</span>
              </div>
              <div style={{ fontSize: 10, color: CB.ink3, fontVariantNumeric: 'tabular-nums' }}>09:14</div>
            </div>

            <div style={{ marginTop: 12, padding: '10px 12px', background: CB.bg, borderRadius: 10,
              fontFamily: CB.serif, fontSize: 13, color: CB.ink2, fontStyle: 'italic', lineHeight: 1.5 }}>
              「客户已经发出了正式招标邀请,标书提交截止 5月15日。」
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
              <div style={{ flex: 1, padding: '8px', borderRadius: 10, border: `1px solid ${CB.dividerStrong}`,
                fontSize: 12, color: CB.ink2, textAlign: 'center', fontWeight: 500 }}>查看项目</div>
              <div style={{ flex: 1, padding: '8px', borderRadius: 10, background: CB.ink, color: '#fff',
                fontSize: 12, textAlign: 'center', fontWeight: 600 }}>讨论</div>
            </div>
          </div>
        </div>

        <MsgBlock variant="C" mine time="09:18" text="收到,我今晚约客户。"/>
      </div>
      <Composer/>
    </div>
  );
}

// ─── Screen 5: 1:1 DM ──────────────────────────────────────────────
function DMChat() {
  return (
    <div style={{ background: CB.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: CB.sans }}>
      <StatusPad/>
      <ChatNav title="李明" sub="产品经理 · 在线"/>
      <div style={{ flex: 1, overflow: 'hidden', paddingTop: 8 }}>
        <DayDivider label="昨天"/>
        <MsgBlock variant="C" avatar="李" from="李明" time="17:42" text="深圳那个项目方案 PDF 你有吗?"/>
        <MsgBlock variant="C" mine time="17:45" text="有,我现在发给你。"/>
        {/* file card */}
        <div style={{ padding: '4px 16px', display: 'flex', justifyContent: 'flex-end' }}>
          <div style={{ background: CB.ink, color: '#fff', padding: '10px 12px', borderRadius: 16, borderTopRightRadius: 4,
            display: 'flex', gap: 10, alignItems: 'center', maxWidth: 260 }}>
            <div style={{ width: 36, height: 44, background: 'rgba(255,255,255,0.12)', borderRadius: 6,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, fontWeight: 600, letterSpacing: 0.5 }}>PDF</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontFamily: CB.serif, fontSize: 13, lineHeight: 1.3 }}>深圳半导体方案 V3.pdf</div>
              <div style={{ fontSize: 10, opacity: 0.6, marginTop: 2 }}>2.4 MB · 12 页</div>
            </div>
          </div>
        </div>
        <div style={{ padding: '0 16px 4px', display: 'flex', justifyContent: 'flex-end' }}>
          <span style={{ fontSize: 10, color: CB.ink4 }}>17:45 · ✓✓ 已读</span>
        </div>
        <DayDivider label="今天"/>
        <MsgBlock variant="C" avatar="李" from="李明" time="09:02" text="收到了,谢谢!客户那边什么时候反馈?"/>
        {/* voice msg */}
        <div style={{ padding: '4px 16px', display: 'flex', justifyContent: 'flex-start', gap: 8 }}>
          <div style={{ width: 30, height: 30, borderRadius: 15, background: CB.blueSoft, color: CB.blue,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: CB.serif, fontSize: 13, fontWeight: 600, marginTop: 14 }}>李</div>
          <div>
            <div style={{ fontSize: 11, color: CB.ink3, marginBottom: 3, marginLeft: 4 }}>李明</div>
            <div style={{ background: CB.card, padding: '10px 14px', borderRadius: 16, borderTopLeftRadius: 4,
              border: `1px solid ${CB.divider}`, display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ width: 26, height: 26, borderRadius: 13, background: CB.accent, color: '#fff',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 10 }}>▶</span>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 20 }}>
                {[6,11,8,15,12,18,9,14,7,11,5,9,12,8].map((h,i)=>(<div key={i} style={{width:2,height:h,background:CB.ink2,borderRadius:1}}/>))}
              </div>
              <span style={{ fontSize: 11, color: CB.ink3, fontVariantNumeric: 'tabular-nums' }}>00:08</span>
            </div>
            <div style={{ fontSize: 10, color: CB.ink4, marginTop: 3, marginLeft: 4, fontVariantNumeric: 'tabular-nums' }}>09:03</div>
          </div>
        </div>
      </div>
      <Composer/>
    </div>
  );
}

// ─── Screen 6: Chat settings ───────────────────────────────────────
function ChatSettings() {
  return (
    <div style={{ background: CB.bg, height: '100%', fontFamily: CB.sans, paddingTop: 54, overflow: 'auto', paddingBottom: 40 }}>
      <ChatNav title="聊天设置"/>
      <div style={{ padding: '24px 24px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
        <div style={{ width: 64, height: 64, borderRadius: 18, background: CB.accentSoft, color: CB.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: CB.serif, fontSize: 28, fontWeight: 500 }}>深</div>
        <div style={{ fontFamily: CB.serif, fontSize: 19, fontWeight: 500, textAlign: 'center', lineHeight: 1.3 }}>深圳半导体工厂扩产</div>
        <div style={{ fontSize: 12, color: CB.ink3 }}>5 人 · 创建于 2026-04-20</div>
      </div>

      {/* linked entity */}
      <div style={{ padding: '0 24px 18px' }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: CB.ink3, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 8 }}>关联</div>
        <EntityCard kind="project" name="深圳半导体工厂扩产" stage="招标中" stageColor={CB.accent} amount="320.00"/>
      </div>

      {/* announcement */}
      <div style={{ padding: '0 24px 18px' }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: CB.ink3, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 8 }}>公告</div>
        <div style={{ background: CB.card, border: `1px solid ${CB.divider}`, borderRadius: 14, padding: '14px 16px',
          fontFamily: CB.serif, fontSize: 14, color: CB.ink2, lineHeight: 1.55, fontStyle: 'italic' }}>
          标书提交截止 5/15。每周一例会 9:00,陈刚主持。
        </div>
      </div>

      {/* members */}
      <div style={{ padding: '0 24px 18px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: CB.ink3, letterSpacing: 1, textTransform: 'uppercase' }}>成员 · 5</div>
          <span style={{ fontSize: 12, color: CB.accent, fontWeight: 500 }}>+ 添加</span>
        </div>
        <div style={{ background: CB.card, borderRadius: 14, border: `1px solid ${CB.divider}` }}>
          {[['张伟','项目负责人','负责'],['陈刚','商务','管理'],['李明','产品',''],['王芳','现场',''],['刘洋','技术','']].map(([n,r,t],i,a)=>(
            <div key={i} style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12,
              borderBottom: i === a.length-1 ? 'none' : `1px solid ${CB.divider}` }}>
              <div style={{ width: 32, height: 32, borderRadius: 16, background: CB.accentSoft, color: CB.accent,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: CB.serif, fontSize: 13, fontWeight: 600 }}>{n.charAt(0)}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: CB.serif, fontSize: 14, fontWeight: 500 }}>{n}</div>
                <div style={{ fontSize: 11, color: CB.ink3 }}>{r}</div>
              </div>
              {t && <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 4, background: CB.bg,
                color: CB.ink3, fontWeight: 600, letterSpacing: 0.4 }}>{t}</span>}
            </div>
          ))}
        </div>
      </div>

      {/* options */}
      <div style={{ padding: '0 24px 24px' }}>
        <div style={{ background: CB.card, borderRadius: 14, border: `1px solid ${CB.divider}` }}>
          {[['消息免打扰','关'],['置顶聊天','开'],['查找消息','']].map(([l,v],i,a)=>(
            <div key={i} style={{ padding: '14px 16px', display: 'flex', justifyContent: 'space-between',
              borderBottom: i === a.length-1 ? 'none' : `1px solid ${CB.divider}`, fontSize: 14 }}>
              <span style={{ color: CB.ink2 }}>{l}</span>
              <span style={{ color: CB.ink3, fontSize: 13 }}>{v} ›</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 14, padding: '14px', background: CB.card, borderRadius: 14, border: `1px solid ${CB.divider}`,
          textAlign: 'center', color: '#A04848', fontSize: 14, fontWeight: 500 }}>退出群聊</div>
      </div>
    </div>
  );
}

// ─── Variants showcase ─────────────────────────────────────────────
function ChatVariantA() {
  return (
    <div style={{ background: CB.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: CB.sans }}>
      <StatusPad/>
      <ChatNav title="深圳半导体工厂扩产" sub="A · 无气泡报刊体"/>
      <div style={{ flex: 1, overflow: 'hidden', paddingTop: 4 }}>
        <DayDivider label="今天"/>
        <MsgBlock variant="A" from="陈刚" time="09:08" text="客户那边方案我已经看过初稿。"/>
        <MsgBlock variant="A" from="李明" time="09:10" text="标书时间紧,这周必须出 V2。"/>
        <StageBar from="嵌入" to="招标中" by="陈刚"/>
        <MsgBlock variant="A" mine time="09:18" text="收到,今晚约客户。"/>
      </div>
      <Composer/>
    </div>
  );
}
function ChatVariantB() { return <ProjectChat variant="B"/>; }
function ChatVariantC() { return <ProjectChat variant="C"/>; }

// ─── 跨库消息提示卡(方案甲) ────────────────────────────────────
const CR_AMBER = { bg: '#FBF1DF', bgStrong: '#F6E4BE', ink: '#6E4814', accent: '#B8762A' };

function CrossRegionInChat({ region, count, projects, mentions }) {
  return (
    <div style={{
      margin: '4px 16px 10px',
      background: CR_AMBER.bg,
      border: `1px solid ${CR_AMBER.bgStrong}`,
      borderRadius: 12,
      padding: '11px 13px',
      display: 'flex', alignItems: 'center', gap: 12,
      fontFamily: CB.sans,
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 10,
        background: CB.card, border: `1px solid ${CR_AMBER.bgStrong}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 19, flexShrink: 0,
      }}>{region.flag}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
          <span style={{ fontSize: 13.5, fontWeight: 600, color: CR_AMBER.ink }}>{region.name}库</span>
          <span style={{ fontSize: 13, color: CR_AMBER.ink, fontWeight: 500 }}>· {count} 条新消息</span>
        </div>
        <div style={{ fontSize: 11.5, color: CR_AMBER.accent, marginTop: 2, fontWeight: 500 }}>
          {projects} 个项目群
          {mentions > 0 && <> · <span style={{ fontWeight: 700 }}>@ 你 {mentions} 次</span></>}
        </div>
      </div>
      <span style={{ fontSize: 12.5, color: CR_AMBER.accent, fontWeight: 600, flexShrink: 0 }}>
        切去看 ›
      </span>
    </div>
  );
}

// ─── 顶部全局琥珀条(他库内) ───────────────────────────────────
function CrossRegionTopBar({ region }) {
  return (
    <div style={{
      background: CR_AMBER.bg,
      borderBottom: `1px solid ${CR_AMBER.bgStrong}`,
      padding: '8px 16px',
      display: 'flex', alignItems: 'center', gap: 8,
      fontFamily: CB.sans,
    }}>
      <span style={{ fontSize: 13 }}>{region.flag}</span>
      <span style={{ fontSize: 12.5, color: CR_AMBER.ink, fontWeight: 500 }}>
        正在浏览 · <strong style={{ fontWeight: 700 }}>{region.name}库</strong>
      </span>
      <span style={{ marginLeft: 'auto', fontSize: 12, color: CR_AMBER.accent, fontWeight: 600 }}>
        切回 ›
      </span>
    </div>
  );
}

// ─── 多库 · 在中国库的会话列表(顶部多了一张跨库卡) ────────────
function ConvListWithCrossRegion() {
  const items = [
    { kind: 'broadcast', name: '公司广播', last: 'Q2 全员目标已发布', time: '09:21', unread: 0, pinned: true },
    { kind: 'project', name: '深圳半导体工厂扩产', sub: '5 人', last: '陈刚:周三现场勘查没问题', time: '09:18', unread: 3, stage: '招标中', stageColor: CB.accent },
    { kind: 'project', name: '上海某制造厂节能改造', sub: '4 人', last: '系统:阶段已推进至嵌入', time: '昨天', unread: 0, stage: '嵌入', stageColor: CB.ink3, system: true },
    { kind: 'dm', name: '李明', sub: '产品经理', last: '记得把方案 PDF 发我', time: '昨天', unread: 1 },
    { kind: 'project', name: '杭州光伏电站二期', sub: '6 人', last: '王芳:@张伟 标书需补章程', time: '周二', unread: 0, stage: '招标中', stageColor: CB.accent, mention: true },
  ];
  return (
    <div style={{ background: CB.bg, height: '100%', fontFamily: CB.sans, color: CB.ink, paddingTop: 54 }}>
      <div style={{ padding: '14px 24px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 11, color: CB.ink3, fontWeight: 500, letterSpacing: 1.2, textTransform: 'uppercase' }}>2026 · 5月</div>
          <h1 style={{ fontFamily: CB.serif, fontSize: 32, fontWeight: 500, margin: '4px 0 0', letterSpacing: -0.4 }}>消息</h1>
        </div>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: CB.ink, color: '#fff',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 300 }}>+</span>
      </div>

      {/* 跨库提示卡 — 顶部 */}
      <CrossRegionInChat region={{ flag: '🇸🇬', name: '新加坡' }} count={5} projects={2} mentions={1}/>

      <div style={{ padding: '0 24px 12px', display: 'flex', gap: 8 }}>
        {['全部', '未读 4', '@我', '项目'].map((t, i) => (
          <span key={i} style={{ padding: '5px 12px', borderRadius: 999, fontSize: 12, fontWeight: 500,
            background: i === 0 ? CB.ink : 'transparent', color: i === 0 ? '#fff' : CB.ink2,
            border: i === 0 ? 'none' : `1px solid ${CB.dividerStrong}` }}>{t}</span>
        ))}
      </div>
      <div style={{ background: CB.card }}>
        {items.map((it, i) => (
          <div key={i} style={{ padding: '14px 20px', display: 'flex', gap: 12, borderBottom: i === items.length - 1 ? 'none' : `1px solid ${CB.divider}`, alignItems: 'flex-start' }}>
            <Avatar kind={it.kind} name={it.name} system={it.system}/>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontFamily: CB.serif, fontSize: 15, fontWeight: 500, color: CB.ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {it.pinned && <span style={{ color: CB.accent, marginRight: 4 }}>★</span>}{it.name}
                </span>
                <span style={{ fontSize: 11, color: it.unread ? CB.accent : CB.ink3, fontWeight: it.unread ? 600 : 400, whiteSpace: 'nowrap' }}>{it.time}</span>
              </div>
              {it.sub && (
                <div style={{ fontSize: 11, color: CB.ink3, marginTop: 2, display: 'flex', alignItems: 'center', gap: 6 }}>
                  {it.stage && <span style={{ color: it.stageColor, fontWeight: 500 }}>● {it.stage}</span>}
                  {it.stage && <span>·</span>}
                  <span>{it.sub}</span>
                </div>
              )}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                {it.mention && <span style={{ fontSize: 10, color: CB.accent, fontWeight: 600, padding: '1px 5px', borderRadius: 3, background: CB.accentBg }}>@我</span>}
                <span style={{ fontSize: 13, color: it.unread ? CB.ink2 : CB.ink3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1, fontStyle: it.system ? 'italic' : 'normal', fontFamily: it.system ? CB.serif : CB.sans }}>
                  {it.last}
                </span>
                {it.unread > 0 && <span style={{ background: CB.accent, color: '#fff', fontSize: 10, fontWeight: 600, padding: '1px 6px', borderRadius: 999, minWidth: 16, textAlign: 'center' }}>{it.unread}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
      <TabBar active="msg"/>
    </div>
  );
}

// ─── 在他库(SG)的会话列表 — 顶部琥珀条 + 反向跨库卡指回中国库 ──
function ConvListAway() {
  const items = [
    { kind: 'broadcast', name: 'Company Broadcast', last: 'Q2 OPS update — Singapore', time: '09:42', unread: 0, pinned: true },
    { kind: 'project', name: 'KL Subcontract · Semi-Wafer', sub: '6 ppl', last: 'Aisyah: client drawings reviewed.', time: '09:35', unread: 4, stage: 'Bidding', stageColor: CB.accent, mention: true },
    { kind: 'project', name: 'Tuas Substation Phase II', sub: '5 ppl', last: 'Rizal: water cut, restart by 14:00.', time: 'Yesterday', unread: 1, stage: 'On-site', stageColor: CB.ink3 },
    { kind: 'dm', name: 'Aisyah Lim', sub: 'KL Lead', last: 'Could you send me the spec?', time: 'Mon', unread: 0 },
  ];
  return (
    <div style={{ background: CB.bg, height: '100%', fontFamily: CB.sans, color: CB.ink, paddingTop: 54 }}>
      {/* 顶部全局琥珀条 — 他库内常驻 */}
      <CrossRegionTopBar region={{ flag: '🇸🇬', name: '新加坡' }}/>

      <div style={{ padding: '14px 24px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 11, color: CB.ink3, fontWeight: 500, letterSpacing: 1.2, textTransform: 'uppercase' }}>2026 · May</div>
          <h1 style={{ fontFamily: CB.serif, fontSize: 32, fontWeight: 500, margin: '4px 0 0', letterSpacing: -0.4 }}>Messages</h1>
        </div>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: CB.ink, color: '#fff',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 20, fontWeight: 300 }}>+</span>
      </div>

      {/* 反向跨库卡 — 指回中国库 */}
      <CrossRegionInChat region={{ flag: '🇨🇳', name: '中国' }} count={12} projects={4} mentions={2}/>

      <div style={{ padding: '0 24px 12px', display: 'flex', gap: 8 }}>
        {['All', 'Unread 5', '@me', 'Projects'].map((t, i) => (
          <span key={i} style={{ padding: '5px 12px', borderRadius: 999, fontSize: 12, fontWeight: 500,
            background: i === 0 ? CB.ink : 'transparent', color: i === 0 ? '#fff' : CB.ink2,
            border: i === 0 ? 'none' : `1px solid ${CB.dividerStrong}` }}>{t}</span>
        ))}
      </div>
      <div style={{ background: CB.card }}>
        {items.map((it, i) => (
          <div key={i} style={{ padding: '14px 20px', display: 'flex', gap: 12, borderBottom: i === items.length - 1 ? 'none' : `1px solid ${CB.divider}`, alignItems: 'flex-start' }}>
            <Avatar kind={it.kind} name={it.name}/>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontFamily: CB.serif, fontSize: 15, fontWeight: 500, color: CB.ink, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {it.pinned && <span style={{ color: CB.accent, marginRight: 4 }}>★</span>}{it.name}
                </span>
                <span style={{ fontSize: 11, color: it.unread ? CB.accent : CB.ink3, fontWeight: it.unread ? 600 : 400, whiteSpace: 'nowrap' }}>{it.time}</span>
              </div>
              {it.sub && (
                <div style={{ fontSize: 11, color: CB.ink3, marginTop: 2, display: 'flex', alignItems: 'center', gap: 6 }}>
                  {it.stage && <span style={{ color: it.stageColor, fontWeight: 500 }}>● {it.stage}</span>}
                  {it.stage && <span>·</span>}
                  <span>{it.sub}</span>
                </div>
              )}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
                {it.mention && <span style={{ fontSize: 10, color: CB.accent, fontWeight: 600, padding: '1px 5px', borderRadius: 3, background: CB.accentBg }}>@me</span>}
                <span style={{ fontSize: 13, color: it.unread ? CB.ink2 : CB.ink3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
                  {it.last}
                </span>
                {it.unread > 0 && <span style={{ background: CB.accent, color: '#fff', fontSize: 10, fontWeight: 600, padding: '1px 6px', borderRadius: 999, minWidth: 16, textAlign: 'center' }}>{it.unread}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
      <TabBar active="msg"/>
    </div>
  );
}

Object.assign(window, { ConvList, ProjectChat, MentionState, StageAdvance, DMChat, ChatSettings,
  ChatVariantA, ChatVariantB, ChatVariantC,
  ConvListWithCrossRegion, ConvListAway, CrossRegionInChat, CrossRegionTopBar });
