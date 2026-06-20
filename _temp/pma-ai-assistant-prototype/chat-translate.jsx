// PMA Chat · 多语翻译 — EN/MS ↔ ZH 双语气泡
// 4 屏:1) 自动翻译群聊  2) 长按气泡的翻译 menu  3) 翻译设置  4) 私聊跨语种(中→英)

const TR = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#C2BBB3',
  divider: 'rgba(0,0,0,0.06)', dividerStrong: 'rgba(0,0,0,0.10)',
  accent: '#D97757', accentSoft: '#F4E4D8', accentBg: 'rgba(217,119,87,0.08)',
  blue: '#4D82E0', blueSoft: '#E5EDFA',
  serif: '"Tiempos Headline","Source Serif Pro","Noto Serif SC",Georgia,serif',
  sans: '-apple-system,"SF Pro Text","PingFang SC",system-ui,sans-serif',
  mono: 'ui-monospace,"SF Mono",monospace',
};

function TRStatusPad() { return <div style={{ height: 54 }}/>; }

function TRNav({ title, sub, banner }) {
  return (
    <div style={{ borderBottom: `1px solid ${TR.divider}`, background: TR.bg }}>
      <div style={{ padding: '6px 16px 10px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 22, color: TR.ink2, padding: '0 4px' }}>‹</span>
        <div style={{ flex: 1, textAlign: 'center', minWidth: 0 }}>
          <div style={{ fontFamily: TR.serif, fontSize: 16, fontWeight: 500 }}>{title}</div>
          {sub && <div style={{ fontSize: 11, color: TR.ink3, marginTop: 1 }}>{sub}</div>}
        </div>
        <span style={{ width: 24, color: TR.ink3, fontSize: 18 }}>···</span>
      </div>
      {banner}
    </div>
  );
}

// 译文 banner — 顶部小提示
function AutoTranslateBanner({ from, to, onLabel = '自动翻译已开启' }) {
  return (
    <div style={{ padding: '6px 16px 8px', display: 'flex', alignItems: 'center', gap: 8,
      background: TR.accentBg, borderTop: `1px solid ${TR.accentSoft}` }}>
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M2 4h6M5 2v2M3 4l4 5M6 9l-3-3" stroke={TR.accent} strokeWidth="1.4" strokeLinecap="round"/>
        <path d="M9 13l3-7 3 7M10 11h4" stroke={TR.accent} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" transform="translate(-2 -2)"/>
      </svg>
      <span style={{ fontSize: 11, color: TR.accent, fontWeight: 600 }}>{onLabel}</span>
      <span style={{ fontSize: 11, color: TR.ink3, marginLeft: 'auto' }}>
        {from} → <strong style={{ fontWeight: 600 }}>{to}</strong>
      </span>
    </div>
  );
}

function TRDay({ label }) {
  return (
    <div style={{ textAlign: 'center', padding: '14px 0 8px' }}>
      <span style={{ fontSize: 11, color: TR.ink3, fontFamily: TR.serif, fontStyle: 'italic' }}>{label}</span>
    </div>
  );
}

// ═══ 双语气泡 ════════════════════════════════════════════════════════
// translated: 译文(主)+ 原文(辅)
function BiMsg({ avatar, from, time, mine, translated, original, srcLang, mood, note }) {
  // mood: undefined | 'highlighted' (长按选中态)
  return (
    <div style={{ padding: '6px 14px', display: 'flex', flexDirection: mine ? 'row-reverse' : 'row',
      alignItems: 'flex-start', gap: 8 }}>
      {!mine && (
        <div style={{ width: 30, height: 30, borderRadius: 15, background: TR.accentSoft, color: TR.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: TR.serif,
          fontSize: 13, fontWeight: 600, flexShrink: 0 }}>{avatar}</div>
      )}
      <div style={{ maxWidth: 304, display: 'flex', flexDirection: 'column', alignItems: mine ? 'flex-end' : 'flex-start' }}>
        {!mine && from && <div style={{ fontSize: 11, color: TR.ink3, marginBottom: 3, marginLeft: 2 }}>{from} · {time}</div>}
        <div style={{
          background: mood === 'highlighted' ? '#FFF8E8' : (mine ? TR.ink : TR.card),
          color: mine ? '#fff' : TR.ink,
          padding: '10px 13px 6px', borderRadius: 14,
          border: mine ? 'none' : `1px solid ${mood === 'highlighted' ? '#F0E1A8' : TR.divider}`,
          boxShadow: mood === 'highlighted' ? '0 4px 18px rgba(0,0,0,0.10)' : 'none',
        }}>
          {/* 主译文 */}
          <div style={{ fontFamily: TR.serif, fontSize: 14.5, lineHeight: 1.5 }}>{translated}</div>
          {/* 分隔线 */}
          <div style={{ height: 1,
            background: mine ? 'rgba(255,255,255,0.18)' : TR.divider,
            margin: '8px 0 6px' }}/>
          {/* 原文 — 弱化 */}
          <div style={{
            fontFamily: TR.sans, fontSize: 12.5, lineHeight: 1.45,
            color: mine ? 'rgba(255,255,255,0.62)' : TR.ink3,
            fontStyle: srcLang === 'EN' ? 'italic' : 'normal',
          }}>{original}</div>
          {/* 译文 meta — 去掉语言代码标签，只留 note */}
          {note && (
            <div style={{ marginTop: 5, display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 10, color: mine ? 'rgba(255,255,255,0.5)' : TR.ink4, marginLeft: 'auto' }}>{note}</span>
            </div>
          )}
        </div>
        {mine && <div style={{ fontSize: 11, color: TR.ink3, marginTop: 3, marginRight: 2 }}>{time} · 已读</div>}
      </div>
    </div>
  );
}

// 单语气泡(本来就是中文,不需要翻译)
function MonoMsg({ avatar, from, time, mine, text }) {
  return (
    <div style={{ padding: '6px 14px', display: 'flex', flexDirection: mine ? 'row-reverse' : 'row',
      alignItems: 'flex-start', gap: 8 }}>
      {!mine && (
        <div style={{ width: 30, height: 30, borderRadius: 15, background: TR.accentSoft, color: TR.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: TR.serif,
          fontSize: 13, fontWeight: 600, flexShrink: 0 }}>{avatar}</div>
      )}
      <div style={{ maxWidth: 280, display: 'flex', flexDirection: 'column', alignItems: mine ? 'flex-end' : 'flex-start' }}>
        {!mine && from && <div style={{ fontSize: 11, color: TR.ink3, marginBottom: 3, marginLeft: 2 }}>{from} · {time}</div>}
        <div style={{
          background: mine ? TR.ink : TR.card,
          color: mine ? '#fff' : TR.ink,
          padding: '9px 13px', borderRadius: 14,
          fontFamily: TR.serif, fontSize: 14.5, lineHeight: 1.5,
          border: mine ? 'none' : `1px solid ${TR.divider}`,
        }}>{text}</div>
        {mine && <div style={{ fontSize: 11, color: TR.ink3, marginTop: 3, marginRight: 2 }}>{time}</div>}
      </div>
    </div>
  );
}

// 简易输入栏(只用作下方装饰)
function TRComposer({ placeholder = '说点什么…' }) {
  return (
    <div style={{ borderTop: `1px solid ${TR.divider}`, background: TR.bg,
      padding: '8px 12px 24px', display: 'flex', alignItems: 'flex-end', gap: 8 }}>
      <span style={{ width: 36, height: 36, borderRadius: 18, background: TR.card, border: `1px solid ${TR.dividerStrong}`,
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: TR.ink2, fontWeight: 300 }}>+</span>
      <div style={{ flex: 1, background: TR.card, borderRadius: 20, border: `1px solid ${TR.dividerStrong}`,
        padding: '9px 14px', fontFamily: TR.serif, fontSize: 14, color: TR.ink3, fontStyle: 'italic',
        minHeight: 36, display: 'flex', alignItems: 'center' }}>
        {placeholder}
      </div>
      <span style={{ width: 36, height: 36, borderRadius: 18, background: TR.card, border: `1px solid ${TR.dividerStrong}`,
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="6" y="2" width="4" height="8" rx="2" stroke={TR.ink2} strokeWidth="1.4"/>
          <path d="M3.5 8a4.5 4.5 0 009 0M8 12.5V14" stroke={TR.ink2} strokeWidth="1.4" strokeLinecap="round"/>
        </svg>
      </span>
    </div>
  );
}

// ═══ 1) 群聊 · 多语自动翻译 ═══════════════════════════════════════════
function GroupTranslate() {
  return (
    <div style={{ background: TR.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: TR.sans }}>
      <TRStatusPad/>
      <TRNav
        title="深圳半导体 · 马来西亚分包"
        sub="6 人"
      />
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 0 8px' }}>
        <TRDay label="今天 · Today"/>

        {/* 1) 英文消息 */}
        <BiMsg
          avatar="A" from="Aisyah · KL Lead" time="09:08" srcLang="EN"
          translated="客户那边图纸已经看过了,有几个细节要再确认。"
          original="Got the drawings reviewed on the client side — there are a few details we need to confirm again."
        />

        {/* 2) 马来文消息 */}
        <BiMsg
          avatar="R" from="Rizal · Site" time="09:10" srcLang="MS"
          translated="今天工地停水,工人下午才能继续浇筑。"
          original="Air di tapak terputus hari ini, pekerja hanya dapat sambung kerja konkrit selepas tengah hari."
        />

        {/* 3) 我的中文回复 — 单语 */}
        <MonoMsg mine time="09:12" text="收到,我下午联系业主协调供水。"/>

        {/* 4) 英文紧接 */}
        <BiMsg
          avatar="A" from="Aisyah · KL Lead" time="09:13" srcLang="EN"
          translated="谢谢,顺便问下变压器是周四到货吗?"
          original="Thanks. By the way, is the transformer arriving on Thursday?"
        />

        {/* 5) 我的中文回复 — 译给对方(发送时附原文 → 对方看到的是英文) */}
        <BiMsg mine time="09:15" srcLang="ZH"
          translated="Yes, the transformer is scheduled to arrive on Thu morning. We'll let you know once it's loaded."
          original="是的,变压器周四上午到。装车后我会同步给你们。"
          note="对方看到英文"
        />
      </div>
      <TRComposer placeholder="说点什么…(对方按其语言偏好接收)"/>
    </div>
  );
}

// ═══ 2) 长按气泡 · 翻译 menu ═══════════════════════════════════════════
function TranslateActionMenu() {
  return (
    <div style={{ background: TR.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: TR.sans, position: 'relative' }}>
      <TRStatusPad/>
      <TRNav title="Aisyah Rahman" sub="KL Lead · 在线"/>

      {/* 遮罩 + 突出选中气泡 */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {/* 遮罩 */}
        <div style={{ position: 'absolute', inset: 0, background: 'rgba(20,20,20,0.55)', backdropFilter: 'blur(2px)' }}/>

        {/* 上方:翻译后的气泡(浮起 — 高亮态)*/}
        <div style={{ position: 'absolute', top: 28, left: 0, right: 0, zIndex: 2 }}>
          <BiMsg
            avatar="A" from="Aisyah Rahman" time="09:13" srcLang="EN" mood="highlighted"
            translated="谢谢,顺便问下变压器是周四到货吗?"
            original="Thanks. By the way, is the transformer arriving on Thursday?"
          />
        </div>

        {/* 弹出 action menu */}
        <div style={{
          position: 'absolute', top: 195, left: 56, zIndex: 3,
          background: TR.card, borderRadius: 12, overflow: 'hidden',
          width: 220, boxShadow: '0 10px 30px rgba(0,0,0,0.22)',
          border: `1px solid ${TR.divider}`,
        }}>
          {[
            ['回复', '↩'],
            ['复制', '⎘'],
            ['翻译为中文', '🌐', true],
            ['查看原文', '👁'],
            ['转发', '→'],
            ['标记为待办', '☆'],
            ['删除', '🗑', false, true],
          ].map(([label, ic, active, danger], i) => (
            <div key={i} style={{
              padding: '11px 14px',
              borderBottom: i < 6 ? `1px solid ${TR.divider}` : 'none',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              background: active ? TR.accentBg : 'transparent',
              color: danger ? '#C44' : (active ? TR.accent : TR.ink),
              fontSize: 14,
              fontFamily: TR.serif,
              fontWeight: active ? 600 : 400,
            }}>
              <span>{label}</span>
              <span style={{ fontSize: 14, opacity: 0.7 }}>{ic}</span>
            </div>
          ))}
        </div>

        {/* 翻译切换器 — 底部 emoji-style row */}
        <div style={{
          position: 'absolute', top: 130, left: 60, right: 60, zIndex: 3,
          background: TR.card, borderRadius: 999, padding: '6px 8px',
          display: 'flex', gap: 4, alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 14px rgba(0,0,0,0.15)',
          border: `1px solid ${TR.divider}`,
        }}>
          {['👍', '✓', '?', '🙏', '...'].map((e, i) => (
            <span key={i} style={{ width: 30, height: 30, borderRadius: 15,
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              background: 'transparent', fontSize: 16 }}>{e}</span>
          ))}
        </div>
      </div>

      <TRComposer placeholder="回复…"/>
    </div>
  );
}

// ═══ 3) 翻译设置面板 ══════════════════════════════════════════════════
function TranslateSettings() {
  return (
    <div style={{ background: TR.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: TR.sans }}>
      <TRStatusPad/>
      <div style={{ padding: '10px 16px 12px', display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: `1px solid ${TR.divider}` }}>
        <span style={{ fontSize: 22, color: TR.ink2 }}>‹</span>
        <span style={{ fontFamily: TR.serif, fontSize: 17, fontWeight: 500 }}>翻译设置</span>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '8px 0 24px' }}>
        {/* 主开关 */}
        <SecHdr label="自动翻译"/>
        <Card>
          <Row label="收到非偏好语消息时自动翻译"
            sub="基于消息发送语言自动判断"
            right={<Toggle on/>}/>
          <Row label="发送时附带翻译"
            sub="对方看到自动翻译后的版本(可选附原文)"
            right={<Toggle on/>}/>
          <Row label="附带原文"
            sub="对方在译文下方看到我发的原文"
            right={<Toggle on/>}
            last/>
        </Card>

        {/* 我的偏好语 */}
        <SecHdr label="我的偏好语"/>
        <Card>
          <Row label="主语言" right={<Pill text="中文 · 简体" caret/>} last/>
        </Card>
        <Hint>收到的非中文消息会被翻译显示为中文。</Hint>

        {/* 翻译方向白名单 */}
        <SecHdr label="启用语对"/>
        <Card>
          <LangPair from="English" to="中文" code="EN ⇄ ZH" on/>
          <LangPair from="Bahasa Melayu" to="中文" code="MS ⇄ ZH" on/>
          <LangPair from="English" to="Bahasa Melayu" code="EN ⇄ MS" on/>
          <LangPair from="日本語" to="中文" code="JA ⇄ ZH" on={false} last/>
        </Card>

        {/* 显示样式 */}
        <SecHdr label="显示样式"/>
        <Card>
          <Row label="译文显示位置"
            sub="译文在上 · 原文在下"
            right={<Pill text="译文在上"/>}/>
          <Row label="译文标记"
            sub="底部小标签显示语对(EN→ZH)"
            right={<Toggle on/>}/>
          <Row label="单击气泡切换"
            sub="点击可切换「显示译文 / 仅原文」"
            right={<Toggle/>}
            last/>
        </Card>

        {/* 此群单独覆盖 */}
        <SecHdr label="本群单独配置"/>
        <Card>
          <Row label="深圳半导体 · 马来西亚分包"
            sub="3 国语言 · 6 人 · 自动翻译开启"
            right={<span style={{ fontSize: 12, color: TR.accent, fontWeight: 600 }}>已配置 ›</span>}
            last/>
        </Card>

        <Hint>翻译由 PMA 与第三方引擎共同提供 · 重要内容请人工核对。</Hint>
      </div>
    </div>
  );
}

function SecHdr({ label }) {
  return (
    <div style={{ padding: '20px 24px 8px' }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: TR.ink3, letterSpacing: 1, textTransform: 'uppercase' }}>{label}</div>
    </div>
  );
}

function Card({ children }) {
  return (
    <div style={{ margin: '0 16px', background: TR.card, borderRadius: 14,
      border: `1px solid ${TR.divider}`, overflow: 'hidden' }}>
      {children}
    </div>
  );
}

function Row({ label, sub, right, last }) {
  return (
    <div style={{
      padding: '12px 16px',
      borderBottom: last ? 'none' : `1px solid ${TR.divider}`,
      display: 'flex', alignItems: 'center', gap: 12,
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: TR.serif, fontSize: 14, fontWeight: 500, color: TR.ink, lineHeight: 1.3 }}>{label}</div>
        {sub && <div style={{ fontSize: 11.5, color: TR.ink3, marginTop: 3, lineHeight: 1.4 }}>{sub}</div>}
      </div>
      <div style={{ flexShrink: 0 }}>{right}</div>
    </div>
  );
}

function Hint({ children }) {
  return (
    <div style={{ padding: '8px 24px 0', fontSize: 11, color: TR.ink3, lineHeight: 1.5 }}>{children}</div>
  );
}

function Toggle({ on }) {
  return (
    <span style={{
      width: 42, height: 26, borderRadius: 13, padding: 2,
      background: on ? TR.accent : '#D8D2C8',
      display: 'inline-flex', alignItems: 'center', justifyContent: on ? 'flex-end' : 'flex-start',
      transition: 'background .2s',
    }}>
      <span style={{ width: 22, height: 22, borderRadius: 11, background: '#fff',
        boxShadow: '0 1px 3px rgba(0,0,0,0.15)' }}/>
    </span>
  );
}

function Pill({ text, caret }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '5px 10px', borderRadius: 999,
      background: TR.bg, color: TR.ink2, fontSize: 12, fontWeight: 500,
      border: `1px solid ${TR.divider}`,
    }}>
      {text}
      {caret && <svg width="8" height="6" viewBox="0 0 8 6"><path d="M1 1l3 3 3-3" stroke={TR.ink3} strokeWidth="1.4" fill="none" strokeLinecap="round"/></svg>}
    </span>
  );
}

function LangPair({ from, to, code, on, last }) {
  return (
    <div style={{
      padding: '12px 16px',
      borderBottom: last ? 'none' : `1px solid ${TR.divider}`,
      display: 'flex', alignItems: 'center', gap: 12,
    }}>
      <span style={{
        fontSize: 9, fontWeight: 700, letterSpacing: 0.5, padding: '3px 6px', borderRadius: 4,
        fontFamily: TR.mono,
        background: on ? TR.accentBg : TR.bg,
        color: on ? TR.accent : TR.ink3,
        border: `1px solid ${on ? TR.accentSoft : TR.divider}`,
        flexShrink: 0,
      }}>{code}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: TR.serif, fontSize: 14, fontWeight: 500, color: TR.ink }}>
          {from} <span style={{ color: TR.ink4, margin: '0 6px' }}>⇄</span> {to}
        </div>
      </div>
      <Toggle on={on}/>
    </div>
  );
}

// ═══ 4) 私聊 · 中→英 跨语种 ═══════════════════════════════════════════
function DMTranslate() {
  return (
    <div style={{ background: TR.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: TR.sans }}>
      <TRStatusPad/>
      <TRNav
        title="Aisyah Rahman"
        sub="KL Lead · 在线"
        banner={<AutoTranslateBanner from="EN" to="ZH"/>}
      />
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 0 8px' }}>
        <TRDay label="昨天 · Yesterday"/>

        <BiMsg
          avatar="A" from="Aisyah" time="16:42" srcLang="EN"
          translated="刚和客户碰完,他们倾向于先做 A 区,B 区延后两周。"
          original="Just finished with the client. They prefer to start with Zone A first and delay Zone B by two weeks."
        />

        <MonoMsg mine time="16:50" text="OK,那物料采购单我重新拆一下。"/>

        <BiMsg mine time="16:51" srcLang="ZH"
          translated="OK, I'll re-split the material purchase list accordingly."
          original="OK,那物料采购单我重新拆一下。"
          note="译给对方"
        />

        <BiMsg
          avatar="A" from="Aisyah" time="16:55" srcLang="EN"
          translated="谢谢!另外周四的视频会议要不要往后挪?变压器到货可能晚一天。"
          original="Thanks! Also, should we postpone Thursday's video call? The transformer might arrive a day late."
        />

        <TRDay label="今天 · Today"/>

        <MonoMsg mine time="09:15" text="周四不用挪。变压器装车了,今晚发,周四上午到。"/>

        <BiMsg mine time="09:15" srcLang="ZH"
          translated="No need to postpone Thursday. The transformer is loaded — it ships tonight and arrives Thu morning."
          original="周四不用挪。变压器装车了,今晚发,周四上午到。"
          note="译给对方"
        />

        <BiMsg
          avatar="A" from="Aisyah" time="09:18" srcLang="EN"
          translated="完美 👍 那我们如约。"
          original="Perfect 👍 We'll keep it as scheduled then."
        />
      </div>
      <TRComposer placeholder="说点什么…(发送时自动译为 EN)"/>
    </div>
  );
}

Object.assign(window, { GroupTranslate, TranslateActionMenu, TranslateSettings, DMTranslate });
