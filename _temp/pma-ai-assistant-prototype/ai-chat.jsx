// PMA · AI 聊天「源助手」
// 5 屏:新建聊天选择器 / AI 一对一 / 群里 @AI / 私聊里 @AI 起草 / 会话列表 AI 入口

const AI = {
  bg: '#F7F5F2', card: '#FFFFFF',
  ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#C2BBB3',
  divider: 'rgba(0,0,0,0.06)', dividerStrong: 'rgba(0,0,0,0.10)',
  accent: '#D97757', accentSoft: '#F4E4D8', accentBg: 'rgba(217,119,87,0.08)',
  // AI 专属冷色系,与 PMA 像素蓝品牌一致
  ai: '#2F66D6',         // AI 主色 · PMA pixel blue (deeper)
  aiSoft: '#E5EEFB',     // AI 浅底
  aiBg: 'rgba(47,102,214,0.06)',
  aiInk: '#1E4FAA',
  green: '#2F7A45',
  serif: '"Tiempos Headline","Source Serif Pro","Noto Serif SC",Georgia,serif',
  sans: '-apple-system,"SF Pro Text","PingFang SC",system-ui,sans-serif',
};

function StatusPad() { return <div style={{ height: 54 }}/>; }

// PMA 像素 P logo —— 与 splash 用的 PixelP 一致
const AI_PIXEL_P = [
  { r: 0, c: 1, t: 'b' }, { r: 0, c: 2, t: 'b' }, { r: 0, c: 3, t: 'b' }, { r: 0, c: 4, t: 'b' },
  { r: 1, c: 1, t: 'b' }, { r: 1, c: 4, t: 'b' },
  { r: 2, c: 1, t: 'b' }, { r: 2, c: 3, t: 'w' }, { r: 2, c: 4, t: 'h' }, { r: 2, c: 5, t: 'b' },
  { r: 3, c: 1, t: 'b' }, { r: 3, c: 2, t: 'b' }, { r: 3, c: 3, t: 'b' }, { r: 3, c: 4, t: 'b' },
  { r: 4, c: 1, t: 'b' }, { r: 4, c: 2, t: 'd' },
  { r: 5, c: 1, t: 'b' }, { r: 5, c: 2, t: 'd' },
];

function AILogo({ size = 28 }) {
  // 纯像素 P,无外框无背景 — 像素方块直接漂在浅底上
  const cell = size / 6.6;
  const gap = cell * 0.16;
  const totalW = cell * 6 + gap * 5;
  const totalH = cell * 6 + gap * 5;
  return (
    <div style={{ width: size, height: size, position: 'relative', flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: totalW, height: totalH, position: 'relative' }}>
        {AI_PIXEL_P.map(p => {
          // 'h'(hole)在无背景版下没意义,跳过
          if (p.t === 'h') return null;
          // 'w' 高亮像素改成 pixel-blue 浅色,免得空白
          const color = p.t === 'b' ? '#2F66D6' : p.t === 'd' ? '#1E4FAA' : p.t === 'w' ? '#7FA6E8' : 'transparent';
          return (
            <div key={`${p.r}-${p.c}`} style={{
              position: 'absolute',
              left: p.c * (cell + gap),
              top: p.r * (cell + gap),
              width: cell, height: cell,
              background: color, borderRadius: cell * 0.18,
            }}/>
          );
        })}
      </div>
    </div>
  );
}

// ═══ 1) 新建聊天选择器 ════════════════════════════════════════════
function NewChatPicker() {
  return (
    <div style={{ background: AI.bg, height: '100%', fontFamily: AI.sans, color: AI.ink, paddingTop: 54 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 20px' }}>
        <span style={{ color: AI.accent, fontSize: 15 }}>取消</span>
        <span style={{ fontFamily: AI.serif, fontSize: 16, fontWeight: 500 }}>发起聊天</span>
        <span style={{ width: 30 }}/>
      </div>

      <div style={{ padding: '20px 28px 0' }}>
        <div style={{ fontFamily: AI.serif, fontSize: 22, fontWeight: 500, lineHeight: 1.3 }}>
          想和谁聊?
        </div>
        <div style={{ fontSize: 13, color: AI.ink3, marginTop: 6, fontStyle: 'italic', fontFamily: AI.serif }}>
          选一个开始 · 也可以先问 AI 助手
        </div>
      </div>

      <div style={{ padding: '24px 20px 0', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {/* AI 助手 — 主推 */}
        <button style={{ background: AI.card, border: `2px solid ${AI.ai}`, borderRadius: 16, padding: 18,
          textAlign: 'left', display: 'flex', gap: 14, alignItems: 'flex-start', position: 'relative' }}>
          <AILogo size={36}/>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontFamily: AI.serif, fontSize: 17, fontWeight: 600 }}>源助手 AI</span>
              <span style={{ fontSize: 9, fontWeight: 700, color: AI.ai, padding: '2px 6px', borderRadius: 4, background: AI.aiSoft, letterSpacing: 0.5 }}>BETA</span>
            </div>
            <div style={{ fontSize: 12, color: AI.ink3, marginTop: 4, lineHeight: 1.5 }}>
              你的销售助理 · 知道你所有项目、客户、跟进记录,可以总结、起草、分析。
            </div>
            <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
              {['/分析赢率','/起草回复','/总结群消息'].map(t => (
                <span key={t} style={{ fontSize: 10, color: AI.ai, padding: '3px 8px', borderRadius: 999,
                  background: AI.aiSoft, fontFamily: 'ui-monospace,monospace' }}>{t}</span>
              ))}
            </div>
          </div>
          <span style={{ position: 'absolute', top: 14, right: 14, fontSize: 11, color: AI.ai, fontWeight: 600 }}>推荐 →</span>
        </button>

        {/* 私聊同事 */}
        <button style={{ background: AI.card, border: `1px solid ${AI.divider}`, borderRadius: 16, padding: 18,
          textAlign: 'left', display: 'flex', gap: 14, alignItems: 'center' }}>
          <div style={{ width: 44, height: 44, borderRadius: 14, background: AI.accentSoft, color: AI.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="6" r="3" stroke="currentColor" strokeWidth="1.6"/>
              <path d="M3 17c0-3.5 3-6.5 7-6.5s7 3 7 6.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: AI.serif, fontSize: 16, fontWeight: 500 }}>私聊同事</div>
            <div style={{ fontSize: 12, color: AI.ink3, marginTop: 3 }}>从通讯录选 1 人,开始一对一对话</div>
          </div>
          <span style={{ color: AI.ink3, fontSize: 18 }}>›</span>
        </button>

        {/* 创建项目群 */}
        <button style={{ background: AI.card, border: `1px solid ${AI.divider}`, borderRadius: 16, padding: 18,
          textAlign: 'left', display: 'flex', gap: 14, alignItems: 'center' }}>
          <div style={{ width: 44, height: 44, borderRadius: 14, background: '#1A1A1A', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <circle cx="7" cy="7" r="2.5" stroke="currentColor" strokeWidth="1.5"/>
              <circle cx="14" cy="8" r="2" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M2 16c0-2.5 2-4.5 5-4.5s5 2 5 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              <path d="M11 16c0-2 1.5-3.5 3.5-3.5s3.5 1.5 3.5 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: AI.serif, fontSize: 16, fontWeight: 500 }}>项目群</div>
            <div style={{ fontSize: 12, color: AI.ink3, marginTop: 3 }}>选一个项目 · 自动拉相关人 · 群内可 @AI</div>
          </div>
          <span style={{ color: AI.ink3, fontSize: 18 }}>›</span>
        </button>
      </div>

      <div style={{ padding: '24px 28px', fontSize: 11, color: AI.ink3, fontStyle: 'italic',
        fontFamily: AI.serif, textAlign: 'center' }}>
        群和私聊里都可以 @源助手 提问,无需切换
      </div>
    </div>
  );
}

// ═══ 2) AI 一对一聊天 ═════════════════════════════════════════════
function AIOneOnOne() {
  return (
    <div style={{ background: AI.bg, height: '100%', fontFamily: AI.sans, color: AI.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      {/* nav */}
      <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: `1px solid ${AI.divider}`, background: AI.card }}>
        <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={AI.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
        <AILogo size={26}/>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontFamily: AI.serif, fontSize: 15, fontWeight: 600 }}>源助手</span>
            <span style={{ fontSize: 9, fontWeight: 700, color: AI.ai, padding: '1px 5px', borderRadius: 3, background: AI.aiSoft }}>BETA</span>
          </div>
          <div style={{ fontSize: 11, color: AI.green, marginTop: 1 }}>● 在线 · 已连接你的 6 个项目</div>
        </div>
        <span style={{ fontSize: 18, color: AI.ink3 }}>···</span>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        {/* 用户提问 */}
        <UserBubble time="14:21" text="帮我分析一下宝山节能这个客户的赢率怎么样?最近的项目有几个有戏?"/>

        {/* AI 回答 */}
        <AIBubble time="14:21" thinking={false}>
          <div>结合我看到的数据,<b>宝山节能整体赢率较高(约 72%)</b>,主要原因有三点:</div>
          <ol style={{ margin: '8px 0', paddingLeft: 20, lineHeight: 1.8 }}>
            <li>是老客户,过往合作 2 个签约项目</li>
            <li>主要联系人 <b>李华</b>(采购部经理)对你信任度高</li>
            <li>名下进行中 3 个项目,其中 1 个已到「招标中」</li>
          </ol>
          <div>名下项目中,<b>「宝山节能改造项目」</b>最值得重点跟进:</div>
          <AIRefCard kind="project" name="宝山节能改造项目" stage="招标中" amount="42.50"/>
          <div style={{ fontSize: 11, color: AI.ink3, marginTop: 10, fontStyle: 'italic', fontFamily: AI.serif }}>
            数据来源:6 个名下项目 · 12 条跟进记录 · 上次拜访 04 · 22
          </div>
        </AIBubble>

        {/* AI 建议追问 */}
        <SuggestRow tags={['这个项目下一步该做什么?', '帮我起草约见短信', '其他客户对比一下']}/>

        {/* 用户继续 */}
        <UserBubble time="14:24" text="帮我起草约见短信"/>

        {/* AI 思考中 */}
        <AIBubble time="14:24" thinking/>
      </div>

      {/* composer with quick commands */}
      <div style={{ borderTop: `1px solid ${AI.divider}`, background: AI.card }}>
        <div style={{ padding: '8px 12px 6px', display: 'flex', gap: 6, overflowX: 'auto' }}>
          {['/起草回复','/分析赢率','/总结群消息','/查合同','/找联系人'].map(t => (
            <span key={t} style={{ flexShrink: 0, fontSize: 11, color: AI.ai,
              padding: '5px 10px', borderRadius: 999, background: AI.aiSoft, fontFamily: 'ui-monospace,monospace' }}>{t}</span>
          ))}
        </div>
        <div style={{ padding: '4px 12px 24px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 36, height: 36, borderRadius: 18, background: AI.bg, border: `1px solid ${AI.dividerStrong}`,
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: AI.ink2 }}>+</span>
          <div style={{ flex: 1, background: AI.bg, borderRadius: 20, border: `1.5px solid ${AI.ai}`,
            padding: '9px 14px', fontFamily: AI.serif, fontSize: 14, color: AI.ink, display: 'flex', alignItems: 'center' }}>
            <span style={{ flex: 1 }}>
              帮我起草约见短信
              <span style={{ display: 'inline-block', width: 2, height: 16, background: AI.ai, marginLeft: 1,
                animation: 'aiBlink 1s infinite' }}/>
            </span>
          </div>
          <button style={{ width: 36, height: 36, borderRadius: 18, background: AI.ai, color: '#fff', border: 'none',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700 }}>↑</button>
        </div>
      </div>
      <style>{`@keyframes aiBlink{0%,49%{opacity:1}50%,100%{opacity:0}}@keyframes aiDot{0%,80%,100%{opacity:0.3}40%{opacity:1}}`}</style>
    </div>
  );
}

function UserBubble({ time, text }) {
  return (
    <div style={{ padding: '6px 16px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
      <div style={{ background: AI.ink, color: '#fff', borderRadius: '14px 14px 4px 14px',
        padding: '10px 14px', maxWidth: 300, fontFamily: AI.serif, fontSize: 14, lineHeight: 1.5 }}>{text}</div>
      <div style={{ fontSize: 10, color: AI.ink3, marginTop: 4 }}>{time}</div>
    </div>
  );
}

function AIBubble({ time, thinking, children, compact }) {
  return (
    <div style={{ padding: '6px 16px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
      <AILogo size={22}/>
      <div style={{ flex: 1, minWidth: 0 }}>
        {!compact && <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 4 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: AI.aiInk }}>源助手</span>
          <span style={{ fontSize: 10, color: AI.ink3 }}>{time}</span>
        </div>}
        <div style={{ background: AI.aiBg, border: `1px solid rgba(47,102,214,0.18)`, borderRadius: '4px 14px 14px 14px',
          padding: '12px 14px', fontFamily: AI.serif, fontSize: 14, lineHeight: 1.55, color: AI.ink }}>
          {thinking ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
              <span style={{ display: 'inline-flex', gap: 3 }}>
                {[0,1,2].map(i => <span key={i} style={{ width: 6, height: 6, borderRadius: 3, background: AI.ai,
                  animation: `aiDot 1.4s ${i * 0.16}s infinite` }}/>)}
              </span>
              <span style={{ fontSize: 12, color: AI.ink3, fontStyle: 'italic' }}>正在分析你的项目数据…</span>
            </div>
          ) : children}
        </div>
        {!thinking && !compact && (
          <div style={{ display: 'flex', gap: 14, marginTop: 6, fontSize: 11, color: AI.ink3 }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path d="M3 6h6M6 3l3 3-3 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
              </svg>重新生成
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <rect x="2" y="2" width="6" height="8" rx="1" stroke="currentColor" strokeWidth="1.2"/>
                <path d="M4 5h2M4 7h2" stroke="currentColor" strokeWidth="1.2"/>
              </svg>复制
            </span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>👍</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>👎</span>
          </div>
        )}
      </div>
    </div>
  );
}

function AIRefCard({ kind, name, stage, amount }) {
  return (
    <div style={{ marginTop: 8, background: AI.card, border: `1px solid ${AI.dividerStrong}`,
      borderRadius: 10, padding: '10px 12px', display: 'flex', gap: 10, alignItems: 'center' }}>
      <div style={{ width: 30, height: 30, borderRadius: 8, background: '#1A1A1A', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700 }}>#</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: AI.serif, fontSize: 13, fontWeight: 500, lineHeight: 1.3 }}>{name}</div>
        <div style={{ display: 'flex', gap: 8, marginTop: 2, fontSize: 11, color: AI.ink3 }}>
          <span style={{ color: AI.accent, fontWeight: 600 }}>● {stage}</span>
          <span>·</span>
          <span style={{ color: AI.ink, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>¥{amount}万</span>
        </div>
      </div>
      <span style={{ color: AI.ink3, fontSize: 14 }}>›</span>
    </div>
  );
}

function SuggestRow({ tags }) {
  return (
    <div style={{ padding: '6px 16px 6px 54px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
      {tags.map((t, i) => (
        <span key={i} style={{ fontSize: 12, padding: '6px 12px', borderRadius: 999,
          border: `1px solid ${AI.dividerStrong}`, background: AI.card, color: AI.ink2,
          fontFamily: AI.serif, fontStyle: 'italic' }}>{t}</span>
      ))}
    </div>
  );
}

// ═══ 3) 项目群里 @AI ═════════════════════════════════════════════
function GroupAtAI() {
  return (
    <div style={{ background: AI.bg, height: '100%', fontFamily: AI.sans, color: AI.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: `1px solid ${AI.divider}`, background: AI.card }}>
        <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={AI.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: AI.serif, fontSize: 15, fontWeight: 600 }}>深圳半导体工厂扩产</div>
          <div style={{ fontSize: 11, color: AI.ink3 }}>5 人 + 源助手 · 招标中</div>
        </div>
        <span style={{ fontSize: 18, color: AI.ink3 }}>···</span>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        {/* 一条普通消息 */}
        <div style={{ padding: '6px 16px', display: 'flex', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 14, background: AI.accentSoft, color: AI.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: AI.serif, fontSize: 12, fontWeight: 600 }}>李</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: AI.ink2, marginBottom: 4 }}>李明 · 09:32</div>
            <div style={{ background: AI.card, border: `1px solid ${AI.divider}`, borderRadius: '14px 14px 14px 4px',
              padding: '10px 14px', display: 'inline-block', maxWidth: 300, fontFamily: AI.serif, fontSize: 14, lineHeight: 1.45 }}>
              <span style={{ color: AI.ai, fontWeight: 600 }}>@源助手</span> 帮我们总结一下这个项目最近的进展,要发周报。
            </div>
          </div>
        </div>

        {/* AI 公开回答 */}
        <AIBubble time="09:32">
          <div style={{ fontSize: 11, color: AI.ai, fontWeight: 600, marginBottom: 4 }}>📊 项目周报 · 第 17 周</div>
          <div><b>深圳半导体工厂扩产</b>本周关键进展:</div>
          <ol style={{ margin: '8px 0', paddingLeft: 20, lineHeight: 1.8 }}>
            <li>04 · 25 阶段从「嵌入」推进到「招标中」(陈刚)</li>
            <li>04 · 26 客户方案 V1 已交付,正在评审</li>
            <li>本周新增 2 条跟进 · 群内消息 38 条</li>
          </ol>
          <div style={{ fontSize: 12, color: AI.ink3, fontStyle: 'italic', fontFamily: AI.serif, marginTop: 6 }}>
            ⚠️ 提示:标书 V2 截止 周五,目前进度待跟进
          </div>
        </AIBubble>

        {/* 群里其他成员追问 */}
        <div style={{ padding: '6px 16px', display: 'flex', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 14, background: AI.accentSoft, color: AI.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: AI.serif, fontSize: 12, fontWeight: 600 }}>陈</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: AI.ink2, marginBottom: 4 }}>陈刚 · 09:34</div>
            <div style={{ background: AI.card, border: `1px solid ${AI.divider}`, borderRadius: '14px 14px 14px 4px',
              padding: '10px 14px', display: 'inline-block', maxWidth: 300, fontFamily: AI.serif, fontSize: 14, lineHeight: 1.45 }}>
              <span style={{ color: AI.ai, fontWeight: 600 }}>@源助手</span> 把这段总结导出成飞书可以贴的格式
            </div>
          </div>
        </div>
        <AIBubble time="09:34" thinking/>
      </div>

      <div style={{ padding: '8px 12px 24px', borderTop: `1px solid ${AI.divider}`, background: AI.card,
        display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: AI.bg, border: `1px solid ${AI.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: AI.ink2 }}>+</span>
        <div style={{ flex: 1, background: AI.bg, borderRadius: 20, border: `1px solid ${AI.dividerStrong}`,
          padding: '9px 14px', fontFamily: AI.serif, fontSize: 14, color: AI.ink3, fontStyle: 'italic',
          display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ flex: 1 }}>说点什么…</span>
          <span style={{ fontSize: 11, color: AI.ai, fontWeight: 700, fontStyle: 'normal', fontFamily: 'ui-monospace,monospace' }}>@AI</span>
          <span style={{ fontSize: 11, color: AI.ink4, fontStyle: 'normal', fontFamily: AI.sans }}># $</span>
        </div>
      </div>
    </div>
  );
}

// ═══ 4) 私聊里 @AI 起草草稿 ═══════════════════════════════════════
function DMAIDraft() {
  return (
    <div style={{ background: AI.bg, height: '100%', fontFamily: AI.sans, color: AI.ink, paddingTop: 54,
      display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: `1px solid ${AI.divider}`, background: AI.card }}>
        <svg width="9" height="14" viewBox="0 0 9 14"><path d="M7 1L1 7l6 6" fill="none" stroke={AI.ink2} strokeWidth="1.6" strokeLinecap="round"/></svg>
        <div style={{ width: 30, height: 30, borderRadius: 15, background: AI.accentSoft, color: AI.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: AI.serif, fontSize: 13, fontWeight: 600 }}>李</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontFamily: AI.serif, fontSize: 15, fontWeight: 600 }}>李华</div>
          <div style={{ fontSize: 11, color: AI.ink3 }}>采购部经理 · 上海宝山节能科技</div>
        </div>
        <span style={{ fontSize: 18, color: AI.ink3 }}>···</span>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: '12px 0' }}>
        {/* 对方消息 */}
        <div style={{ padding: '6px 16px', display: 'flex', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 14, background: AI.accentSoft, color: AI.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: AI.serif, fontSize: 12, fontWeight: 600 }}>李</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 11, color: AI.ink3, marginBottom: 4 }}>昨天 17:42</div>
            <div style={{ background: AI.card, border: `1px solid ${AI.divider}`, borderRadius: '14px 14px 14px 4px',
              padding: '10px 14px', display: 'inline-block', maxWidth: 300, fontFamily: AI.serif, fontSize: 14, lineHeight: 1.45 }}>
              方案我看过了。报价能不能再优化一下?另外工期希望压缩到 90 天。
            </div>
          </div>
        </div>

        <div style={{ padding: '20px 16px 8px', display: 'flex', justifyContent: 'center' }}>
          <span style={{ fontSize: 10, color: AI.ai, padding: '4px 10px', borderRadius: 999,
            background: AI.aiSoft, fontWeight: 600, letterSpacing: 0.5 }}>✨ 仅你可见 · AI 草稿区</span>
        </div>

        {/* AI 起草草稿(仅当前用户可见) */}
        <AIBubble time="今天 09:12">
          <div style={{ fontSize: 11, color: AI.ai, fontWeight: 600, marginBottom: 6 }}>建议回复 · 已结合客户偏好与历史报价</div>
          <div style={{ background: AI.card, border: `1px dashed ${AI.dividerStrong}`, borderRadius: 8,
            padding: '10px 12px', fontFamily: AI.serif, fontSize: 14, lineHeight: 1.6, color: AI.ink, marginTop: 4 }}>
            李经理您好,报价方面我这边已经申请到约 5% 的让利空间,稍后单独发您。工期方面,90 天是有挑战但可以做,前提是设备分两批进场。今晚我先把更新版方案发您,明天我们当面对一遍?
          </div>
          <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 10, color: AI.ink3, padding: '3px 8px', borderRadius: 999,
              background: AI.aiBg, fontFamily: AI.serif, fontStyle: 'italic' }}>语气:专业但温暖</span>
            <span style={{ fontSize: 10, color: AI.ink3, padding: '3px 8px', borderRadius: 999,
              background: AI.aiBg, fontFamily: AI.serif, fontStyle: 'italic' }}>引用:历史 5% 让利记录</span>
          </div>
        </AIBubble>

        <div style={{ padding: '8px 16px 8px 54px', display: 'flex', gap: 8 }}>
          <button style={{ flex: 1, padding: '10px 0', borderRadius: 12, border: 'none', background: AI.ai, color: '#fff',
            fontSize: 13, fontWeight: 600 }}>采用 · 填入输入框</button>
          <button style={{ padding: '10px 14px', borderRadius: 12, border: `1px solid ${AI.dividerStrong}`,
            background: AI.card, color: AI.ink2, fontSize: 13 }}>换一版</button>
          <button style={{ padding: '10px 14px', borderRadius: 12, border: `1px solid ${AI.dividerStrong}`,
            background: AI.card, color: AI.ink2, fontSize: 13 }}>×</button>
        </div>

        <SuggestRow tags={['更简短一点', '更正式一点', '加一句关于产能的']}/>
      </div>

      <div style={{ padding: '8px 12px 24px', borderTop: `1px solid ${AI.divider}`, background: AI.card,
        display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: AI.bg, border: `1px solid ${AI.dividerStrong}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: AI.ink2 }}>+</span>
        <div style={{ flex: 1, background: AI.bg, borderRadius: 20, border: `1px solid ${AI.dividerStrong}`,
          padding: '9px 14px', fontFamily: AI.serif, fontSize: 14, color: AI.ink3, fontStyle: 'italic',
          display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ flex: 1 }}>给李华回复…</span>
          <span style={{ fontSize: 11, color: AI.ai, fontWeight: 700, fontStyle: 'normal', fontFamily: 'ui-monospace,monospace' }}>@AI</span>
        </div>
      </div>
    </div>
  );
}

// ═══ 5) 会话列表里的 AI 入口 ══════════════════════════════════════
function ConvListWithAI() {
  return (
    <div style={{ background: AI.bg, height: '100%', fontFamily: AI.sans, color: AI.ink, paddingTop: 54 }}>
      <div style={{ padding: '14px 24px 8px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: 11, color: AI.ink3, fontWeight: 500, letterSpacing: 1.2, textTransform: 'uppercase' }}>消息</div>
          <h1 style={{ fontFamily: AI.serif, fontSize: 30, fontWeight: 500, margin: '4px 0 0', letterSpacing: -0.4 }}>聊天</h1>
        </div>
        <span style={{ width: 36, height: 36, borderRadius: 18, background: AI.card, border: `1px solid ${AI.dividerStrong}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: AI.ink }}>+</span>
      </div>

      {/* AI 助手置顶卡 — 视觉特殊 */}
      <div style={{ padding: '8px 16px 4px' }}>
        <div style={{ background: `linear-gradient(135deg, ${AI.aiBg} 0%, rgba(26,180,200,0.07) 100%)`,
          border: `1px solid rgba(47,102,214,0.25)`, borderRadius: 16, padding: 14,
          display: 'flex', gap: 12, alignItems: 'center' }}>
          <AILogo size={34}/>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontFamily: AI.serif, fontSize: 15, fontWeight: 600 }}>源助手</span>
              <span style={{ fontSize: 9, fontWeight: 700, color: AI.ai, padding: '1px 5px', borderRadius: 3, background: AI.aiSoft }}>BETA</span>
              <span style={{ fontSize: 11, color: AI.ink3, marginLeft: 'auto' }}>14:24</span>
            </div>
            <div style={{ fontSize: 12, color: AI.ink2, marginTop: 3, fontFamily: AI.serif, lineHeight: 1.4,
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              已为你起草约见短信,可以采用了 ✨
            </div>
          </div>
        </div>
      </div>

      {/* 普通会话列表 */}
      <div style={{ marginTop: 8, background: AI.card }}>
        {[
          { kind: 'broadcast', name: '公司广播', last: 'Q2 全员目标已发布', time: '09:21', unread: 0, pinned: true, initial: '广' },
          { kind: 'group', name: '深圳半导体工厂扩产', last: '陈刚:客户晚上约见…', time: '09:18', unread: 3, ai: true, initial: '深' },
          { kind: 'dm', name: '李华', last: '方案我看过了。报价能不能再优化…', time: '昨天', unread: 0, draft: true, initial: '李' },
          { kind: 'group', name: '上海某制造厂节能改造', last: '系统:阶段已切换到「招标中」', time: '昨天', unread: 0, initial: '上' },
        ].map((c, i, a) => (
          <div key={i} style={{ padding: '14px 16px', borderBottom: i < a.length - 1 ? `1px solid ${AI.divider}` : 'none',
            display: 'flex', gap: 12 }}>
            <div style={{ width: 42, height: 42, borderRadius: c.kind === 'broadcast' ? 14 : 21,
              background: c.kind === 'broadcast' ? AI.ink : AI.accentSoft,
              color: c.kind === 'broadcast' ? '#fff' : AI.accent,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: AI.serif, fontSize: 16, fontWeight: 600, flexShrink: 0 }}>{c.initial}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
                <div style={{ fontFamily: AI.serif, fontSize: 15, fontWeight: 500, display: 'flex', alignItems: 'center', gap: 6 }}>
                  {c.name}
                  {c.ai && <span style={{ fontSize: 9, color: AI.ai, fontWeight: 700, padding: '1px 5px',
                    borderRadius: 3, background: AI.aiSoft }}>AI</span>}
                </div>
                <span style={{ fontSize: 11, color: AI.ink3 }}>{c.time}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginTop: 3 }}>
                <span style={{ fontSize: 12, color: AI.ink3, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', flex: 1, paddingRight: 8 }}>
                  {c.draft && <span style={{ color: AI.ai, fontWeight: 600 }}>[AI 草稿] </span>}
                  {c.last}
                </span>
                {c.unread > 0 && <span style={{ background: AI.accent, color: '#fff', fontSize: 10, fontWeight: 700,
                  padding: '2px 7px', borderRadius: 999, fontVariantNumeric: 'tabular-nums' }}>{c.unread}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { NewChatPicker, AIOneOnOne, GroupAtAI, DMAIDraft, ConvListWithAI });
