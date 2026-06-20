// PMA · Work Calendar (EN) — Agenda / month sheet / scope picker

function CalendarAgendaEN({ submitted = false } = {}) {
  const log = submitted ? CALEN_DAILY_LOG_SUBMITTED : CALEN_DAILY_LOG;
  return (
    <div style={{ background: CALEN.bg, height: '100%', fontFamily: CALEN.sans, color: CALEN.ink, position: 'relative' }}>
      <CALENStatusPad/>
      <div style={{ paddingBottom: 84, height: '100%', overflow: 'auto', boxSizing: 'border-box' }}>
        <div style={{ padding: '28px 20px 14px', display: 'flex', alignItems: 'flex-start',
          justifyContent: 'space-between', gap: 14 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontFamily: CALEN.serif, fontSize: 26, fontWeight: 600, letterSpacing: -0.3 }}>
                Work Calendar
              </span>
              <span style={{ fontSize: 16, color: CALEN.ink3 }}>▾</span>
            </div>
            <div style={{ fontSize: 13, color: CALEN.ink3, marginTop: 4 }}>
              My Calendar · Zhang Xiang · 32 items this May
            </div>
          </div>
          <div style={{ width: 36, height: 36, borderRadius: 18, background: CALEN.ink, color: '#FFF',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 300,
            lineHeight: 1, flexShrink: 0 }}>+</div>
        </div>
        <div style={{ height: 1, background: CALEN.divider }}/>

        <div style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 16 }}>
            <span style={{ color: CALEN.ink3, fontSize: 18 }}>‹</span>
            <span style={{ fontSize: 16, fontWeight: 600, fontFamily: CALEN.serif }}>May 2026</span>
            <span style={{ color: CALEN.ink3, fontSize: 18 }}>›</span>
          </div>
          <div style={{ display: 'flex', background: CALEN.dividerSoft, padding: 2, borderRadius: 7,
            fontSize: 11.5, fontWeight: 600 }}>
            {['Month', 'Week', 'Day'].map((v, i) => (
              <span key={v} style={{ padding: '5px 10px', borderRadius: 5,
                background: i === 1 ? CALEN.card : 'transparent',
                color: i === 1 ? CALEN.ink : CALEN.ink3,
                boxShadow: i === 1 ? '0 1px 2px rgba(0,0,0,0.06)' : 'none' }}>{v}</span>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', padding: '0 12px 14px', gap: 4 }}>
          {CALEN_WEEK.map(d => {
            const sel = d.sel;
            return (
              <div key={d.d} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
                padding: '8px 0', borderRadius: 10,
                background: sel ? CALEN.ink : 'transparent',
                color: sel ? '#FFF' : (d.weekend ? CALEN.ink4 : CALEN.ink2) }}>
                <span style={{ fontSize: 10, fontWeight: 500, letterSpacing: 0.3,
                  color: sel ? 'rgba(255,255,255,0.7)' : (d.weekend ? CALEN.ink4 : CALEN.ink3) }}>{d.w}</span>
                <span style={{ fontSize: 18, fontWeight: 600, fontFamily: CALEN.serif, marginTop: 3 }}>{d.d}</span>
                {d.items > 0 && (
                  <span style={{ marginTop: 4, width: 4, height: 4, borderRadius: 2,
                    background: sel ? '#FFF' : CALEN.accent }}/>
                )}
                {d.holiday && <span style={{ fontSize: 9, marginTop: 2,
                  color: sel ? 'rgba(255,255,255,0.85)' : CALEN.red, fontWeight: 600 }}>{d.holiday}</span>}
              </div>
            );
          })}
        </div>

        <div style={{ padding: '4px 20px 6px', display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6, fontWeight: 600, textTransform: 'uppercase' }}>
              Thursday · Today
            </div>
            <div style={{ fontFamily: CALEN.serif, fontSize: 22, fontWeight: 600, marginTop: 2 }}>
              May 14 · {CALEN_ITEMS_TODAY.length} items
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 10, color: CALEN.ink3, textTransform: 'uppercase', letterSpacing: 0.4, fontWeight: 600 }}>Total</div>
            <div style={{ fontFamily: CALEN.serif, fontSize: 18, fontWeight: 600, color: CALEN.blue,
              fontVariantNumeric: 'tabular-nums' }}>{cfmtEN(log.totalHours)}h</div>
          </div>
        </div>

        <div style={{ background: CALEN.card, marginTop: 6, borderTop: `1px solid ${CALEN.dividerSoft}`,
          borderBottom: `1px solid ${CALEN.dividerSoft}` }}>
          {CALEN_ITEMS_TODAY.map((it, i) => <WorkItemRowEN key={it.id} item={it} last={i === CALEN_ITEMS_TODAY.length - 1}/>)}
        </div>

        <div style={{ padding: '18px 16px 0' }}>
          <DailyLogCardEN log={log} submitted={submitted}/>
        </div>
      </div>
    </div>
  );
}
function CalendarAgendaSubmittedEN() { return <CalendarAgendaEN submitted/>; }

function WorkItemRowEN({ item, last }) {
  const t = calTypeEN(item.type);
  const done = item.status === 'completed';
  return (
    <div style={{ padding: '14px 20px', borderBottom: last ? 'none' : `1px solid ${CALEN.dividerSoft}`,
      display: 'flex', alignItems: 'flex-start', gap: 12,
      opacity: done ? 0.55 : 1 }}>
      <div style={{ width: 46, flexShrink: 0, textAlign: 'right', paddingTop: 1 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: CALEN.ink, fontVariantNumeric: 'tabular-nums', fontFamily: CALEN.serif }}>
          {item.start}
        </div>
        <div style={{ fontSize: 10, color: CALEN.ink4, fontVariantNumeric: 'tabular-nums', marginTop: 1 }}>
          {item.end}
        </div>
      </div>
      <div style={{ width: 3, alignSelf: 'stretch', background: t.color, borderRadius: 2, flexShrink: 0 }}/>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 10, color: t.color, background: t.bg, padding: '1px 6px',
            borderRadius: 3, fontWeight: 700, letterSpacing: 0.3, textTransform: 'uppercase' }}>{t.label}</span>
          {item.dingtalk && (
            <span style={{ fontSize: 9, color: CALEN.ink3, background: CALEN.dividerSoft, padding: '1px 5px',
              borderRadius: 3, fontWeight: 600, letterSpacing: 0.3, textTransform: 'uppercase' }}>Synced</span>
          )}
          {done && <span style={{ fontSize: 9.5, color: CALEN.green, background: CALEN.greenSoft, padding: '1px 5px',
            borderRadius: 3, fontWeight: 700, letterSpacing: 0.3, textTransform: 'uppercase' }}>✓ Done</span>}
        </div>
        <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, lineHeight: 1.35,
          textDecoration: done ? 'line-through' : 'none' }}>{item.title}</div>
        <div style={{ fontSize: 11.5, color: CALEN.ink3, marginTop: 3, lineHeight: 1.4 }}>{item.sub}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6, fontSize: 10.5, color: CALEN.ink3, flexWrap: 'wrap' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
            <span>⏱</span>{cfmtEN(item.hours)}h
          </span>
          {item.project && (
            <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 3,
              background: CALEN.accentSoft, color: CALEN.accent, fontWeight: 600,
              maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              #{item.project}
            </span>
          )}
          {item.customer && (
            <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 3,
              background: CALEN.tealSoft, color: CALEN.teal, fontWeight: 600,
              maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.customer}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function DailyLogCardEN({ log, submitted }) {
  return (
    <div style={{ background: CALEN.card, borderRadius: 14, border: `1px solid ${CALEN.divider}`, padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6, fontWeight: 600,
          textTransform: 'uppercase' }}>Daily Log · May 14</span>
        {submitted ? (
          <span style={{ fontSize: 10, color: CALEN.green, background: CALEN.greenSoft, padding: '2px 7px',
            borderRadius: 3, fontWeight: 700, textTransform: 'uppercase' }}>Submitted</span>
        ) : (
          <span style={{ fontSize: 10, color: CALEN.warn, background: CALEN.warnSoft, padding: '2px 7px',
            borderRadius: 3, fontWeight: 700, textTransform: 'uppercase' }}>Draft</span>
        )}
      </div>

      {!submitted && (
        <>
          <div style={{ display: 'flex', gap: 14, marginBottom: 12 }}>
            <StatEN label="Hours" val={`${cfmtEN(log.totalHours)}h`} color={CALEN.blue}/>
            <StatEN label="Items" val={log.itemCount} color={CALEN.ink}/>
            <StatEN label="Quality" val="—" color={CALEN.ink4}/>
          </div>
          <div style={{ fontSize: 11, color: CALEN.ink3, marginBottom: 5, letterSpacing: 0.4,
            textTransform: 'uppercase', fontWeight: 600 }}>Auto Summary</div>
          <div style={{ fontSize: 13, color: CALEN.ink2, lineHeight: 1.55, paddingBottom: 14,
            borderBottom: `1px solid ${CALEN.dividerSoft}`, marginBottom: 12 }}>
            {log.summary}
          </div>
          <button style={{ width: '100%', padding: '11px 0', borderRadius: 12, background: CALEN.accent,
            border: 'none', color: '#FFF', fontSize: 14, fontWeight: 600 }}>
            Write & submit log →
          </button>
        </>
      )}

      {submitted && (
        <>
          <div style={{ display: 'flex', gap: 14, marginBottom: 14, alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 10, color: CALEN.ink3, fontWeight: 600, letterSpacing: 0.4, textTransform: 'uppercase' }}>Quality</div>
              <div style={{ display: 'inline-flex', alignItems: 'baseline', gap: 4, marginTop: 4 }}>
                <span style={{ fontFamily: CALEN.serif, fontSize: 38, fontWeight: 600, color: CALEN.green,
                  letterSpacing: -1, lineHeight: 1 }}>{log.qualityScore}</span>
                <span style={{ fontSize: 12, color: CALEN.ink3 }}>/ 100</span>
              </div>
              <div style={{ fontSize: 11, color: CALEN.green, marginTop: 4, fontWeight: 600 }}>{log.grade}</div>
            </div>
            <StatEN label="Hours" val={`${cfmtEN(log.totalHours)}h`} color={CALEN.blue}/>
            <StatEN label="Items" val={log.itemCount} color={CALEN.ink}/>
          </div>

          <div style={{ fontSize: 11, color: CALEN.ink3, marginBottom: 5, letterSpacing: 0.4,
            textTransform: 'uppercase', fontWeight: 600 }}>Notes</div>
          <div style={{ fontSize: 12.5, color: CALEN.ink2, lineHeight: 1.55, paddingBottom: 12,
            borderBottom: `1px solid ${CALEN.dividerSoft}`, marginBottom: 10 }}>
            {log.notes}
          </div>

          <div style={{ fontSize: 11, color: CALEN.ink3, marginBottom: 8, letterSpacing: 0.4,
            textTransform: 'uppercase', fontWeight: 600 }}>Suggestions</div>
          {log.issues.map((iss, i) => (
            <div key={i} style={{ padding: '8px 10px', background: iss.tone === 'warn' ? CALEN.warnSoft : CALEN.blueSoft,
              borderRadius: 8, marginBottom: 6 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: iss.tone === 'warn' ? CALEN.warn : CALEN.blueDeep }}>
                · {iss.label}
              </div>
              <div style={{ fontSize: 11, color: CALEN.ink2, marginTop: 2 }}>{iss.tip}</div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
function StatEN({ label, val, color }) {
  return (
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 10, color: CALEN.ink3, fontWeight: 600, letterSpacing: 0.4, textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontFamily: CALEN.serif, fontSize: 17, fontWeight: 600, color: color || CALEN.ink,
        marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>{val}</div>
    </div>
  );
}

function CalendarMonthSheetEN() {
  const days = [];
  for (let i = 0; i < 4; i++) days.push({ d: 27 + i, prev: true });
  for (let i = 1; i <= 31; i++) days.push({ d: i });
  while (days.length % 7 !== 0) days.push({ d: days.length - 30, next: true });
  const hotDays = { 12: { color: CALEN.purple }, 14: { color: CALEN.blue, today: true },
    15: { color: CALEN.accent }, 20: { color: CALEN.warn }, 22: { color: CALEN.green },
    28: { color: CALEN.accent }, 30: { color: CALEN.purple } };

  return (
    <div style={{ background: 'rgba(26,26,26,.42)', height: '100%', position: 'relative',
      fontFamily: CALEN.sans, color: CALEN.ink }}>
      <div style={{ position: 'absolute', inset: 0, opacity: 0.3 }}><CalendarAgendaEN/></div>
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, background: CALEN.bg,
        borderRadius: '20px 20px 0 0', padding: '14px 0 26px', maxHeight: '80%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ width: 36, height: 4, background: CALEN.divider, borderRadius: 2, margin: '0 auto 14px' }}/>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px 12px' }}>
          <span style={{ color: CALEN.ink3, fontSize: 18 }}>‹</span>
          <span style={{ fontFamily: CALEN.serif, fontSize: 19, fontWeight: 600 }}>May 2026</span>
          <span style={{ color: CALEN.ink3, fontSize: 18 }}>›</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', padding: '0 12px',
          fontSize: 10, color: CALEN.ink3, fontWeight: 600, marginBottom: 6, letterSpacing: 0.4 }}>
          {['M','T','W','T','F','S','S'].map((w, i) => (
            <div key={i} style={{ textAlign: 'center', color: i > 4 ? CALEN.ink4 : CALEN.ink3 }}>{w}</div>
          ))}
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 12px 12px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2 }}>
            {days.map((d, i) => {
              const hot = !d.prev && !d.next && hotDays[d.d];
              const today = hot && hot.today;
              const isWeekend = i % 7 === 5 || i % 7 === 6;
              return (
                <div key={i} style={{ aspectRatio: '1 / 1.05', display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center', padding: 4,
                  background: today ? CALEN.ink : 'transparent',
                  borderRadius: today ? 10 : 0,
                  color: today ? '#FFF' : (d.prev || d.next) ? CALEN.ink4 : isWeekend ? CALEN.ink4 : CALEN.ink }}>
                  <span style={{ fontSize: 13, fontWeight: today ? 700 : 500, fontFamily: CALEN.serif,
                    fontVariantNumeric: 'tabular-nums' }}>{d.d}</span>
                  {hot && !today && <span style={{ marginTop: 3, width: 5, height: 5, borderRadius: 2.5, background: hot.color }}/>}
                  {today && <span style={{ marginTop: 2, width: 4, height: 4, borderRadius: 2, background: '#FFF' }}/>}
                </div>
              );
            })}
          </div>
        </div>
        <div style={{ padding: '10px 16px 0', borderTop: `1px solid ${CALEN.dividerSoft}`,
          fontSize: 11, color: CALEN.ink3, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <LegendEN color={CALEN.blue}   label="Meeting"/>
          <LegendEN color={CALEN.accent} label="Visit"/>
          <LegendEN color={CALEN.purple} label="Training"/>
          <LegendEN color={CALEN.warn}   label="Business"/>
          <LegendEN color={CALEN.green}  label="Service"/>
        </div>
      </div>
    </div>
  );
}
function LegendEN({ color, label }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <span style={{ width: 6, height: 6, borderRadius: 3, background: color }}/>
      <span>{label}</span>
    </span>
  );
}

function CalendarScopeSheetEN() {
  const others = [
    { id: 'gxh', name: 'Guo Xiaohui',  count: 12 },
    { id: 'dw',  name: 'Dong Wei',     count: 6 },
    { id: 'kgj', name: 'Kang Guojie',  count: 9 },
    { id: 'sy',  name: 'Shi Yugeng',   count: 4 },
    { id: 'zh',  name: 'Zhang He',     count: 8 },
    { id: 'hzy', name: 'He Zhiyou',    count: 5 },
  ];
  return (
    <div style={{ background: 'rgba(26,26,26,.42)', height: '100%', position: 'relative',
      fontFamily: CALEN.sans, color: CALEN.ink }}>
      <div style={{ position: 'absolute', inset: 0, opacity: 0.3 }}><CalendarAgendaEN/></div>
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, background: CALEN.bg,
        borderRadius: '20px 20px 0 0', padding: '14px 0 26px', maxHeight: '80%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ width: 36, height: 4, background: CALEN.divider, borderRadius: 2, margin: '0 auto 14px' }}/>
        <div style={{ padding: '0 20px 14px' }}>
          <div style={{ fontFamily: CALEN.serif, fontSize: 20, fontWeight: 600 }}>Switch Calendar</div>
          <div style={{ fontSize: 12, color: CALEN.ink3, marginTop: 3 }}>View any teammate's calendar within your permission scope</div>
        </div>
        <div style={{ padding: '0 16px 12px' }}>
          <div style={{ background: CALEN.card, borderRadius: 10, padding: '9px 12px',
            border: `1px solid ${CALEN.divider}`, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: CALEN.ink3 }}>⌕</span>
            <span style={{ fontSize: 13, color: CALEN.ink4 }}>Search by name</span>
          </div>
        </div>
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <div style={{ padding: '0 20px 6px', fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6,
            fontWeight: 600, textTransform: 'uppercase' }}>You</div>
          <CalPersonRowEN name="Zhang Xiang (You)" sub="Product & Solutions" count={5} selected/>
          <div style={{ padding: '14px 20px 6px', fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6,
            fontWeight: 600, textTransform: 'uppercase', display: 'flex', justifyContent: 'space-between' }}>
            <span>Teammates · 6</span><span>44 items total</span>
          </div>
          {others.map(p => <CalPersonRowEN key={p.id} name={p.name} sub="Product & Solutions" count={p.count}/>)}
        </div>
      </div>
    </div>
  );
}
function CalPersonRowEN({ name, sub, count, selected }) {
  const init = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  return (
    <div style={{ padding: '11px 20px', display: 'flex', alignItems: 'center', gap: 12,
      borderBottom: `1px solid ${CALEN.dividerSoft}`,
      background: selected ? CALEN.accentSoft + '88' : 'transparent' }}>
      <span style={{ width: 36, height: 36, borderRadius: 18,
        background: selected ? '#3A6FB7' : '#7B5BAC',
        color: '#FFF', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 12, fontWeight: 700, letterSpacing: 0.3 }}>{init}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{name}</span>
          {selected && <span style={{ fontSize: 9.5, color: CALEN.accent, background: CALEN.accentSoft,
            padding: '1px 5px', borderRadius: 3, fontWeight: 700, letterSpacing: 0.4, textTransform: 'uppercase' }}>Current</span>}
        </div>
        <div style={{ fontSize: 11.5, color: CALEN.ink3, marginTop: 2 }}>{sub}</div>
      </div>
      <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: 14, fontWeight: 600, fontFamily: CALEN.serif }}>{count}</div>
        <div style={{ fontSize: 9, color: CALEN.ink4, textTransform: 'uppercase', letterSpacing: 0.3 }}>This Week</div>
      </div>
      <span style={{ color: CALEN.ink4, fontSize: 14 }}>›</span>
    </div>
  );
}

Object.assign(window, { CalendarAgendaEN, CalendarAgendaSubmittedEN, CalendarMonthSheetEN, CalendarScopeSheetEN });
