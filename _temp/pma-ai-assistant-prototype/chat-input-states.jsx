// PMA Chat · 输入栏状态扩展 — + 展开 / 录音 / 附件预览 / AI 文件分析
// 复用 chat-screens.jsx 的 CB / StatusPad / ChatNav

// 简易 status pad / nav 复用(独立定义,避免依赖加载顺序)
const CIS = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#C2BBB3',
  divider: 'rgba(0,0,0,0.06)', dividerStrong: 'rgba(0,0,0,0.10)',
  accent: '#D97757', accentSoft: '#F4E4D8', accentBg: 'rgba(217,119,87,0.08)',
  red: '#C44',
  blue: '#4D82E0', blueSoft: '#E5EDFA',
  serif: '"Tiempos Headline","Source Serif Pro","Noto Serif SC",Georgia,serif',
  sans: '-apple-system,"SF Pro Text","PingFang SC",system-ui,sans-serif',
};

function CISStatusPad() { return <div style={{ height: 54 }}/>; }

function CISNav({ title, sub }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', padding: '6px 16px 10px', gap: 10,
      borderBottom: `1px solid ${CIS.divider}`, background: CIS.bg,
    }}>
      <span style={{ fontSize: 22, color: CIS.ink2, padding: '0 4px' }}>‹</span>
      <div style={{ flex: 1, textAlign: 'center', minWidth: 0 }}>
        <div style={{ fontFamily: CIS.serif, fontSize: 16, fontWeight: 500, color: CIS.ink,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{title}</div>
        {sub && <div style={{ fontSize: 11, color: CIS.ink3, marginTop: 1 }}>{sub}</div>}
      </div>
      <div style={{ width: 24, fontSize: 18, color: CIS.ink3 }}>···</div>
    </div>
  );
}

function CISDay({ label }) {
  return (
    <div style={{ textAlign: 'center', padding: '14px 0 8px' }}>
      <span style={{ fontSize: 11, color: CIS.ink3, fontFamily: CIS.serif, fontStyle: 'italic',
        background: 'transparent', padding: '0 12px' }}>{label}</span>
    </div>
  );
}

// 简化版气泡(与主 chat 风格保持一致 — 仅用作背景)
function CISBubble({ mine, avatar, from, text, time, attached }) {
  return (
    <div style={{ padding: '6px 14px', display: 'flex', flexDirection: mine ? 'row-reverse' : 'row',
      alignItems: 'flex-start', gap: 8 }}>
      {!mine && (
        <div style={{ width: 30, height: 30, borderRadius: 15, background: CIS.accentSoft, color: CIS.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: CIS.serif,
          fontSize: 13, fontWeight: 600, flexShrink: 0 }}>{avatar}</div>
      )}
      <div style={{ maxWidth: 280, display: 'flex', flexDirection: 'column', alignItems: mine ? 'flex-end' : 'flex-start' }}>
        {!mine && from && <div style={{ fontSize: 11, color: CIS.ink3, marginBottom: 3, marginLeft: 2 }}>{from} · {time}</div>}
        <div style={{
          background: mine ? CIS.ink : CIS.card,
          color: mine ? '#fff' : CIS.ink,
          padding: '9px 13px', borderRadius: 14,
          fontFamily: CIS.serif, fontSize: 14.5, lineHeight: 1.5,
          border: mine ? 'none' : `1px solid ${CIS.divider}`,
        }}>{text}</div>
        {attached}
        {mine && <div style={{ fontSize: 11, color: CIS.ink3, marginTop: 3, marginRight: 2 }}>{time}</div>}
      </div>
    </div>
  );
}

// ═══ 1) + 展开面板 ════════════════════════════════════════════════════
function ChatPlusPanel() {
  const actions = [
    { label: '相册', color: CIS.accent, soft: CIS.accentSoft, icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="1.6"/>
        <circle cx="9" cy="10" r="1.6" fill="currentColor"/>
        <path d="M3 17l5-5 4 4 3-3 6 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    )},
    { label: '拍照', color: '#3a8c5a', soft: '#E2EFE6', icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
        <path d="M9 6l1.5-2h3L15 6h4a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h4z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
        <circle cx="12" cy="12.5" r="3.6" stroke="currentColor" strokeWidth="1.6"/>
      </svg>
    )},
    { label: '位置', color: CIS.blue, soft: CIS.blueSoft, icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
        <path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
        <circle cx="12" cy="9" r="2.4" stroke="currentColor" strokeWidth="1.6"/>
      </svg>
    )},
    { label: '文件', color: '#7355C9', soft: '#EBE4F8', icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
        <path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
        <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
        {/* 闪烁星 sparkle for AI */}
        <path d="M11 12.5l.6 1.5 1.5.6-1.5.6-.6 1.5-.6-1.5-1.5-.6 1.5-.6.6-1.5z" fill="currentColor"/>
      </svg>
    )},
  ];

  return (
    <div style={{ background: CIS.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: CIS.sans }}>
      <CISStatusPad/>
      <CISNav title="深圳半导体工厂扩产" sub="5 人 · 招标中"/>
      <div style={{ flex: 1, overflow: 'hidden', padding: '6px 0' }}>
        <CISDay label="今天"/>
        <CISBubble avatar="陈" from="陈刚" time="09:08" text="客户那边方案我已经看过初稿,下午开会过一遍。"/>
        <CISBubble avatar="李" from="李明" time="09:10" text="@张伟 配电图纸传给客户没?"/>
        <CISBubble mine time="09:12" text="还没,等下整理好一并发。"/>
      </div>

      {/* 收起态的输入栏(+ 已变成 ×, 占位提示) */}
      <div style={{ borderTop: `1px solid ${CIS.divider}`, background: CIS.bg }}>
        <div style={{ padding: '8px 12px 10px', display: 'flex', alignItems: 'flex-end', gap: 8 }}>
          {/* + 旋转 45° 表示展开 */}
          <span style={{ width: 36, height: 36, borderRadius: 18, background: CIS.ink, color: '#fff',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 200, lineHeight: 1, transform: 'rotate(45deg)' }}>+</span>
          <div style={{ flex: 1, background: CIS.card, borderRadius: 20, border: `1px solid ${CIS.dividerStrong}`,
            padding: '9px 14px', fontFamily: CIS.serif, fontSize: 14, color: CIS.ink3, fontStyle: 'italic',
            display: 'flex', alignItems: 'center', minHeight: 36 }}>
            说点什么…
          </div>
          {/* 麦克风 button */}
          <span style={{ width: 36, height: 36, borderRadius: 18, background: CIS.card, border: `1px solid ${CIS.dividerStrong}`,
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="6" y="2" width="4" height="8" rx="2" stroke={CIS.ink2} strokeWidth="1.4"/>
              <path d="M3.5 8a4.5 4.5 0 009 0M8 12.5V14" stroke={CIS.ink2} strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
          </span>
        </div>

        {/* expanded panel */}
        <div style={{ padding: '12px 24px 28px', background: CIS.bg, borderTop: `1px solid ${CIS.divider}`,
          display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, rowGap: 16 }}>
          {actions.map((a, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 60, height: 60, borderRadius: 18, background: CIS.card,
                border: `1px solid ${CIS.divider}`,
                color: a.color,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 1px 2px rgba(0,0,0,0.03)' }}>
                {a.icon}
              </div>
              <span style={{ fontSize: 12, color: CIS.ink2, fontWeight: 500 }}>{a.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ═══ 2) 录音中 ════════════════════════════════════════════════════════
function ChatRecording({ cancel = false }) {
  // 生成稳定的波形高度
  const bars = Array.from({ length: 38 }, (_, i) => {
    const s = Math.sin(i * 0.6) * 0.5 + 0.5;
    const r = ((i * 17) % 11) / 11;
    return 8 + (s * 0.6 + r * 0.4) * 38;
  });

  return (
    <div style={{ background: CIS.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: CIS.sans, position: 'relative' }}>
      <CISStatusPad/>
      <CISNav title="李明" sub="产品经理"/>
      <div style={{ flex: 1, overflow: 'hidden', padding: '6px 0', opacity: 0.45 }}>
        <CISDay label="今天"/>
        <CISBubble avatar="李" from="李明" time="09:14" text="方案 PDF 看到了,下午一起对一遍?"/>
      </div>

      {/* 上滑取消提示 */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 220, textAlign: 'center', pointerEvents: 'none' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          padding: '10px 18px',
          borderRadius: 999,
          background: cancel ? CIS.red : CIS.ink,
          color: '#fff', fontSize: 13, fontWeight: 500,
        }}>
          {cancel ? (
            <>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 11l8-8M3 3l8 8" stroke="#fff" strokeWidth="1.6" strokeLinecap="round"/>
              </svg>
              松开手指 · 取消发送
            </>
          ) : (
            <>
              <svg width="12" height="12" viewBox="0 0 14 14" fill="none">
                <path d="M7 11V3M3 7l4-4 4 4" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              上滑取消
            </>
          )}
        </div>
      </div>

      {/* 录音核心区 — 替代 composer */}
      <div style={{ borderTop: `1px solid ${CIS.divider}`, background: CIS.bg, padding: '20px 20px 28px' }}>
        {/* 顶行 — 文字提示 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: CIS.ink3 }}>
            <span style={{ width: 7, height: 7, borderRadius: 4, background: CIS.red,
              animation: 'cisPulse 1.2s infinite' }}/>
            录音中
          </span>
          <span style={{ fontFamily: CIS.mono || 'monospace', fontSize: 14, color: CIS.ink, fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
            00:08
          </span>
        </div>
        <style>{`@keyframes cisPulse{0%,100%{opacity:.4}50%{opacity:1}}`}</style>

        {/* waveform */}
        <div style={{
          background: cancel ? '#FBE5E5' : CIS.card,
          border: `1px solid ${cancel ? '#F4C8C8' : CIS.divider}`,
          borderRadius: 18,
          padding: '20px 16px',
          display: 'flex', alignItems: 'center', gap: 3, justifyContent: 'center',
          height: 70,
        }}>
          {bars.map((h, i) => (
            <span key={i} style={{
              width: 3, height: h, borderRadius: 2,
              background: cancel ? CIS.red : CIS.accent,
              opacity: i < 26 ? 1 : 0.25,
            }}/>
          ))}
        </div>

        {/* mic 按钮 — 大圆按下态 */}
        <div style={{ marginTop: 18, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 28 }}>
          <span style={{ fontSize: 11, color: CIS.ink3, width: 60, textAlign: 'right' }}>松开 · 发送</span>
          <span style={{
            width: 76, height: 76, borderRadius: 38,
            background: cancel ? CIS.red : CIS.accent,
            color: '#fff',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: cancel ? `0 0 0 8px rgba(196,68,68,0.18)` : `0 0 0 8px ${CIS.accentSoft}`,
            transform: cancel ? 'translateY(-6px)' : 'none',
            transition: 'all .15s',
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <rect x="9" y="3" width="6" height="11" rx="3" fill="#fff"/>
              <path d="M5 12a7 7 0 0014 0M12 19v3" stroke="#fff" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </span>
          <span style={{ fontSize: 11, color: cancel ? CIS.red : CIS.ink3, width: 60, fontWeight: cancel ? 600 : 400 }}>
            {cancel ? '已上滑' : '上滑 · 取消'}
          </span>
        </div>
      </div>
    </div>
  );
}

function ChatRecordingCancel() { return <ChatRecording cancel/>; }

// ═══ 3) 附件预览栏(选了图后) ═══════════════════════════════════════
function ChatAttachPreview() {
  // 三张缩略图 placeholder
  const photos = [
    { c1: '#E5DCC8', c2: '#C8B89A' },
    { c1: '#D6E0EA', c2: '#A8BACE' },
    { c1: '#E8D6D0', c2: '#C9A99E' },
  ];

  return (
    <div style={{ background: CIS.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: CIS.sans }}>
      <CISStatusPad/>
      <CISNav title="深圳半导体工厂扩产" sub="5 人 · 招标中"/>
      <div style={{ flex: 1, overflow: 'hidden', padding: '6px 0' }}>
        <CISDay label="今天"/>
        <CISBubble avatar="李" from="李明" time="09:10" text="@张伟 现场照片发一下"/>
      </div>

      <div style={{ borderTop: `1px solid ${CIS.divider}`, background: CIS.bg }}>
        {/* 预览条 */}
        <div style={{ padding: '12px 12px 8px', borderBottom: `1px solid ${CIS.divider}`,
          display: 'flex', alignItems: 'center', gap: 8, overflowX: 'auto' }}>
          {photos.map((p, i) => (
            <div key={i} style={{ position: 'relative', flexShrink: 0 }}>
              <div style={{
                width: 64, height: 64, borderRadius: 12,
                background: `linear-gradient(135deg, ${p.c1}, ${p.c2})`,
                border: `1px solid ${CIS.divider}`,
                position: 'relative',
                overflow: 'hidden',
              }}>
                {/* 假装是机房 / 配电 / 现场 — 用低保真 svg 形态点缀 */}
                <svg width="64" height="64" viewBox="0 0 64 64" style={{ opacity: 0.55 }}>
                  <rect x="14" y="20" width="14" height="28" fill="rgba(0,0,0,0.18)"/>
                  <rect x="34" y="14" width="14" height="34" fill="rgba(0,0,0,0.22)"/>
                  <path d="M0 48 L20 38 L34 44 L48 36 L64 44 L64 64 L0 64 Z" fill="rgba(0,0,0,0.10)"/>
                </svg>
              </div>
              {/* 删除按钮 */}
              <span style={{ position: 'absolute', top: -5, right: -5, width: 18, height: 18, borderRadius: 9,
                background: CIS.ink, color: '#fff', fontSize: 11, lineHeight: '18px', textAlign: 'center', fontWeight: 300 }}>×</span>
            </div>
          ))}
          {/* 加号 — 继续添加 */}
          <span style={{
            flexShrink: 0, width: 64, height: 64, borderRadius: 12,
            border: `1px dashed ${CIS.dividerStrong}`,
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            color: CIS.ink3, fontSize: 22, fontWeight: 200,
          }}>+</span>
        </div>

        {/* 输入栏(改为「发送」按钮亮起) */}
        <div style={{ padding: '8px 12px 24px', display: 'flex', alignItems: 'flex-end', gap: 8 }}>
          <span style={{ width: 36, height: 36, borderRadius: 18, background: CIS.card, border: `1px solid ${CIS.dividerStrong}`,
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: CIS.ink2, fontWeight: 300 }}>+</span>
          <div style={{ flex: 1, background: CIS.card, borderRadius: 20, border: `1px solid ${CIS.dividerStrong}`,
            padding: '9px 14px', fontFamily: CIS.serif, fontSize: 14, color: CIS.ink, minHeight: 36, display: 'flex', alignItems: 'center' }}>
            周三现场情况,3 张
            <span style={{ width: 1.5, height: 16, background: CIS.accent, marginLeft: 1, animation: 'cisBlink 1s infinite' }}/>
          </div>
          <style>{`@keyframes cisBlink{0%,49%{opacity:1}50%,100%{opacity:0}}`}</style>
          <span style={{
            padding: '8px 16px', borderRadius: 18,
            background: CIS.accent, color: '#fff', fontSize: 13, fontWeight: 600,
          }}>发送 · 3</span>
        </div>
      </div>
    </div>
  );
}

// ═══ 4) AI 文件分析 ════════════════════════════════════════════════════
function ChatAnalyzeFile() {
  return (
    <div style={{ background: CIS.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: CIS.sans }}>
      <CISStatusPad/>
      <CISNav title="源助手 · AI" sub="项目助手 · 在线"/>
      <div style={{ flex: 1, overflow: 'auto', padding: '6px 0' }}>
        <CISDay label="今天"/>
        <CISBubble avatar="AI" from="源助手" time="09:08"
          text="把图纸或合同丢进来,我可以帮你提关键参数、风险点、里程碑。"/>
        <CISBubble mine time="09:14" text="我先看一下这份招标文件。"/>

        {/* 用户上传的文件气泡 */}
        <div style={{ padding: '4px 14px', display: 'flex', justifyContent: 'flex-end' }}>
          <div style={{
            background: CIS.ink, color: '#fff', borderRadius: 14,
            padding: '12px 14px', display: 'flex', alignItems: 'center', gap: 12, maxWidth: 280,
          }}>
            <span style={{
              width: 36, height: 44, borderRadius: 6, background: 'rgba(255,255,255,0.12)',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 9, fontWeight: 700, letterSpacing: 0.5, fontFamily: CIS.mono,
              border: '1px solid rgba(255,255,255,0.2)',
            }}>PDF</span>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontFamily: CIS.serif, fontSize: 14, fontWeight: 500, overflow: 'hidden',
                textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                深铁阅洺境招标书.pdf
              </div>
              <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>2.4 MB · 47 页</div>
            </div>
          </div>
        </div>

        {/* AI 分析卡片 — 紫色 accent */}
        <div style={{ padding: '8px 14px' }}>
          <div style={{
            background: '#FAF8FE', border: '1px solid #E5DCFA', borderRadius: 14,
            padding: '12px 14px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <span style={{
                width: 22, height: 22, borderRadius: 11,
                background: 'linear-gradient(135deg, #7355C9, #4D82E0)',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <svg width="11" height="11" viewBox="0 0 12 12" fill="#fff">
                  <path d="M6 1l1.2 3 3 1.2-3 1.2L6 9.4 4.8 6.4 1.8 5.2l3-1.2L6 1z"/>
                </svg>
              </span>
              <span style={{ fontSize: 12, color: '#7355C9', fontWeight: 600, letterSpacing: 0.3 }}>分析完成 · 47 页 · 用时 11s</span>
            </div>

            <div style={{ fontFamily: CIS.serif, fontSize: 14, color: CIS.ink, lineHeight: 1.6, marginBottom: 12 }}>
              这是一份住宅 + 商业综合体的智能化招标。<strong style={{ fontWeight: 600 }}>预算上限 4,800 万</strong>,
              要求 7 月 31 日前提交方案。我提取了 5 个关键点 ——
            </div>

            {/* 提取的要点 */}
            <div style={{ display: 'grid', gap: 8 }}>
              {[
                ['💰', '预算', '总包 ≤ 4,800 万'],
                ['📅', '关键节点', '7-31 提案 · 9-15 中标 · 12-1 进场'],
                ['⚙', '系统范围', '楼宇自控 / 安防 / 信息发布 / 一卡通'],
                ['⚠', '风险', '资质要求一级,需联合体投标'],
                ['📍', '现场', '龙岗区宝龙街道站前路3号'],
              ].map(([emoji, k, v], i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10,
                  padding: '6px 0', borderTop: i ? `1px solid ${CIS.divider}` : 'none' }}>
                  <span style={{ fontSize: 14, width: 16, textAlign: 'center', flexShrink: 0,
                    fontFamily: CIS.serif, color: '#7355C9', fontWeight: 600 }}>{emoji}</span>
                  <span style={{ fontSize: 12, color: CIS.ink3, width: 60, flexShrink: 0, paddingTop: 1 }}>{k}</span>
                  <span style={{ fontSize: 13, color: CIS.ink, flex: 1, fontWeight: 500 }}>{v}</span>
                </div>
              ))}
            </div>

            {/* 后续操作 chip */}
            <div style={{ marginTop: 12, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {['生成内部立项卡', '检查我们的资质', '排个时间表'].map((t, i) => (
                <span key={i} style={{
                  fontSize: 12, padding: '6px 11px', borderRadius: 999,
                  background: '#fff', border: '1px solid #E5DCFA', color: '#7355C9', fontWeight: 500,
                }}>{t}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* composer */}
      <div style={{ borderTop: `1px solid ${CIS.divider}`, background: CIS.bg,
        padding: '8px 12px 24px', display: 'flex', alignItems: 'flex-end', gap: 8 }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: CIS.card, border: `1px solid ${CIS.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: CIS.ink2, fontWeight: 300 }}>+</span>
        <div style={{ flex: 1, background: CIS.card, borderRadius: 20, border: `1px solid ${CIS.dividerStrong}`,
          padding: '9px 14px', fontFamily: CIS.serif, fontSize: 14, color: CIS.ink3, fontStyle: 'italic',
          minHeight: 36, display: 'flex', alignItems: 'center' }}>
          继续追问…
        </div>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: CIS.card, border: `1px solid ${CIS.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="6" y="2" width="4" height="8" rx="2" stroke={CIS.ink2} strokeWidth="1.4"/>
            <path d="M3.5 8a4.5 4.5 0 009 0M8 12.5V14" stroke={CIS.ink2} strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
        </span>
      </div>
    </div>
  );
}

Object.assign(window, { ChatPlusPanel, ChatRecording, ChatRecordingCancel, ChatAttachPreview, ChatAnalyzeFile });
