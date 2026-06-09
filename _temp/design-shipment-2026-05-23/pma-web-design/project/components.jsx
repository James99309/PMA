/* ─────────────────────────────────────────────────────────────
   PMA · 采购订单 · 共享组件 + 应用主框架
   ───────────────────────────────────────────────────────────── */

const { useState, useEffect, useRef, useMemo, useCallback, Fragment } = React;

/* ─── Icons (inline strokes, 1.5px) ────────────────────────── */

const Icon = ({ name, size = 16, ...rest }) => {
  const paths = {
    search:   <><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></>,
    plus:     <><path d="M12 5v14M5 12h14"/></>,
    close:    <><path d="M6 6l12 12M18 6L6 18"/></>,
    check:    <><path d="M5 13l4 4L19 7"/></>,
    chev:     <><path d="m9 18 6-6-6-6"/></>,
    chevd:    <><path d="m6 9 6 6 6-6"/></>,
    back:     <><path d="M19 12H5M12 19l-7-7 7-7"/></>,
    download: <><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></>,
    edit:     <><path d="M16 3l5 5L8 21H3v-5z"/></>,
    upload:   <><path d="M12 21V9M7 14l5-5 5 5M5 3h14"/></>,
    file:     <><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></>,
    truck:    <><path d="M3 6h11v9H3zM14 9h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></>,
    flask:    <><path d="M9 3h6M10 3v5L4 19a1 1 0 0 0 1 1h14a1 1 0 0 0 .9-1.4L14 8V3"/></>,
    cube:     <><path d="M12 3 4 7v10l8 4 8-4V7zM4 7l8 4 8-4M12 11v10"/></>,
    factory:  <><path d="M3 21V10l6 4V10l6 4V7l6-4v18z"/></>,
    archive:  <><path d="M3 6h18v4H3zM5 10v11h14V10M10 14h4"/></>,
    pen:      <><path d="m12 19 7-7 3 3-7 7-3-1zM18 13l-1.5-7.5L2 2l3.5 14.5L13 18M2 2l8.6 8.6"/></>,
    user:     <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
    bell:     <><path d="M18 16v-5a6 6 0 0 0-12 0v5l-2 3h16zM10 21a2 2 0 0 0 4 0"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></>,
    clock:    <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    grid:     <><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></>,
    cart:     <><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M3 4h2l3 12h11l2-8H7"/></>,
    box:      <><path d="m3 7 9-4 9 4-9 4z"/><path d="M3 7v10l9 4 9-4V7M12 11v10"/></>,
    chart:    <><path d="M3 21h18M6 17V9M11 17V5M16 17v-6M21 17v-3"/></>,
    users:    <><path d="M16 21a4 4 0 0 0-8 0M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M21 21a4 4 0 0 0-3-3.87M17 3.13a4 4 0 0 1 0 7.75"/></>,
    sun:      <><circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4l1.4-1.4M17 7l1.4-1.4"/></>,
    moon:     <><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></>,
    arrowRt:  <><path d="M5 12h14M12 5l7 7-7 7"/></>,
    filter:   <><path d="M3 5h18l-7 9v6l-4-2v-4z"/></>,
    history:  <><path d="M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5"/></>,
    info:     <><circle cx="12" cy="12" r="9"/><path d="M12 8v0M12 11v5"/></>,
    docs:     <><path d="M8 3h8l4 4v14H8zM4 7v14h12"/></>,
    cancel:   <><circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/></>,
  };
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke="currentColor"
      strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden="true" {...rest}
    >
      {paths[name] || null}
    </svg>
  );
};

/* ─── Stage icons (per-stage) ───────────────────────────────── */

const STAGE_ICON = {
  submit:  "edit",
  confirm: "check",
  prep:    "box",
  produce: "factory",
  test:    "flask",
  ship:    "truck",
  receive: "archive",
};

/* ─── Pill ─────────────────────────────────────────────────── */

const Pill = ({ tone = "neutral", children, dot = false, size = "md", ...rest }) => {
  const toneStyle = {
    neutral: { bg: "var(--bg-sunk)",   fg: "var(--ink-2)" },
    accent:  { bg: "var(--accent-soft)", fg: "var(--accent)" },
    success: { bg: "var(--success-soft)", fg: "var(--success)" },
    warn:    { bg: "var(--warn-soft)",  fg: "var(--warn)" },
    info:    { bg: "var(--info-soft)",  fg: "var(--info)" },
    danger:  { bg: "var(--danger-soft)",fg: "var(--danger)" },
  }[tone] || { bg: "var(--bg-sunk)", fg: "var(--ink-2)" };
  const isLg = size === "lg";
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      background: toneStyle.bg, color: toneStyle.fg,
      padding: isLg ? "5px 10px" : "2px 8px",
      borderRadius: 999, fontSize: isLg ? 12 : 11,
      fontWeight: 500, lineHeight: 1.5, whiteSpace: "nowrap",
      letterSpacing: "0.02em",
    }} {...rest}>
      {dot && <span style={{ width: 6, height: 6, borderRadius: "50%", background: toneStyle.fg }} />}
      {children}
    </span>
  );
};

/* ─── Avatar ───────────────────────────────────────────────── */

const Avatar = ({ name, size = 24, tone = "auto" }) => {
  const letter = name ? name[0] : "?";
  const palette = [
    ["#D97757", "#FFFFFF"], ["#2A5F8F", "#FFFFFF"],
    ["#2F7155", "#FFFFFF"], ["#7A5AE0", "#FFFFFF"],
    ["#B8742E", "#FFFFFF"], ["#A23B3B", "#FFFFFF"],
  ];
  const seed = (name || "").split("").reduce((s, c) => s + c.charCodeAt(0), 0);
  const [bg, fg] = palette[seed % palette.length];
  return (
    <span style={{
      width: size, height: size, borderRadius: "50%",
      background: bg, color: fg,
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      fontSize: Math.round(size * 0.42), fontWeight: 600,
      fontFamily: "var(--font-sans)", flexShrink: 0,
    }}>{letter}</span>
  );
};

/* ─── Button ───────────────────────────────────────────────── */

const Btn = ({ variant = "ghost", size = "md", iconL, iconR, children, style, ...rest }) => {
  const sizes = {
    sm: { h: 28, px: 10, font: 12, gap: 6, iconSize: 14 },
    md: { h: 34, px: 14, font: 13, gap: 8, iconSize: 14 },
    lg: { h: 40, px: 18, font: 14, gap: 8, iconSize: 16 },
  }[size];
  const variants = {
    primary: { bg: "var(--ink)",       fg: "var(--bg-page)", border: "1px solid var(--ink)" },
    accent:  { bg: "var(--accent)",    fg: "#fff",           border: "1px solid var(--accent)" },
    ghost:   { bg: "transparent",      fg: "var(--ink)",     border: "1px solid var(--line-2)" },
    soft:    { bg: "var(--bg-sunk)",   fg: "var(--ink)",     border: "1px solid transparent" },
    bare:    { bg: "transparent",      fg: "var(--ink-2)",   border: "1px solid transparent" },
    danger:  { bg: "transparent",      fg: "var(--danger)",  border: "1px solid var(--danger-soft)" },
  }[variant];
  return (
    <button
      style={{
        height: sizes.h, padding: `0 ${sizes.px}px`,
        display: "inline-flex", alignItems: "center", gap: sizes.gap,
        background: variants.bg, color: variants.fg, border: variants.border,
        borderRadius: 6, fontSize: sizes.font, fontWeight: 500,
        letterSpacing: "0.01em",
        transition: "background 120ms ease, border-color 120ms ease, transform 80ms ease",
        ...style,
      }}
      onMouseDown={e => { e.currentTarget.style.transform = "translateY(0.5px)"; }}
      onMouseUp={e => { e.currentTarget.style.transform = "translateY(0)"; }}
      onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; }}
      {...rest}
    >
      {iconL && <Icon name={iconL} size={sizes.iconSize} />}
      {children}
      {iconR && <Icon name={iconR} size={sizes.iconSize} />}
    </button>
  );
};

/* ─── Input ────────────────────────────────────────────────── */

const Input = ({ iconL, style, ...rest }) => (
  <div style={{
    display: "inline-flex", alignItems: "center", gap: 8,
    height: 34, padding: "0 12px",
    background: "var(--bg-elev)", border: "1px solid var(--line-2)",
    borderRadius: 6, fontSize: 13,
    ...style,
  }}>
    {iconL && <span style={{ color: "var(--ink-3)" }}><Icon name={iconL} size={14} /></span>}
    <input
      style={{
        flex: 1, width: "100%", height: "100%",
        background: "transparent", border: 0, outline: "none",
        color: "var(--ink)", fontSize: 13,
        minWidth: 0,
      }}
      {...rest}
    />
  </div>
);

const Select = ({ value, options, onChange, placeholder, style }) => (
  <div style={{
    display: "inline-flex", alignItems: "center",
    height: 34, padding: "0 10px 0 12px",
    background: "var(--bg-elev)", border: "1px solid var(--line-2)",
    borderRadius: 6, fontSize: 13, position: "relative",
    ...style,
  }}>
    <select
      value={value} onChange={e => onChange?.(e.target.value)}
      style={{
        appearance: "none", border: 0, outline: "none",
        background: "transparent", color: "var(--ink)",
        font: "inherit", paddingRight: 22, width: "100%",
      }}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(o => (
        <option key={typeof o === "string" ? o : o.value} value={typeof o === "string" ? o : o.value}>
          {typeof o === "string" ? o : o.label}
        </option>
      ))}
    </select>
    <span style={{ position: "absolute", right: 8, color: "var(--ink-3)", pointerEvents: "none" }}>
      <Icon name="chevd" size={14} />
    </span>
  </div>
);

/* ─── Progress bar (thin, calm) ─────────────────────────────── */

const Progress = ({ value = 0, width = 80, tone }) => {
  const fillTone = tone || (value >= 100 ? "var(--success)" : value > 0 ? "var(--accent)" : "var(--ink-4)");
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 10,
    }}>
      <div style={{
        width, height: 4, background: "var(--bg-sunk)",
        borderRadius: 2, overflow: "hidden",
      }}>
        <div style={{
          width: `${value}%`, height: "100%", background: fillTone,
          transition: "width 400ms cubic-bezier(.2,.7,.2,1)",
        }} />
      </div>
      <span className="tab-num mono" style={{ fontSize: 11, color: "var(--ink-3)", minWidth: 28 }}>
        {value}%
      </span>
    </div>
  );
};

/* ─── Currency formatter ───────────────────────────────────── */

const fmtCNY = (n) => {
  if (n === 0 || n == null) return "¥0.00";
  return "¥" + Number(n).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};
const fmtNum = (n) => Number(n || 0).toLocaleString("zh-CN");
const fmtShortDate = (d) => d ? d.slice(5) : "—";

/* ─── App shell: sidebar + topbar ──────────────────────────── */

const NAV = [
  { key: "dashboard",  icon: "grid",    label: "工作台" },
  { key: "purchase",   icon: "cart",    label: "采购管理", active: true,
    sub: [
      { key: "po",       label: "采购订单", current: true },
      { key: "supplier", label: "供应商" },
      { key: "request",  label: "采购申请" },
    ]
  },
  { key: "sales",      icon: "chart",   label: "销售管理" },
  { key: "inventory",  icon: "box",     label: "库存管理" },
  { key: "customers",  icon: "users",   label: "客户" },
  { key: "reports",    icon: "docs",    label: "报表" },
];

function Sidebar({ collapsed, onToggle }) {
  const [hovered, setHovered] = useState(false);
  const showExpanded = !collapsed || hovered;
  const isFloating = collapsed && hovered;

  return (
    <aside
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: collapsed ? 64 : 232,
        background: "var(--bg-page)",
        borderRight: "1px solid var(--line)",
        flexShrink: 0, position: "sticky", top: 0, height: "100vh",
        transition: "width 240ms cubic-bezier(.2,.7,.2,1)",
        zIndex: isFloating ? 50 : 1,
      }}
    >
      <div style={{
        width: showExpanded ? 232 : 64,
        height: "100vh",
        background: "var(--bg-page)",
        borderRight: isFloating ? "1px solid var(--line)" : "0",
        display: "flex", flexDirection: "column",
        position: "absolute", inset: 0,
        transition: "width 220ms cubic-bezier(.2,.7,.2,1), box-shadow 220ms",
        boxShadow: isFloating ? "8px 0 24px rgba(31,30,27,0.08)" : "none",
        overflow: "hidden",
      }}>
      {/* Brand */}
      <div style={{
        height: 56, padding: "0 18px",
        display: "flex", alignItems: "center", gap: 10,
        borderBottom: "1px solid var(--line)",
        flexShrink: 0,
      }}>
        <div style={{
          width: 26, height: 26, borderRadius: 6,
          background: "var(--ink)", color: "var(--bg-page)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: "var(--font-serif)", fontWeight: 600,
          fontSize: 14, letterSpacing: "-0.02em",
          flexShrink: 0,
        }}>和</div>
        {showExpanded && (
          <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.1, whiteSpace: "nowrap" }}>
            <span style={{ fontFamily: "var(--font-serif)", fontSize: 15, fontWeight: 600, letterSpacing: "0.02em" }}>
              和意通信
            </span>
            <span className="dim mono" style={{ fontSize: 10, letterSpacing: "0.1em" }}>PMA · v2</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: "auto", padding: "12px 8px", display: "flex", flexDirection: "column", gap: 2 }}>
        {NAV.map(item => (
          <div key={item.key}>
            <button
              title={!showExpanded ? item.label : undefined}
              style={{
                display: "flex", alignItems: "center", gap: 12,
                padding: "8px 10px", borderRadius: 6,
                color: item.active ? "var(--ink)" : "var(--ink-3)",
                background: item.active ? "var(--bg-active)" : "transparent",
                fontSize: 13, fontWeight: item.active ? 500 : 400,
                width: "100%", textAlign: "left",
                whiteSpace: "nowrap", overflow: "hidden",
              }}
              onMouseEnter={e => { if (!item.active) e.currentTarget.style.background = "var(--bg-hover)"; }}
              onMouseLeave={e => { if (!item.active) e.currentTarget.style.background = "transparent"; }}
            >
              <Icon name={item.icon} size={16} />
              {showExpanded && <span style={{ flex: 1 }}>{item.label}</span>}
            </button>
            {showExpanded && item.active && item.sub && (
              <div style={{ marginLeft: 30, marginTop: 2, marginBottom: 6, display: "flex", flexDirection: "column", gap: 1, borderLeft: "1px solid var(--line)", paddingLeft: 10 }}>
                {item.sub.map(s => (
                  <button key={s.key} style={{
                    padding: "5px 8px", borderRadius: 4,
                    fontSize: 12.5,
                    color: s.current ? "var(--accent)" : "var(--ink-3)",
                    fontWeight: s.current ? 500 : 400,
                    background: s.current ? "var(--accent-tint)" : "transparent",
                    textAlign: "left", whiteSpace: "nowrap",
                  }}>{s.label}</button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* User */}
      <div style={{
        padding: "12px 14px", borderTop: "1px solid var(--line)",
        display: "flex", alignItems: "center", gap: 10,
        flexShrink: 0,
      }}>
        <Avatar name="张" size={28} />
        {showExpanded && (
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 12.5, fontWeight: 500, lineHeight: 1.2, whiteSpace: "nowrap" }}>张伟</div>
            <div className="dim" style={{ fontSize: 11, lineHeight: 1.3, whiteSpace: "nowrap" }}>采购经理</div>
          </div>
        )}
        {showExpanded && (
          <button style={{ color: "var(--ink-3)" }} title="设置">
            <Icon name="settings" size={14} />
          </button>
        )}
      </div>
      </div>

      {/* Collapse toggle (only visible when not floating-on-hover) */}
      {!isFloating && (
        <button
          onClick={onToggle}
          title={collapsed ? "固定展开" : "收起"}
          style={{
            position: "absolute", top: 14, right: -12,
            width: 24, height: 24, borderRadius: "50%",
            background: "var(--bg-elev)", border: "1px solid var(--line)",
            color: "var(--ink-3)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 2px 6px rgba(0,0,0,0.04)",
            transform: collapsed ? "rotate(0deg)" : "rotate(180deg)",
            transition: "transform 240ms",
            zIndex: 2,
          }}
        ><Icon name="chev" size={12} /></button>
      )}
    </aside>
  );
}

function Topbar({ breadcrumbs = [], onBack }) {
  return (
    <header style={{
      height: 56, padding: "0 24px",
      borderBottom: "1px solid var(--line)",
      background: "rgba(250,249,245,0.85)",
      backdropFilter: "blur(10px)",
      WebkitBackdropFilter: "blur(10px)",
      display: "flex", alignItems: "center", gap: 16,
      position: "sticky", top: 0, zIndex: 30,
    }}>
      {/* Breadcrumb */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "var(--ink-3)", flex: 1, minWidth: 0 }}>
        {breadcrumbs.map((b, i) => (
          <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            {i > 0 && <span style={{ color: "var(--ink-4)" }}>/</span>}
            <button
              onClick={b.onClick}
              style={{
                color: i === breadcrumbs.length - 1 ? "var(--ink)" : "var(--ink-3)",
                fontWeight: i === breadcrumbs.length - 1 ? 500 : 400,
                cursor: b.onClick ? "pointer" : "default",
              }}
            >{b.label}</button>
          </span>
        ))}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <Input iconL="search" placeholder="搜索订单、产品、供应商…" style={{ width: 260 }} />
        <button style={{
          width: 34, height: 34, borderRadius: 6, color: "var(--ink-3)",
          display: "flex", alignItems: "center", justifyContent: "center",
          border: "1px solid transparent",
        }}
          onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
        ><Icon name="bell" size={16} /></button>
      </div>
    </header>
  );
}

/* Export to globals */
Object.assign(window, {
  Icon, STAGE_ICON, Pill, Avatar, Btn, Input, Select, Progress,
  fmtCNY, fmtNum, fmtShortDate,
  Sidebar, Topbar,
});
