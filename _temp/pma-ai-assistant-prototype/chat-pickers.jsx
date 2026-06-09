// PMA · 输入栏 + 弹出 — 相册 / 摄像头 / 文件 / 位置 选择器
// 复用 CIS 命名空间(chat-input-states.jsx 里定义),独立写一份避免依赖加载顺序
const PIK = {
  bg: '#F7F5F2', card: '#FFFFFF', ink: '#1A1A1A', ink2: '#3A3A3A', ink3: '#7A7570', ink4: '#C2BBB3',
  divider: 'rgba(0,0,0,0.06)', dividerStrong: 'rgba(0,0,0,0.10)',
  accent: '#D97757', accentSoft: '#F4E4D8', accentBg: 'rgba(217,119,87,0.08)',
  blue: '#4D82E0', blueSoft: '#E5EDFA',
  red: '#C44',
  serif: '"Tiempos Headline","Source Serif Pro","Noto Serif SC",Georgia,serif',
  sans: '-apple-system,"SF Pro Text","PingFang SC",system-ui,sans-serif',
  mono: 'ui-monospace,"SF Mono",monospace',
};

function PIKStatusPad({ light }) {
  return <div style={{ height: 54, background: light ? 'transparent' : 'inherit' }}/>;
}

// ═══ 1) 相册 · 多选 ═══════════════════════════════════════════════════
function PickAlbum() {
  // 36 个 thumbnails — 不同色块表示不同照片
  const tints = [
    ['#E5DCC8', '#C8B89A'], ['#D6E0EA', '#A8BACE'], ['#E8D6D0', '#C9A99E'],
    ['#D8E2D5', '#A8B89E'], ['#E0D2D8', '#B8A0AE'], ['#DEDED2', '#B0B0A0'],
    ['#D2D6DC', '#9AA0AE'], ['#E8DDC4', '#C8B484'],
  ];
  const checked = new Set([1, 4, 9]); // 选了 3 张

  return (
    <div style={{ background: PIK.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: PIK.sans }}>
      <PIKStatusPad/>
      {/* nav */}
      <div style={{ padding: '6px 16px 10px', display: 'flex', alignItems: 'center',
        borderBottom: `1px solid ${PIK.divider}`, background: PIK.bg }}>
        <span style={{ fontSize: 14, color: PIK.ink2, fontWeight: 500 }}>取消</span>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontFamily: PIK.serif, fontSize: 16, fontWeight: 500 }}>所有照片</div>
          <div style={{ fontSize: 11, color: PIK.ink3, marginTop: 1 }}>已选 3 / 9</div>
        </div>
        <span style={{ fontSize: 13, color: PIK.ink2, display: 'inline-flex', alignItems: 'center', gap: 3 }}>
          相册 <svg width="8" height="6" viewBox="0 0 8 6"><path d="M1 1l3 3 3-3" stroke={PIK.ink2} strokeWidth="1.4" fill="none" strokeLinecap="round"/></svg>
        </span>
      </div>

      {/* 类别 chips */}
      <div style={{ padding: '8px 12px 6px', display: 'flex', gap: 6, overflowX: 'auto' }}>
        {[['全部', true], ['最近 7 天'], ['项目相关'], ['截图'], ['文档照片']].map(([n, sel], i) => (
          <span key={i} style={{ flexShrink: 0, fontSize: 12, padding: '5px 10px', borderRadius: 999,
            background: sel ? PIK.ink : PIK.card, color: sel ? '#fff' : PIK.ink2,
            border: sel ? 'none' : `1px solid ${PIK.divider}`, fontWeight: sel ? 600 : 400 }}>{n}</span>
        ))}
      </div>

      {/* 照片网格 — 4 列 */}
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 2px 100px', display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)', gap: 2 }}>
        {Array.from({ length: 24 }).map((_, i) => {
          const t = tints[i % tints.length];
          const isChecked = checked.has(i);
          return (
            <div key={i} style={{ position: 'relative', aspectRatio: '1' }}>
              <div style={{
                position: 'absolute', inset: 0,
                background: `linear-gradient(${135 + (i * 13) % 90}deg, ${t[0]}, ${t[1]})`,
              }}>
                <svg width="100%" height="100%" viewBox="0 0 60 60" style={{ opacity: 0.45 }} preserveAspectRatio="none">
                  {i % 3 === 0 && <>
                    <rect x="14" y="20" width="14" height="28" fill="rgba(0,0,0,0.18)"/>
                    <rect x="32" y="14" width="14" height="34" fill="rgba(0,0,0,0.22)"/>
                  </>}
                  {i % 3 === 1 && <>
                    <circle cx="30" cy="22" r="8" fill="rgba(0,0,0,0.12)"/>
                    <path d="M0 50 L20 38 L40 44 L60 36 L60 60 L0 60 Z" fill="rgba(0,0,0,0.18)"/>
                  </>}
                  {i % 3 === 2 && <>
                    <path d="M0 32 L60 32 M0 38 L60 38 M0 44 L60 44" stroke="rgba(0,0,0,0.18)" strokeWidth="2"/>
                  </>}
                </svg>
              </div>
              {/* 选择 checkbox */}
              <span style={{
                position: 'absolute', top: 6, right: 6,
                width: 22, height: 22, borderRadius: 11,
                background: isChecked ? PIK.accent : 'rgba(0,0,0,0.25)',
                border: '1.5px solid #fff',
                color: '#fff',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, fontWeight: 700,
              }}>
                {isChecked && (Array.from(checked).indexOf(i) + 1)}
              </span>
              {/* 视频时长 / HEIC 标记 */}
              {i === 6 && (
                <span style={{ position: 'absolute', bottom: 4, right: 6, fontSize: 10, color: '#fff',
                  textShadow: '0 1px 2px rgba(0,0,0,0.6)', fontVariantNumeric: 'tabular-nums' }}>0:42</span>
              )}
            </div>
          );
        })}
      </div>

      {/* 底部 confirm bar */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0,
        padding: '12px 16px 28px', background: 'rgba(247,245,242,0.95)',
        borderTop: `1px solid ${PIK.divider}`, backdropFilter: 'blur(10px)',
        display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 12, color: PIK.ink3, flex: 1 }}>
          <span style={{ color: PIK.accent, fontWeight: 600 }}>3</span> 张已选 · 原图 4.8MB
        </span>
        <span style={{ fontSize: 12, color: PIK.ink2,
          padding: '7px 12px', borderRadius: 999, border: `1px solid ${PIK.dividerStrong}`, background: PIK.card }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 12, height: 12, borderRadius: 6, border: `1.5px solid ${PIK.ink3}` }}/>
            原图
          </span>
        </span>
        <span style={{
          background: PIK.accent, color: '#fff', fontSize: 14, fontWeight: 600,
          padding: '9px 18px', borderRadius: 999,
        }}>发送 · 3</span>
      </div>
    </div>
  );
}

// ═══ 2) 摄像头 · 取景器 ═══════════════════════════════════════════════
function PickCamera() {
  return (
    <div style={{ background: '#0a0a0a', height: '100%', position: 'relative', overflow: 'hidden', fontFamily: PIK.sans, color: '#fff' }}>
      {/* 取景画面 — 模拟一个工地场景 */}
      <div style={{ position: 'absolute', inset: 0,
        background: 'linear-gradient(180deg, #b0a89a 0%, #8a8074 35%, #5a5247 70%, #2a2521 100%)' }}>
        <svg width="100%" height="100%" viewBox="0 0 430 970" preserveAspectRatio="none">
          {/* 远山 */}
          <path d="M0 480 L80 400 L160 440 L240 380 L320 420 L430 380 L430 500 L0 500 Z" fill="rgba(0,0,0,0.18)"/>
          {/* 厂房 */}
          <rect x="80" y="430" width="100" height="180" fill="rgba(0,0,0,0.25)"/>
          <rect x="180" y="380" width="160" height="230" fill="rgba(0,0,0,0.32)"/>
          <rect x="340" y="420" width="80" height="190" fill="rgba(0,0,0,0.28)"/>
          {/* 配电塔 */}
          <path d="M210 380 L220 370 L230 380 L230 400 L210 400 Z" fill="rgba(0,0,0,0.4)"/>
          <path d="M222 370 L222 320" stroke="rgba(0,0,0,0.4)" strokeWidth="2"/>
          {/* 地面 */}
          <rect x="0" y="610" width="430" height="360" fill="rgba(0,0,0,0.55)"/>
          {/* 网格透视线 */}
          <path d="M0 700 L430 700 M0 780 L430 780 M0 860 L430 860" stroke="rgba(255,255,255,0.06)"/>
        </svg>
      </div>

      {/* 顶部状态条 */}
      <PIKStatusPad light/>
      <div style={{ position: 'absolute', top: 54, left: 0, right: 0, padding: '10px 16px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'linear-gradient(to bottom, rgba(0,0,0,0.4), transparent)' }}>
        <span style={{ fontSize: 14, color: '#fff', fontWeight: 500 }}>取消</span>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 12px',
            borderRadius: 999, background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)',
            fontSize: 11, fontWeight: 500, letterSpacing: 0.5 }}>
            <span style={{ width: 6, height: 6, borderRadius: 3, background: PIK.accent }}/>
            HDR
          </span>
        </div>
        <span style={{
          width: 32, height: 32, borderRadius: 16, background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 1L9.5 6 14 7 10 10.5 11 15 8 12 5 15 6 10.5 2 7 6.5 6z" stroke="#fff" strokeWidth="1.3" strokeLinejoin="round"/>
          </svg>
        </span>
      </div>

      {/* 中央对焦框 */}
      <div style={{ position: 'absolute', top: '40%', left: '50%', transform: 'translate(-50%, -50%)',
        width: 80, height: 80, border: '1.5px solid rgba(255,255,255,0.85)', borderRadius: 4 }}>
        <span style={{ position: 'absolute', top: -2, left: -2, width: 12, height: 12, borderTop: '2px solid #fff', borderLeft: '2px solid #fff' }}/>
        <span style={{ position: 'absolute', top: -2, right: -2, width: 12, height: 12, borderTop: '2px solid #fff', borderRight: '2px solid #fff' }}/>
        <span style={{ position: 'absolute', bottom: -2, left: -2, width: 12, height: 12, borderBottom: '2px solid #fff', borderLeft: '2px solid #fff' }}/>
        <span style={{ position: 'absolute', bottom: -2, right: -2, width: 12, height: 12, borderBottom: '2px solid #fff', borderRight: '2px solid #fff' }}/>
        {/* 曝光滑块 */}
        <span style={{ position: 'absolute', top: '50%', right: -28, transform: 'translateY(-50%)',
          width: 16, height: 16, borderRadius: 8, background: '#FFD43A',
          boxShadow: '0 0 0 1.5px #fff' }}>
          <svg width="16" height="16" viewBox="0 0 16 16">
            <circle cx="8" cy="8" r="3" fill="none" stroke="#fff" strokeWidth="1.2"/>
            <path d="M8 2v2M8 12v2M2 8h2M12 8h2" stroke="#fff" strokeWidth="1.2"/>
          </svg>
        </span>
      </div>

      {/* 模式选择(拍照 / 视频 / 全景 ) */}
      <div style={{ position: 'absolute', bottom: 200, left: 0, right: 0, display: 'flex',
        justifyContent: 'center', gap: 24 }}>
        {[['全景', false], ['视频', false], ['拍照', true], ['人像', false]].map(([n, sel], i) => (
          <span key={i} style={{
            fontSize: 12, fontWeight: sel ? 600 : 400,
            color: sel ? PIK.accent : 'rgba(255,255,255,0.7)',
            letterSpacing: 0.5,
          }}>{n}</span>
        ))}
      </div>

      {/* 底部控制栏 */}
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 180,
        background: 'linear-gradient(to top, rgba(0,0,0,0.85), transparent)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 32px 36px' }}>
        {/* 相册预览 */}
        <span style={{ width: 48, height: 48, borderRadius: 8,
          background: 'linear-gradient(135deg, #b0a89a, #8a8074)',
          border: '1.5px solid rgba(255,255,255,0.6)' }}>
          <svg width="48" height="48" viewBox="0 0 48 48" style={{ opacity: 0.6 }}>
            <rect x="10" y="14" width="11" height="22" fill="rgba(0,0,0,0.3)"/>
            <rect x="25" y="10" width="11" height="26" fill="rgba(0,0,0,0.4)"/>
          </svg>
        </span>
        {/* 快门 */}
        <span style={{
          width: 76, height: 76, borderRadius: 38,
          background: '#fff',
          boxShadow: '0 0 0 4px rgba(255,255,255,0.25), 0 0 0 6px rgba(255,255,255,0.6)',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ width: 64, height: 64, borderRadius: 32, background: '#fff',
            border: '2.5px solid #0a0a0a' }}/>
        </span>
        {/* 切换镜头 */}
        <span style={{ width: 48, height: 48, borderRadius: 24,
          background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path d="M3 8a5 5 0 015-5h2M21 16a5 5 0 01-5 5h-2" stroke="#fff" strokeWidth="1.6" strokeLinecap="round"/>
            <path d="M7 4l3-1 0 2M17 20l-3 1 0-2" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
            <circle cx="12" cy="12" r="4" stroke="#fff" strokeWidth="1.6"/>
          </svg>
        </span>
      </div>
    </div>
  );
}

// ═══ 3) 文件选择器 ════════════════════════════════════════════════════
function PickFile() {
  const recents = [
    { name: '深铁阅洺境招标书.pdf',     ext: 'PDF',  size: '2.4 MB',  date: '今天 09:08',   from: '李明',  color: '#C44' },
    { name: '配电方案 V3.pdf',         ext: 'PDF',  size: '1.8 MB',  date: '昨天 17:22',   from: '张伟',  color: '#C44' },
    { name: '现场勘查记录.docx',       ext: 'DOC',  size: '320 KB',  date: '昨天 14:05',   from: '陈刚',  color: '#3a6dc4' },
    { name: '合同清单.xlsx',           ext: 'XLS',  size: '88 KB',   date: '4-28',         from: '王芳',  color: '#3a8c5a' },
    { name: '深铁项目-平面图.dwg',     ext: 'DWG',  size: '14.2 MB', date: '4-26',         from: '设计部', color: '#7355C9' },
    { name: '会议纪要-0425.md',        ext: 'MD',   size: '12 KB',   date: '4-25',         from: '我',     color: PIK.ink3 },
  ];
  const checked = new Set([0, 4]); // 招标书 + 平面图

  return (
    <div style={{ background: PIK.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: PIK.sans }}>
      <PIKStatusPad/>
      <div style={{ padding: '6px 16px 10px', display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: `1px solid ${PIK.divider}`, background: PIK.bg }}>
        <span style={{ fontSize: 14, color: PIK.ink2, fontWeight: 500 }}>取消</span>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontFamily: PIK.serif, fontSize: 16, fontWeight: 500 }}>选择文件</div>
          <div style={{ fontSize: 11, color: PIK.ink3, marginTop: 1 }}>已选 2 · 16.6 MB</div>
        </div>
        <span style={{ fontSize: 13, color: PIK.ink3 }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="7" cy="7" r="5" stroke={PIK.ink3} strokeWidth="1.4"/>
            <path d="M11 11l3 3" stroke={PIK.ink3} strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
        </span>
      </div>

      {/* 来源 tabs */}
      <div style={{ padding: '8px 12px 0', display: 'flex', gap: 6, overflowX: 'auto' }}>
        {[['最近', true], ['项目文件'], ['本机'], ['云盘'], ['企业微信']].map(([n, sel], i) => (
          <span key={i} style={{ flexShrink: 0, fontSize: 12, padding: '6px 11px', borderRadius: 999,
            background: sel ? PIK.ink : PIK.card, color: sel ? '#fff' : PIK.ink2,
            border: sel ? 'none' : `1px solid ${PIK.divider}`, fontWeight: sel ? 600 : 400 }}>{n}</span>
        ))}
      </div>

      {/* 类型 filter row */}
      <div style={{ padding: '10px 16px 6px', fontSize: 11, color: PIK.ink3, letterSpacing: 1, fontWeight: 600, textTransform: 'uppercase' }}>
        最近 7 天
      </div>

      {/* 文件列表 */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 0 100px' }}>
        {recents.map((f, i) => {
          const isChecked = checked.has(i);
          return (
            <div key={i} style={{
              padding: '12px 16px',
              borderBottom: `1px solid ${PIK.divider}`,
              display: 'flex', alignItems: 'center', gap: 12,
              background: isChecked ? PIK.accentBg : 'transparent',
            }}>
              {/* 文件类型图标 */}
              <span style={{
                width: 38, height: 46, borderRadius: 6, background: PIK.card,
                border: `1px solid ${PIK.divider}`, position: 'relative', flexShrink: 0,
                display: 'flex', alignItems: 'flex-end', justifyContent: 'center', paddingBottom: 4,
              }}>
                {/* 折角 */}
                <span style={{ position: 'absolute', top: 0, right: 0, width: 10, height: 10,
                  background: 'linear-gradient(225deg, transparent 50%, ' + PIK.bg + ' 50%)',
                  borderLeft: `1px solid ${PIK.divider}`, borderBottom: `1px solid ${PIK.divider}` }}/>
                <span style={{
                  fontSize: 9, fontWeight: 700, letterSpacing: 0.4, color: '#fff',
                  background: f.color, padding: '1px 4px', borderRadius: 2,
                  fontFamily: PIK.mono,
                }}>{f.ext}</span>
              </span>
              {/* meta */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontFamily: PIK.serif, fontSize: 14, fontWeight: 500, color: PIK.ink,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {f.name}
                </div>
                <div style={{ fontSize: 11, color: PIK.ink3, marginTop: 3, display: 'flex', gap: 8 }}>
                  <span>{f.size}</span><span>·</span><span>{f.date}</span><span>·</span><span>{f.from}</span>
                </div>
              </div>
              {/* checkbox */}
              <span style={{
                width: 22, height: 22, borderRadius: 11, flexShrink: 0,
                background: isChecked ? PIK.accent : 'transparent',
                border: `1.5px solid ${isChecked ? PIK.accent : PIK.dividerStrong}`,
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {isChecked && <svg width="11" height="11" viewBox="0 0 12 12"><path d="M2 6l3 3 5-7" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/></svg>}
              </span>
            </div>
          );
        })}
      </div>

      {/* 底部 confirm bar */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0,
        padding: '12px 16px 28px', background: 'rgba(247,245,242,0.95)',
        borderTop: `1px solid ${PIK.divider}`, backdropFilter: 'blur(10px)',
        display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 12, color: PIK.ink3, flex: 1 }}>
          已选 <span style={{ color: PIK.accent, fontWeight: 600 }}>2</span> 个文件
        </span>
        <span style={{ fontSize: 12, color: PIK.ink2, padding: '7px 12px', borderRadius: 999,
          background: PIK.card, border: `1px solid ${PIK.dividerStrong}` }}>
          连同 AI 分析
        </span>
        <span style={{
          background: PIK.accent, color: '#fff', fontSize: 14, fontWeight: 600,
          padding: '9px 18px', borderRadius: 999,
        }}>发送 · 2</span>
      </div>
    </div>
  );
}

// ═══ 4) 位置共享 ══════════════════════════════════════════════════════
function PickLocation() {
  const pois = [
    { name: '深铁阅洺境花园(售楼处)', addr: '深圳市龙岗区宝龙街道站前路3号', dist: '当前位置 · 0 m', selected: true },
    { name: '深铁阅洺境花园西门',       addr: '宝龙街道站前路3号-1', dist: '120 m' },
    { name: '宝龙地铁站 A 出口',        addr: '深圳地铁 3 号线', dist: '380 m' },
    { name: '阅洺境工地临时办公楼',      addr: '站前路3号工地北侧', dist: '95 m' },
    { name: '宝龙街道办事处',          addr: '宝龙街道龙岗大道', dist: '720 m' },
  ];

  return (
    <div style={{ background: PIK.bg, height: '100%', display: 'flex', flexDirection: 'column', fontFamily: PIK.sans, position: 'relative' }}>
      <PIKStatusPad/>
      <div style={{ padding: '6px 16px 10px', display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: `1px solid ${PIK.divider}`, background: PIK.bg }}>
        <span style={{ fontSize: 14, color: PIK.ink2, fontWeight: 500 }}>取消</span>
        <div style={{ flex: 1, textAlign: 'center' }}>
          <div style={{ fontFamily: PIK.serif, fontSize: 16, fontWeight: 500 }}>共享位置</div>
          <div style={{ fontSize: 11, color: PIK.ink3, marginTop: 1 }}>选择一个地点</div>
        </div>
        <span style={{ fontSize: 13, color: PIK.accent, fontWeight: 600 }}>发送</span>
      </div>

      {/* 搜索 */}
      <div style={{ padding: '10px 16px 8px' }}>
        <div style={{ background: PIK.card, borderRadius: 10, padding: '8px 12px',
          display: 'flex', alignItems: 'center', gap: 8, border: `1px solid ${PIK.divider}` }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <circle cx="6" cy="6" r="4.5" stroke={PIK.ink3} strokeWidth="1.4"/>
            <path d="M9.5 9.5L13 13" stroke={PIK.ink3} strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
          <span style={{ fontSize: 13, color: PIK.ink3, fontFamily: PIK.serif, fontStyle: 'italic' }}>搜索地点 · 学校 / 商场 / 地址</span>
        </div>
      </div>

      {/* 地图区域 */}
      <div style={{ position: 'relative', height: 240, background: '#E8E4DC',
        borderTop: `1px solid ${PIK.divider}`, borderBottom: `1px solid ${PIK.divider}` }}>
        {/* 假地图 — 道路 / 区块 */}
        <svg width="100%" height="100%" viewBox="0 0 430 240" preserveAspectRatio="none">
          {/* 区块底色 */}
          <rect x="0" y="0" width="430" height="240" fill="#E8E4DC"/>
          {/* 主干道 */}
          <path d="M-20 90 L450 130" stroke="#fff" strokeWidth="14"/>
          <path d="M-20 90 L450 130" stroke="#D6D0C2" strokeWidth="14" strokeDasharray="2 6" strokeOpacity="0.6"/>
          <path d="M180 -20 L240 260" stroke="#fff" strokeWidth="10"/>
          {/* 次干道 */}
          <path d="M-20 180 L450 200" stroke="#F1ECE3" strokeWidth="6"/>
          <path d="M50 -20 L80 260" stroke="#F1ECE3" strokeWidth="6"/>
          <path d="M340 -20 L370 260" stroke="#F1ECE3" strokeWidth="6"/>
          {/* 街区 */}
          <rect x="100" y="20" width="60" height="60" fill="#DCD5C5" rx="2"/>
          <rect x="260" y="20" width="60" height="60" fill="#DCD5C5" rx="2"/>
          <rect x="80" y="200" width="80" height="40" fill="#DCD5C5" rx="2"/>
          <rect x="270" y="200" width="80" height="40" fill="#DCD5C5" rx="2"/>
          {/* 公园 */}
          <path d="M250 140 L390 140 L390 195 L250 195 Z" fill="#D4DDC8" rx="2"/>
          <text x="320" y="172" textAnchor="middle" fill="#8a9277" fontSize="9" fontFamily="serif" fontStyle="italic">龙岗公园</text>
          {/* 主路名称 */}
          <text x="380" y="116" fill="#aaa" fontSize="9" fontStyle="italic">龙岗大道</text>
          <text x="195" y="50" fill="#aaa" fontSize="9" fontStyle="italic" transform="rotate(-89 195 50)">站前路</text>
        </svg>

        {/* 中心 pin */}
        <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%, -100%)' }}>
          <div style={{ position: 'relative', filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.18))' }}>
            <svg width="32" height="40" viewBox="0 0 32 40">
              <path d="M16 38 C 16 38, 4 22, 4 14 A 12 12 0 1 1 28 14 C 28 22, 16 38, 16 38 Z" fill={PIK.accent}/>
              <circle cx="16" cy="14" r="5" fill="#fff"/>
            </svg>
          </div>
          {/* 阴影点 */}
          <div style={{ position: 'absolute', left: '50%', top: '100%', transform: 'translate(-50%, 0)',
            width: 14, height: 4, borderRadius: 7, background: 'rgba(0,0,0,0.18)', filter: 'blur(2px)' }}/>
        </div>

        {/* 我的位置 button */}
        <span style={{
          position: 'absolute', right: 14, bottom: 14,
          width: 38, height: 38, borderRadius: 19,
          background: PIK.card, border: `1px solid ${PIK.divider}`,
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 2px 6px rgba(0,0,0,0.08)',
        }}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="3.5" stroke={PIK.accent} strokeWidth="1.6"/>
            <circle cx="9" cy="9" r="1.5" fill={PIK.accent}/>
            <path d="M9 1v2.5M9 14.5V17M1 9h2.5M14.5 9H17" stroke={PIK.accent} strokeWidth="1.4" strokeLinecap="round"/>
          </svg>
        </span>
      </div>

      {/* POI 列表 */}
      <div style={{ flex: 1, overflow: 'auto', background: PIK.bg }}>
        <div style={{ padding: '12px 16px 6px', fontSize: 11, color: PIK.ink3, letterSpacing: 1, fontWeight: 600, textTransform: 'uppercase' }}>
          附近地点
        </div>
        {pois.map((p, i) => (
          <div key={i} style={{
            padding: '12px 16px',
            borderBottom: `1px solid ${PIK.divider}`,
            display: 'flex', alignItems: 'flex-start', gap: 12,
            background: p.selected ? PIK.accentBg : 'transparent',
          }}>
            <span style={{
              width: 28, height: 28, borderRadius: 14, flexShrink: 0,
              background: p.selected ? PIK.accent : PIK.card,
              border: p.selected ? 'none' : `1px solid ${PIK.dividerStrong}`,
              color: p.selected ? '#fff' : PIK.ink3,
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginTop: 2,
            }}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 13s5-4.5 5-8a5 5 0 10-10 0c0 3.5 5 8 5 8z" fill="currentColor" stroke="currentColor"/>
                <circle cx="7" cy="5" r="1.5" fill={p.selected ? PIK.accent : '#fff'}/>
              </svg>
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontFamily: PIK.serif, fontSize: 14, fontWeight: 500, color: PIK.ink,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
              <div style={{ fontSize: 12, color: PIK.ink3, marginTop: 2, overflow: 'hidden',
                textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.addr}</div>
            </div>
            <span style={{ fontSize: 11, color: p.selected ? PIK.accent : PIK.ink3,
              fontVariantNumeric: 'tabular-nums', flexShrink: 0, paddingTop: 4, fontWeight: p.selected ? 600 : 400 }}>
              {p.dist}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { PickAlbum, PickCamera, PickFile, PickLocation });
