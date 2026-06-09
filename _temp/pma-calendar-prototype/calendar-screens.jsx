// PMA · 工作日历 — Agenda / 列表 / 月视图 sheet

function CALNav({ title, sub, leftLabel = '我的', right }) {
  return (
    <div style={{ position: 'absolute', top: STATUS_PAD_CAL, left: 0, right: 0, height: 52,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 12px', background: CAL.bg, borderBottom: `1px solid ${CAL.divider}`, zIndex: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: CAL.ink2, fontSize: 14 }}>
        <span style={{ fontSize: 22, fontWeight: 300 }}>‹</span>
        <span>{leftLabel}</span>
      </div>
      <div style={{ textAlign: 'center', flex: 1 }}>
        <div style={{ fontSize: 15, fontWeight: 600, color: CAL.ink }}>{title}</div>
        {sub && <div style={{ fontSize: 10.5, color: CAL.ink3, marginTop: 1 }}>{sub}</div>}
      </div>
      <div style={{ minWidth: 40, textAlign: 'right' }}>{right}</div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 屏 1 · Agenda · 今日(默认)
// ════════════════════════════════════════════════════════════
function CalendarAgenda({ submitted = false } = {}) {
  const log = submitted ? CAL_DAILY_LOG_SUBMITTED : CAL_DAILY_LOG;
  return (
    <div style={{ background: CAL.bg, height: '100%', fontFamily: CAL.sans, color: CAL.ink, position: 'relative' }}>
      <CALStatusPad/>
      <div style={{ paddingBottom: 84, height: '100%', overflow: 'auto', boxSizing: 'border-box' }}>

        {/* hero */}
        <div style={{ padding: '28px 20px 14px', display: 'flex', alignItems: 'flex-start',
          justifyContent: 'space-between', gap: 14 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontFamily: CAL.serif, fontSize: 26, fontWeight: 600, letterSpacing: -0.3 }}>
                工作日历
              </span>
              <span style={{ fontSize: 16, color: CAL.ink3 }}>▾</span>
            </div>
            <div style={{ fontSize: 13, color: CAL.ink3, marginTop: 4 }}>
              我的日历 · 张翔 · 5 月共 32 项
            </div>
          </div>
          <div style={{ width: 36, height: 36, borderRadius: 18, background: CAL.ink, color: '#FFF',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 300,
            lineHeight: 1, flexShrink: 0 }}>+</div>
        </div>
        <div style={{ height: 1, background: CAL.divider }}/>

        {/* 月份切换 + 视图 toggle */}
        <div style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 16 }}>
            <span style={{ color: CAL.ink3, fontSize: 18 }}>‹</span>
            <span style={{ fontSize: 16, fontWeight: 600, fontFamily: CAL.serif }}>2026 年 5 月</span>
            <span style={{ color: CAL.ink3, fontSize: 18 }}>›</span>
          </div>
          <div style={{ display: 'flex', gap: 0, background: CAL.dividerSoft, padding: 2, borderRadius: 7,
            fontSize: 11.5, fontWeight: 600 }}>
            {['月', '周', '日'].map((v, i) => (
              <span key={v} style={{ padding: '5px 11px', borderRadius: 5,
                background: i === 1 ? CAL.card : 'transparent',
                color: i === 1 ? CAL.ink : CAL.ink3,
                boxShadow: i === 1 ? '0 1px 2px rgba(0,0,0,0.06)' : 'none' }}>{v}</span>
            ))}
          </div>
        </div>

        {/* 周日期条 */}
        <div style={{ display: 'flex', padding: '0 12px 14px', gap: 4 }}>
          {CAL_WEEK.map(d => {
            const sel = d.sel;
            return (
              <div key={d.d} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
                padding: '8px 0', borderRadius: 10,
                background: sel ? CAL.ink : 'transparent',
                color: sel ? '#FFF' : (d.weekend ? CAL.ink4 : CAL.ink2) }}>
                <span style={{ fontSize: 10, fontWeight: 500, letterSpacing: 0.3,
                  color: sel ? 'rgba(255,255,255,0.7)' : (d.weekend ? CAL.ink4 : CAL.ink3) }}>{d.w}</span>
                <span style={{ fontSize: 18, fontWeight: 600, fontFamily: CAL.serif, marginTop: 3 }}>{d.d}</span>
                {d.items > 0 && (
                  <span style={{ marginTop: 4, width: 4, height: 4, borderRadius: 2,
                    background: sel ? '#FFF' : CAL.accent }}/>
                )}
                {d.holiday && <span style={{ fontSize: 9, marginTop: 2,
                  color: sel ? 'rgba(255,255,255,0.85)' : CAL.red, fontWeight: 600 }}>{d.holiday}</span>}
              </div>
            );
          })}
        </div>

        {/* day hero */}
        <div style={{ padding: '4px 20px 6px', display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 11, color: CAL.ink3, letterSpacing: 0.6, fontWeight: 600, textTransform: 'uppercase' }}>
              周四 · 今天
            </div>
            <div style={{ fontFamily: CAL.serif, fontSize: 22, fontWeight: 600, marginTop: 2 }}>
              5 月 14 日 · {CAL_ITEMS_TODAY.length} 项工作
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 10, color: CAL.ink3 }}>累计工时</div>
            <div style={{ fontFamily: CAL.serif, fontSize: 18, fontWeight: 600, color: CAL.blue,
              fontVariantNumeric: 'tabular-nums' }}>{cfmt(log.totalHours)}h</div>
          </div>
        </div>

        {/* 工作项列表 */}
        <div style={{ background: CAL.card, marginTop: 6, borderTop: `1px solid ${CAL.dividerSoft}`,
          borderBottom: `1px solid ${CAL.dividerSoft}` }}>
          {CAL_ITEMS_TODAY.map((it, i) => <WorkItemRow key={it.id} item={it} last={i === CAL_ITEMS_TODAY.length - 1}/>)}
        </div>

        {/* 日报卡 */}
        <div style={{ padding: '18px 16px 0' }}>
          <DailyLogCard log={log} submitted={submitted}/>
        </div>
      </div>
    </div>
  );
}
function CalendarAgendaSubmitted() { return <CalendarAgenda submitted/>; }

// ─── 工作项行 ────────────────────────────────────────────
function WorkItemRow({ item, last }) {
  const t = calType(item.type);
  const done = item.status === 'completed';
  return (
    <div style={{ padding: '14px 20px', borderBottom: last ? 'none' : `1px solid ${CAL.dividerSoft}`,
      display: 'flex', alignItems: 'flex-start', gap: 12,
      opacity: done ? 0.55 : 1 }}>
      {/* 时间柱 */}
      <div style={{ width: 46, flexShrink: 0, textAlign: 'right', paddingTop: 1 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: CAL.ink, fontVariantNumeric: 'tabular-nums', fontFamily: CAL.serif }}>
          {item.start}
        </div>
        <div style={{ fontSize: 10, color: CAL.ink4, fontVariantNumeric: 'tabular-nums', marginTop: 1 }}>
          {item.end}
        </div>
      </div>
      {/* 色柱 */}
      <div style={{ width: 3, alignSelf: 'stretch', background: t.color, borderRadius: 2, flexShrink: 0 }}/>
      {/* 内容 */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 10, color: t.color, background: t.bg, padding: '1px 6px',
            borderRadius: 3, fontWeight: 700, letterSpacing: 0.3 }}>{t.label}</span>
          {item.dingtalk && (
            <span style={{ fontSize: 9, color: CAL.ink3, background: CAL.dividerSoft, padding: '1px 5px',
              borderRadius: 3, fontWeight: 600, letterSpacing: 0.3 }}>钉钉同步</span>
          )}
          {done && <span style={{ fontSize: 9.5, color: CAL.green, background: CAL.greenSoft, padding: '1px 5px',
            borderRadius: 3, fontWeight: 700, letterSpacing: 0.3 }}>✓ 已完成</span>}
        </div>
        <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4, lineHeight: 1.35,
          textDecoration: done ? 'line-through' : 'none' }}>{item.title}</div>
        <div style={{ fontSize: 11.5, color: CAL.ink3, marginTop: 3, lineHeight: 1.4 }}>{item.sub}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6, fontSize: 10.5, color: CAL.ink3, flexWrap: 'wrap' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
            <span>⏱</span>{cfmt(item.hours)}h
          </span>
          {item.project && (
            <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 3,
              background: CAL.accentSoft, color: CAL.accent, fontWeight: 600,
              maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              #{item.project}
            </span>
          )}
          {item.customer && (
            <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 3,
              background: CAL.tealSoft, color: CAL.teal, fontWeight: 600,
              maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.customer}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── 日报卡 ──────────────────────────────────────────────
function DailyLogCard({ log, submitted }) {
  const score = log.qualityScore;
  return (
    <div style={{ background: CAL.card, borderRadius: 14, border: `1px solid ${CAL.divider}`, padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 11, color: CAL.ink3, letterSpacing: 0.6, fontWeight: 600,
          textTransform: 'uppercase' }}>日报 · 5 月 14 日</span>
        {submitted ? (
          <span style={{ fontSize: 10, color: CAL.green, background: CAL.greenSoft, padding: '2px 7px',
            borderRadius: 3, fontWeight: 700 }}>已提交</span>
        ) : (
          <span style={{ fontSize: 10, color: CAL.warn, background: CAL.warnSoft, padding: '2px 7px',
            borderRadius: 3, fontWeight: 700 }}>草稿</span>
        )}
      </div>

      {!submitted && (
        <>
          <div style={{ display: 'flex', gap: 14, marginBottom: 12 }}>
            <Stat label="总工时" val={`${cfmt(log.totalHours)} h`} color={CAL.blue}/>
            <Stat label="工作项" val={log.itemCount} color={CAL.ink}/>
            <Stat label="质量分" val="—" color={CAL.ink4}/>
          </div>
          <div style={{ fontSize: 11, color: CAL.ink3, marginBottom: 5, letterSpacing: 0.4, textTransform: 'uppercase', fontWeight: 600 }}>
            自动摘要
          </div>
          <div style={{ fontSize: 13, color: CAL.ink2, lineHeight: 1.55, paddingBottom: 14,
            borderBottom: `1px solid ${CAL.dividerSoft}`, marginBottom: 12 }}>
            {log.summary}
          </div>
          <button style={{ width: '100%', padding: '11px 0', borderRadius: 12, background: CAL.accent,
            border: 'none', color: '#FFF', fontSize: 14, fontWeight: 600 }}>
            撰写并提交日报 →
          </button>
        </>
      )}

      {submitted && (
        <>
          <div style={{ display: 'flex', gap: 14, marginBottom: 14, alignItems: 'flex-start' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 10, color: CAL.ink3, fontWeight: 600, letterSpacing: 0.4 }}>质量分</div>
              <div style={{ display: 'inline-flex', alignItems: 'baseline', gap: 4, marginTop: 4 }}>
                <span style={{ fontFamily: CAL.serif, fontSize: 38, fontWeight: 600, color: CAL.green,
                  letterSpacing: -1, lineHeight: 1 }}>{score}</span>
                <span style={{ fontSize: 12, color: CAL.ink3 }}>/ 100</span>
              </div>
              <div style={{ fontSize: 11, color: CAL.green, marginTop: 4, fontWeight: 600 }}>{log.grade}</div>
            </div>
            <Stat label="总工时" val={`${cfmt(log.totalHours)}h`} color={CAL.blue}/>
            <Stat label="工作项" val={log.itemCount} color={CAL.ink}/>
          </div>

          <div style={{ fontSize: 11, color: CAL.ink3, marginBottom: 5, letterSpacing: 0.4,
            textTransform: 'uppercase', fontWeight: 600 }}>补充说明</div>
          <div style={{ fontSize: 12.5, color: CAL.ink2, lineHeight: 1.55, paddingBottom: 12,
            borderBottom: `1px solid ${CAL.dividerSoft}`, marginBottom: 10 }}>
            {log.notes}
          </div>

          <div style={{ fontSize: 11, color: CAL.ink3, marginBottom: 8, letterSpacing: 0.4,
            textTransform: 'uppercase', fontWeight: 600 }}>改进建议</div>
          {log.issues.map((iss, i) => (
            <div key={i} style={{ padding: '8px 10px', background: iss.tone === 'warn' ? CAL.warnSoft : CAL.blueSoft,
              borderRadius: 8, marginBottom: 6 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: iss.tone === 'warn' ? CAL.warn : CAL.blueDeep }}>
                · {iss.label}
              </div>
              <div style={{ fontSize: 11, color: CAL.ink2, marginTop: 2 }}>{iss.tip}</div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
function Stat({ label, val, color }) {
  return (
    <div style={{ flex: 1 }}>
      <div style={{ fontSize: 10, color: CAL.ink3, fontWeight: 600, letterSpacing: 0.4 }}>{label}</div>
      <div style={{ fontFamily: CAL.serif, fontSize: 17, fontWeight: 600, color: color || CAL.ink,
        marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>{val}</div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════
// 屏 2 · 月视图 sheet(从顶部切换器召出)
// ════════════════════════════════════════════════════════════
function CalendarMonthSheet() {
  // 5/1 是周五,5 月共 31 天
  const days = [];
  for (let i = 0; i < 4; i++) days.push({ d: 27 + i, prev: true });
  for (let i = 1; i <= 31; i++) days.push({ d: i });
  while (days.length % 7 !== 0) days.push({ d: days.length - 30, next: true });

  const hotDays = { 12: { color: CAL.purple }, 14: { color: CAL.blue, today: true },
    15: { color: CAL.accent }, 20: { color: CAL.warn }, 22: { color: CAL.green },
    28: { color: CAL.accent }, 30: { color: CAL.purple } };

  return (
    <div style={{ background: 'rgba(26,26,26,.42)', height: '100%', position: 'relative',
      fontFamily: CAL.sans, color: CAL.ink }}>
      <div style={{ position: 'absolute', inset: 0, opacity: 0.3 }}><CalendarAgenda/></div>

      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, background: CAL.bg,
        borderRadius: '20px 20px 0 0', padding: '14px 0 26px', maxHeight: '80%',
        display: 'flex', flexDirection: 'column' }}>
        <div style={{ width: 36, height: 4, background: CAL.divider, borderRadius: 2, margin: '0 auto 14px' }}/>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px 12px' }}>
          <span style={{ color: CAL.ink3, fontSize: 18, padding: '4px 6px' }}>‹</span>
          <span style={{ fontFamily: CAL.serif, fontSize: 19, fontWeight: 600 }}>2026 年 5 月</span>
          <span style={{ color: CAL.ink3, fontSize: 18, padding: '4px 6px' }}>›</span>
        </div>

        {/* 星期表头 */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', padding: '0 12px',
          fontSize: 10, color: CAL.ink3, fontWeight: 600, marginBottom: 6 }}>
          {['一','二','三','四','五','六','日'].map((w, i) => (
            <div key={i} style={{ textAlign: 'center', color: i > 4 ? CAL.ink4 : CAL.ink3 }}>{w}</div>
          ))}
        </div>

        {/* 日格 */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 12px 12px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 2 }}>
            {days.map((d, i) => {
              const hot = !d.prev && !d.next && hotDays[d.d];
              const today = hot && hot.today;
              const isWeekend = i % 7 === 5 || i % 7 === 6;
              return (
                <div key={i} style={{ aspectRatio: '1 / 1.05', display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center', padding: 4,
                  background: today ? CAL.ink : 'transparent',
                  borderRadius: today ? 10 : 0,
                  color: today ? '#FFF' :
                         (d.prev || d.next) ? CAL.ink4 :
                         isWeekend ? CAL.ink4 : CAL.ink }}>
                  <span style={{ fontSize: 13, fontWeight: today ? 700 : 500, fontFamily: CAL.serif,
                    fontVariantNumeric: 'tabular-nums' }}>{d.d}</span>
                  {hot && !today && (
                    <span style={{ marginTop: 3, width: 5, height: 5, borderRadius: 2.5,
                      background: hot.color }}/>
                  )}
                  {today && <span style={{ marginTop: 2, width: 4, height: 4, borderRadius: 2, background: '#FFF' }}/>}
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ padding: '10px 16px 0', borderTop: `1px solid ${CAL.dividerSoft}`,
          fontSize: 11, color: CAL.ink3, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <Legend color={CAL.blue}   label="会议"/>
          <Legend color={CAL.accent} label="客户拜访"/>
          <Legend color={CAL.purple} label="培训 / 行政"/>
          <Legend color={CAL.warn}   label="商务"/>
          <Legend color={CAL.green}  label="服务"/>
        </div>
      </div>
    </div>
  );
}
function Legend({ color, label }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <span style={{ width: 6, height: 6, borderRadius: 3, background: color }}/>
      <span>{label}</span>
    </span>
  );
}

// ════════════════════════════════════════════════════════════
// 屏 3 · 切换日历(他人/我的)sheet — 复用 Task scope 风格
// ════════════════════════════════════════════════════════════
function CalendarScopeSheet() {
  const others = [
    { id: 'gxh', name: '郭小会', count: 12 },
    { id: 'dw',  name: '董祎',   count: 6 },
    { id: 'kgj', name: '康国杰', count: 9 },
    { id: 'sy',  name: '施裕庚', count: 4 },
    { id: 'zh',  name: '张贺',   count: 8, mine: false },
    { id: 'hzy', name: '何志有', count: 5 },
  ];
  return (
    <div style={{ background: 'rgba(26,26,26,.42)', height: '100%', position: 'relative',
      fontFamily: CAL.sans, color: CAL.ink }}>
      <div style={{ position: 'absolute', inset: 0, opacity: 0.3 }}><CalendarAgenda/></div>

      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, background: CAL.bg,
        borderRadius: '20px 20px 0 0', padding: '14px 0 26px', maxHeight: '80%',
        display: 'flex', flexDirection: 'column' }}>
        <div style={{ width: 36, height: 4, background: CAL.divider, borderRadius: 2, margin: '0 auto 14px' }}/>

        <div style={{ padding: '0 20px 14px' }}>
          <div style={{ fontFamily: CAL.serif, fontSize: 20, fontWeight: 600 }}>切换日历</div>
          <div style={{ fontSize: 12, color: CAL.ink3, marginTop: 3 }}>查看权限范围内任意成员的工作日历</div>
        </div>

        <div style={{ padding: '0 16px 12px' }}>
          <div style={{ background: CAL.card, borderRadius: 10, padding: '9px 12px',
            border: `1px solid ${CAL.divider}`, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: CAL.ink3 }}>⌕</span>
            <span style={{ fontSize: 13, color: CAL.ink4 }}>搜索姓名</span>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <div style={{ padding: '0 20px 6px', fontSize: 11, color: CAL.ink3, letterSpacing: 0.6,
            fontWeight: 600, textTransform: 'uppercase' }}>本人</div>
          <CalPersonRow name="张翔(我)" sub="产品和解决方案部" count={5} selected/>

          <div style={{ padding: '14px 20px 6px', fontSize: 11, color: CAL.ink3, letterSpacing: 0.6,
            fontWeight: 600, textTransform: 'uppercase', display: 'flex', justifyContent: 'space-between' }}>
            <span>同事 · 6 人</span><span>共 44 项</span>
          </div>
          {others.map(p => <CalPersonRow key={p.id} name={p.name} sub="产品和解决方案部" count={p.count}/>)}
        </div>
      </div>
    </div>
  );
}
function CalPersonRow({ name, sub, count, selected }) {
  return (
    <div style={{ padding: '11px 20px', display: 'flex', alignItems: 'center', gap: 12,
      borderBottom: `1px solid ${CAL.dividerSoft}`,
      background: selected ? CAL.accentSoft + '88' : 'transparent' }}>
      <span style={{ width: 36, height: 36, borderRadius: 18,
        background: selected ? '#3A6FB7' : '#7B5BAC',
        color: '#FFF', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: CAL.serif, fontSize: 14, fontWeight: 700 }}>{name.charAt(0)}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 14, fontWeight: 600 }}>{name}</span>
          {selected && <span style={{ fontSize: 9.5, color: CAL.accent, background: CAL.accentSoft,
            padding: '1px 5px', borderRadius: 3, fontWeight: 700, letterSpacing: 0.3 }}>当前</span>}
        </div>
        <div style={{ fontSize: 11.5, color: CAL.ink3, marginTop: 2 }}>{sub}</div>
      </div>
      <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: 14, fontWeight: 600, fontFamily: CAL.serif }}>{count}</div>
        <div style={{ fontSize: 9, color: CAL.ink4 }}>本周</div>
      </div>
      <span style={{ color: CAL.ink4, fontSize: 14 }}>›</span>
    </div>
  );
}

Object.assign(window, { CalendarAgenda, CalendarAgendaSubmitted, CalendarMonthSheet, CalendarScopeSheet });
