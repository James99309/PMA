// PMA · 工作日历 — 新建/编辑工作项 + 类型分组 sheet + 日报提交 + 工作项详情

function CALSection({ title, action }) {
  return (
    <div style={{ padding: '18px 20px 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
      <div style={{ fontSize: 11, color: CAL.ink3, letterSpacing: 0.6, fontWeight: 600, textTransform: 'uppercase' }}>{title}</div>
      {action && <div style={{ fontSize: 12, color: CAL.accent, fontWeight: 600 }}>{action}</div>}
    </div>
  );
}

// ─── 1) 新建/编辑工作项 ───────────────────────────────────
function CalendarItemCreate({ filled = false } = {}) {
  const type = filled ? calType('meeting') : null;
  return (
    <div style={{ background: CAL.bg, height: '100%', fontFamily: CAL.sans, color: CAL.ink, position: 'relative' }}>
      <CALStatusPad/>
      <div style={{ position: 'absolute', top: STATUS_PAD_CAL, left: 0, right: 0, height: 52,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 16px', background: CAL.bg, borderBottom: `1px solid ${CAL.divider}`, zIndex: 10 }}>
        <span style={{ fontSize: 14, color: CAL.ink3 }}>取消</span>
        <span style={{ fontSize: 15, fontWeight: 600 }}>新建工作项</span>
        <span style={{ fontSize: 14, color: filled ? CAL.accent : CAL.ink4, fontWeight: 600 }}>创建</span>
      </div>

      <div style={{ paddingTop: STATUS_PAD_CAL + 52, paddingBottom: 30, height: '100%', overflow: 'auto', boxSizing: 'border-box' }}>
        {/* 类型 + 标题 */}
        <div style={{ padding: '20px 20px 4px' }}>
          <div style={{ fontSize: 11, color: CAL.ink3, fontWeight: 600, letterSpacing: 0.4,
            textTransform: 'uppercase', marginBottom: 8 }}>类型 · 标题 <span style={{ color: CAL.red }}>*</span></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px',
            background: CAL.card, borderRadius: 10, border: `1px solid ${CAL.divider}` }}>
            {filled ? (
              <span style={{ fontSize: 11, color: type.color, background: type.bg, padding: '2px 8px',
                borderRadius: 4, fontWeight: 700, letterSpacing: 0.3, flexShrink: 0 }}>
                {type.label}
              </span>
            ) : (
              <span style={{ fontSize: 11, color: CAL.ink3, background: CAL.dividerSoft, padding: '2px 8px',
                borderRadius: 4, fontWeight: 600, flexShrink: 0 }}>其他 ▾</span>
            )}
            <span style={{ color: CAL.ink4, fontSize: 13 }}>–</span>
            <span style={{ flex: 1, fontSize: 14,
              color: filled ? CAL.ink : CAL.ink4,
              fontWeight: filled ? 500 : 400 }}>
              {filled ? '与技术、产品团队会议 · 推进新加坡 MCP' : '请输入工作内容…'}
            </span>
          </div>
        </div>

        {/* 日期 */}
        <CALSection title="日期与时间"/>
        <div style={{ padding: '0 16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Field label="开始日期" req val={filled ? '2026/05/14' : '2026/05/01'}/>
          <Field label="结束日期" hint="可选,跨天用" val={null}/>
        </div>

        <div style={{ padding: '12px 20px 0', display: 'flex', gap: 18 }}>
          <Check label="全天事件" checked={false}/>
          <Check label="出差"     checked={false}/>
        </div>

        <div style={{ padding: '10px 16px 0', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Field label="开始时间" val={filled ? '09:00' : '21:00'}/>
          <Field label="结束时间" val={filled ? '10:00' : '22:00'}/>
        </div>

        <div style={{ padding: '14px 16px 0' }}>
          <Field label="预计时长(小时)" val={filled ? '1.0' : '1.0'} stepper/>
        </div>

        {/* 关联 */}
        <CALSection title="关联(可选)"/>
        <div style={{ background: CAL.card, borderTop: `1px solid ${CAL.dividerSoft}`,
          borderBottom: `1px solid ${CAL.dividerSoft}` }}>
          <RowLink label="关联项目" val={filled ? '新加坡 MCP 项目' : null} accent={filled}/>
          <RowLink label="关联客户" val={null} last/>
        </div>

        {/* 行动记录 */}
        <CALSection title="行动记录"/>
        <div style={{ margin: '0 16px 14px', padding: 14, background: CAL.card,
          borderRadius: 12, border: `1px solid ${CAL.divider}`,
          fontSize: 13, color: filled ? CAL.ink2 : CAL.ink4, minHeight: 80, lineHeight: 1.6 }}>
          {filled
            ? '同步 MCP 一期上线时间;与张贺、何志有确认部署路径。'
            : '记录工作内容、沟通情况…'}
        </div>

        {/* 附件 + 共享给 */}
        <CALSection title="附件"/>
        <div style={{ margin: '0 16px', display: 'flex', gap: 8 }}>
          <Tag>📎 选择文件</Tag>
          <Tag>📷 拍照</Tag>
        </div>

        <CALSection title="共享给"/>
        <div style={{ margin: '0 16px', display: 'flex', gap: 8 }}>
          {filled && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, padding: '4px 9px 4px 4px',
              borderRadius: 14, background: CAL.dividerSoft, fontSize: 12 }}>
              <span style={{ width: 18, height: 18, borderRadius: 9, background: '#7B5BAC', color: '#FFF',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700 }}>张</span>
              张贺
            </span>
          )}
          <span style={{ fontSize: 12, color: CAL.ink4, padding: '4px 10px',
            border: `1px dashed ${CAL.divider}`, borderRadius: 14 }}>+ 添加</span>
        </div>
      </div>
    </div>
  );
}
function CalendarItemCreateFilled() { return <CalendarItemCreate filled/>; }

function Field({ label, val, req, hint, stepper }) {
  return (
    <div>
      <div style={{ fontSize: 11, color: CAL.ink3, fontWeight: 600, marginBottom: 6,
        textTransform: 'uppercase', letterSpacing: 0.4,
        display: 'flex', alignItems: 'baseline', gap: 4 }}>
        <span>{label}{req && <span style={{ color: CAL.red, marginLeft: 3 }}>*</span>}</span>
        {hint && <span style={{ fontSize: 10, color: CAL.ink4, fontWeight: 400, textTransform: 'none' }}>{hint}</span>}
      </div>
      <div style={{ padding: '9px 12px', background: CAL.card, borderRadius: 8,
        border: `1px solid ${CAL.divider}`,
        display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ flex: 1, fontSize: 14, color: val ? CAL.ink : CAL.ink4,
          fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>
          {val || '选择'}
        </span>
        {stepper ? (
          <div style={{ display: 'inline-flex', flexDirection: 'column', gap: 1 }}>
            <span style={{ fontSize: 9, color: CAL.ink3 }}>▲</span>
            <span style={{ fontSize: 9, color: CAL.ink3 }}>▼</span>
          </div>
        ) : (
          <span style={{ fontSize: 12, color: CAL.ink4 }}>📅</span>
        )}
      </div>
    </div>
  );
}
function Check({ label, checked }) {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, fontSize: 13, color: CAL.ink2 }}>
      <span style={{ width: 16, height: 16, borderRadius: 4,
        border: `1.5px solid ${checked ? CAL.ink : CAL.divider}`,
        background: checked ? CAL.ink : 'transparent',
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
        {checked && <span style={{ color: '#FFF', fontSize: 10 }}>✓</span>}
      </span>
      {label}
    </div>
  );
}
function RowLink({ label, val, accent, last }) {
  return (
    <div style={{ padding: '13px 20px', display: 'flex', gap: 14,
      borderBottom: last ? 'none' : `1px solid ${CAL.dividerSoft}` }}>
      <div style={{ width: 90, fontSize: 12, color: CAL.ink3, paddingTop: 1, flexShrink: 0 }}>{label}</div>
      <div style={{ flex: 1, fontSize: 13.5,
        color: val ? (accent ? CAL.accent : CAL.ink) : CAL.ink4,
        fontWeight: val && accent ? 500 : 400 }}>
        {val || '点击选择'}
      </div>
      <span style={{ color: CAL.ink4 }}>›</span>
    </div>
  );
}
function Tag({ children }) {
  return (
    <span style={{ padding: '8px 14px', borderRadius: 8, background: CAL.card,
      border: `1px solid ${CAL.divider}`, fontSize: 12, color: CAL.ink2,
      display: 'inline-flex', alignItems: 'center', gap: 6 }}>{children}</span>
  );
}

// ─── 2) 类型分组选择 sheet ──────────────────────────────
function CalendarTypePickerSheet() {
  return (
    <div style={{ background: 'rgba(26,26,26,.42)', height: '100%', position: 'relative',
      fontFamily: CAL.sans, color: CAL.ink }}>
      <div style={{ position: 'absolute', inset: 0, opacity: 0.3 }}><CalendarItemCreate/></div>

      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, background: CAL.bg,
        borderRadius: '20px 20px 0 0', padding: '14px 0 26px', maxHeight: '82%',
        display: 'flex', flexDirection: 'column', boxShadow: '0 -10px 30px rgba(0,0,0,.18)' }}>
        <div style={{ width: 36, height: 4, background: CAL.divider, borderRadius: 2, margin: '0 auto 14px' }}/>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px 12px' }}>
          <span style={{ fontSize: 13, color: CAL.ink3 }}>取消</span>
          <span style={{ fontFamily: CAL.serif, fontSize: 18, fontWeight: 600 }}>选择工作类型</span>
          <span style={{ fontSize: 13, color: CAL.accent, fontWeight: 600 }}>确定</span>
        </div>

        {/* 分段 chip(组) */}
        <div style={{ padding: '0 16px 12px', display: 'flex', gap: 6, overflowX: 'auto' }}>
          {CAL_TYPE_GROUPS.map((g, i) => (
            <span key={g.id} style={{ padding: '6px 12px', borderRadius: 999, fontSize: 12,
              fontWeight: i === 1 ? 600 : 500,
              background: i === 1 ? CAL.ink : CAL.card,
              color: i === 1 ? '#FFF' : CAL.ink2,
              border: i === 1 ? 'none' : `1px solid ${CAL.divider}`,
              whiteSpace: 'nowrap', flexShrink: 0 }}>{g.label}</span>
          ))}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0 16px 8px' }}>
          {/* 行销组 - 展开 */}
          <div style={{ fontSize: 11, color: CAL.ink3, letterSpacing: 0.6, fontWeight: 600,
            textTransform: 'uppercase', padding: '6px 4px 10px' }}>行销 · 4 类</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
            {CAL_TYPE_GROUPS[1].types.map((t, i) => (
              <div key={t.id} style={{ padding: '11px 12px',
                background: i === 0 ? t.bg : CAL.card,
                border: i === 0 ? `1.5px solid ${t.color}` : `1px solid ${CAL.divider}`,
                borderRadius: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ width: 8, height: 8, borderRadius: 4, background: t.color, flexShrink: 0 }}/>
                <span style={{ fontSize: 13, fontWeight: i === 0 ? 600 : 500,
                  color: i === 0 ? t.color : CAL.ink }}>{t.label}</span>
                {i === 0 && <span style={{ marginLeft: 'auto', color: t.color, fontSize: 12, fontWeight: 700 }}>✓</span>}
              </div>
            ))}
          </div>

          {/* 其它组折叠预览 */}
          {CAL_TYPE_GROUPS.filter((_, i) => i !== 1).map(g => (
            <div key={g.id}>
              <div style={{ fontSize: 11, color: CAL.ink3, letterSpacing: 0.6, fontWeight: 600,
                textTransform: 'uppercase', padding: '16px 4px 8px' }}>{g.label} · {g.types.length} 类</div>
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

// ─── 3) 日报提交 ────────────────────────────────────────
function DailyLogSubmit() {
  return (
    <div style={{ background: CAL.bg, height: '100%', fontFamily: CAL.sans, color: CAL.ink, position: 'relative' }}>
      <CALStatusPad/>
      <div style={{ position: 'absolute', top: STATUS_PAD_CAL, left: 0, right: 0, height: 52,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 16px', background: CAL.bg, borderBottom: `1px solid ${CAL.divider}`, zIndex: 10 }}>
        <span style={{ fontSize: 14, color: CAL.ink3 }}>取消</span>
        <span style={{ fontSize: 15, fontWeight: 600 }}>撰写日报</span>
        <span style={{ fontSize: 14, color: CAL.accent, fontWeight: 600 }}>提交</span>
      </div>

      <div style={{ paddingTop: STATUS_PAD_CAL + 52, paddingBottom: 30, height: '100%', overflow: 'auto' }}>
        {/* hero */}
        <div style={{ padding: '20px 20px 4px' }}>
          <div style={{ fontSize: 11, color: CAL.ink3, letterSpacing: 0.6, fontWeight: 600, textTransform: 'uppercase' }}>
            周四 · 2026/05/14
          </div>
          <div style={{ fontFamily: CAL.serif, fontSize: 24, fontWeight: 600, marginTop: 4 }}>5 月 14 日 日报</div>
        </div>

        {/* 统计 3 卡 */}
        <div style={{ padding: '14px 16px', display: 'flex', gap: 10 }}>
          {[
            { l: '工作项', v: '5', c: CAL.ink },
            { l: '总工时', v: '7.5 h', c: CAL.blue },
            { l: '类型', v: '4 种', c: CAL.purple },
          ].map((s, i) => (
            <div key={i} style={{ flex: 1, padding: '10px 12px', background: CAL.card,
              borderRadius: 10, border: `1px solid ${CAL.divider}` }}>
              <div style={{ fontSize: 10, color: CAL.ink3, fontWeight: 600, letterSpacing: 0.4 }}>{s.l}</div>
              <div style={{ fontFamily: CAL.serif, fontSize: 19, fontWeight: 600,
                color: s.c, marginTop: 3, fontVariantNumeric: 'tabular-nums' }}>{s.v}</div>
            </div>
          ))}
        </div>

        {/* 自动摘要 */}
        <CALSection title="自动摘要 · 系统生成"/>
        <div style={{ margin: '0 16px', padding: '12px 14px', background: CAL.blueSoft,
          borderRadius: 10, border: `1px solid #DCE6F2` }}>
          <div style={{ fontSize: 13, color: CAL.ink, lineHeight: 1.65 }}>
            今日完成 <strong>5</strong> 项工作:1 次客户拜访(上海宝山节能科技)、2 次跨部门会议、
            1 项技术支持(新加坡 MCP 部署)、1 项行政事务。共计 <strong>7.5 小时</strong>。
          </div>
          <div style={{ fontSize: 11, color: CAL.blueDeep, marginTop: 6, fontWeight: 600 }}>
            ⚡ 摘要由系统根据工作项自动生成 · 可在补充说明里修改
          </div>
        </div>

        {/* 补充说明 */}
        <CALSection title="补充说明"/>
        <div style={{ margin: '0 16px 14px', padding: '14px 14px', background: CAL.card,
          borderRadius: 12, border: `1.5px solid ${CAL.accent}`,
          fontSize: 13, color: CAL.ink, minHeight: 100, lineHeight: 1.65 }}>
          客户拜访期间发现现场配电柜与图纸不符,已记录到项目跟进。
          <span style={{ display: 'inline-block', width: 1.5, height: 16, background: CAL.accent,
            marginLeft: 2, animation: 'calBlink 1s infinite', verticalAlign: 'middle' }}/>
          <style>{`@keyframes calBlink{0%,49%{opacity:1}50%,100%{opacity:0}}`}</style>
        </div>

        {/* @人 # 项目 chips */}
        <div style={{ padding: '0 20px 4px', fontSize: 11, color: CAL.ink3,
          letterSpacing: 0.4, fontWeight: 600, textTransform: 'uppercase' }}>提及 · 关联</div>
        <div style={{ padding: '8px 16px 0', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {['@ 张贺', '@ 何志有', '# 新加坡 MCP', '# 上海宝山节能'].map(c => {
            const isAt = c.startsWith('@');
            return (
              <span key={c} style={{ padding: '4px 10px', borderRadius: 999, fontSize: 12,
                background: isAt ? CAL.purpleSoft : CAL.accentSoft,
                color: isAt ? CAL.purple : CAL.accent,
                fontWeight: 600 }}>{c}</span>
            );
          })}
          <span style={{ padding: '4px 10px', borderRadius: 999, fontSize: 12, color: CAL.ink4,
            border: `1px dashed ${CAL.divider}` }}>+ 添加</span>
        </div>

        {/* 提示 */}
        <div style={{ margin: '20px 16px 0', padding: '11px 12px', background: CAL.warnSoft,
          borderRadius: 8, fontSize: 12, color: CAL.warn, lineHeight: 1.55 }}>
          ⓘ 提交后无法编辑工作项数量 · 质量分将基于工作项完整度、描述长度、关联完整度等自动计算
        </div>
      </div>
    </div>
  );
}

// ─── 4) 工作项详情 sheet(点行打开) ────────────────────
function WorkItemDetailSheet({ completed = false } = {}) {
  const it = CAL_ITEMS_TODAY[1]; // 客户拜访
  const t = calType(it.type);
  return (
    <div style={{ background: 'rgba(26,26,26,.42)', height: '100%', position: 'relative',
      fontFamily: CAL.sans, color: CAL.ink }}>
      <div style={{ position: 'absolute', inset: 0, opacity: 0.3 }}><CalendarAgenda/></div>

      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, background: CAL.bg,
        borderRadius: '20px 20px 0 0', padding: '14px 0 22px', maxHeight: '82%',
        display: 'flex', flexDirection: 'column' }}>
        <div style={{ width: 36, height: 4, background: CAL.divider, borderRadius: 2, margin: '0 auto 14px' }}/>

        <div style={{ padding: '0 20px 12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ fontFamily: CAL.serif, fontSize: 20, fontWeight: 600 }}>工作项详情</span>
            <span style={{ fontSize: 10, color: completed ? CAL.green : CAL.blue,
              background: completed ? CAL.greenSoft : CAL.blueSoft,
              padding: '2px 7px', borderRadius: 4, fontWeight: 700 }}>
              {completed ? '已完成' : '进行中'}
            </span>
          </div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <span style={{ fontSize: 11, color: t.color, background: t.bg, padding: '2px 7px',
              borderRadius: 3, fontWeight: 700, letterSpacing: 0.3 }}>{t.label}</span>
          </div>
          <div style={{ fontFamily: CAL.serif, fontSize: 22, fontWeight: 600, lineHeight: 1.3, marginTop: 4 }}>{it.title}</div>
          <div style={{ fontSize: 12.5, color: CAL.ink3, marginTop: 4 }}>{it.sub}</div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '0 16px' }}>
          {/* 4 格 meta */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
            <MetaCard label="计划日期" val="2026-05-14"/>
            <MetaCard label="时间" val={`${it.start} – ${it.end}`}/>
            <MetaCard label="累计时长" val={`${cfmt(it.hours)} 小时`} accent/>
            <MetaCard label="状态" val={completed ? '已完成' : '进行中'} accent={completed} green={completed}/>
          </div>

          {/* 关联 */}
          {(it.project || it.customer) && (
            <>
              <div style={{ fontSize: 11, color: CAL.ink3, letterSpacing: 0.6, fontWeight: 600, textTransform: 'uppercase', marginBottom: 8 }}>
                关联
              </div>
              <div style={{ background: CAL.card, borderRadius: 10, border: `1px solid ${CAL.divider}`,
                padding: '10px 14px', marginBottom: 12 }}>
                {it.project && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13,
                    paddingBottom: 6, borderBottom: it.customer ? `1px solid ${CAL.dividerSoft}` : 'none', marginBottom: it.customer ? 6 : 0 }}>
                    <span style={{ color: CAL.ink3 }}>项目</span>
                    <span style={{ color: CAL.accent, fontWeight: 500 }}>#{it.project} ›</span>
                  </div>
                )}
                {it.customer && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span style={{ color: CAL.ink3 }}>客户</span>
                    <span style={{ color: CAL.accent, fontWeight: 500 }}>{it.customer} ›</span>
                  </div>
                )}
              </div>
            </>
          )}

          {/* 行动记录 */}
          <div style={{ fontSize: 11, color: CAL.ink3, letterSpacing: 0.6, fontWeight: 600,
            textTransform: 'uppercase', marginBottom: 8 }}>行动记录</div>
          <div style={{ background: CAL.card, borderRadius: 10, border: `1px solid ${CAL.divider}`,
            padding: '12px 14px', fontSize: 13, color: CAL.ink2, lineHeight: 1.65 }}>
            上午 10:30 抵达现场,与设备部李华、运营总监刘亮沟通。需求初步确认,后续提供详细方案。
          </div>
        </div>

        {/* 底部 action */}
        <div style={{ padding: '14px 16px 0', borderTop: `1px solid ${CAL.divider}`,
          display: 'flex', gap: 10, flexShrink: 0, marginTop: 14 }}>
          <button style={{ flex: 1, height: 44, borderRadius: 22, background: CAL.card,
            border: `1.5px solid ${CAL.divider}`, color: CAL.ink2, fontSize: 13.5, fontWeight: 600 }}>编辑</button>
          {completed ? (
            <button style={{ flex: 2, height: 44, borderRadius: 22, background: CAL.card,
              border: `1.5px solid ${CAL.red}`, color: CAL.red, fontSize: 13.5, fontWeight: 600 }}>取消完成</button>
          ) : (
            <button style={{ flex: 2, height: 44, borderRadius: 22, background: CAL.green,
              border: 'none', color: '#FFF', fontSize: 13.5, fontWeight: 600 }}>标记完成</button>
          )}
        </div>
      </div>
    </div>
  );
}
function MetaCard({ label, val, accent, green }) {
  return (
    <div style={{ padding: '10px 12px', background: CAL.card, borderRadius: 10,
      border: `1px solid ${CAL.divider}` }}>
      <div style={{ fontSize: 10, color: CAL.ink3, fontWeight: 600, letterSpacing: 0.4 }}>{label}</div>
      <div style={{ fontFamily: CAL.serif, fontSize: 15, fontWeight: 600,
        color: green ? CAL.green : (accent ? CAL.blue : CAL.ink), marginTop: 3,
        fontVariantNumeric: 'tabular-nums' }}>{val}</div>
    </div>
  );
}
function WorkItemDetailSheetCompleted() { return <WorkItemDetailSheet completed/>; }

Object.assign(window, { CalendarItemCreate, CalendarItemCreateFilled,
  CalendarTypePickerSheet, DailyLogSubmit, WorkItemDetailSheet, WorkItemDetailSheetCompleted });
