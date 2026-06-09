// PMA · Work Calendar (EN) — Create item, Type picker, Daily log submit, Item detail

function CALENSection({ title, action }) {
  return (
    <div style={{ padding: '18px 20px 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
      <div style={{ fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6, fontWeight: 600, textTransform: 'uppercase' }}>{title}</div>
      {action && <div style={{ fontSize: 12, color: CALEN.accent, fontWeight: 600 }}>{action}</div>}
    </div>
  );
}

function CalendarItemCreateEN({ filled = false } = {}) {
  const type = filled ? calTypeEN('meeting') : null;
  return (
    <div style={{ background: CALEN.bg, height: '100%', fontFamily: CALEN.sans, color: CALEN.ink, position: 'relative' }}>
      <CALENStatusPad/>
      <div style={{ position: 'absolute', top: STATUS_PAD_CALEN, left: 0, right: 0, height: 52,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 16px', background: CALEN.bg, borderBottom: `1px solid ${CALEN.divider}`, zIndex: 10 }}>
        <span style={{ fontSize: 14, color: CALEN.ink3 }}>Cancel</span>
        <span style={{ fontSize: 15, fontWeight: 600 }}>New Work Item</span>
        <span style={{ fontSize: 14, color: filled ? CALEN.accent : CALEN.ink4, fontWeight: 600 }}>Create</span>
      </div>

      <div style={{ paddingTop: STATUS_PAD_CALEN + 52, paddingBottom: 30, height: '100%', overflow: 'auto' }}>
        <div style={{ padding: '20px 20px 4px' }}>
          <div style={{ fontSize: 11, color: CALEN.ink3, fontWeight: 600, letterSpacing: 0.4,
            textTransform: 'uppercase', marginBottom: 8 }}>Type · Title <span style={{ color: CALEN.red }}>*</span></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px',
            background: CALEN.card, borderRadius: 10, border: `1px solid ${CALEN.divider}` }}>
            {filled ? (
              <span style={{ fontSize: 11, color: type.color, background: type.bg, padding: '2px 8px',
                borderRadius: 4, fontWeight: 700, letterSpacing: 0.3, flexShrink: 0, textTransform: 'uppercase' }}>{type.label}</span>
            ) : (
              <span style={{ fontSize: 11, color: CALEN.ink3, background: CALEN.dividerSoft, padding: '2px 8px',
                borderRadius: 4, fontWeight: 600, flexShrink: 0, textTransform: 'uppercase' }}>Other ▾</span>
            )}
            <span style={{ color: CALEN.ink4, fontSize: 13 }}>–</span>
            <span style={{ flex: 1, fontSize: 14,
              color: filled ? CALEN.ink : CALEN.ink4, fontWeight: filled ? 500 : 400 }}>
              {filled ? 'Tech & Product Sync · push SG MCP' : 'Enter work content…'}
            </span>
          </div>
        </div>

        <CALENSection title="Date & Time"/>
        <div style={{ padding: '0 16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <FieldEN label="Start Date" req val={filled ? '2026/05/14' : '2026/05/01'}/>
          <FieldEN label="End Date" hint="Optional · multi-day" val={null}/>
        </div>
        <div style={{ padding: '12px 20px 0', display: 'flex', gap: 18 }}>
          <CheckEN label="All-day"/><CheckEN label="Business trip"/>
        </div>
        <div style={{ padding: '10px 16px 0', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <FieldEN label="Start Time" val={filled ? '09:00' : '21:00'}/>
          <FieldEN label="End Time" val={filled ? '10:00' : '22:00'}/>
        </div>
        <div style={{ padding: '14px 16px 0' }}>
          <FieldEN label="Estimated (hours)" val={filled ? '1.0' : '1.0'} stepper/>
        </div>

        <CALENSection title="Links (optional)"/>
        <div style={{ background: CALEN.card, borderTop: `1px solid ${CALEN.dividerSoft}`,
          borderBottom: `1px solid ${CALEN.dividerSoft}` }}>
          <RowLinkEN label="Project"  val={filled ? 'SG MCP' : null} accent={filled}/>
          <RowLinkEN label="Customer" val={null} last/>
        </div>

        <CALENSection title="Action Log"/>
        <div style={{ margin: '0 16px 14px', padding: 14, background: CALEN.card,
          borderRadius: 12, border: `1px solid ${CALEN.divider}`,
          fontSize: 13, color: filled ? CALEN.ink2 : CALEN.ink4, minHeight: 80, lineHeight: 1.6 }}>
          {filled
            ? 'Sync MCP Phase-1 go-live; confirm deployment path with Zhang He and He Zhiyou.'
            : 'Log work content, communication…'}
        </div>

        <CALENSection title="Attachments"/>
        <div style={{ margin: '0 16px', display: 'flex', gap: 8 }}>
          <TagEN>📎 Choose file</TagEN>
          <TagEN>📷 Camera</TagEN>
        </div>

        <CALENSection title="Shared with"/>
        <div style={{ margin: '0 16px', display: 'flex', gap: 8 }}>
          {filled && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 9px 4px 4px',
              borderRadius: 14, background: CALEN.dividerSoft, fontSize: 12 }}>
              <span style={{ width: 18, height: 18, borderRadius: 9, background: '#7B5BAC', color: '#FFF',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, fontWeight: 700 }}>ZH</span>
              Zhang He
            </span>
          )}
          <span style={{ fontSize: 12, color: CALEN.ink4, padding: '4px 10px',
            border: `1px dashed ${CALEN.divider}`, borderRadius: 14 }}>+ Add</span>
        </div>
      </div>
    </div>
  );
}
function CalendarItemCreateFilledEN() { return <CalendarItemCreateEN filled/>; }

function FieldEN({ label, val, req, hint, stepper }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: CALEN.ink3, fontWeight: 600, marginBottom: 6,
        textTransform: 'uppercase', letterSpacing: 0.4,
        display: 'flex', alignItems: 'baseline', gap: 4 }}>
        <span>{label}{req && <span style={{ color: CALEN.red, marginLeft: 3 }}>*</span>}</span>
        {hint && <span style={{ fontSize: 10, color: CALEN.ink4, fontWeight: 400, textTransform: 'none' }}>{hint}</span>}
      </div>
      <div style={{ padding: '9px 12px', background: CALEN.card, borderRadius: 8,
        border: `1px solid ${CALEN.divider}`, display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ flex: 1, fontSize: 14, color: val ? CALEN.ink : CALEN.ink4,
          fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{val || 'Select'}</span>
        {stepper ? (
          <div style={{ display: 'inline-flex', flexDirection: 'column', gap: 1 }}>
            <span style={{ fontSize: 9, color: CALEN.ink3 }}>▲</span>
            <span style={{ fontSize: 9, color: CALEN.ink3 }}>▼</span>
          </div>
        ) : <span style={{ fontSize: 12, color: CALEN.ink4 }}>📅</span>}
      </div>
    </div>
  );
}
function CheckEN({ label }) {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 13, color: CALEN.ink2 }}>
      <span style={{ width: 16, height: 16, borderRadius: 4, border: `1.5px solid ${CALEN.divider}` }}/>
      {label}
    </div>
  );
}
function RowLinkEN({ label, val, accent, last }) {
  return (
    <div style={{ padding: '13px 20px', display: 'flex', gap: 14,
      borderBottom: last ? 'none' : `1px solid ${CALEN.dividerSoft}` }}>
      <div style={{ width: 90, fontSize: 12, color: CALEN.ink3, paddingTop: 1, flexShrink: 0 }}>{label}</div>
      <div style={{ flex: 1, fontSize: 13.5,
        color: val ? (accent ? CALEN.accent : CALEN.ink) : CALEN.ink4,
        fontWeight: val && accent ? 500 : 400 }}>{val || 'Tap to select'}</div>
      <span style={{ color: CALEN.ink4 }}>›</span>
    </div>
  );
}
function TagEN({ children }) {
  return (
    <span style={{ padding: '8px 14px', borderRadius: 8, background: CALEN.card,
      border: `1px solid ${CALEN.divider}`, fontSize: 12, color: CALEN.ink2,
      display: 'inline-flex', alignItems: 'center', gap: 6 }}>{children}</span>
  );
}

function CalendarTypePickerSheetEN() {
  return (
    <div style={{ background: 'rgba(26,26,26,.42)', height: '100%', position: 'relative',
      fontFamily: CALEN.sans, color: CALEN.ink }}>
      <div style={{ position: 'absolute', inset: 0, opacity: 0.3 }}><CalendarItemCreateEN/></div>
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, background: CALEN.bg,
        borderRadius: '20px 20px 0 0', padding: '14px 0 26px', maxHeight: '82%',
        display: 'flex', flexDirection: 'column' }}>
        <div style={{ width: 36, height: 4, background: CALEN.divider, borderRadius: 2, margin: '0 auto 14px' }}/>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px 12px' }}>
          <span style={{ fontSize: 13, color: CALEN.ink3 }}>Cancel</span>
          <span style={{ fontFamily: CALEN.serif, fontSize: 18, fontWeight: 600 }}>Select Type</span>
          <span style={{ fontSize: 13, color: CALEN.accent, fontWeight: 600 }}>Done</span>
        </div>
        <div style={{ padding: '0 16px 12px', display: 'flex', gap: 6, overflowX: 'auto' }}>
          {CALEN_TYPE_GROUPS.map((g, i) => (
            <span key={g.id} style={{ padding: '6px 12px', borderRadius: 999, fontSize: 12,
              fontWeight: i === 1 ? 600 : 500,
              background: i === 1 ? CALEN.ink : CALEN.card,
              color: i === 1 ? '#FFF' : CALEN.ink2,
              border: i === 1 ? 'none' : `1px solid ${CALEN.divider}`,
              whiteSpace: 'nowrap', flexShrink: 0 }}>{g.label}</span>
          ))}
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 16px 8px' }}>
          <div style={{ fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6, fontWeight: 600,
            textTransform: 'uppercase', padding: '6px 4px 10px' }}>Sales · 4 types</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
            {CALEN_TYPE_GROUPS[1].types.map((t, i) => (
              <div key={t.id} style={{ padding: '11px 12px',
                background: i === 0 ? t.bg : CALEN.card,
                border: i === 0 ? `1.5px solid ${t.color}` : `1px solid ${CALEN.divider}`,
                borderRadius: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ width: 8, height: 8, borderRadius: 4, background: t.color, flexShrink: 0 }}/>
                <span style={{ fontSize: 13, fontWeight: i === 0 ? 600 : 500,
                  color: i === 0 ? t.color : CALEN.ink }}>{t.label}</span>
                {i === 0 && <span style={{ marginLeft: 'auto', color: t.color, fontSize: 12, fontWeight: 700 }}>✓</span>}
              </div>
            ))}
          </div>
          {CALEN_TYPE_GROUPS.filter((_, i) => i !== 1).map(g => (
            <div key={g.id}>
              <div style={{ fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6, fontWeight: 600,
                textTransform: 'uppercase', padding: '16px 4px 8px' }}>{g.label} · {g.types.length}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {g.types.map(t => (
                  <span key={t.id} style={{ padding: '5px 11px', borderRadius: 999, fontSize: 12,
                    background: t.bg, color: t.color, fontWeight: 600 }}>{t.label}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function DailyLogSubmitEN() {
  return (
    <div style={{ background: CALEN.bg, height: '100%', fontFamily: CALEN.sans, color: CALEN.ink, position: 'relative' }}>
      <CALENStatusPad/>
      <div style={{ position: 'absolute', top: STATUS_PAD_CALEN, left: 0, right: 0, height: 52,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 16px', background: CALEN.bg, borderBottom: `1px solid ${CALEN.divider}`, zIndex: 10 }}>
        <span style={{ fontSize: 14, color: CALEN.ink3 }}>Cancel</span>
        <span style={{ fontSize: 15, fontWeight: 600 }}>Write Daily Log</span>
        <span style={{ fontSize: 14, color: CALEN.accent, fontWeight: 600 }}>Submit</span>
      </div>
      <div style={{ paddingTop: STATUS_PAD_CALEN + 52, paddingBottom: 30, height: '100%', overflow: 'auto' }}>
        <div style={{ padding: '20px 20px 4px' }}>
          <div style={{ fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6, fontWeight: 600, textTransform: 'uppercase' }}>
            Thursday · 2026/05/14
          </div>
          <div style={{ fontFamily: CALEN.serif, fontSize: 24, fontWeight: 600, marginTop: 4 }}>Daily Log · May 14</div>
        </div>
        <div style={{ padding: '14px 16px', display: 'flex', gap: 10 }}>
          {[
            { l: 'Items', v: '5', c: CALEN.ink },
            { l: 'Hours', v: '7.5h', c: CALEN.blue },
            { l: 'Types', v: '4', c: CALEN.purple },
          ].map((s, i) => (
            <div key={i} style={{ flex: 1, padding: '10px 12px', background: CALEN.card,
              borderRadius: 10, border: `1px solid ${CALEN.divider}` }}>
              <div style={{ fontSize: 10, color: CALEN.ink3, fontWeight: 600, letterSpacing: 0.4, textTransform: 'uppercase' }}>{s.l}</div>
              <div style={{ fontFamily: CALEN.serif, fontSize: 19, fontWeight: 600,
                color: s.c, marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>{s.v}</div>
            </div>
          ))}
        </div>

        <CALENSection title="Auto Summary · system generated"/>
        <div style={{ margin: '0 16px', padding: '12px 14px', background: CALEN.blueSoft,
          borderRadius: 10, border: `1px solid #DCE6F2` }}>
          <div style={{ fontSize: 13, color: CALEN.ink, lineHeight: 1.65 }}>
            Today: <strong>5</strong> work items — 1 customer visit (Shanghai Baoshan), 2 cross-team meetings,
            1 tech support (SG MCP), 1 admin. Total <strong>7.5 hours</strong>.
          </div>
          <div style={{ fontSize: 11, color: CALEN.blueDeep, marginTop: 6, fontWeight: 600 }}>
            ⚡ Auto-generated from your work items · edit below in Notes
          </div>
        </div>

        <CALENSection title="Notes"/>
        <div style={{ margin: '0 16px 14px', padding: 14, background: CALEN.card,
          borderRadius: 12, border: `1.5px solid ${CALEN.accent}`,
          fontSize: 13, color: CALEN.ink, minHeight: 100, lineHeight: 1.65 }}>
          On the customer visit, found the on-site switchboard differs from drawings. Logged to project follow-up.
          <span style={{ display: 'inline-block', width: 1.5, height: 16, background: CALEN.accent,
            marginLeft: 2, animation: 'calEnBlink 1s infinite', verticalAlign: 'middle' }}/>
          <style>{`@keyframes calEnBlink{0%,49%{opacity:1}50%,100%{opacity:0}}`}</style>
        </div>

        <div style={{ padding: '0 20px 4px', fontSize: 11, color: CALEN.ink3,
          letterSpacing: 0.4, fontWeight: 600, textTransform: 'uppercase' }}>Mentions · Links</div>
        <div style={{ padding: '8px 16px 0', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {['@ Zhang He', '@ He Zhiyou', '# SG MCP', '# Shanghai Baoshan'].map(c => {
            const isAt = c.startsWith('@');
            return (
              <span key={c} style={{ padding: '4px 10px', borderRadius: 999, fontSize: 12,
                background: isAt ? CALEN.purpleSoft : CALEN.accentSoft,
                color: isAt ? CALEN.purple : CALEN.accent, fontWeight: 600 }}>{c}</span>
            );
          })}
          <span style={{ padding: '4px 10px', borderRadius: 999, fontSize: 12, color: CALEN.ink4,
            border: `1px dashed ${CALEN.divider}` }}>+ Add</span>
        </div>

        <div style={{ margin: '20px 16px 0', padding: '11px 12px', background: CALEN.warnSoft,
          borderRadius: 8, fontSize: 12, color: CALEN.warn, lineHeight: 1.55 }}>
          ⓘ Items cannot be edited after submit · Quality score is computed from item completeness, description length, and link coverage
        </div>
      </div>
    </div>
  );
}

function WorkItemDetailSheetEN({ completed = false } = {}) {
  const it = CALEN_ITEMS_TODAY[1];
  const t = calTypeEN(it.type);
  return (
    <div style={{ background: 'rgba(26,26,26,.42)', height: '100%', position: 'relative',
      fontFamily: CALEN.sans, color: CALEN.ink }}>
      <div style={{ position: 'absolute', inset: 0, opacity: 0.3 }}><CalendarAgendaEN/></div>
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, background: CALEN.bg,
        borderRadius: '20px 20px 0 0', padding: '14px 0 22px', maxHeight: '82%',
        display: 'flex', flexDirection: 'column' }}>
        <div style={{ width: 36, height: 4, background: CALEN.divider, borderRadius: 2, margin: '0 auto 14px' }}/>
        <div style={{ padding: '0 20px 12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ fontFamily: CALEN.serif, fontSize: 20, fontWeight: 600 }}>Work Item</span>
            <span style={{ fontSize: 10, color: completed ? CALEN.green : CALEN.blue,
              background: completed ? CALEN.greenSoft : CALEN.blueSoft,
              padding: '2px 7px', borderRadius: 4, fontWeight: 700, textTransform: 'uppercase' }}>
              {completed ? 'Done' : 'In Progress'}
            </span>
          </div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <span style={{ fontSize: 11, color: t.color, background: t.bg, padding: '2px 7px',
              borderRadius: 3, fontWeight: 700, letterSpacing: 0.3, textTransform: 'uppercase' }}>{t.label}</span>
          </div>
          <div style={{ fontFamily: CALEN.serif, fontSize: 22, fontWeight: 600, lineHeight: 1.3, marginTop: 4 }}>{it.title}</div>
          <div style={{ fontSize: 12.5, color: CALEN.ink3, marginTop: 4 }}>{it.sub}</div>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
            <MetaCardEN label="Date" val="2026-05-14"/>
            <MetaCardEN label="Time" val={`${it.start} – ${it.end}`}/>
            <MetaCardEN label="Duration" val={`${cfmtEN(it.hours)} h`} accent/>
            <MetaCardEN label="Status" val={completed ? 'Done' : 'In Progress'} green={completed} accent={completed}/>
          </div>
          {(it.project || it.customer) && (
            <>
              <div style={{ fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6, fontWeight: 600, textTransform: 'uppercase', marginBottom: 8 }}>Links</div>
              <div style={{ background: CALEN.card, borderRadius: 10, border: `1px solid ${CALEN.divider}`,
                padding: '10px 14px', marginBottom: 12 }}>
                {it.project && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13,
                    paddingBottom: 6, borderBottom: it.customer ? `1px solid ${CALEN.dividerSoft}` : 'none',
                    marginBottom: it.customer ? 6 : 0 }}>
                    <span style={{ color: CALEN.ink3 }}>Project</span>
                    <span style={{ color: CALEN.accent, fontWeight: 500 }}>#{it.project} ›</span>
                  </div>
                )}
                {it.customer && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span style={{ color: CALEN.ink3 }}>Customer</span>
                    <span style={{ color: CALEN.accent, fontWeight: 500 }}>{it.customer} ›</span>
                  </div>
                )}
              </div>
            </>
          )}
          <div style={{ fontSize: 11, color: CALEN.ink3, letterSpacing: 0.6, fontWeight: 600,
            textTransform: 'uppercase', marginBottom: 8 }}>Action Log</div>
          <div style={{ background: CALEN.card, borderRadius: 10, border: `1px solid ${CALEN.divider}`,
            padding: '12px 14px', fontSize: 13, color: CALEN.ink2, lineHeight: 1.65 }}>
            Arrived on site at 10:30. Met with Li Hua (Equipment) and Liu Liang (Operations Director).
            Initial requirements confirmed; detailed proposal to follow.
          </div>
        </div>
        <div style={{ padding: '14px 16px 0', borderTop: `1px solid ${CALEN.divider}`,
          display: 'flex', gap: 10, flexShrink: 0, marginTop: 14 }}>
          <button style={{ flex: 1, height: 44, borderRadius: 22, background: CALEN.card,
            border: `1.5px solid ${CALEN.divider}`, color: CALEN.ink2, fontSize: 13.5, fontWeight: 600 }}>Edit</button>
          {completed ? (
            <button style={{ flex: 2, height: 44, borderRadius: 22, background: CALEN.card,
              border: `1.5px solid ${CALEN.red}`, color: CALEN.red, fontSize: 13.5, fontWeight: 600 }}>Undo Complete</button>
          ) : (
            <button style={{ flex: 2, height: 44, borderRadius: 22, background: CALEN.green,
              border: 'none', color: '#FFF', fontSize: 13.5, fontWeight: 600 }}>Mark Complete</button>
          )}
        </div>
      </div>
    </div>
  );
}
function MetaCardEN({ label, val, accent, green }) {
  return (
    <div style={{ padding: '10px 12px', background: CALEN.card, borderRadius: 10,
      border: `1px solid ${CALEN.divider}` }}>
      <div style={{ fontSize: 10, color: CALEN.ink3, fontWeight: 600, letterSpacing: 0.4, textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontFamily: CALEN.serif, fontSize: 15, fontWeight: 600,
        color: green ? CALEN.green : (accent ? CALEN.blue : CALEN.ink), marginTop: 3,
        fontVariantNumeric: 'tabular-nums' }}>{val}</div>
    </div>
  );
}
function WorkItemDetailSheetCompletedEN() { return <WorkItemDetailSheetEN completed/>; }

Object.assign(window, { CalendarItemCreateEN, CalendarItemCreateFilledEN,
  CalendarTypePickerSheetEN, DailyLogSubmitEN,
  WorkItemDetailSheetEN, WorkItemDetailSheetCompletedEN });
