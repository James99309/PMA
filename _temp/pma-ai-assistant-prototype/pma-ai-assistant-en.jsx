// PMA · Assistant (EN) · content-interaction extension
// 12 screens · 1:1 EN mirror of pma-ai-assistant.jsx · localised for SG · standalone

const AIX = {
  bg: '#F7F5F2', card: '#FFFFFF',
  ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#C2BBB3',
  divider: 'rgba(0,0,0,0.06)', dividerStrong: 'rgba(0,0,0,0.10)',
  accent: '#D97757', accentSoft: '#F4E4D8', accentBg: 'rgba(217,119,87,0.08)',
  ai: '#2F66D6', aiSoft: '#E5EEFB', aiBg: 'rgba(47,102,214,0.06)', aiInk: '#1E4FAA',
  wiki: '#1F8478', wikiSoft: '#DEEFEB',
  train: '#7B5BAC', trainSoft: '#EEE6F5',
  cmd: '#2F66D6', cmdSoft: '#E5EEFB',
  data: '#1E4FAA', dataSoft: '#E5EEFB',
  green: '#2F7A45', greenSoft: '#E9F1EB', warn: '#C77B22',
  serif: '"Tiempos Headline","Source Serif Pro",Georgia,serif',
  sans: '-apple-system,"SF Pro Text",system-ui,sans-serif',
  mono: 'ui-monospace,"SF Mono","JetBrains Mono",monospace',
};

const AIX_PIXEL_P = [
  { r: 0, c: 1 }, { r: 0, c: 2 }, { r: 0, c: 3 }, { r: 0, c: 4 },
  { r: 1, c: 1 }, { r: 1, c: 4 },
  { r: 2, c: 1 }, { r: 2, c: 5, d: true },
  { r: 3, c: 1 }, { r: 3, c: 2 }, { r: 3, c: 3 }, { r: 3, c: 4 },
  { r: 4, c: 1 }, { r: 4, c: 2, d: true },
  { r: 5, c: 1 }, { r: 5, c: 2, d: true },
];
function AIXLogo({ size = 26 }) {
  const cell = size / 6.6, gap = cell * 0.16;
  const tot = cell * 6 + gap * 5;
  return (
    <div style={{ width: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
      <div style={{ width: tot, height: tot, position: 'relative' }}>
        {AIX_PIXEL_P.map(p => (
          <div key={`${p.r}-${p.c}`} style={{ position: 'absolute', left: p.c * (cell + gap), top: p.r * (cell + gap),
            width: cell, height: cell, background: p.d ? AIX.aiInk : AIX.ai, borderRadius: cell * 0.18 }}/>
        ))}
      </div>
    </div>
  );
}

function AIXNav({ title = 'PMA Assistant', sub = '● Online · Connected to all PMA data + knowledge base' }) {
  return (
    <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10,
      borderBottom: `1px solid ${AIX.divider}`, background: AIX.card }}>
      <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={AIX.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
      <AIXLogo size={26}/>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontFamily: AIX.serif, fontSize: 15, fontWeight: 600 }}>{title}</span>
          <span style={{ fontSize: 9, fontWeight: 700, color: AIX.ai, padding: '1px 5px', borderRadius: 3, background: AIX.aiSoft }}>BETA</span>
        </div>
        <div style={{ fontSize: 10.5, color: AIX.green, marginTop: 1 }}>{sub}</div>
      </div>
      <span style={{ fontSize: 18, color: AIX.ink3 }}>···</span>
    </div>
  );
}

const AIX_KIND = {
  data:  { label: 'Data',     color: AIX.data,  bg: AIX.dataSoft,  icon: '◧' },
  wiki:  { label: 'Wiki',     color: AIX.wiki,  bg: AIX.wikiSoft,  icon: '❝' },
  cmd:   { label: 'Command',  color: AIX.cmd,   bg: AIX.cmdSoft,   icon: '⌘' },
  train: { label: 'Training', color: AIX.train, bg: AIX.trainSoft, icon: '◷' },
};
function AIXBadge({ kind, note }) {
  const k = AIX_KIND[kind] || AIX_KIND.data;
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '2px 8px 2px 6px',
      borderRadius: 999, background: k.bg, marginBottom: 6 }}>
      <span style={{ fontSize: 11, color: k.color }}>{k.icon}</span>
      <span style={{ fontSize: 10.5, fontWeight: 700, color: k.color, letterSpacing: 0.3 }}>{k.label}</span>
      {note && <span style={{ fontSize: 10, color: k.color, opacity: 0.75 }}>· {note}</span>}
    </div>
  );
}

function AIXUser({ time, text }) {
  return (
    <div style={{ padding: '6px 16px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
      <div style={{ background: AIX.ink, color: '#fff', borderRadius: '14px 14px 4px 14px',
        padding: '10px 14px', maxWidth: 300, fontFamily: AIX.serif, fontSize: 14, lineHeight: 1.5 }}>{text}</div>
      {time && <div style={{ fontSize: 10, color: AIX.ink3, marginTop: 4 }}>{time}</div>}
    </div>
  );
}

function AIXAnswer({ kind, note, time, children, actions = true, compact }) {
  return (
    <div style={{ padding: '6px 16px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
      <AIXLogo size={22}/>
      <div style={{ flex: 1, minWidth: 0 }}>
        {!compact && <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 4 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: AIX.aiInk }}>PMA Assistant</span>
          {time && <span style={{ fontSize: 10, color: AIX.ink3 }}>{time}</span>}
        </div>}
        <div style={{ background: AIX.aiBg, border: '1px solid rgba(47,102,214,0.18)', borderRadius: '4px 14px 14px 14px',
          padding: '12px 14px', fontFamily: AIX.serif, fontSize: 14, lineHeight: 1.55, color: AIX.ink }}>
          {kind && <AIXBadge kind={kind} note={note}/>}
          {children}
        </div>
        {actions && !compact && (
          <div style={{ display: 'flex', gap: 14, marginTop: 6, fontSize: 11, color: AIX.ink3 }}>
            <span>↻ Regenerate</span><span>⧉ Copy</span><span>👍</span><span>👎</span>
          </div>
        )}
      </div>
    </div>
  );
}

function AIXSuggest({ tags }) {
  return (
    <div style={{ padding: '6px 16px 6px 54px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
      {tags.map((t, i) => (
        <span key={i} style={{ fontSize: 12, padding: '6px 12px', borderRadius: 999,
          border: `1px solid ${AIX.dividerStrong}`, background: AIX.card, color: AIX.ink2,
          fontFamily: AIX.serif, fontStyle: 'italic' }}>{t}</span>
      ))}
    </div>
  );
}

function AIXEntityCard({ tag, name, metaA, metaB, metaC }) {
  return (
    <div style={{ marginTop: 8, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`,
      borderRadius: 10, padding: '11px 12px', display: 'flex', gap: 10, alignItems: 'center' }}>
      <div style={{ width: 30, height: 30, borderRadius: 8, background: '#1A1A1A', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700 }}>{tag}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: AIX.serif, fontSize: 13, fontWeight: 600, lineHeight: 1.3 }}>{name}</div>
        <div style={{ display: 'flex', gap: 8, marginTop: 3, fontSize: 11, color: AIX.ink3, flexWrap: 'wrap' }}>
          {metaA && <span style={{ color: AIX.accent, fontWeight: 600 }}>{metaA}</span>}
          {metaB && <><span>·</span><span>{metaB}</span></>}
          {metaC && <><span>·</span><span style={{ color: AIX.ink, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{metaC}</span></>}
        </div>
      </div>
      <span style={{ color: AIX.ink3, fontSize: 14 }}>›</span>
    </div>
  );
}

function AIXSource({ children }) {
  return <div style={{ fontSize: 11, color: AIX.ink3, marginTop: 10, fontStyle: 'italic', fontFamily: AIX.serif }}>{children}</div>;
}

function AIXComposer({ value, ph = 'Ask me anything · or pick one to start', hints = ['@AI', '#', '/'], panel }) {
  return (
    <div style={{ borderTop: `1px solid ${AIX.divider}`, background: AIX.card }}>
      {panel}
      <div style={{ padding: '8px 12px 6px', display: 'flex', gap: 6, overflowX: 'auto' }}>
        {['/win-rate', '/bidding projects', '/quarter signings', '/how to quote', '/onboarding'].map(t => (
          <span key={t} style={{ flexShrink: 0, fontSize: 11, color: AIX.ai, padding: '5px 10px',
            borderRadius: 999, background: AIX.aiSoft, fontFamily: AIX.mono }}>{t}</span>
        ))}
      </div>
      <div style={{ padding: '4px 12px 24px', display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: AIX.bg, border: `1px solid ${AIX.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: AIX.ink2 }}>+</span>
        <div style={{ flex: 1, background: AIX.bg, borderRadius: 20, border: `1.5px solid ${value ? AIX.ai : AIX.dividerStrong}`,
          padding: '9px 14px', fontFamily: AIX.serif, fontSize: 14,
          color: value ? AIX.ink : AIX.ink3, fontStyle: value ? 'normal' : 'italic',
          display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ flex: 1 }}>
            {value || ph}
            {value && <span style={{ display: 'inline-block', width: 2, height: 16, background: AIX.ai, marginLeft: 1, animation: 'aixBlink 1s infinite' }}/>}
          </span>
          {!value && hints.map(h => (
            <span key={h} style={{ fontSize: 11, color: h === '@AI' ? AIX.ai : AIX.ink4,
              fontWeight: h === '@AI' ? 700 : 500, fontStyle: 'normal', fontFamily: AIX.mono }}>{h}</span>
          ))}
        </div>
        <button style={{ width: 36, height: 36, borderRadius: 18, background: value ? AIX.ai : AIX.ink4, color: '#fff',
          border: 'none', fontSize: 14, fontWeight: 700 }}>↑</button>
      </div>
      <style>{`@keyframes aixBlink{0%,49%{opacity:1}50%,100%{opacity:0}}@keyframes aixDot{0%,80%,100%{opacity:.3}40%{opacity:1}}`}</style>
    </div>
  );
}

function AIXCmdPanel({ focus }) {
  const groups = [
    { id: 'data',  k: 'data',  title: 'Data query',       items: ['/win-rate', '/bidding projects', '/quarter signings', '/this-month expenses', '/find contact'] },
    { id: 'wiki',  k: 'wiki',  title: 'Wiki Q&A',          items: ['/export FX rate', '/approval flow', '/product specs'] },
    { id: 'train', k: 'train', title: 'Training',          items: ['/onboarding', '/how to quote', '/CRM entry rules'] },
    { id: 'draft', k: 'cmd',   title: 'Draft · Summarise', items: ['/draft client reply', '/weekly report', '/summarise group'] },
  ];
  return (
    <div style={{ padding: '12px 14px 4px', borderBottom: `1px solid ${AIX.divider}` }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: AIX.ink2, letterSpacing: 0.3 }}>Pick one to start · tap = fill an editable intent</span>
        <span style={{ fontSize: 11, color: AIX.ink3 }}>collapse ⌄</span>
      </div>
      {groups.map(g => {
        const kk = AIX_KIND[g.k];
        return (
          <div key={g.id} style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
              <span style={{ fontSize: 10, color: kk.color }}>{kk.icon}</span>
              <span style={{ fontSize: 10.5, fontWeight: 700, color: kk.color, letterSpacing: 0.6, textTransform: 'uppercase' }}>{g.title}</span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {g.items.map(it => {
                const hot = focus === it;
                return (
                  <span key={it} style={{ fontSize: 12, padding: '6px 11px', borderRadius: 999,
                    fontFamily: AIX.mono, color: hot ? '#fff' : kk.color,
                    background: hot ? kk.color : kk.bg,
                    border: hot ? 'none' : `1px solid ${kk.color}22` }}>{it}</span>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ═══ 1) Command-panel entry ═══════════════════════════════════════
function AIXEntryEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '18px 0' }}>
        <div style={{ padding: '0 24px' }}>
          <AIXLogo size={40}/>
          <div style={{ fontFamily: AIX.serif, fontSize: 20, fontWeight: 500, marginTop: 14, lineHeight: 1.32 }}>
            Ask me anything — I'll decide whether to<br/>query data, search the KB, or teach you.
          </div>
          <div style={{ fontSize: 12, color: AIX.ink3, marginTop: 8, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.6 }}>
            Type directly, or tap one below — no need to pick a mode first. Every answer is labelled with its source.
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, padding: '18px 24px 0', flexWrap: 'wrap' }}>
          {[['◧','Data','Customers / projects / quotes / expenses — live'],['❝','Wiki','Process / policy / specs — ask the KB'],
            ['⌘','Command','Draft / summarise / export in one line'],['◷','Training','Onboarding · learn by doing']].map((x,i)=>(
            <div key={i} style={{ width: 'calc(50% - 4px)', background: AIX.card, border: `1px solid ${AIX.divider}`,
              borderRadius: 12, padding: '11px 12px' }}>
              <div style={{ fontSize: 14, color: AIX.ai }}>{x[0]} <span style={{ fontSize: 12, fontWeight: 700, color: AIX.ink }}>{x[1]}</span></div>
              <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 4, lineHeight: 1.45 }}>{x[2]}</div>
            </div>
          ))}
        </div>
      </div>
      <AIXComposer panel={<AIXCmdPanel/>}/>
    </div>
  );
}

// ═══ 2) Data query · entity card ══════════════════════════════════
function AIXDataEntityEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="14:21" text="How's the win rate for Baoshan Energy? Any projects worth chasing?"/>
        <AIXAnswer kind="data" note="Customer · live" time="14:21">
          <div><b>Shanghai Baoshan Energy Tech</b> overall win rate <b style={{ color: AIX.green }}>~72%</b> — returning client, high contact trust, 3 active. Top to chase:</div>
          <AIXEntityCard tag="#" name="Baoshan Energy Retrofit" metaA="● Bidding" metaB="Owner You" metaC="¥425K"/>
          <AIXEntityCard tag="#" name="Baoshan Phase-2 Efficiency Audit" metaA="● Proposal" metaB="Li Hua" metaC="¥180K"/>
          <AIXSource>Source: 6 owned projects · 12 follow-ups · last visit May 22 · tap a card for detail</AIXSource>
        </AIXAnswer>
        <AIXSuggest tags={['What’s the next step here?', 'Draft a meeting request', 'Compare with other clients']}/>
      </div>
      <AIXComposer value="Draft a meeting-request message"/>
    </div>
  );
}

// ═══ 3) Data query · mini-table ═══════════════════════════════════
function AIXDataTableEN() {
  const rows = [
    ['Shenzhen Semiconductor Fab Expansion', 'Bidding', '¥1.20M', 'Chen Gang'],
    ['Baoshan Energy Retrofit', 'Bidding', '¥425K', 'You'],
    ['Suzhou Data-Center Fresh-Air', 'Bidding', '¥880K', 'Wang Lei'],
    ['Nantong Li-Battery Line Efficiency', 'Bidding', '¥362K', 'You'],
    ['Hangzhou Hospital Cleanroom', 'Bidding', '¥540K', 'Zhou Min'],
  ];
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="15:02" text="List all projects in Bidding, sorted by amount"/>
        <AIXAnswer kind="data" note="7 results">
          <div><b>7</b> owned projects in "Bidding", totalling <b>¥4.69M</b>. Top 5 by amount:</div>
          <div style={{ marginTop: 10, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 10, overflow: 'hidden', background: AIX.card }}>
            <div style={{ display: 'flex', padding: '8px 12px', background: AIX.bg, fontSize: 10, fontWeight: 700,
              color: AIX.ink3, letterSpacing: 0.4 }}>
              <span style={{ flex: 1 }}>Project</span><span style={{ width: 56, textAlign: 'right' }}>Amount</span><span style={{ width: 56, textAlign: 'right' }}>Owner</span>
            </div>
            {rows.map((r, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', padding: '10px 12px',
                borderTop: `1px solid ${AIX.divider}`, fontSize: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: AIX.serif, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r[0]}</div>
                  <div style={{ fontSize: 10, color: AIX.accent, fontWeight: 600, marginTop: 1 }}>● {r[1]}</div>
                </div>
                <span style={{ width: 56, textAlign: 'right', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{r[2]}</span>
                <span style={{ width: 56, textAlign: 'right', color: AIX.ink3 }}>{r[3]}</span>
              </div>
            ))}
            <div style={{ padding: '9px 12px', borderTop: `1px solid ${AIX.divider}`, fontSize: 12,
              color: AIX.ai, fontWeight: 600, textAlign: 'center' }}>See all 7 · Export ›</div>
          </div>
          <AIXSource>Source: projects table · stage=Bidding · owner∈your scope · live</AIXSource>
        </AIXAnswer>
        <AIXSuggest tags={['Only mine', 'Export to Excel', 'Which closes soonest?']}/>
      </div>
      <AIXComposer/>
    </div>
  );
}

// ═══ 4) Data query · aggregate + mini chart ═══════════════════════
function AIXBar({ label, val, max, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 7 }}>
      <span style={{ width: 62, fontSize: 11, color: AIX.ink3 }}>{label}</span>
      <div style={{ flex: 1, height: 8, background: AIX.bg, borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${(val / max) * 100}%`, height: '100%', background: color, borderRadius: 4 }}/>
      </div>
      <span style={{ width: 26, textAlign: 'right', fontSize: 11, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{val}</span>
    </div>
  );
}
function AIXDataAggregateEN() {
  const spark = [38, 52, 47, 63, 71, 58, 82, 96];
  const mx = Math.max(...spark);
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="09:40" text="What are this quarter's signings? YoY? Stage distribution?"/>
        <AIXAnswer kind="data" note="Stats · Q2">
          <div>Q2 to date:</div>
          <div style={{ marginTop: 10, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 12, padding: 14 }}>
            <div style={{ fontSize: 11, color: AIX.ink3, letterSpacing: 0.5 }}>Signed · this quarter</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 2 }}>
              <span style={{ fontFamily: AIX.serif, fontSize: 30, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>¥3.19M</span>
              <span style={{ fontSize: 12, color: AIX.green, fontWeight: 700, marginLeft: 'auto' }}>▲ YoY +24%</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 44, marginTop: 12 }}>
              {spark.map((v, i) => (
                <div key={i} style={{ flex: 1, height: `${(v / mx) * 100}%`,
                  background: i === spark.length - 1 ? AIX.ai : 'rgba(47,102,214,0.25)', borderRadius: 2 }}/>
              ))}
            </div>
            <div style={{ fontSize: 10, color: AIX.ink4, marginTop: 4 }}>Last 8 weeks · final week a new high</div>
          </div>
          <div style={{ marginTop: 10, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 12, padding: '12px 14px' }}>
            <div style={{ fontSize: 11, color: AIX.ink3, letterSpacing: 0.5, marginBottom: 2 }}>Projects by stage</div>
            <AIXBar label="Embedded" val={12} max={18} color="rgba(47,102,214,0.5)"/>
            <AIXBar label="Proposal" val={9} max={18} color="rgba(47,102,214,0.65)"/>
            <AIXBar label="Bidding" val={7} max={18} color={AIX.ai}/>
            <AIXBar label="Signed" val={18} max={18} color={AIX.green}/>
          </div>
          <AIXSource>Source: pricing_orders + projects aggregate · DB SP8D · live</AIXSource>
        </AIXAnswer>
        <AIXSuggest tags={['Break down by person', 'vs Q1', 'Export quarterly report']}/>
      </div>
      <AIXComposer/>
    </div>
  );
}

// ═══ 5) Wiki Q&A · source citation ════════════════════════════════
function AIXWikiSrc({ title, anchor, date }) {
  return (
    <div style={{ background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 10,
      padding: '10px 12px', display: 'flex', gap: 10, alignItems: 'flex-start', marginTop: 6 }}>
      <div style={{ width: 26, height: 26, borderRadius: 7, background: AIX.wikiSoft, color: AIX.wiki,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, flexShrink: 0 }}>❝</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: AIX.serif, fontSize: 12.5, fontWeight: 600, lineHeight: 1.35 }}>{title}</div>
        <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 3 }}>§ {anchor} · updated {date}</div>
      </div>
      <span style={{ fontSize: 11, color: AIX.wiki, fontWeight: 600, flexShrink: 0 }}>Open ›</span>
    </div>
  );
}
function AIXWikiEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="11:08" text="What FX rate applies to export quotes, and who can change it?"/>
        <AIXAnswer kind="wiki" note="KB · 2 sources">
          <div style={{ marginBottom: 2 }}>Per the current Pricing Policy:</div>
          <ol style={{ margin: '6px 0', paddingLeft: 20, lineHeight: 1.8 }}>
            <li>FX = system mid-rate on the <b>day the quote is submitted for approval</b> (not creation day)</li>
            <li>Locked after approval — not recalculated on FX moves</li>
            <li>Only <b>Finance Director / CEO</b> may change FX before approval, with a note</li>
          </ol>
          <div style={{ marginTop: 8, marginBottom: 2, fontSize: 12.5, color: AIX.ink3, fontWeight: 600 }}>Sources ▾</div>
          <AIXWikiSrc title="Pricing Policy v3" anchor="4.2 FX & Currency" date="2026·03"/>
          <AIXWikiSrc title="SG Export Pricing Handbook" anchor="FX lock timing" date="2026·04"/>
          <div style={{ fontSize: 11, color: AIX.warn, marginTop: 10, fontStyle: 'italic', fontFamily: AIX.serif }}>
            ⚠ Generated from the KB, may lag; defer to the source. Ask Finance for anything not covered.
          </div>
        </AIXAnswer>
        <AIXSuggest tags={['Then how is currency chosen?', 'Where to see historical FX?', '@Finance to confirm']}/>
      </div>
      <AIXComposer/>
    </div>
  );
}

// ═══ 6) Training · step card ══════════════════════════════════════
function AIXTrainEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav sub="◷ Onboarding · Quotation hands-on"/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="10:15" text="I'm new — teach me how to create a quotation"/>
        <AIXAnswer kind="train" note="Step 2 / 5" actions={false}>
          <div style={{ display: 'flex', gap: 5, marginBottom: 10 }}>
            {[1,1,0,0,0].map((on, i) => (
              <div key={i} style={{ flex: 1, height: 4, borderRadius: 2,
                background: on ? AIX.train : 'rgba(123,91,172,0.2)' }}/>
            ))}
          </div>
          <div style={{ fontFamily: AIX.serif, fontSize: 16, fontWeight: 600 }}>Step 2 · Pick customer & project</div>
          <div style={{ fontSize: 13, marginTop: 6, lineHeight: 1.6, color: AIX.ink2 }}>
            On the New Quotation screen, pick "Linked Project" first — the system auto-fills customer, contact and currency, so you don't type them. Can't find the project? Create it in the Projects module first.
          </div>
          <div style={{ marginTop: 10, height: 116, borderRadius: 10, background: AIX.bg,
            border: `1px dashed ${AIX.dividerStrong}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: AIX.ink4, fontSize: 11.5, textAlign: 'center', padding: '0 16px' }}>
            〔 App screenshot placeholder: New Quotation · Linked Project dropdown 〕
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button style={{ flex: 1, padding: '10px 0', borderRadius: 12, border: 'none', background: AIX.train,
              color: '#fff', fontSize: 13, fontWeight: 700 }}>Try it in the App →</button>
            <button style={{ padding: '10px 16px', borderRadius: 12, border: `1px solid ${AIX.dividerStrong}`,
              background: AIX.card, color: AIX.ink2, fontSize: 13 }}>Next</button>
          </div>
          <div style={{ fontSize: 11, color: AIX.ink3, marginTop: 8, textAlign: 'center', fontStyle: 'italic', fontFamily: AIX.serif }}>
            "Try it in the App" takes you to the real screen — come back here to continue
          </div>
        </AIXAnswer>
        <AIXSuggest tags={['I’m stuck on this step', 'Skip — just let me do it', 'Previous']}/>
      </div>
      <AIXComposer value="I'm stuck — my project isn't in the Linked Project list"/>
    </div>
  );
}

// ═══ 7) Adaptive routing overview ═════════════════════════════════
function AIXMixedEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <div style={{ padding: '4px 16px 10px', textAlign: 'center' }}>
          <span style={{ fontSize: 10.5, color: AIX.ink3, background: AIX.card, padding: '4px 12px',
            borderRadius: 999, border: `1px solid ${AIX.divider}`, fontStyle: 'italic', fontFamily: AIX.serif }}>
            One composer · the AI decides where to fetch · the badge tells you the source
          </span>
        </div>
        <AIXUser text="How's Baoshan Energy's win rate"/>
        <AIXAnswer kind="data" note="Customer" compact actions={false}>
          <div>Overall win rate <b style={{ color: AIX.green }}>~72%</b>, chase:</div>
          <AIXEntityCard tag="#" name="Baoshan Energy Retrofit" metaA="● Bidding" metaC="¥425K"/>
        </AIXAnswer>
        <AIXUser text="What day's FX for export quotes"/>
        <AIXAnswer kind="wiki" note="KB" compact actions={false}>
          <div>Mid-rate on the <b>submit-for-approval day</b>, locked after approval.</div>
          <AIXWikiSrc title="Pricing Policy v3" anchor="4.2 FX & Currency" date="2026·03"/>
        </AIXAnswer>
        <AIXUser text="/weekly report"/>
        <AIXAnswer kind="cmd" note="/weekly report" compact actions={false}>
          <div style={{ fontSize: 11, color: AIX.cmd, fontWeight: 700, marginBottom: 4 }}>Generated from your 5 work items + group messages ▾</div>
          <div style={{ background: AIX.card, border: `1px dashed ${AIX.dividerStrong}`, borderRadius: 8,
            padding: '9px 11px', fontFamily: AIX.serif, fontSize: 13, lineHeight: 1.55 }}>
            This week: Baoshan Energy visit + SG MCP deployment; advanced 2 bidding projects…
          </div>
          <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
            <span style={{ fontSize: 11, color: '#fff', background: AIX.cmd, padding: '5px 12px', borderRadius: 999, fontWeight: 600 }}>Adopt</span>
            <span style={{ fontSize: 11, color: AIX.ink2, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, padding: '5px 12px', borderRadius: 999 }}>Regenerate</span>
          </div>
        </AIXAnswer>
        <AIXUser text="Teach me to create a quotation"/>
        <AIXAnswer kind="train" note="5 steps · started" compact actions={false}>
          <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
            {[1,0,0,0,0].map((on,i)=><div key={i} style={{ flex:1, height:3, borderRadius:2, background:on?AIX.train:'rgba(123,91,172,0.2)' }}/>)}
          </div>
          <div><b>Step 1</b> · Open New Quotation — tap here to go ›</div>
        </AIXAnswer>
      </div>
      <AIXComposer/>
    </div>
  );
}

// ═══ 8) Composer states (# reference + / command) ═════════════════
function AIXChip({ children, hot }) {
  return (
    <span style={{ fontSize: 12, padding: '6px 11px', borderRadius: 999, fontFamily: AIX.mono,
      color: hot ? '#fff' : AIX.ink2, background: hot ? AIX.ink : AIX.card,
      border: `1px solid ${hot ? AIX.ink : AIX.dividerStrong}` }}>{children}</span>
  );
}
function AIXComposerStatesEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '16px 16px 0' }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: AIX.ink3, letterSpacing: 0.6, textTransform: 'uppercase' }}>Type # · reference an entity</div>
        <div style={{ background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 14, padding: 14, marginTop: 8 }}>
          <div style={{ fontFamily: AIX.serif, fontSize: 13.5, color: AIX.ink }}>
            Analyse <span style={{ color: AIX.ai, fontWeight: 700, background: AIX.aiSoft, padding: '1px 5px', borderRadius: 4 }}>#Baoshan</span>
            <span style={{ display: 'inline-block', width: 2, height: 15, background: AIX.ai, marginLeft: 1, verticalAlign: -2, animation: 'aixBlink 1s infinite' }}/>
          </div>
          <div style={{ fontSize: 10.5, color: AIX.ink3, margin: '12px 0 6px' }}>Recent · Project / Customer / Quote</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            <AIXChip hot>#Baoshan Energy Retrofit</AIXChip><AIXChip>#Shanghai Baoshan Energy Tech</AIXChip>
            <AIXChip>#Baoshan Phase-2 Audit</AIXChip><AIXChip>#QT-2026-0418 Quote</AIXChip>
          </div>
        </div>

        <div style={{ fontSize: 11, fontWeight: 700, color: AIX.ink3, letterSpacing: 0.6, textTransform: 'uppercase', marginTop: 20 }}>Type / · command panel (grouped)</div>
        <div style={{ background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 14, marginTop: 8, overflow: 'hidden' }}>
          <AIXCmdPanel focus="/bidding projects"/>
        </div>
        <div style={{ fontSize: 11, color: AIX.ink3, margin: '14px 4px 0', fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.6 }}>
          # lets the AI lock the exact object — no "which Baoshan?"; / is a shortcut, and selecting still fills an editable natural-language line — fast for pros, clear for newcomers.
        </div>
      </div>
      <AIXComposer value="Analyse the win rate & risks of #Baoshan Energy Retrofit" panel={null}/>
    </div>
  );
}

// ═══ 9a) `/` trigger · typing & filtering ═════════════════════════
function AIXSlashRow({ kind, cmd, q, desc, hot }) {
  const k = AIX_KIND[kind];
  const idx = cmd.indexOf(q);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px',
      borderRadius: 10, background: hot ? k.bg : 'transparent' }}>
      <span style={{ width: 22, height: 22, borderRadius: 6, background: k.bg, color: k.color,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, flexShrink: 0 }}>{k.icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: AIX.mono, fontSize: 12.5, color: AIX.ink }}>
          {idx >= 0 ? <>{cmd.slice(0, idx)}<span style={{ background: 'rgba(47,102,214,0.22)', color: AIX.aiInk, fontWeight: 700 }}>{q}</span>{cmd.slice(idx + q.length)}</> : cmd}
        </div>
        <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{desc}</div>
      </div>
      <span style={{ fontSize: 9, fontWeight: 700, color: k.color, padding: '1px 5px', borderRadius: 3, background: k.bg, flexShrink: 0 }}>{k.label}</span>
      {hot && <span style={{ fontSize: 11, color: AIX.ink3, flexShrink: 0 }}>↵</span>}
    </div>
  );
}
function AIXSlashTypingEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="Yesterday" text="Thanks"/>
        <AIXAnswer compact actions={false}><div style={{ color: AIX.ink3 }}>You're welcome — ping me anytime 👋</div></AIXAnswer>
      </div>
      <div style={{ margin: '0 12px 6px', background: AIX.card, border: `1px solid ${AIX.dividerStrong}`,
        borderRadius: 16, boxShadow: '0 -6px 24px rgba(0,0,0,0.10)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px 6px' }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: AIX.ink2 }}>/ Command · live filter · <span style={{ color: AIX.ai }}>4 matches</span></span>
          <span style={{ fontSize: 10.5, color: AIX.ink3 }}>↑↓ select · ↵ insert · esc close</span>
        </div>
        <div style={{ padding: '2px 8px 8px' }}>
          <AIXSlashRow kind="data" cmd="/bidding projects" q="bid" desc="Projects in Bidding · sorted by amount" hot/>
          <AIXSlashRow kind="data" cmd="/bid win-rate" q="bid" desc="Win rate & key projects for a customer"/>
          <AIXSlashRow kind="data" cmd="/bid contracts" q="bid" desc="Search signed contracts by customer/project"/>
          <AIXSlashRow kind="wiki" cmd="/bid product specs" q="bid" desc="KB: product specs / comparison table"/>
        </div>
      </div>
      <div style={{ padding: '0 16px 6px', fontSize: 10.5, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif }}>
        Type <b style={{ fontFamily: AIX.mono, fontStyle: 'normal' }}>/</b> to summon · keep typing to filter · select = fill editable natural language, not auto-execute
      </div>
      <div style={{ padding: '4px 12px 24px', display: 'flex', alignItems: 'center', gap: 8,
        borderTop: `1px solid ${AIX.divider}`, background: AIX.card }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: AIX.bg, border: `1px solid ${AIX.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: AIX.ink2, marginTop: 4 }}>+</span>
        <div style={{ flex: 1, background: AIX.bg, borderRadius: 20, border: `1.5px solid ${AIX.ai}`,
          padding: '9px 14px', fontFamily: AIX.mono, fontSize: 14, color: AIX.ink, display: 'flex', alignItems: 'center', marginTop: 4 }}>
          <span style={{ flex: 1 }}>/bid
            <span style={{ display: 'inline-block', width: 2, height: 16, background: AIX.ai, marginLeft: 1, verticalAlign: -2, animation: 'aixBlink 1s infinite' }}/>
          </span>
        </div>
        <button style={{ width: 36, height: 36, borderRadius: 18, background: AIX.ink4, color: '#fff', border: 'none', fontSize: 14, fontWeight: 700, marginTop: 4 }}>↑</button>
      </div>
    </div>
  );
}

// ═══ 9b) `/` trigger · selected → editable NL ═════════════════════
function AIXSlashFilledEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="Yesterday" text="Thanks"/>
        <AIXAnswer compact actions={false}><div style={{ color: AIX.ink3 }}>You're welcome — ping me anytime 👋</div></AIXAnswer>
      </div>
      <div style={{ borderTop: `1px solid ${AIX.divider}`, background: AIX.card }}>
        <div style={{ padding: '10px 14px 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 10.5, color: AIX.ai, fontWeight: 700 }}>✓ Filled from <span style={{ fontFamily: AIX.mono }}>/bidding projects</span></span>
          <span style={{ fontSize: 10.5, color: AIX.ink3 }}>· edit before send</span>
          <span style={{ marginLeft: 'auto', fontSize: 10.5, color: AIX.ink3, border: `1px solid ${AIX.dividerStrong}`,
            padding: '2px 8px', borderRadius: 999 }}>× remove command</span>
        </div>
        <div style={{ padding: '4px 12px 8px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 36, height: 36, borderRadius: 18, background: AIX.bg, border: `1px solid ${AIX.dividerStrong}`,
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: AIX.ink2 }}>+</span>
          <div style={{ flex: 1, background: AIX.bg, borderRadius: 20, border: `1.5px solid ${AIX.ai}`,
            padding: '9px 14px', fontFamily: AIX.serif, fontSize: 14, color: AIX.ink, lineHeight: 1.4 }}>
            Show all my projects in <b>Bidding</b>, sorted by amount high → low
            <span style={{ display: 'inline-block', width: 2, height: 16, background: AIX.ai, marginLeft: 1, verticalAlign: -2, animation: 'aixBlink 1s infinite' }}/>
          </div>
          <button style={{ width: 36, height: 36, borderRadius: 18, background: AIX.ai, color: '#fff', border: 'none', fontSize: 14, fontWeight: 700 }}>↑</button>
        </div>
        <div style={{ padding: '0 16px 22px', fontSize: 10.5, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.55 }}>
          Closed loop: slash select → translated to editable NL → tweak params (stage / sort) then send → AI routes to the same capability. Fast, editable, traceable.
        </div>
      </div>
    </div>
  );
}

// ═══ 10a) Skill registry · catalog list ═══════════════════════════
function AIXCatRow({ kind, cmd, name, desc, params, role, out }) {
  const k = AIX_KIND[kind];
  return (
    <div style={{ padding: '13px 16px', borderBottom: `1px solid ${AIX.divider}`, display: 'flex', gap: 12 }}>
      <span style={{ width: 30, height: 30, borderRadius: 8, background: k.bg, color: k.color,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0 }}>{k.icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontFamily: AIX.mono, fontSize: 12, color: AIX.ink, fontWeight: 600 }}>{cmd}</span>
          <span style={{ fontFamily: AIX.serif, fontSize: 12, color: AIX.ink2 }}>{name}</span>
          <span style={{ marginLeft: 'auto', fontSize: 9, fontWeight: 700, color: k.color, padding: '1px 5px', borderRadius: 3, background: k.bg }}>{k.label}</span>
        </div>
        <div style={{ fontSize: 11, color: AIX.ink3, marginTop: 3, lineHeight: 1.4 }}>{desc}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 7 }}>
          {params.map(p => (
            <span key={p} style={{ fontSize: 9.5, color: AIX.ink3, background: AIX.bg, border: `1px solid ${AIX.divider}`, padding: '2px 6px', borderRadius: 4, fontFamily: AIX.mono }}>{p}</span>
          ))}
          <span style={{ fontSize: 9.5, color: AIX.accent, background: AIX.accentBg, padding: '2px 6px', borderRadius: 4 }}>{role}</span>
          <span style={{ fontSize: 9.5, color: k.color, background: k.bg, padding: '2px 6px', borderRadius: 4 }}>→ {out}</span>
        </div>
      </div>
      <span style={{ color: AIX.ink4, fontSize: 14, alignSelf: 'center' }}>›</span>
    </div>
  );
}
function AIXSkillCatalogEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54, overflow: 'auto' }}>
      <div style={{ padding: '14px 20px 6px' }}>
        <div style={{ fontSize: 11, color: AIX.ink3, fontWeight: 600, letterSpacing: 1.2, textTransform: 'uppercase' }}>PMA · Capability Contract</div>
        <h1 style={{ fontFamily: AIX.serif, fontSize: 25, fontWeight: 500, margin: '4px 0 0', letterSpacing: -0.3 }}>Command Registry</h1>
        <div style={{ fontSize: 11.5, color: AIX.ink3, marginTop: 6, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.5 }}>
          Single source of truth · panel generated from it · NL routing targets it · permissions gated by it
        </div>
      </div>
      <div style={{ display: 'flex', gap: 6, padding: '8px 16px 12px', overflowX: 'auto' }}>
        {[['All', true], ['◧ Data', false], ['❝ Wiki', false], ['⌘ Command', false], ['◷ Training', false]].map(([t, h], i) => (
          <span key={i} style={{ flexShrink: 0, fontSize: 12, padding: '6px 12px', borderRadius: 999,
            background: h ? AIX.ink : AIX.card, color: h ? '#fff' : AIX.ink2,
            border: `1px solid ${h ? AIX.ink : AIX.dividerStrong}` }}>{t}</span>
        ))}
      </div>
      <div style={{ background: AIX.card }}>
        <AIXCatRow kind="data" cmd="/bidding projects" name="Bidding list" desc="Projects in a given stage, sorted by amount" params={['Stage', 'Owner', 'Sort']} role="All · by scope" out="Adaptive"/>
        <AIXCatRow kind="data" cmd="/win-rate" name="Customer win-rate" desc="Historical win rate + key projects" params={['Customer*']} role="All" out="Entity card"/>
        <AIXCatRow kind="data" cmd="/quarter signings" name="Performance rollup" desc="Period signings · YoY · stage split" params={['Period']} role="Sales+Mgmt" out="Stat chart"/>
        <AIXCatRow kind="wiki" cmd="/export-FX" name="Pricing policy Q&A" desc="KB RAG · sources required · time-stamped" params={['—']} role="All" out="Source card"/>
        <AIXCatRow kind="cmd" cmd="/weekly-report" name="Weekly report draft" desc="From work items + group msgs · needs adopt" params={['Period']} role="All" out="Draft block"/>
        <AIXCatRow kind="train" cmd="/onboarding" name="Quotation hands-on" desc="5-step machine · deep-links into App" params={['Module']} role="New hire" out="Step card"/>
      </div>
      <div style={{ padding: '14px 20px 26px', fontSize: 11, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.6 }}>
        + New capability = one row in this table; panel / routing / permissions auto-apply — no front-end change.
      </div>
    </div>
  );
}

// ═══ 10b) Skill registry · capability contract ════════════════════
function AIXKV({ k, v, mono }) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: `1px solid ${AIX.divider}` }}>
      <span style={{ width: 76, fontSize: 11, color: AIX.ink3, flexShrink: 0 }}>{k}</span>
      <span style={{ flex: 1, fontSize: 11.5, color: AIX.ink, fontFamily: mono ? AIX.mono : AIX.sans, lineHeight: 1.5 }}>{v}</span>
    </div>
  );
}
function AIXSkillDetailEN() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54, overflow: 'auto' }}>
      <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10, borderBottom: `1px solid ${AIX.divider}`, background: AIX.card }}>
        <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={AIX.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
        <span style={{ fontFamily: AIX.mono, fontSize: 13.5, fontWeight: 600 }}>/bidding projects</span>
        <span style={{ marginLeft: 'auto', fontSize: 9.5, fontWeight: 700, color: AIX.data, padding: '2px 7px', borderRadius: 4, background: AIX.dataSoft }}>◧ Data · deterministic</span>
      </div>
      <div style={{ padding: '16px 20px' }}>
        <div style={{ fontFamily: AIX.serif, fontSize: 17, fontWeight: 600 }}>Bidding project list</div>
        <div style={{ fontSize: 12.5, color: AIX.ink2, marginTop: 6, lineHeight: 1.6 }}>
          Query projects in the given stage within the user's permission scope, sorted by amount. Deterministic, cacheable, exportable.
        </div>

        <div style={{ fontSize: 11, fontWeight: 700, color: AIX.ink3, letterSpacing: 0.6, textTransform: 'uppercase', margin: '18px 0 4px' }}>Parameter schema</div>
        <div style={{ background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ display: 'flex', padding: '8px 12px', background: AIX.bg, fontSize: 10, fontWeight: 700, color: AIX.ink3 }}>
            <span style={{ flex: 1 }}>Param</span><span style={{ width: 42 }}>Type</span><span style={{ width: 34 }}>Req</span><span style={{ width: 104 }}>Default / source</span>
          </div>
          {[['stage', 'enum', 'No', 'Bidding · stage dict'], ['owner', 'ref', 'No', 'current user scope'], ['sort', 'enum', 'No', 'amount↓'], ['limit', 'int', 'No', '20']].map((r, i) => (
            <div key={i} style={{ display: 'flex', padding: '8px 12px', borderTop: `1px solid ${AIX.divider}`, fontSize: 11, fontFamily: AIX.mono }}>
              <span style={{ flex: 1, color: AIX.aiInk, fontWeight: 600 }}>{r[0]}</span>
              <span style={{ width: 42, color: AIX.ink3 }}>{r[1]}</span>
              <span style={{ width: 34, color: AIX.ink3 }}>{r[2]}</span>
              <span style={{ width: 104, color: AIX.ink2 }}>{r[3]}</span>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 18, background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 12, padding: '4px 14px' }}>
          <AIXKV k="Handler" v="projects table query · deterministic · cache 5min · Excel export"/>
          <AIXKV k="Permission" v="All roles · data scope = get_viewable_data(owner) · cross-DB by PMA_DB_TYPE"/>
          <AIXKV k="Output" v="≤3 → entity card; >3 → scrollable mini-table · badge ◧Data"/>
          <AIXKV k="NL synonyms" v="“what projects are in bidding” / “list the deals out for tender” / “how many am I bidding” → same capability"/>
        </div>

        <div style={{ marginTop: 16, background: AIX.aiBg, border: '1px solid rgba(47,102,214,0.18)', borderRadius: 12, padding: '12px 14px' }}>
          <div style={{ fontSize: 11, color: AIX.aiInk, fontWeight: 700, marginBottom: 6 }}>Example</div>
          <div style={{ fontFamily: AIX.mono, fontSize: 11, color: AIX.ink2 }}>in: /bidding projects --sort=amount</div>
          <div style={{ fontFamily: AIX.mono, fontSize: 11, color: AIX.ink2, marginTop: 4 }}>out: mini-table · 7 rows · ◧Data · source note</div>
        </div>
        <div style={{ margin: '16px 0 26px', fontSize: 11, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.6 }}>
          The contract is the truth: front-end panel, NL router and permission gate all read this one — changing the contract is safer than changing three code paths.
        </div>
      </div>
    </div>
  );
}

// ═══ 11) Edge states ══════════════════════════════════════════════
function AIXEdgeBtns({ items }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
      {items.map(([t, pri], i) => (
        <span key={i} style={{ fontSize: 12, padding: '7px 12px', borderRadius: 999, fontWeight: 600,
          color: pri ? '#fff' : AIX.ink2, background: pri ? AIX.ai : AIX.card,
          border: `1px solid ${pri ? AIX.ai : AIX.dividerStrong}` }}>{t}</span>
      ))}
    </div>
  );
}
function AIXEdgeShell({ children }) {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>{children}</div>
      <AIXComposer/>
    </div>
  );
}
function AIXThinkStep({ s, label, sub }) {
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '7px 0' }}>
      <span style={{ width: 16, height: 16, borderRadius: 8, flexShrink: 0, marginTop: 1,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10,
        background: s === 'done' ? AIX.green : s === 'now' ? AIX.aiSoft : 'transparent',
        color: s === 'done' ? '#fff' : AIX.ink3,
        border: s === 'todo' ? `1px solid ${AIX.dividerStrong}` : 'none' }}>
        {s === 'done' ? '✓' : ''}
      </span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: s === 'todo' ? AIX.ink3 : AIX.ink }}>{label}</div>
        {sub && <div style={{ fontSize: 11, color: AIX.ink3, marginTop: 2 }}>{sub}</div>}
      </div>
      {s === 'now' && <span style={{ display: 'inline-flex', gap: 3, marginTop: 6 }}>
        {[0, 1, 2].map(i => <span key={i} style={{ width: 5, height: 5, borderRadius: 3, background: AIX.ai, animation: `aixDot 1.4s ${i * 0.16}s infinite` }}/>)}
      </span>}
    </div>
  );
}
function AIXThinkingEN() {
  return (
    <AIXEdgeShell>
      <AIXUser time="14:21" text="Analyse Baoshan Energy's win rate, then compare with Shenzhen Semiconductor"/>
      <div style={{ padding: '6px 16px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <AIXLogo size={22}/>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: AIX.aiInk }}>PMA Assistant</span>
            <span style={{ fontSize: 10, color: AIX.ink3 }}>thinking…</span>
          </div>
          <div style={{ background: AIX.aiBg, border: '1px solid rgba(47,102,214,0.18)', borderRadius: '4px 14px 14px 14px', padding: '10px 14px' }}>
            <AIXThinkStep s="done" label="Classify intent" sub="Data query · win-rate + cross-customer compare"/>
            <AIXThinkStep s="done" label="Resolve permission scope" sub="get_viewable_data · your visible data"/>
            <AIXThinkStep s="now" label="Querying" sub="projects + pricing_orders · 2 customers"/>
            <AIXThinkStep s="todo" label="Aggregate & compose answer"/>
            <div style={{ fontSize: 10.5, color: AIX.ink4, marginTop: 8, fontStyle: 'italic', fontFamily: AIX.serif }}>2.4s elapsed · complex queries usually &lt; 8s · live data, no cache</div>
          </div>
          <div style={{ marginTop: 8 }}>
            <span style={{ fontSize: 12, color: AIX.ink2, border: `1px solid ${AIX.dividerStrong}`, background: AIX.card, padding: '6px 14px', borderRadius: 999, fontWeight: 600 }}>■ Stop</span>
          </div>
        </div>
      </div>
    </AIXEdgeShell>
  );
}
function AIXErrorStateEN() {
  return (
    <AIXEdgeShell>
      <AIXUser time="14:22" text="Export all this quarter's signed deals to Excel"/>
      <AIXAnswer kind="cmd" note="/export signings" actions={false}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <span style={{ width: 26, height: 26, borderRadius: 13, flexShrink: 0, background: 'rgba(181,69,58,0.10)',
            color: '#B5453A', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>!</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, color: '#B5453A' }}>Export didn't go through</div>
            <div style={{ fontSize: 13, color: AIX.ink2, marginTop: 4, lineHeight: 1.55 }}>
              Data source timed out: pricing_orders quarterly aggregate didn't return in 30s, auto-retried once and still failed. <b>Not something you did wrong.</b>
            </div>
          </div>
        </div>
        <AIXEdgeBtns items={[['Retry', true], ['Narrow · export by month', false], ['Report to admin', false]]}/>
        <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 10, fontFamily: AIX.mono }}>Error GW-504 · 14:22 · req_8af3 · screenshot to IT</div>
      </AIXAnswer>
    </AIXEdgeShell>
  );
}
function AIXNoPermissionEN() {
  return (
    <AIXEdgeShell>
      <AIXUser time="10:05" text="Show me the amounts on all of Wang Lei's projects"/>
      <AIXAnswer kind="data" note="🔒 out of scope" actions={false}>
        <div style={{ fontWeight: 700 }}>That's outside your data scope</div>
        <div style={{ fontSize: 13, color: AIX.ink2, marginTop: 5, lineHeight: 1.6 }}>
          Wang Lei's projects belong to <b>East-China Sales Team 2</b>. Your current scope is <b>you + direct reports</b> — peer colleagues' project amounts aren't visible.
        </div>
        <div style={{ marginTop: 10, background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 10, padding: '10px 12px', fontSize: 12, color: AIX.ink3 }}>
          You can see: <b style={{ color: AIX.ink }}>your 6</b> + <b style={{ color: AIX.ink }}>3 reports'</b> projects
        </div>
        <AIXEdgeBtns items={[['Show my reports instead', true], ['Request wider scope →', false], ['Ask Wang Lei directly', false]]}/>
        <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 10, fontStyle: 'italic', fontFamily: AIX.serif }}>Scope enforced by get_viewable_data · requests go through OA approval</div>
      </AIXAnswer>
    </AIXEdgeShell>
  );
}
function AIXEmptyResultEN() {
  return (
    <AIXEdgeShell>
      <AIXUser time="09:12" text="Which projects were newly Signed this month?"/>
      <AIXAnswer kind="data" note="0 results" actions={false}>
        <div style={{ fontWeight: 700 }}>No matching results</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 8 }}>
          {['stage = Signed', 'new this month', 'your scope'].map(t => (
            <span key={t} style={{ fontSize: 10.5, color: AIX.ink3, background: AIX.bg, border: `1px solid ${AIX.divider}`, padding: '2px 7px', borderRadius: 4, fontFamily: AIX.mono }}>{t}</span>
          ))}
        </div>
        <div style={{ fontSize: 13, color: AIX.ink2, marginTop: 10, lineHeight: 1.6 }}>
          The query ran fine — nothing was newly signed this month yet. Latest was <b>Apr 28 "Baoshan Energy Retrofit"</b>.
        </div>
        <AIXEdgeBtns items={[['Show this-quarter Signed (18)', true], ['Show Bidding (7)', false], ['Clear filters', false]]}/>
      </AIXAnswer>
    </AIXEdgeShell>
  );
}
function AIXLongResultEN() {
  return (
    <AIXEdgeShell>
      <AIXUser time="16:30" text="List every follow-up record across all my customers"/>
      <AIXAnswer kind="data" note="many results" actions={false}>
        <div>Matched <b>1,284</b> follow-up records — listing all would flood the chat. Latest 3:</div>
        <div style={{ marginTop: 10, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 10, overflow: 'hidden' }}>
          {[['Baoshan Energy Retrofit', 'May 14 visit · pricing to refine'], ['Shenzhen Fab Expansion', 'May 13 bid V2 in progress'], ['Suzhou Data-Center', 'May 12 proposal delivered']].map((r, i) => (
            <div key={i} style={{ padding: '9px 12px', borderTop: i ? `1px solid ${AIX.divider}` : 'none', fontSize: 12 }}>
              <span style={{ fontFamily: AIX.serif, fontWeight: 600 }}>{r[0]}</span>
              <span style={{ color: AIX.ink3 }}> · {r[1]}</span>
            </div>
          ))}
          <div style={{ padding: '8px 12px', borderTop: `1px dashed ${AIX.dividerStrong}`, fontSize: 11.5, color: AIX.ink3, textAlign: 'center', fontStyle: 'italic', fontFamily: AIX.serif }}>
            1,281 more collapsed
          </div>
        </div>
        <AIXEdgeBtns items={[['Summarise the key points', true], ['Group by customer', false], ['Last 7 days only (56)', false], ['Export Excel', false]]}/>
        <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 10, fontStyle: 'italic', fontFamily: AIX.serif }}>Chat renders ≤ 20 rows at once · large results go to summary / group / export</div>
      </AIXAnswer>
    </AIXEdgeShell>
  );
}

Object.assign(window, {
  AIXEntryEN, AIXDataEntityEN, AIXDataTableEN, AIXDataAggregateEN,
  AIXWikiEN, AIXTrainEN, AIXMixedEN, AIXComposerStatesEN,
  AIXSlashTypingEN, AIXSlashFilledEN, AIXSkillCatalogEN, AIXSkillDetailEN,
  AIXThinkingEN, AIXErrorStateEN, AIXNoPermissionEN, AIXEmptyResultEN, AIXLongResultEN,
});
