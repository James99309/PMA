// PMA · 项目↔聊天桥接屏
// 1) 项目详情底部新增「项目讨论」预览卡 + 最近 3 条消息(进入项目群转场)
// 2) 引用卡片在消息流里的 4 种样态:项目 / 客户 / 合同 / 联系人

const B = {
  bg: '#F7F5F2', card: '#FFFFFF',
  ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#C2BBB3',
  divider: 'rgba(0,0,0,0.06)', dividerStrong: 'rgba(0,0,0,0.10)',
  accent: '#D97757', accentSoft: '#F4E4D8', accentBg: 'rgba(217,119,87,0.08)',
  green: '#2F7A45',
  serif: '"Tiempos Headline","Source Serif Pro","Noto Serif SC",Georgia,serif',
  sans: '-apple-system,"SF Pro Text","PingFang SC",system-ui,sans-serif',
};

// ═══ 1) 项目详情 — 新增「项目讨论」卡片 ═══════════════════════════
function ProjectDetailWithChat() {
  return (
    <div style={{ background: B.bg, height: '100%', fontFamily: B.sans, color: B.ink, paddingTop: 54, overflow: 'auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: B.ink2, fontSize: 15 }}>
          <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={B.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
          项目
        </div>
        <div style={{ fontSize: 14, color: B.ink3 }}>···</div>
      </div>

      <div style={{ padding: '20px 28px 16px' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 14 }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 500, color: B.accent }}>
            <span style={{ width: 5, height: 5, borderRadius: 3, background: B.accent }}/>招标中
          </span>
          <span style={{ fontSize: 11, color: B.ink3 }}>· AUTH-2024-0089</span>
        </div>
        <h1 style={{ fontFamily: B.serif, fontSize: 28, fontWeight: 500, lineHeight: 1.2, margin: 0, letterSpacing: -0.3 }}>
          上海某制造厂<br/>节能改造项目
        </h1>
        <div style={{ marginTop: 14, fontSize: 13, color: B.ink3 }}>张伟 · 制造业 · 上海浦东</div>
        <div style={{ marginTop: 22, display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontFamily: B.serif, fontSize: 40, fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>¥42.50</span>
          <span style={{ fontSize: 14, color: B.ink3 }}>万 · 预计签约</span>
        </div>
      </div>

      {/* CTA */}
      <div style={{ padding: '0 20px 8px', display: 'flex', gap: 10 }}>
        <button style={{ flex: 1, height: 48, borderRadius: 14, border: 'none', background: B.accent, color: '#fff', fontSize: 15, fontWeight: 600 }}>推进到 授权 →</button>
        <button style={{ width: 48, height: 48, borderRadius: 14, background: B.card, border: `1px solid ${B.divider}` }}>+</button>
      </div>

      {/* ===== 新增:项目讨论预览卡 ===== */}
      <div style={{ padding: '24px 28px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: B.ink3, letterSpacing: 1, textTransform: 'uppercase' }}>项目讨论</div>
          <span style={{ fontSize: 12, color: B.accent, fontWeight: 500 }}>加入讨论 →</span>
        </div>

        <div style={{ background: B.card, borderRadius: 16, border: `1px solid ${B.divider}`, overflow: 'hidden' }}>
          {/* 群头 */}
          <div style={{ padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 12, borderBottom: `1px solid ${B.divider}` }}>
            <div style={{ width: 38, height: 38, borderRadius: 12, background: B.accentSoft, color: B.accent,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: B.serif, fontSize: 15, fontWeight: 600 }}>上</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 600 }}>项目群 · 5 人</div>
              <div style={{ fontSize: 11, color: B.ink3, marginTop: 2 }}>张伟 · 陈刚 · 李明 · 王芳 · 系统</div>
            </div>
            <span style={{ background: B.accent, color: '#fff', fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 999 }}>3</span>
          </div>

          {/* 最近 3 条消息预览 */}
          <div style={{ padding: '8px 16px 4px' }}>
            <PreviewMsg name="李明" time="09:10" text="@张伟 标书这周五前必须出 V2" mention/>
            <PreviewMsg name="系统" time="09:14" italic text="阶段已切换到「招标中」 · 陈刚操作"/>
            <PreviewMsg name="陈刚" time="09:18" text="客户晚上约见,问下他们对工期的期望。"/>
          </div>

          {/* 输入框入口 */}
          <div style={{ padding: '8px 16px 14px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ flex: 1, height: 36, borderRadius: 18, background: B.bg, border: `1px solid ${B.dividerStrong}`,
              display: 'flex', alignItems: 'center', padding: '0 14px',
              fontFamily: B.serif, fontSize: 13, color: B.ink3, fontStyle: 'italic' }}>
              在群里说点什么…
            </div>
            <span style={{ width: 36, height: 36, borderRadius: 18, background: B.ink, color: '#fff',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>›</span>
          </div>
        </div>
      </div>

      {/* 详情(简化) */}
      <div style={{ padding: '24px 28px 16px' }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: B.ink3, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12 }}>详情</div>
        <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', rowGap: 12, fontSize: 14 }}>
          <span style={{ color: B.ink3 }}>客户</span>
          <span style={{ color: B.accent, fontWeight: 500 }}>上海宝山节能科技 ›</span>
          <span style={{ color: B.ink3 }}>负责人</span><span>张伟</span>
          <span style={{ color: B.ink3 }}>预计交付</span><span style={{ fontVariantNumeric: 'tabular-nums' }}>2026 · 06 · 30</span>
        </div>
      </div>

      <div style={{ padding: '20px 28px 100px' }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: B.ink3, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12 }}>跟进记录</div>
        <div style={{ borderLeft: `2px solid ${B.accent}`, paddingLeft: 14 }}>
          <div style={{ fontSize: 11, color: B.ink3, marginBottom: 4 }}>2026 · 04 · 28 — 张伟</div>
          <div style={{ fontFamily: B.serif, fontSize: 16, lineHeight: 1.55 }}>与客户采购部完成初步需求确认,要求提交方案和报价。</div>
        </div>
      </div>
    </div>
  );
}

function PreviewMsg({ name, time, text, italic, mention }) {
  return (
    <div style={{ padding: '8px 0', borderBottom: `1px dashed ${B.divider}` }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: B.ink2 }}>{name}</span>
        <span style={{ fontSize: 11, color: B.ink3 }}>{time}</span>
        {mention && <span style={{ fontSize: 10, color: B.accent, fontWeight: 600, padding: '1px 5px', borderRadius: 3, background: B.accentBg }}>@我</span>}
      </div>
      <div style={{ fontSize: 13, color: italic ? B.ink3 : B.ink2, marginTop: 2,
        fontStyle: italic ? 'italic' : 'normal', fontFamily: italic ? B.serif : B.sans, lineHeight: 1.4 }}>{text}</div>
    </div>
  );
}

// ═══ 2) 引用卡片 4 种样态 ═════════════════════════════════════════
function EntityCardsShowcase() {
  return (
    <div style={{ background: B.bg, height: '100%', fontFamily: B.sans, color: B.ink, paddingTop: 54, display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 20px' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 15, color: B.ink2 }}>
          <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={B.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
        </span>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontFamily: B.serif, fontSize: 15, fontWeight: 500 }}>深圳半导体工厂扩产</div>
          <div style={{ fontSize: 11, color: B.ink3 }}>5 人 · 招标中</div>
        </div>
        <span style={{ fontSize: 14, color: B.ink3 }}>···</span>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0 8px', background: B.bg }}>
        <Day label="今天 · 引用样态展示"/>

        {/* @ 项目 */}
        <BubbleRow avatar="陈" name="陈刚" time="09:08" text="项目卡片(#)— 嵌入到消息中" >
          <ProjectRefCard name="深圳半导体工厂扩产" stage="招标中" stageTone={B.accent} amount={320} owner="陈刚" region="深圳"/>
        </BubbleRow>

        {/* $ 客户 */}
        <BubbleRow avatar="李" name="李明" time="09:10" text="客户卡片($)— 跨项目讨论时引用">
          <CustomerRefCard name="上海宝山节能科技" tier="A" status="活跃" value={380.50} contact="李华 · 采购部经理"/>
        </BubbleRow>

        {/* § 合同 */}
        <BubbleRow avatar="王" name="王芳" time="09:14" text="合同卡片(§)— 关联到具体合同号">
          <ContractRefCard no="HT-2026-0312" name="节能改造一期主合同" amount={420} status="待签署" date="2026 · 05 · 15"/>
        </BubbleRow>

        {/* @ 人 */}
        <BubbleRow mine time="09:18" text="联系人卡片(@)— 介绍客户对接人,可一键拨打">
          <ContactRefCard name="李华" role="采购部经理" company="上海宝山节能科技" phone="138 0011 ****" />
        </BubbleRow>
      </div>

      {/* composer */}
      <div style={{ padding: '8px 12px 24px', borderTop: `1px solid ${B.divider}`, background: B.bg,
        display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: B.card, border: `1px solid ${B.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: B.ink2 }}>+</span>
        <div style={{ flex: 1, background: B.card, borderRadius: 20, border: `1px solid ${B.dividerStrong}`,
          padding: '9px 14px', fontFamily: B.serif, fontSize: 14, color: B.ink3, fontStyle: 'italic',
          display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ flex: 1 }}>说点什么…</span>
          <span style={{ fontSize: 11, color: B.ink4, fontStyle: 'normal', fontFamily: B.sans }}># $ § @</span>
        </div>
      </div>
    </div>
  );
}

function Day({ label }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: '6px 0 12px' }}>
      <span style={{ fontSize: 10, color: B.ink3, padding: '4px 12px', borderRadius: 999,
        background: B.card, border: `1px solid ${B.divider}`, letterSpacing: 0.5, textTransform: 'uppercase', fontWeight: 600 }}>{label}</span>
    </div>
  );
}

function BubbleRow({ avatar, name, time, text, mine, children }) {
  if (mine) {
    return (
      <div style={{ padding: '8px 16px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
        <div style={{ background: B.ink, color: '#fff', borderRadius: '14px 14px 4px 14px',
          padding: '10px 14px', maxWidth: 300, fontFamily: B.serif, fontSize: 14, lineHeight: 1.45 }}>{text}</div>
        <div style={{ marginTop: 6, maxWidth: 300 }}>{children}</div>
        <div style={{ fontSize: 10, color: B.ink3, marginTop: 4 }}>{time}</div>
      </div>
    );
  }
  return (
    <div style={{ padding: '8px 16px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
      <div style={{ width: 30, height: 30, borderRadius: 15, background: B.accentSoft, color: B.accent,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: B.serif, fontSize: 13, fontWeight: 600, flexShrink: 0 }}>{avatar}</div>
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 4 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: B.ink2 }}>{name}</span>
          <span style={{ fontSize: 10, color: B.ink3 }}>{time}</span>
        </div>
        <div style={{ background: B.card, borderRadius: '14px 14px 14px 4px', padding: '10px 14px',
          display: 'inline-block', maxWidth: 300, fontFamily: B.serif, fontSize: 14, lineHeight: 1.45,
          border: `1px solid ${B.divider}` }}>{text}</div>
        <div style={{ marginTop: 6, maxWidth: 300 }}>{children}</div>
      </div>
    </div>
  );
}

// ─── 4 种引用卡片 ─────────────────────────────────────────────────
function ProjectRefCard({ name, stage, stageTone, amount, owner, region }) {
  return (
    <div style={{ background: B.card, border: `1px solid ${B.dividerStrong}`, borderRadius: 12, padding: 12, display: 'flex', gap: 12 }}>
      <div style={{ width: 36, height: 36, borderRadius: 9, background: '#1A1A1A', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 700, flexShrink: 0 }}>#</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 9, color: B.ink3, letterSpacing: 1, fontWeight: 700 }}>项目</div>
        <div style={{ fontFamily: B.serif, fontSize: 14, fontWeight: 500, marginTop: 1, lineHeight: 1.3 }}>{name}</div>
        <div style={{ display: 'flex', gap: 8, marginTop: 5, fontSize: 11, color: B.ink3, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ color: stageTone, fontWeight: 600 }}>● {stage}</span>
          <span>·</span>
          <span style={{ color: B.ink, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>¥{amount}万</span>
          <span>·</span>
          <span>{owner} · {region}</span>
        </div>
      </div>
      <div style={{ alignSelf: 'center', color: B.ink3, fontSize: 18 }}>›</div>
    </div>
  );
}

function CustomerRefCard({ name, tier, status, value, contact }) {
  return (
    <div style={{ background: B.card, border: `1px solid ${B.dividerStrong}`, borderRadius: 12, padding: 12, display: 'flex', gap: 12 }}>
      <div style={{ width: 36, height: 36, borderRadius: 9, background: B.accent, color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700, flexShrink: 0,
        position: 'relative' }}>
        $
        <span style={{ position: 'absolute', bottom: -3, right: -3, width: 14, height: 14, borderRadius: 7,
          background: B.ink, color: '#fff', fontSize: 8, fontWeight: 700,
          display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 0 0 2px ${B.card}` }}>{tier}</span>
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 9, color: B.ink3, letterSpacing: 1, fontWeight: 700 }}>客户</div>
        <div style={{ fontFamily: B.serif, fontSize: 14, fontWeight: 500, marginTop: 1, lineHeight: 1.3 }}>{name}</div>
        <div style={{ display: 'flex', gap: 6, marginTop: 5, fontSize: 11, color: B.ink3, alignItems: 'center' }}>
          <span style={{ color: B.green, fontWeight: 600 }}>● {status}</span>
          <span>·</span>
          <span style={{ color: B.ink, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>¥{value}万</span>
        </div>
        <div style={{ fontSize: 11, color: B.ink3, marginTop: 3, fontStyle: 'italic', fontFamily: B.serif }}>{contact}</div>
      </div>
      <div style={{ alignSelf: 'center', color: B.ink3, fontSize: 18 }}>›</div>
    </div>
  );
}

function ContractRefCard({ no, name, amount, status, date }) {
  return (
    <div style={{ background: B.card, border: `1px solid ${B.dividerStrong}`, borderRadius: 12, padding: 12 }}>
      <div style={{ display: 'flex', gap: 12 }}>
        <div style={{ width: 36, height: 36, borderRadius: 9, background: '#0E1828', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 700, flexShrink: 0 }}>§</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
            <div style={{ fontSize: 9, color: B.ink3, letterSpacing: 1, fontWeight: 700 }}>合同</div>
            <span style={{ fontSize: 10, color: B.accent, fontWeight: 600, padding: '1px 7px', borderRadius: 999, background: B.accentBg }}>{status}</span>
          </div>
          <div style={{ fontFamily: B.serif, fontSize: 14, fontWeight: 500, marginTop: 1, lineHeight: 1.3 }}>{name}</div>
          <div style={{ fontSize: 11, color: B.ink3, marginTop: 3, fontVariantNumeric: 'tabular-nums', display: 'flex', gap: 8 }}>
            <span>{no}</span>
            <span>·</span>
            <span style={{ color: B.ink, fontWeight: 600 }}>¥{amount}万</span>
          </div>
        </div>
      </div>
      <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px dashed ${B.divider}`, display: 'flex', gap: 8 }}>
        <button style={{ flex: 1, fontSize: 12, padding: '7px 0', borderRadius: 8, border: `1px solid ${B.dividerStrong}`, background: 'transparent', color: B.ink2 }}>查看 PDF</button>
        <button style={{ flex: 1, fontSize: 12, padding: '7px 0', borderRadius: 8, border: 'none', background: B.ink, color: '#fff', fontWeight: 500 }}>去签署 →</button>
      </div>
    </div>
  );
}

function ContactRefCard({ name, role, company, phone }) {
  return (
    <div style={{ background: B.card, border: `1px solid ${B.dividerStrong}`, borderRadius: 12, padding: 12 }}>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <div style={{ width: 40, height: 40, borderRadius: 20, background: B.accentSoft, color: B.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: B.serif, fontSize: 16, fontWeight: 600, flexShrink: 0 }}>{name.charAt(0)}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 9, color: B.ink3, letterSpacing: 1, fontWeight: 700 }}>联系人</div>
          <div style={{ fontFamily: B.serif, fontSize: 14, fontWeight: 500, lineHeight: 1.3 }}>{name} · <span style={{ color: B.ink3, fontSize: 12 }}>{role}</span></div>
          <div style={{ fontSize: 11, color: B.ink3, marginTop: 2, fontStyle: 'italic', fontFamily: B.serif }}>{company}</div>
        </div>
      </div>
      <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px dashed ${B.divider}`,
        display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 12, color: B.ink2, fontVariantNumeric: 'tabular-nums', fontWeight: 500 }}>{phone}</span>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
          <button style={{ width: 32, height: 32, borderRadius: 16, border: `1px solid ${B.dividerStrong}`, background: 'transparent',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="13" height="13" viewBox="0 0 14 14"><path d="M3 2l2 3-1.5 1.5a8 8 0 004 4L9 9l3 2-1 2.5a1 1 0 01-1 .5C5.5 14 0 8.5 0 4a1 1 0 01.5-1L3 2z" fill={B.ink2}/></svg>
          </button>
          <button style={{ width: 32, height: 32, borderRadius: 16, background: B.accent, color: '#fff', border: 'none',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700 }}>+</button>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { ProjectDetailWithChat, EntityCardsShowcase });
