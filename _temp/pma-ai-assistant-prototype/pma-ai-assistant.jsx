// PMA · 源助手 AI · 内容交互扩展
// 8 屏:命令面板 / 数据·实体卡 / 数据·迷你表 / 数据·聚合 / Wiki问答 / 培训引导 / 自适应路由总览 / 组合框状态
// 沿用 ai-chat.jsx 的视觉 DNA(同 token / 像素-P logo / 气泡形态),独立可跑,不依赖 ai-chat.jsx

const AIX = {
  bg: '#F7F5F2', card: '#FFFFFF',
  ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#C2BBB3',
  divider: 'rgba(0,0,0,0.06)', dividerStrong: 'rgba(0,0,0,0.10)',
  accent: '#D97757', accentSoft: '#F4E4D8', accentBg: 'rgba(217,119,87,0.08)',
  ai: '#2F66D6', aiSoft: '#E5EEFB', aiBg: 'rgba(47,102,214,0.06)', aiInk: '#1E4FAA',
  // 内容类型签名色(都从 ai 蓝派生 / 仅徽章用,正文不染色)
  wiki: '#1F8478', wikiSoft: '#DEEFEB',
  train: '#7B5BAC', trainSoft: '#EEE6F5',
  cmd: '#2F66D6', cmdSoft: '#E5EEFB',
  data: '#1E4FAA', dataSoft: '#E5EEFB',
  green: '#2F7A45', greenSoft: '#E9F1EB', warn: '#C77B22',
  serif: '"Tiempos Headline","Source Serif Pro","Noto Serif SC",Georgia,serif',
  sans: '-apple-system,"SF Pro Text","PingFang SC",system-ui,sans-serif',
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

function AIXStatusPad() { return <div style={{ height: 54 }}/>; }

function AIXNav({ title = '源助手', sub = '● 在线 · 已接入 PMA 全量数据 + 知识库' }) {
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
        <div style={{ fontSize: 11, color: AIX.green, marginTop: 1 }}>{sub}</div>
      </div>
      <span style={{ fontSize: 18, color: AIX.ink3 }}>···</span>
    </div>
  );
}

// ── 来源徽章:核心新语法 ─────────────────────────────────────────
const AIX_KIND = {
  data:  { label: '数据',  color: AIX.data,  bg: AIX.dataSoft,  icon: '◧' },
  wiki:  { label: 'Wiki',  color: AIX.wiki,  bg: AIX.wikiSoft,  icon: '❝' },
  cmd:   { label: '命令',  color: AIX.cmd,   bg: AIX.cmdSoft,   icon: '⌘' },
  train: { label: '培训',  color: AIX.train, bg: AIX.trainSoft, icon: '◷' },
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
          <span style={{ fontSize: 12, fontWeight: 600, color: AIX.aiInk }}>源助手</span>
          {time && <span style={{ fontSize: 10, color: AIX.ink3 }}>{time}</span>}
        </div>}
        <div style={{ background: AIX.aiBg, border: '1px solid rgba(47,102,214,0.18)', borderRadius: '4px 14px 14px 14px',
          padding: '12px 14px', fontFamily: AIX.serif, fontSize: 14, lineHeight: 1.55, color: AIX.ink }}>
          {kind && <AIXBadge kind={kind} note={note}/>}
          {children}
        </div>
        {actions && !compact && (
          <div style={{ display: 'flex', gap: 14, marginTop: 6, fontSize: 11, color: AIX.ink3 }}>
            <span>↻ 重新生成</span><span>⧉ 复制</span><span>👍</span><span>👎</span>
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

// 复用 AIRefCard 的实体卡(支持 客户 / 项目 / 报价 三态)
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

// composer(可注入展开面板)
function AIXComposer({ value, ph = '问我任何事 · 或选一个开始', hints = ['@AI', '#', '/'], panel }) {
  return (
    <div style={{ borderTop: `1px solid ${AIX.divider}`, background: AIX.card }}>
      {panel}
      <div style={{ padding: '8px 12px 6px', display: 'flex', gap: 6, overflowX: 'auto' }}>
        {['/分析赢率', '/查招标中项目', '/本季签约额', '/怎么报价', '/新人上手'].map(t => (
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

// 命令面板(分组)
function AIXCmdPanel({ focus }) {
  const groups = [
    { id: 'data',  k: 'data',  title: '数据查询', items: ['/分析赢率', '/查招标中项目', '/本季签约额', '/本月报销', '/找联系人'] },
    { id: 'wiki',  k: 'wiki',  title: 'Wiki 问答', items: ['/出口报价汇率', '/审批流程', '/产品参数对照'] },
    { id: 'train', k: 'train', title: '培训',      items: ['/新人上手', '/报价单怎么开', '/CRM 录入规范'] },
    { id: 'draft', k: 'cmd',   title: '起草 · 总结', items: ['/起草客户回复', '/写本周周报', '/总结群消息'] },
  ];
  return (
    <div style={{ padding: '12px 14px 4px', borderBottom: `1px solid ${AIX.divider}` }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: AIX.ink2, letterSpacing: 0.3 }}>选一个开始 · 点一下=填入可改的意图</span>
        <span style={{ fontSize: 11, color: AIX.ink3 }}>收起 ⌄</span>
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

// ═══ 1) 命令面板入口 ═══════════════════════════════════════════════
function AIXEntry() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '18px 0' }}>
        <div style={{ padding: '0 24px' }}>
          <AIXLogo size={40}/>
          <div style={{ fontFamily: AIX.serif, fontSize: 21, fontWeight: 500, marginTop: 14, lineHeight: 1.3 }}>
            问我任何事 —— 我会自己判断<br/>去查数据、查知识库、还是教你怎么做。
          </div>
          <div style={{ fontSize: 12.5, color: AIX.ink3, marginTop: 8, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.6 }}>
            打字直接问,或点下方面板里的一条 —— 不用先选模式。每条回答都会标来源。
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, padding: '18px 24px 0', flexWrap: 'wrap' }}>
          {[['◧','数据','客户/项目/报价/报销 实时查'],['❝','Wiki','流程/规范/产品参数 问知识库'],
            ['⌘','命令','起草/总结/导出 一句话执行'],['◷','培训','新人上手 · 边学边练']].map((x,i)=>(
            <div key={i} style={{ width: 'calc(50% - 4px)', background: AIX.card, border: `1px solid ${AIX.divider}`,
              borderRadius: 12, padding: '11px 12px' }}>
              <div style={{ fontSize: 14, color: AIX.ai }}>{x[0]} <span style={{ fontSize: 12, fontWeight: 700, color: AIX.ink }}>{x[1]}</span></div>
              <div style={{ fontSize: 11, color: AIX.ink3, marginTop: 4, lineHeight: 1.45 }}>{x[2]}</div>
            </div>
          ))}
        </div>
      </div>
      <AIXComposer panel={<AIXCmdPanel/>}/>
    </div>
  );
}

// ═══ 2) 数据查询 · 实体卡 ══════════════════════════════════════════
function AIXDataEntity() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="14:21" text="宝山节能这个客户赢率怎么样?有几个项目值得跟?"/>
        <AIXAnswer kind="data" note="客户 · 实时" time="14:21">
          <div><b>上海宝山节能科技</b> 整体赢率 <b style={{ color: AIX.green }}>约 72%</b> —— 老客户、联系人信任度高、名下 3 个进行中。最值得重点跟的是:</div>
          <AIXEntityCard tag="#" name="宝山节能改造项目" metaA="● 招标中" metaB="负责人 你" metaC="¥42.50万"/>
          <AIXEntityCard tag="#" name="宝山二期能效诊断" metaA="● 方案中" metaB="李华对接" metaC="¥18.00万"/>
          <AIXSource>数据来源:6 个名下项目 · 12 条跟进 · 上次拜访 04·22 · 点卡片进详情</AIXSource>
        </AIXAnswer>
        <AIXSuggest tags={['这个项目下一步做什么?', '帮我起草约见短信', '和其他客户对比']}/>
      </div>
      <AIXComposer value="帮我起草约见短信"/>
    </div>
  );
}

// ═══ 3) 数据查询 · 迷你表 ══════════════════════════════════════════
function AIXDataTable() {
  const rows = [
    ['深圳半导体工厂扩产', '招标中', '120.0', '陈刚'],
    ['宝山节能改造项目', '招标中', '42.5', '你'],
    ['苏州数据中心新风', '招标中', '88.0', '王磊'],
    ['南通锂电产线节能', '招标中', '36.2', '你'],
    ['杭州医院洁净改造', '招标中', '54.0', '周敏'],
  ];
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="15:02" text="列一下所有招标中的项目,按金额排"/>
        <AIXAnswer kind="data" note="7 条结果">
          <div>名下「招标中」共 <b>7 个</b>,合计 <b>¥468.7万</b>。前 5 个(按金额):</div>
          <div style={{ marginTop: 10, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 10, overflow: 'hidden', background: AIX.card }}>
            <div style={{ display: 'flex', padding: '8px 12px', background: AIX.bg, fontSize: 10.5, fontWeight: 700,
              color: AIX.ink3, letterSpacing: 0.4 }}>
              <span style={{ flex: 1 }}>项目</span><span style={{ width: 56, textAlign: 'right' }}>金额万</span><span style={{ width: 40, textAlign: 'right' }}>负责</span>
            </div>
            {rows.map((r, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', padding: '10px 12px',
                borderTop: `1px solid ${AIX.divider}`, fontSize: 12.5 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: AIX.serif, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r[0]}</div>
                  <div style={{ fontSize: 10.5, color: AIX.accent, fontWeight: 600, marginTop: 1 }}>● {r[1]}</div>
                </div>
                <span style={{ width: 56, textAlign: 'right', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{r[2]}</span>
                <span style={{ width: 40, textAlign: 'right', color: AIX.ink3 }}>{r[3]}</span>
              </div>
            ))}
            <div style={{ padding: '9px 12px', borderTop: `1px solid ${AIX.divider}`, fontSize: 12,
              color: AIX.ai, fontWeight: 600, textAlign: 'center' }}>查看全部 7 条 · 导出 ›</div>
          </div>
          <AIXSource>来源:projects 表 · stage=招标中 · owner∈你的权限范围 · 实时</AIXSource>
        </AIXAnswer>
        <AIXSuggest tags={['只看我负责的', '导出 Excel', '哪个最快要截标?']}/>
      </div>
      <AIXComposer/>
    </div>
  );
}

// ═══ 4) 数据查询 · 聚合数字 + 迷你图 ════════════════════════════════
function AIXBar({ label, val, max, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 7 }}>
      <span style={{ width: 52, fontSize: 11, color: AIX.ink3 }}>{label}</span>
      <div style={{ flex: 1, height: 8, background: AIX.bg, borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${(val / max) * 100}%`, height: '100%', background: color, borderRadius: 4 }}/>
      </div>
      <span style={{ width: 26, textAlign: 'right', fontSize: 11, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{val}</span>
    </div>
  );
}
function AIXDataAggregate() {
  const spark = [38, 52, 47, 63, 71, 58, 82, 96];
  const mx = Math.max(...spark);
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="09:40" text="本季度签约额多少?同比如何?各阶段项目分布?"/>
        <AIXAnswer kind="data" note="统计 · Q2">
          <div>Q2 截至今日:</div>
          <div style={{ marginTop: 10, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 12, padding: 14 }}>
            <div style={{ fontSize: 11, color: AIX.ink3, letterSpacing: 0.5 }}>签约额 · 本季</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 2 }}>
              <span style={{ fontFamily: AIX.serif, fontSize: 30, fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>¥318.6</span>
              <span style={{ fontSize: 13, color: AIX.ink3 }}>万</span>
              <span style={{ fontSize: 12, color: AIX.green, fontWeight: 700, marginLeft: 'auto' }}>▲ 同比 +24%</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 44, marginTop: 12 }}>
              {spark.map((v, i) => (
                <div key={i} style={{ flex: 1, height: `${(v / mx) * 100}%`,
                  background: i === spark.length - 1 ? AIX.ai : 'rgba(47,102,214,0.25)', borderRadius: 2 }}/>
              ))}
            </div>
            <div style={{ fontSize: 10, color: AIX.ink4, marginTop: 4 }}>近 8 周趋势 · 末周创新高</div>
          </div>
          <div style={{ marginTop: 10, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 12, padding: '12px 14px' }}>
            <div style={{ fontSize: 11, color: AIX.ink3, letterSpacing: 0.5, marginBottom: 2 }}>各阶段项目数</div>
            <AIXBar label="嵌入" val={12} max={18} color="rgba(47,102,214,0.5)"/>
            <AIXBar label="方案中" val={9} max={18} color="rgba(47,102,214,0.65)"/>
            <AIXBar label="招标中" val={7} max={18} color={AIX.ai}/>
            <AIXBar label="已签约" val={18} max={18} color={AIX.green}/>
          </div>
          <AIXSource>来源:pricing_orders + projects 聚合 · 公司 SP8D · 实时</AIXSource>
        </AIXAnswer>
        <AIXSuggest tags={['拆到每个人', '和 Q1 比', '导出季度报表']}/>
      </div>
      <AIXComposer/>
    </div>
  );
}

// ═══ 5) Wiki 问答 · 来源引用 ═══════════════════════════════════════
function AIXWikiSrc({ title, anchor, date }) {
  return (
    <div style={{ background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 10,
      padding: '10px 12px', display: 'flex', gap: 10, alignItems: 'flex-start', marginTop: 6 }}>
      <div style={{ width: 26, height: 26, borderRadius: 7, background: AIX.wikiSoft, color: AIX.wiki,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, flexShrink: 0 }}>❝</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: AIX.serif, fontSize: 12.5, fontWeight: 600, lineHeight: 1.35 }}>{title}</div>
        <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 3 }}>§ {anchor} · 更新 {date}</div>
      </div>
      <span style={{ fontSize: 11, color: AIX.wiki, fontWeight: 600, flexShrink: 0 }}>看原文 ›</span>
    </div>
  );
}
function AIXWiki() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="11:08" text="出口报价的汇率按什么时点取?谁能改?"/>
        <AIXAnswer kind="wiki" note="知识库 · 2 篇来源">
          <div style={{ marginBottom: 2 }}>按现行《报价管理规范》:</div>
          <ol style={{ margin: '6px 0', paddingLeft: 20, lineHeight: 1.85 }}>
            <li>汇率取 <b>报价单提交审批当日</b> 的系统中间价(非创建日)</li>
            <li>审批通过后锁定,后续不随汇率波动重算</li>
            <li>仅 <b>财务总监 / CEO</b> 可在审批前手动改汇率,需备注原因</li>
          </ol>
          <div style={{ marginTop: 8, marginBottom: 2, fontSize: 12.5, color: AIX.ink3, fontWeight: 600 }}>来源 ▾</div>
          <AIXWikiSrc title="报价管理规范 v3" anchor="4.2 汇率与币种" date="2026·03"/>
          <AIXWikiSrc title="SG 出口报价操作手册" anchor="汇率锁定时点" date="2026·04"/>
          <div style={{ fontSize: 11, color: AIX.warn, marginTop: 10, fontStyle: 'italic', fontFamily: AIX.serif }}>
            ⚠ 答案由知识库生成,可能滞后;以原文为准。未覆盖的请问财务。
          </div>
        </AIXAnswer>
        <AIXSuggest tags={['那币种怎么选?', '历史汇率在哪看?', '@财务 确认一下']}/>
      </div>
      <AIXComposer/>
    </div>
  );
}

// ═══ 6) 培训引导 · 步骤卡 ══════════════════════════════════════════
function AIXTrain() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav sub="◷ 新人上手 · 报价单实操"/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="10:15" text="我是新人,教我怎么开一张报价单"/>
        <AIXAnswer kind="train" note="第 2 / 5 步" actions={false}>
          <div style={{ display: 'flex', gap: 5, marginBottom: 10 }}>
            {[1,1,0,0,0].map((on, i) => (
              <div key={i} style={{ flex: 1, height: 4, borderRadius: 2,
                background: on ? AIX.train : 'rgba(123,91,172,0.2)' }}/>
            ))}
          </div>
          <div style={{ fontFamily: AIX.serif, fontSize: 16, fontWeight: 600 }}>第 2 步 · 选客户与项目</div>
          <div style={{ fontSize: 13.5, marginTop: 6, lineHeight: 1.6, color: AIX.ink2 }}>
            在新建报价单页,先选「关联项目」—— 系统会自动带出客户、联系人和币种,你不用手填。找不到项目就先去项目模块建。
          </div>
          <div style={{ marginTop: 10, height: 116, borderRadius: 10, background: AIX.bg,
            border: `1px dashed ${AIX.dividerStrong}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: AIX.ink4, fontSize: 12 }}>
            〔 App 实际截图占位:新建报价单 · 关联项目下拉 〕
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button style={{ flex: 1, padding: '10px 0', borderRadius: 12, border: 'none', background: AIX.train,
              color: '#fff', fontSize: 13, fontWeight: 700 }}>在 App 里试一下 →</button>
            <button style={{ padding: '10px 16px', borderRadius: 12, border: `1px solid ${AIX.dividerStrong}`,
              background: AIX.card, color: AIX.ink2, fontSize: 13 }}>下一步</button>
          </div>
          <div style={{ fontSize: 11, color: AIX.ink3, marginTop: 8, textAlign: 'center', fontStyle: 'italic', fontFamily: AIX.serif }}>
            「在 App 里试一下」会带你跳到真实页面,做完回这里继续
          </div>
        </AIXAnswer>
        <AIXSuggest tags={['这一步我卡住了', '跳过教学直接做', '上一步']}/>
      </div>
      <AIXComposer value="这一步我卡住了,关联项目里没有我的项目"/>
    </div>
  );
}

// ═══ 7) 自适应路由总览(一条 scroll 混排,体现"不分模式") ════════════
function AIXMixed() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <div style={{ padding: '4px 16px 10px', textAlign: 'center' }}>
          <span style={{ fontSize: 10.5, color: AIX.ink3, background: AIX.card, padding: '4px 12px',
            borderRadius: 999, border: `1px solid ${AIX.divider}`, fontStyle: 'italic', fontFamily: AIX.serif }}>
            同一个对话框 · AI 自己判断去哪取数 · 徽章告诉你来源
          </span>
        </div>
        <AIXUser text="宝山节能赢率怎么样"/>
        <AIXAnswer kind="data" note="客户" compact actions={false}>
          <div>整体赢率 <b style={{ color: AIX.green }}>约 72%</b>,重点跟:</div>
          <AIXEntityCard tag="#" name="宝山节能改造项目" metaA="● 招标中" metaC="¥42.50万"/>
        </AIXAnswer>
        <AIXUser text="出口报价汇率按哪天取"/>
        <AIXAnswer kind="wiki" note="知识库" compact actions={false}>
          <div>取 <b>提交审批当日</b> 系统中间价,审批后锁定。</div>
          <AIXWikiSrc title="报价管理规范 v3" anchor="4.2 汇率与币种" date="2026·03"/>
        </AIXAnswer>
        <AIXUser text="/写本周周报"/>
        <AIXAnswer kind="cmd" note="/写本周周报" compact actions={false}>
          <div style={{ fontSize: 11, color: AIX.cmd, fontWeight: 700, marginBottom: 4 }}>已据你本周 5 项工作 + 群消息生成 ▾</div>
          <div style={{ background: AIX.card, border: `1px dashed ${AIX.dividerStrong}`, borderRadius: 8,
            padding: '9px 11px', fontFamily: AIX.serif, fontSize: 13, lineHeight: 1.55 }}>
            本周完成宝山节能拜访 + SG MCP 部署;招标中项目推进 2 个…
          </div>
          <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
            <span style={{ fontSize: 11, color: '#fff', background: AIX.cmd, padding: '5px 12px', borderRadius: 999, fontWeight: 600 }}>采用</span>
            <span style={{ fontSize: 11, color: AIX.ink2, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, padding: '5px 12px', borderRadius: 999 }}>换一版</span>
          </div>
        </AIXAnswer>
        <AIXUser text="教我开报价单"/>
        <AIXAnswer kind="train" note="5 步 · 已开始" compact actions={false}>
          <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
            {[1,0,0,0,0].map((on,i)=><div key={i} style={{ flex:1, height:3, borderRadius:2, background:on?AIX.train:'rgba(123,91,172,0.2)' }}/>)}
          </div>
          <div><b>第 1 步</b> · 进入新建报价单 —— 点这里带你去 ›</div>
        </AIXAnswer>
      </div>
      <AIXComposer/>
    </div>
  );
}

// ═══ 8) 组合框状态(#引用 + /命令 面板) ════════════════════════════
function AIXChip({ children, hot }) {
  return (
    <span style={{ fontSize: 12, padding: '6px 11px', borderRadius: 999, fontFamily: AIX.mono,
      color: hot ? '#fff' : AIX.ink2, background: hot ? AIX.ink : AIX.card,
      border: `1px solid ${hot ? AIX.ink : AIX.dividerStrong}` }}>{children}</span>
  );
}
function AIXComposerStates() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '16px 16px 0' }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: AIX.ink3, letterSpacing: 0.6, textTransform: 'uppercase' }}>输入 # · 引用实体</div>
        <div style={{ background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 14, padding: 14, marginTop: 8 }}>
          <div style={{ fontFamily: AIX.serif, fontSize: 13.5, color: AIX.ink }}>
            分析 <span style={{ color: AIX.ai, fontWeight: 700, background: AIX.aiSoft, padding: '1px 5px', borderRadius: 4 }}>#宝山</span>
            <span style={{ display: 'inline-block', width: 2, height: 15, background: AIX.ai, marginLeft: 1, verticalAlign: -2, animation: 'aixBlink 1s infinite' }}/>
          </div>
          <div style={{ fontSize: 10.5, color: AIX.ink3, margin: '12px 0 6px' }}>最近 · 项目 / 客户 / 报价单</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            <AIXChip hot>#宝山节能改造项目</AIXChip><AIXChip>#上海宝山节能科技</AIXChip>
            <AIXChip>#宝山二期能效诊断</AIXChip><AIXChip>#QT-2026-0418 报价</AIXChip>
          </div>
        </div>

        <div style={{ fontSize: 11, fontWeight: 700, color: AIX.ink3, letterSpacing: 0.6, textTransform: 'uppercase', marginTop: 20 }}>输入 / · 命令面板(分组)</div>
        <div style={{ background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 14, marginTop: 8, overflow: 'hidden' }}>
          <AIXCmdPanel focus="/查招标中项目"/>
        </div>
        <div style={{ fontSize: 11, color: AIX.ink3, margin: '14px 4px 0', fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.6 }}>
          # 引用让 AI 精准锁定对象,免得问"哪个宝山";/ 命令是快捷入口,选中后仍以可编辑的自然语言填进输入框 —— 老手快、新人不懵。
        </div>
      </div>
      <AIXComposer value="分析 #宝山节能改造项目 的赢率和风险" panel={null}/>
    </div>
  );
}

// ═══ 9) `/` 触发转场 · a 打字过滤态 ═══════════════════════════════
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
function AIXSlashTyping() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="昨天" text="谢谢"/>
        <AIXAnswer compact actions={false}><div style={{ color: AIX.ink3 }}>不客气,随时找我 👋</div></AIXAnswer>
      </div>
      {/* 浮层:从键盘上方滑出 · 实时过滤 */}
      <div style={{ margin: '0 12px 6px', background: AIX.card, border: `1px solid ${AIX.dividerStrong}`,
        borderRadius: 16, boxShadow: '0 -6px 24px rgba(0,0,0,0.10)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 14px 6px' }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: AIX.ink2 }}>/ 命令 · 实时过滤 · <span style={{ color: AIX.ai }}>4 个匹配</span></span>
          <span style={{ fontSize: 11, color: AIX.ink3 }}>↑↓ 选 · ↵ 填入 · esc 关</span>
        </div>
        <div style={{ padding: '2px 8px 8px' }}>
          <AIXSlashRow kind="data" cmd="/查招标中项目" q="查" desc="名下处于招标中的项目清单 · 按金额排" hot/>
          <AIXSlashRow kind="data" cmd="/查客户赢率" q="查" desc="某客户历史赢率与重点项目"/>
          <AIXSlashRow kind="data" cmd="/查合同" q="查" desc="按客户/项目检索已签合同"/>
          <AIXSlashRow kind="wiki" cmd="/查产品参数" q="查" desc="知识库:产品规格/对照表"/>
        </div>
      </div>
      <div style={{ padding: '0 16px 6px', fontSize: 10.5, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif }}>
        打 <b style={{ fontFamily: AIX.mono, fontStyle: 'normal' }}>/</b> 唤出 · 继续打字即过滤 · 选中=填入可改的自然语言,不直接执行
      </div>
      <div style={{ padding: '4px 12px 24px', display: 'flex', alignItems: 'center', gap: 8,
        borderTop: `1px solid ${AIX.divider}`, background: AIX.card }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: AIX.bg, border: `1px solid ${AIX.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: AIX.ink2, marginTop: 4 }}>+</span>
        <div style={{ flex: 1, background: AIX.bg, borderRadius: 20, border: `1.5px solid ${AIX.ai}`,
          padding: '9px 14px', fontFamily: AIX.mono, fontSize: 14, color: AIX.ink, display: 'flex', alignItems: 'center', marginTop: 4 }}>
          <span style={{ flex: 1 }}>/查
            <span style={{ display: 'inline-block', width: 2, height: 16, background: AIX.ai, marginLeft: 1, verticalAlign: -2, animation: 'aixBlink 1s infinite' }}/>
          </span>
        </div>
        <button style={{ width: 36, height: 36, borderRadius: 18, background: AIX.ink4, color: '#fff', border: 'none', fontSize: 14, fontWeight: 700, marginTop: 4 }}>↑</button>
      </div>
    </div>
  );
}

// ═══ 9) `/` 触发转场 · b 选中→回填可编辑意图 ════════════════════════
function AIXSlashFilled() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <AIXNav/>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <AIXUser time="昨天" text="谢谢"/>
        <AIXAnswer compact actions={false}><div style={{ color: AIX.ink3 }}>不客气,随时找我 👋</div></AIXAnswer>
      </div>
      <div style={{ borderTop: `1px solid ${AIX.divider}`, background: AIX.card }}>
        <div style={{ padding: '10px 14px 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 10.5, color: AIX.ai, fontWeight: 700 }}>✓ 由 <span style={{ fontFamily: AIX.mono }}>/查招标中项目</span> 填入</span>
          <span style={{ fontSize: 10.5, color: AIX.ink3 }}>· 可改后再发</span>
          <span style={{ marginLeft: 'auto', fontSize: 10.5, color: AIX.ink3, border: `1px solid ${AIX.dividerStrong}`,
            padding: '2px 8px', borderRadius: 999 }}>× 移除命令</span>
        </div>
        <div style={{ padding: '4px 12px 8px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 36, height: 36, borderRadius: 18, background: AIX.bg, border: `1px solid ${AIX.dividerStrong}`,
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: AIX.ink2 }}>+</span>
          <div style={{ flex: 1, background: AIX.bg, borderRadius: 20, border: `1.5px solid ${AIX.ai}`,
            padding: '9px 14px', fontFamily: AIX.serif, fontSize: 14, color: AIX.ink, lineHeight: 1.4 }}>
            查一下我名下所有<b>招标中</b>的项目,按金额从高到低排
            <span style={{ display: 'inline-block', width: 2, height: 16, background: AIX.ai, marginLeft: 1, verticalAlign: -2, animation: 'aixBlink 1s infinite' }}/>
          </div>
          <button style={{ width: 36, height: 36, borderRadius: 18, background: AIX.ai, color: '#fff', border: 'none', fontSize: 14, fontWeight: 700 }}>↑</button>
        </div>
        <div style={{ padding: '0 16px 22px', fontSize: 10.5, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.55 }}>
          闭环:slash 选中 → 翻译成可编辑的自然语言 → 你能改参数(改阶段/排序)再发 → AI 路由到同一能力。老手快、可改、可追溯。
        </div>
      </div>
    </div>
  );
}

// ═══ 10) Skill 注册表 · a 目录列表 ═════════════════════════════════
function AIXCatRow({ kind, cmd, name, desc, params, role, out }) {
  const k = AIX_KIND[kind];
  return (
    <div style={{ padding: '13px 16px', borderBottom: `1px solid ${AIX.divider}`, display: 'flex', gap: 12 }}>
      <span style={{ width: 30, height: 30, borderRadius: 8, background: k.bg, color: k.color,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0 }}>{k.icon}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontFamily: AIX.mono, fontSize: 12.5, color: AIX.ink, fontWeight: 600 }}>{cmd}</span>
          <span style={{ fontFamily: AIX.serif, fontSize: 12.5, color: AIX.ink2 }}>{name}</span>
          <span style={{ marginLeft: 'auto', fontSize: 9, fontWeight: 700, color: k.color, padding: '1px 5px', borderRadius: 3, background: k.bg }}>{k.label}</span>
        </div>
        <div style={{ fontSize: 11, color: AIX.ink3, marginTop: 3, lineHeight: 1.4 }}>{desc}</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 7 }}>
          {params.map(p => (
            <span key={p} style={{ fontSize: 9.5, color: AIX.ink3, background: AIX.bg, border: `1px solid ${AIX.divider}`, padding: '2px 6px', borderRadius: 4, fontFamily: AIX.mono }}>{p}</span>
          ))}
          <span style={{ fontSize: 9.5, color: AIX.accent, background: AIX.accentBg, padding: '2px 6px', borderRadius: 4 }}>权限 {role}</span>
          <span style={{ fontSize: 9.5, color: k.color, background: k.bg, padding: '2px 6px', borderRadius: 4 }}>→ {out}</span>
        </div>
      </div>
      <span style={{ color: AIX.ink4, fontSize: 14, alignSelf: 'center' }}>›</span>
    </div>
  );
}
function AIXSkillCatalog() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54, overflow: 'auto' }}>
      <div style={{ padding: '14px 20px 6px' }}>
        <div style={{ fontSize: 11, color: AIX.ink3, fontWeight: 600, letterSpacing: 1.2, textTransform: 'uppercase' }}>PMA · 能力契约</div>
        <h1 style={{ fontFamily: AIX.serif, fontSize: 26, fontWeight: 500, margin: '4px 0 0', letterSpacing: -0.3 }}>命令注册表</h1>
        <div style={{ fontSize: 12, color: AIX.ink3, marginTop: 6, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.5 }}>
          唯一真相源 · 面板由它生成 · NL 路由指向它 · 权限按它卡
        </div>
      </div>
      <div style={{ display: 'flex', gap: 6, padding: '8px 16px 12px', overflowX: 'auto' }}>
        {[['全部', true], ['◧ 数据', false], ['❝ Wiki', false], ['⌘ 命令', false], ['◷ 培训', false]].map(([t, h], i) => (
          <span key={i} style={{ flexShrink: 0, fontSize: 12, padding: '6px 12px', borderRadius: 999,
            background: h ? AIX.ink : AIX.card, color: h ? '#fff' : AIX.ink2,
            border: `1px solid ${h ? AIX.ink : AIX.dividerStrong}` }}>{t}</span>
        ))}
      </div>
      <div style={{ background: AIX.card }}>
        <AIXCatRow kind="data" cmd="/查招标中项目" name="招标项目清单" desc="名下指定阶段项目,按金额排序" params={['阶段', '负责人', '排序']} role="全员·按数据范围" out="自适应"/>
        <AIXCatRow kind="data" cmd="/分析赢率" name="客户赢率分析" desc="某客户历史赢率 + 重点跟进项目" params={['客户*']} role="全员" out="实体卡"/>
        <AIXCatRow kind="data" cmd="/本季签约额" name="业绩聚合" desc="周期签约额 · 同比 · 各阶段分布" params={['周期']} role="销售+管理" out="聚合图"/>
        <AIXCatRow kind="wiki" cmd="/出口报价汇率" name="报价规范问答" desc="知识库 RAG · 必带来源 · 标时效" params={['—']} role="全员" out="来源卡"/>
        <AIXCatRow kind="cmd" cmd="/写本周周报" name="周报起草" desc="据工作项+群消息生成 · 需采用" params={['周期']} role="全员" out="草稿块"/>
        <AIXCatRow kind="train" cmd="/新人上手" name="报价单实操" desc="5 步状态机 · 深链 App 边学边练" params={['模块']} role="新人" out="步骤卡"/>
      </div>
      <div style={{ padding: '14px 20px 26px', fontSize: 11, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.6 }}>
        + 新增能力 = 往这张表加一行,面板/路由/权限自动生效 —— 不改前端代码。
      </div>
    </div>
  );
}

// ═══ 10) Skill 注册表 · b 单条能力契约详情 ════════════════════════
function AIXKV({ k, v, mono }) {
  return (
    <div style={{ display: 'flex', gap: 10, padding: '7px 0', borderBottom: `1px solid ${AIX.divider}` }}>
      <span style={{ width: 64, fontSize: 11, color: AIX.ink3, flexShrink: 0 }}>{k}</span>
      <span style={{ flex: 1, fontSize: 12, color: AIX.ink, fontFamily: mono ? AIX.mono : AIX.sans, lineHeight: 1.5 }}>{v}</span>
    </div>
  );
}
function AIXSkillDetail() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54, overflow: 'auto' }}>
      <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10, borderBottom: `1px solid ${AIX.divider}`, background: AIX.card }}>
        <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={AIX.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
        <span style={{ fontFamily: AIX.mono, fontSize: 14, fontWeight: 600 }}>/查招标中项目</span>
        <span style={{ marginLeft: 'auto', fontSize: 10, fontWeight: 700, color: AIX.data, padding: '2px 7px', borderRadius: 4, background: AIX.dataSoft }}>◧ 数据 · 确定性</span>
      </div>
      <div style={{ padding: '16px 20px' }}>
        <div style={{ fontFamily: AIX.serif, fontSize: 17, fontWeight: 600 }}>招标项目清单</div>
        <div style={{ fontSize: 12.5, color: AIX.ink2, marginTop: 6, lineHeight: 1.6 }}>
          查询当前用户权限范围内、处于指定阶段的项目清单,按金额排序。结果确定、可缓存、可导出。
        </div>

        <div style={{ fontSize: 11, fontWeight: 700, color: AIX.ink3, letterSpacing: 0.6, textTransform: 'uppercase', margin: '18px 0 4px' }}>参数 schema</div>
        <div style={{ background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 12, overflow: 'hidden' }}>
          <div style={{ display: 'flex', padding: '8px 12px', background: AIX.bg, fontSize: 10, fontWeight: 700, color: AIX.ink3 }}>
            <span style={{ flex: 1 }}>参数</span><span style={{ width: 42 }}>类型</span><span style={{ width: 32 }}>必填</span><span style={{ width: 96 }}>默认 / 取值源</span>
          </div>
          {[['stage', 'enum', '否', '招标中 · 阶段字典'], ['owner', 'ref', '否', '当前用户数据范围'], ['sort', 'enum', '否', '金额↓'], ['limit', 'int', '否', '20']].map((r, i) => (
            <div key={i} style={{ display: 'flex', padding: '8px 12px', borderTop: `1px solid ${AIX.divider}`, fontSize: 11.5, fontFamily: AIX.mono }}>
              <span style={{ flex: 1, color: AIX.aiInk, fontWeight: 600 }}>{r[0]}</span>
              <span style={{ width: 42, color: AIX.ink3 }}>{r[1]}</span>
              <span style={{ width: 32, color: AIX.ink3 }}>{r[2]}</span>
              <span style={{ width: 96, color: AIX.ink2 }}>{r[3]}</span>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 18, background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 12, padding: '4px 14px' }}>
          <AIXKV k="Handler" v="projects 表查询 · 确定性 · 缓存 5min · 可导出 Excel"/>
          <AIXKV k="权限" v="全员可调用 · 数据范围 = get_viewable_data(owner) · 跨库按 PMA_DB_TYPE"/>
          <AIXKV k="输出" v="≤3 条→实体卡;>3 条→可横滚迷你表 · 徽章 ◧数据"/>
          <AIXKV k="NL 同义" v="“招标中有哪些项目” / “列一下在投标的单子” / “我有几个项目在招标” → 命中同一能力"/>
        </div>

        <div style={{ marginTop: 16, background: AIX.aiBg, border: '1px solid rgba(47,102,214,0.18)', borderRadius: 12, padding: '12px 14px' }}>
          <div style={{ fontSize: 11, color: AIX.aiInk, fontWeight: 700, marginBottom: 6 }}>示例</div>
          <div style={{ fontFamily: AIX.mono, fontSize: 11.5, color: AIX.ink2 }}>in: /查招标中项目 --sort=amount</div>
          <div style={{ fontFamily: AIX.mono, fontSize: 11.5, color: AIX.ink2, marginTop: 4 }}>out: 迷你表 · 7 行 · ◧数据 · 来源脚注</div>
        </div>
        <div style={{ margin: '16px 0 26px', fontSize: 11, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.6 }}>
          契约即真相:前端面板、NL 路由器、权限网关三方都读这一份 —— 改契约比改三处代码安全。
        </div>
      </div>
    </div>
  );
}

// ═══ 11) 边界态 ════════════════════════════════════════════════════
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
        {s === 'done' ? '✓' : s === 'todo' ? '' : ''}
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
function AIXThinking() {
  return (
    <AIXEdgeShell>
      <AIXUser time="14:21" text="分析宝山节能赢率,再和深圳半导体那个对比"/>
      <div style={{ padding: '6px 16px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <AIXLogo size={22}/>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: AIX.aiInk }}>源助手</span>
            <span style={{ fontSize: 10, color: AIX.ink3 }}>思考中…</span>
          </div>
          <div style={{ background: AIX.aiBg, border: '1px solid rgba(47,102,214,0.18)', borderRadius: '4px 14px 14px 14px', padding: '10px 14px' }}>
            <AIXThinkStep s="done" label="判断意图" sub="数据查询 · 客户赢率 + 跨客户对比"/>
            <AIXThinkStep s="done" label="确认权限范围" sub="get_viewable_data · 你的可见数据"/>
            <AIXThinkStep s="now" label="查询中" sub="projects + pricing_orders · 2 个客户"/>
            <AIXThinkStep s="todo" label="汇总并生成回答"/>
            <div style={{ fontSize: 10.5, color: AIX.ink4, marginTop: 8, fontStyle: 'italic', fontFamily: AIX.serif }}>已用 2.4s · 复杂查询通常 &lt; 8s · 实时数据不走缓存</div>
          </div>
          <div style={{ marginTop: 8 }}>
            <span style={{ fontSize: 12, color: AIX.ink2, border: `1px solid ${AIX.dividerStrong}`, background: AIX.card, padding: '6px 14px', borderRadius: 999, fontWeight: 600 }}>■ 停止</span>
          </div>
        </div>
      </div>
    </AIXEdgeShell>
  );
}
function AIXErrorState() {
  return (
    <AIXEdgeShell>
      <AIXUser time="14:22" text="导出本季所有签约明细到 Excel"/>
      <AIXAnswer kind="cmd" note="/导出签约明细" actions={false}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <span style={{ width: 26, height: 26, borderRadius: 13, flexShrink: 0, background: 'rgba(181,69,58,0.10)',
            color: '#B5453A', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>!</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, color: '#B5453A' }}>导出没成功</div>
            <div style={{ fontSize: 13, color: AIX.ink2, marginTop: 4, lineHeight: 1.55 }}>
              数据源响应超时:pricing_orders 季度聚合 30s 未返回,已自动重试 1 次仍失败。<b>不是你的操作问题。</b>
            </div>
          </div>
        </div>
        <AIXEdgeBtns items={[['重试', true], ['缩小范围 · 按月导', false], ['反馈给管理员', false]]}/>
        <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 10, fontFamily: AIX.mono }}>错误码 GW-504 · 14:22 · req_8af3 · 可截图发 IT</div>
      </AIXAnswer>
    </AIXEdgeShell>
  );
}
function AIXNoPermission() {
  return (
    <AIXEdgeShell>
      <AIXUser time="10:05" text="看一下王磊名下所有项目的金额"/>
      <AIXAnswer kind="data" note="🔒 超出范围" actions={false}>
        <div style={{ fontWeight: 700 }}>这部分超出你的数据范围</div>
        <div style={{ fontSize: 13, color: AIX.ink2, marginTop: 5, lineHeight: 1.6 }}>
          王磊的项目归属在 <b>华东销售二部</b>。你当前可见范围是 <b>你本人 + 直属下属</b>,看不到平级同事的项目金额。
        </div>
        <div style={{ marginTop: 10, background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: 10, padding: '10px 12px', fontSize: 12, color: AIX.ink3 }}>
          你能看:<b style={{ color: AIX.ink }}>自己 6 个</b> + <b style={{ color: AIX.ink }}>下属 3 人</b> 的项目
        </div>
        <AIXEdgeBtns items={[['改成看我下属', true], ['申请扩大范围 →', false], ['找王磊直接要', false]]}/>
        <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 10, fontStyle: 'italic', fontFamily: AIX.serif }}>权限由 get_viewable_data 控制 · 申请走 OA 审批</div>
      </AIXAnswer>
    </AIXEdgeShell>
  );
}
function AIXEmptyResult() {
  return (
    <AIXEdgeShell>
      <AIXUser time="09:12" text="本月新增的『已签约』项目有哪些?"/>
      <AIXAnswer kind="data" note="0 条" actions={false}>
        <div style={{ fontWeight: 700 }}>没有匹配的结果</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 8 }}>
          {['stage = 已签约', '本月新增', '你的范围'].map(t => (
            <span key={t} style={{ fontSize: 10.5, color: AIX.ink3, background: AIX.bg, border: `1px solid ${AIX.divider}`, padding: '2px 7px', borderRadius: 4, fontFamily: AIX.mono }}>{t}</span>
          ))}
        </div>
        <div style={{ fontSize: 13, color: AIX.ink2, marginTop: 10, lineHeight: 1.6 }}>
          查询正常 —— 只是这个月还没有新签约落库。最近一笔是 <b>4·28「宝山节能改造」</b>。
        </div>
        <AIXEdgeBtns items={[['改成看本季已签约(18)', true], ['看招标中(7)', false], ['清空条件', false]]}/>
      </AIXAnswer>
    </AIXEdgeShell>
  );
}
function AIXLongResult() {
  return (
    <AIXEdgeShell>
      <AIXUser time="16:30" text="列出我所有客户的所有跟进记录"/>
      <AIXAnswer kind="data" note="结果很多" actions={false}>
        <div>命中 <b>1,284 条</b> 跟进记录 —— 全列会刷屏。先给最近 3 条:</div>
        <div style={{ marginTop: 10, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`, borderRadius: 10, overflow: 'hidden' }}>
          {[['宝山节能改造', '05·14 拜访 · 报价待优化'], ['深圳半导体扩产', '05·13 标书 V2 进行中'], ['苏州数据中心', '05·12 方案已交付']].map((r, i) => (
            <div key={i} style={{ padding: '9px 12px', borderTop: i ? `1px solid ${AIX.divider}` : 'none', fontSize: 12 }}>
              <span style={{ fontFamily: AIX.serif, fontWeight: 600 }}>{r[0]}</span>
              <span style={{ color: AIX.ink3 }}> · {r[1]}</span>
            </div>
          ))}
          <div style={{ padding: '8px 12px', borderTop: `1px dashed ${AIX.dividerStrong}`, fontSize: 11.5, color: AIX.ink3, textAlign: 'center', fontStyle: 'italic', fontFamily: AIX.serif }}>
            其余 1,281 条已折叠
          </div>
        </div>
        <AIXEdgeBtns items={[['让我先帮你总结要点', true], ['按客户分组看', false], ['只看最近 7 天(56)', false], ['导出 Excel', false]]}/>
        <div style={{ fontSize: 10.5, color: AIX.ink3, marginTop: 10, fontStyle: 'italic', fontFamily: AIX.serif }}>聊天单次最多渲染 20 条 · 大结果走总结 / 分组 / 导出</div>
      </AIXAnswer>
    </AIXEdgeShell>
  );
}

// ═══ 12) 接缝屏 · 与旧聊天整合 ════════════════════════════════════
function AIXVisChip({ mode }) {
  const m = mode === 'pub'
    ? { t: '👥 全群可见', c: AIX.green, bg: AIX.greenSoft }
    : mode === 'draft'
    ? { t: '✎ 仅你可见 · 草稿', c: AIX.accent, bg: AIX.accentSoft }
    : { t: '🔒 1:1 私有', c: AIX.ai, bg: AIX.aiSoft };
  return (
    <span style={{ fontSize: 10, fontWeight: 700, color: m.c, background: m.bg,
      padding: '2px 8px', borderRadius: 999, letterSpacing: 0.2 }}>{m.t}</span>
  );
}

// 12a · 会话列表改版(旧 ConvListWithAI + 新关系标注)
function AIXConvList() {
  const rows = [
    { kind: 'broadcast', name: '公司广播', last: 'Q2 全员目标已发布', time: '09:21', initial: '广', sq: true },
    { kind: 'group', name: '深圳半导体工厂扩产', last: '源助手:📊 周报已生成(全群可见)', time: '09:18', unread: 3, ai: true, initial: '深' },
    { kind: 'dm', name: '李华', last: '[AI 草稿] 李经理您好,报价已申请 5% 让利…', time: '昨天', draft: true, initial: '李' },
    { kind: 'group', name: '上海某制造厂节能改造', last: '系统:阶段已切到「招标中」', time: '昨天', initial: '上' },
  ];
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54, overflow: 'auto' }}>
      <div style={{ padding: '14px 24px 8px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 11, color: AIX.ink3, fontWeight: 500, letterSpacing: 1.2, textTransform: 'uppercase' }}>消息</div>
          <h1 style={{ fontFamily: AIX.serif, fontSize: 30, fontWeight: 500, margin: '4px 0 0', letterSpacing: -0.4 }}>聊天</h1>
        </div>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: AIX.card, border: `1px solid ${AIX.dividerStrong}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>+</span>
      </div>

      {/* 源助手置顶卡 — 整合关键:它就是进 17 屏主界面的门 */}
      <div style={{ padding: '8px 16px 4px' }}>
        <div style={{ background: `linear-gradient(135deg, ${AIX.aiBg} 0%, rgba(31,132,120,0.07) 100%)`,
          border: '1px solid rgba(47,102,214,0.25)', borderRadius: 16, padding: 14 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <AIXLogo size={34}/>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontFamily: AIX.serif, fontSize: 15, fontWeight: 600 }}>源助手</span>
                <span style={{ fontSize: 9, fontWeight: 700, color: AIX.ai, padding: '1px 5px', borderRadius: 3, background: AIX.aiSoft }}>BETA</span>
                <span style={{ marginLeft: 'auto' }}><AIXVisChip mode="solo"/></span>
              </div>
              <div style={{ fontSize: 12, color: AIX.ink2, marginTop: 4, fontFamily: AIX.serif, lineHeight: 1.4,
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                已为你查好招标中 7 个项目 · 点开继续 →
              </div>
            </div>
          </div>
          <div style={{ marginTop: 9, fontSize: 10.5, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif }}>
            点这张卡 = 进源助手主界面(数据 / Wiki / 培训 / 命令,完整 17 屏能力)
          </div>
        </div>
      </div>

      <div style={{ marginTop: 8, background: AIX.card }}>
        {rows.map((c, i, a) => (
          <div key={i} style={{ padding: '13px 16px', borderBottom: i < a.length - 1 ? `1px solid ${AIX.divider}` : 'none', display: 'flex', gap: 12 }}>
            <div style={{ width: 42, height: 42, borderRadius: c.sq ? 13 : 21, flexShrink: 0,
              background: c.sq ? AIX.ink : AIX.accentSoft, color: c.sq ? '#fff' : AIX.accent,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: AIX.serif, fontSize: 16, fontWeight: 600 }}>{c.initial}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
                <div style={{ fontFamily: AIX.serif, fontSize: 15, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 6 }}>
                  {c.name}
                  {c.ai && <span style={{ fontSize: 9, color: AIX.green, fontWeight: 700, padding: '1px 5px', borderRadius: 3, background: AIX.greenSoft }}>可 @源助手</span>}
                </div>
                <span style={{ fontSize: 11, color: AIX.ink3 }}>{c.time}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: 3 }}>
                <span style={{ fontSize: 12, color: AIX.ink3, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1, paddingRight: 8 }}>
                  {c.draft && <span style={{ color: AIX.accent, fontWeight: 600 }}>[AI 草稿] </span>}
                  {!c.draft && c.last}
                  {c.draft && c.last.replace('[AI 草稿] ', '')}
                </span>
                {c.unread > 0 && <span style={{ background: AIX.accent, color: '#fff', fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 999 }}>{c.unread}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ padding: '16px 24px 26px', fontSize: 11, color: AIX.ink3, fontStyle: 'italic', fontFamily: AIX.serif, lineHeight: 1.6 }}>
        置顶卡 = 私有主界面入口;群里「可 @源助手」= 公开问;私聊「[AI 草稿]」= 仅你可见起草。同一个 AI,三种可见性。
      </div>
    </div>
  );
}

// 12b · 群内 @源助手(旧 GroupAtAI + 新徽章/卡 · 公开可见)
function AIXGroupPublic() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10, borderBottom: `1px solid ${AIX.divider}`, background: AIX.card }}>
        <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={AIX.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: AIX.serif, fontSize: 15, fontWeight: 600 }}>深圳半导体工厂扩产</div>
          <div style={{ fontSize: 11, color: AIX.ink3 }}>5 人 + 源助手 · 招标中</div>
        </div>
        <span style={{ fontSize: 18, color: AIX.ink3 }}>···</span>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <div style={{ padding: '6px 16px', display: 'flex', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 14, background: AIX.accentSoft, color: AIX.accent, flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: AIX.serif, fontSize: 12, fontWeight: 600 }}>李</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: AIX.ink2, marginBottom: 4 }}>李明 · 09:32</div>
            <div style={{ background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: '14px 14px 14px 4px',
              padding: '10px 14px', display: 'inline-block', maxWidth: 300, fontFamily: AIX.serif, fontSize: 14, lineHeight: 1.45 }}>
              <span style={{ color: AIX.ai, fontWeight: 600 }}>@源助手</span> 这周招标中项目进展,生成周报发群里
            </div>
          </div>
        </div>
        {/* AI 公开回答:新徽章+卡,但带 @提问人 + 全群可见 */}
        <div style={{ padding: '6px 16px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <AIXLogo size={22}/>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: AIX.aiInk }}>源助手</span>
              <span style={{ fontSize: 10, color: AIX.ink3 }}>回 @李明 · 09:32</span>
              <span style={{ marginLeft: 'auto' }}><AIXVisChip mode="pub"/></span>
            </div>
            <div style={{ background: AIX.aiBg, border: '1px solid rgba(47,102,214,0.18)', borderRadius: '4px 14px 14px 14px', padding: '12px 14px', fontFamily: AIX.serif, fontSize: 14, lineHeight: 1.55 }}>
              <AIXBadge kind="data" note="周报 · 第 17 周"/>
              <div><b>深圳半导体工厂扩产</b> 本周进展:</div>
              <ol style={{ margin: '8px 0', paddingLeft: 20, lineHeight: 1.8 }}>
                <li>04·25 阶段「嵌入」→「招标中」(陈刚)</li>
                <li>客户方案 V1 已交付,评审中</li>
                <li>群内消息 38 条 · 新增跟进 2</li>
              </ol>
              <AIXEntityCard tag="#" name="深圳半导体工厂扩产" metaA="● 招标中" metaB="标书 V2 周五截止" metaC="¥120万"/>
              <AIXSource>数据来源:projects + 本群消息 · 全群可追问 / 转飞书</AIXSource>
            </div>
          </div>
        </div>
        <div style={{ padding: '6px 16px', display: 'flex', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 14, background: AIX.accentSoft, color: AIX.accent, flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: AIX.serif, fontSize: 12, fontWeight: 600 }}>陈</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: AIX.ink2, marginBottom: 4 }}>陈刚 · 09:34</div>
            <div style={{ background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: '14px 14px 14px 4px',
              padding: '10px 14px', display: 'inline-block', maxWidth: 300, fontFamily: AIX.serif, fontSize: 14 }}>
              <span style={{ color: AIX.ai, fontWeight: 600 }}>@源助手</span> 导出成飞书能贴的格式
            </div>
          </div>
        </div>
      </div>
      <AIXComposer ph="说点什么 · @源助手 提问全群可见…"/>
    </div>
  );
}

// 12c · 私聊 @AI 起草(旧 DMAIDraft + 新渲染 · 仅你可见 · 数据支撑)
function AIXDMDraft() {
  return (
    <div style={{ background: AIX.bg, height: '100%', fontFamily: AIX.sans, color: AIX.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10, borderBottom: `1px solid ${AIX.divider}`, background: AIX.card }}>
        <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={AIX.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
        <div style={{ width: 30, height: 30, borderRadius: 15, background: AIX.accentSoft, color: AIX.accent, flexShrink: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: AIX.serif, fontSize: 13, fontWeight: 600 }}>李</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: AIX.serif, fontSize: 15, fontWeight: 600 }}>李华</div>
          <div style={{ fontSize: 11, color: AIX.ink3 }}>采购部经理 · 上海宝山节能科技</div>
        </div>
        <span style={{ fontSize: 18, color: AIX.ink3 }}>···</span>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        <div style={{ padding: '6px 16px', display: 'flex', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 14, background: AIX.accentSoft, color: AIX.accent, flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: AIX.serif, fontSize: 12, fontWeight: 600 }}>李</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 11, color: AIX.ink3, marginBottom: 4 }}>昨天 17:42</div>
            <div style={{ background: AIX.card, border: `1px solid ${AIX.divider}`, borderRadius: '14px 14px 14px 4px',
              padding: '10px 14px', display: 'inline-block', maxWidth: 300, fontFamily: AIX.serif, fontSize: 14, lineHeight: 1.45 }}>
              方案看过了。报价能再优化吗?工期希望压到 90 天。
            </div>
          </div>
        </div>
        <div style={{ padding: '18px 16px 6px', display: 'flex', justifyContent: 'center' }}>
          <AIXVisChip mode="draft"/>
        </div>
        <div style={{ padding: '0 16px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <AIXLogo size={22}/>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ background: AIX.aiBg, border: '1px solid rgba(47,102,214,0.18)', borderRadius: '4px 14px 14px 14px', padding: '12px 14px' }}>
              <AIXBadge kind="cmd" note="起草 · 数据支撑"/>
              <div style={{ background: AIX.card, border: `1px dashed ${AIX.dividerStrong}`, borderRadius: 8,
                padding: '10px 12px', fontFamily: AIX.serif, fontSize: 14, lineHeight: 1.6 }}>
                李经理您好,报价我已申请到约 <b>5%</b> 让利空间,稍后单独发您。工期 90 天有挑战但可行,前提是设备分两批进场。今晚先发更新版方案,明天当面对一遍?
              </div>
              <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 10, color: AIX.ink3, padding: '3px 8px', borderRadius: 999, background: AIX.aiBg, fontStyle: 'italic', fontFamily: AIX.serif }}>语气:专业温暖</span>
                <span style={{ fontSize: 10, color: AIX.data, padding: '3px 8px', borderRadius: 999, background: AIX.dataSoft }}>引用 #历史报价:5% 让利先例</span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button style={{ flex: 1, padding: '10px 0', borderRadius: 12, border: 'none', background: AIX.ai, color: '#fff', fontSize: 13, fontWeight: 600 }}>采用 · 填入输入框</button>
              <button style={{ padding: '10px 14px', borderRadius: 12, border: `1px solid ${AIX.dividerStrong}`, background: AIX.card, color: AIX.ink2, fontSize: 13 }}>换一版</button>
              <button style={{ padding: '10px 14px', borderRadius: 12, border: `1px solid ${AIX.dividerStrong}`, background: AIX.card, color: AIX.ink2, fontSize: 13 }}>×</button>
            </div>
          </div>
        </div>
        <AIXSuggest tags={['更简短', '更正式', '加一句产能保障']}/>
      </div>
      <AIXComposer ph="给李华回复 · @AI 起草仅你可见…"/>
    </div>
  );
}

Object.assign(window, {
  AIXEntry, AIXDataEntity, AIXDataTable, AIXDataAggregate,
  AIXWiki, AIXTrain, AIXMixed, AIXComposerStates,
  AIXSlashTyping, AIXSlashFilled, AIXSkillCatalog, AIXSkillDetail,
  AIXThinking, AIXErrorState, AIXNoPermission, AIXEmptyResult, AIXLongResult,
  AIXConvList, AIXGroupPublic, AIXDMDraft,
});
