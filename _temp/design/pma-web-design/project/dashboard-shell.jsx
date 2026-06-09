/* ─────────────────────────────────────────────────────────────
   PMA · 仪表盘 · 应用框架 (侧边栏 + 顶栏)
   按 spec 完整重组：图标轨道 64 / 浮层 232 / pinned 持久
   顶栏：全局搜索 ⌘K · 快速创建 · 通知集群
   ───────────────────────────────────────────────────────────── */

/* ── 扩展 Icon (在 components.jsx 的基础上补几个图标) ─────── */
const DashIcon = ({ name, size = 16, ...rest }) => {
  const extra = {
    home:     <><path d="M3 11 12 3l9 8"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/></>,
    inbox:    <><path d="M3 13h5l2 3h4l2-3h5"/><path d="M3 13V5h18v8M3 13v6h18v-6"/></>,
    sparkle:  <><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/></>,
    funnel:   <><path d="M3 5h18l-7 9v6l-4-2v-4z"/></>,
    money:    <><circle cx="12" cy="12" r="9"/><path d="M15 9c0-1.5-1.5-2-3-2s-3 .5-3 2 1.5 2 3 2 3 .5 3 2-1.5 2-3 2-3-.5-3-2M12 6v12"/></>,
    alert:    <><path d="m12 3 10 18H2z"/><path d="M12 10v5M12 18v.5"/></>,
    cmd:      <><path d="M9 9V6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3v3M9 9v6m6-6v6m0 0v3a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3v-3"/></>,
    refresh:  <><path d="M3 12a9 9 0 0 1 15.5-6.3L21 8M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.5 6.3L3 16M3 21v-5h5"/></>,
    book:     <><path d="M4 4h7a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H4z"/><path d="M20 4h-7a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h8z"/></>,
    cal:      <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/></>,
    geo:      <><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a13 13 0 0 1 0 18M12 3a13 13 0 0 0 0 18"/></>,
    chat:     <><path d="M21 12a8 8 0 0 1-12.3 6.8L3 21l2.2-5.7A8 8 0 1 1 21 12z"/></>,
    bot:      <><rect x="4" y="8" width="16" height="12" rx="2"/><path d="M12 4v4M9 14v0M15 14v0"/></>,
    star:     <><path d="m12 3 2.6 6 6.4.5-5 4.3 1.6 6.3L12 16.8l-5.6 3.3 1.6-6.3-5-4.3 6.4-.5z"/></>,
    star2:    <><path d="M12 4v16M4 12h16M6 6l12 12M18 6 6 18" /></>,
    flame:    <><path d="M12 3c0 4-4 5-4 9a4 4 0 0 0 8 0c0-2-1.5-3-1.5-5C14.5 5 12 5 12 3z"/></>,
    pin:      <><path d="M9 4h6l-1 5 4 4-5 1v6l-3 2-3-2v-6l-5-1 4-4z"/></>,
    pulse:    <><path d="M3 12h4l2-6 4 12 2-6h6"/></>,
  };
  if (extra[name]) return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...rest}>
      {extra[name]}
    </svg>
  );
  return <Icon name={name} size={size} {...rest} />;
};

/* ── 侧边栏 NAV 结构 (按 spec §6.2) ────────────────────────── */
const DASH_NAV = [
  { kind: "item",  key: "dashboard", icon: "home",    label: "仪表盘" },
  { kind: "item",  key: "todo",      icon: "inbox",   label: "我的待办", badge: 5 },
  { kind: "div" },
  { kind: "group", key: "biz",       label: "业务管理", defaultOpen: true,
    items: [
      { key: "customer", icon: "users",   label: "客户" },
      { key: "project",  icon: "flask",   label: "项目" },
      { key: "quote",    icon: "pen",     label: "报价" },
      { key: "expense",  icon: "money",   label: "报销" },
    ]
  },
  { kind: "group", key: "order",     label: "订单中心", defaultOpen: true,
    items: [
      { key: "pricing", icon: "chart",   label: "批价单" },
      { key: "so",      icon: "cart",    label: "客户订单" },
      { key: "po",      icon: "truck",   label: "采购订单" },
      { key: "ship",    icon: "upload",  label: "发货记录" },
      { key: "stock",   icon: "box",     label: "库存管理" },
    ]
  },
  { kind: "group", key: "product",   label: "产品中心", defaultOpen: false,
    items: [
      { key: "products", icon: "cube",    label: "产品库" },
      { key: "design",   icon: "grid",    label: "系统设计" },
      { key: "analyze",  icon: "pulse",   label: "植入分析" },
    ]
  },
  { kind: "group", key: "tools",     label: "工具",     defaultOpen: false,
    items: [
      { key: "meet",  icon: "users",  label: "会议纪要" },
      { key: "wiki",  icon: "book",   label: "Wiki 知识库" },
      { key: "geo",   icon: "geo",    label: "GEO 监控" },
      { key: "cli",   icon: "cmd",    label: "智能终端" },
    ]
  },
  { kind: "div" },
  { kind: "group", key: "settings",  label: "设置",     defaultOpen: false, bottom: true,
    items: [
      { key: "users",   icon: "user",     label: "账户与字典" },
      { key: "config",  icon: "cube",     label: "产品配置" },
      { key: "system",  icon: "settings", label: "系统运维" },
    ]
  },
];

function DashSidebar({ pinned, onPinToggle, current, onNavigate }) {
  const [hovered, setHovered] = useState(false);
  const [openGroups, setOpenGroups] = useState(() => {
    const init = {};
    DASH_NAV.forEach(n => { if (n.kind === "group") init[n.key] = n.defaultOpen; });
    return init;
  });
  const expanded = pinned || hovered;
  const floating = !pinned && hovered;
  const W = 232, RAIL = 64;

  return (
    <aside
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        width: pinned ? W : RAIL,
        background: "var(--bg-page)",
        borderRight: "1px solid var(--line)",
        flexShrink: 0, position: "sticky", top: 0, height: "100vh",
        transition: "width 240ms cubic-bezier(.2,.7,.2,1)",
        zIndex: floating ? 50 : 1,
      }}
    >
      <div style={{
        width: expanded ? W : RAIL,
        height: "100vh",
        background: "var(--bg-page)",
        borderRight: floating ? "1px solid var(--line)" : "0",
        display: "flex", flexDirection: "column",
        position: "absolute", inset: 0,
        transition: "width 220ms cubic-bezier(.2,.7,.2,1), box-shadow 220ms",
        boxShadow: floating ? "8px 0 28px rgba(31,30,27,0.10)" : "none",
        overflow: "hidden",
      }}>
        {/* Brand */}
        <div style={{
          height: 56, padding: "0 18px",
          display: "flex", alignItems: "center", gap: 10,
          borderBottom: "1px solid var(--line)", flexShrink: 0,
        }}>
          <div style={{
            width: 28, height: 28, borderRadius: 7,
            background: "var(--ink)", color: "var(--bg-page)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "var(--font-serif)", fontWeight: 600,
            fontSize: 14, letterSpacing: "-0.02em", flexShrink: 0,
          }}>和</div>
          {expanded && (
            <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.1, whiteSpace: "nowrap", flex: 1, minWidth: 0 }}>
              <span style={{ fontFamily: "var(--font-serif)", fontSize: 15, fontWeight: 600, letterSpacing: "0.02em" }}>
                和意通信
              </span>
              <span className="dim mono" style={{ fontSize: 10, letterSpacing: "0.1em" }}>PMA · v3.0.3</span>
            </div>
          )}
          {expanded && (
            <button
              onClick={onPinToggle}
              title={pinned ? "取消固定" : "固定展开"}
              style={{
                width: 24, height: 24, borderRadius: 4,
                color: pinned ? "var(--accent)" : "var(--ink-3)",
                background: pinned ? "var(--accent-tint)" : "transparent",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}
            ><DashIcon name="pin" size={13} /></button>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, overflowY: "auto", padding: "10px 8px", display: "flex", flexDirection: "column", gap: 1 }}>
          {DASH_NAV.map((n, idx) => {
            if (n.kind === "div") return <div key={idx} style={{ height: 1, background: "var(--line)", margin: "8px 6px" }} />;
            if (n.kind === "item") return (
              <SidebarItem key={n.key} n={n} active={current === n.key}
                expanded={expanded} onClick={() => onNavigate?.(n.key)} />
            );
            // group
            const open = openGroups[n.key];
            return (
              <div key={n.key} style={n.bottom ? { marginTop: "auto" } : {}}>
                {expanded ? (
                  <button
                    onClick={() => setOpenGroups(s => ({...s, [n.key]: !s[n.key]}))}
                    style={{
                      width: "100%", display: "flex", alignItems: "center", gap: 8,
                      padding: "8px 10px", color: "var(--ink-3)",
                      fontSize: 11, fontWeight: 500, letterSpacing: "0.08em",
                      textTransform: "uppercase",
                    }}
                  >
                    <span style={{ flex: 1, textAlign: "left" }}>{n.label}</span>
                    <span style={{
                      transform: open ? "rotate(0deg)" : "rotate(-90deg)",
                      transition: "transform 160ms", color: "var(--ink-4)",
                    }}><DashIcon name="chevd" size={12} /></span>
                  </button>
                ) : (
                  <div style={{ height: 8 }} />
                )}
                {(open || !expanded) && n.items.map(it => (
                  <SidebarItem key={it.key} n={it} active={current === it.key}
                    expanded={expanded} onClick={() => onNavigate?.(it.key)} />
                ))}
              </div>
            );
          })}
        </nav>

        {/* User footer */}
        <div style={{
          padding: "12px 12px", borderTop: "1px solid var(--line)",
          display: "flex", alignItems: "center", gap: 10, flexShrink: 0,
        }}>
          <Avatar name={DASH.currentUser.name} size={30} />
          {expanded && (
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12.5, fontWeight: 500, lineHeight: 1.2, whiteSpace: "nowrap" }}>{DASH.currentUser.name}</div>
              <div className="dim" style={{ fontSize: 11, lineHeight: 1.3, whiteSpace: "nowrap" }}>{DASH.currentUser.title}</div>
            </div>
          )}
          {expanded && (
            <button style={{ color: "var(--ink-3)" }} title="设置">
              <DashIcon name="settings" size={14} />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}

function SidebarItem({ n, active, expanded, onClick }) {
  return (
    <button
      title={!expanded ? n.label : undefined}
      onClick={onClick}
      style={{
        position: "relative",
        display: "flex", alignItems: "center", gap: 12,
        padding: "8px 10px", borderRadius: 6,
        color: active ? "var(--ink)" : "var(--ink-2)",
        background: active ? "var(--bg-active)" : "transparent",
        fontSize: 13, fontWeight: active ? 500 : 400,
        width: "100%", textAlign: "left", whiteSpace: "nowrap", overflow: "hidden",
        transition: "background 100ms",
      }}
      onMouseEnter={e => { if (!active) e.currentTarget.style.background = "var(--bg-hover)"; }}
      onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
    >
      {active && <span style={{
        position: "absolute", left: 0, top: 8, bottom: 8, width: 2,
        borderRadius: 2, background: "var(--accent)",
      }} />}
      <DashIcon name={n.icon} size={16} />
      {expanded && <span style={{ flex: 1 }}>{n.label}</span>}
      {expanded && n.badge != null && (
        <span style={{
          minWidth: 18, height: 18, padding: "0 5px", borderRadius: 9,
          background: "var(--accent)", color: "#fff",
          fontSize: 10, fontWeight: 600,
          display: "inline-flex", alignItems: "center", justifyContent: "center",
        }}>{n.badge}</span>
      )}
    </button>
  );
}

/* ─── Topbar ─────────────────────────────────────────────── */

function DashTopbar({ onCreate }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [notifyOpen, setNotifyOpen] = useState(false);

  useEffect(() => {
    const h = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
      if (e.key === "Escape") { setSearchOpen(false); setCreateOpen(false); setNotifyOpen(false); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  return (
    <>
      <header style={{
        height: 56, padding: "0 24px",
        borderBottom: "1px solid var(--line)",
        background: "rgba(250,249,245,0.85)",
        backdropFilter: "blur(10px)",
        WebkitBackdropFilter: "blur(10px)",
        display: "flex", alignItems: "center", gap: 14,
        position: "sticky", top: 0, zIndex: 30,
      }}>
        {/* Breadcrumb / page title (compact, since we have sidebar) */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--ink-3)", fontSize: 13 }}>
          <span style={{ color: "var(--ink)", fontWeight: 500 }}>仪表盘</span>
          <span style={{ color: "var(--ink-4)" }}>·</span>
          <span>{new Date().toLocaleDateString("zh-CN", { year: "numeric", month: "long", day: "numeric", weekday: "long" })}</span>
        </div>

        <div style={{ flex: 1 }} />

        {/* Global search trigger */}
        <button
          onClick={() => setSearchOpen(true)}
          style={{
            display: "flex", alignItems: "center", gap: 8,
            height: 34, padding: "0 12px",
            background: "var(--bg-elev)", border: "1px solid var(--line-2)",
            borderRadius: 8, color: "var(--ink-3)",
            fontSize: 12.5, minWidth: 320,
          }}>
          <DashIcon name="search" size={14} />
          <span style={{ flex: 1, textAlign: "left" }}>搜索客户、项目、报价、SN…</span>
          <span style={{
            padding: "2px 6px", border: "1px solid var(--line)", borderRadius: 4,
            background: "var(--bg-sunk)", color: "var(--ink-3)",
            fontFamily: "var(--font-mono)", fontSize: 10,
          }}>⌘K</span>
        </button>

        {/* Quick create */}
        <div style={{ position: "relative" }}>
          <Btn variant="accent" iconL="plus" size="md" onClick={() => setCreateOpen(o => !o)}>
            创建
          </Btn>
          {createOpen && <QuickCreateMenu onClose={() => setCreateOpen(false)} />}
        </div>

        {/* Right cluster */}
        <div style={{ display: "flex", alignItems: "center", gap: 2, marginLeft: 4 }}>
          <TopIcon name="cal"  title="工作日历"   dot />
          <TopIcon name="bell" title="通知"        badge="3" onClick={() => setNotifyOpen(o => !o)} active={notifyOpen} />
          <TopIcon name="upload" title="快捷上传"  />
          <TopIcon name="bot"  title="AI 助手"      />
          <TopIcon name="info" title="帮助"        />
          <div style={{ width: 1, height: 22, background: "var(--line)", margin: "0 4px" }} />
          <button title="切换主题"
            onClick={() => {
              const cur = document.documentElement.getAttribute("data-theme");
              document.documentElement.setAttribute("data-theme", cur === "dark" ? "light" : "dark");
            }}
            style={{
              width: 34, height: 34, borderRadius: 6, color: "var(--ink-3)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}
            onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          ><DashIcon name="moon" size={15} /></button>

          {notifyOpen && <NotificationsPanel onClose={() => setNotifyOpen(false)} />}
        </div>
      </header>

      {searchOpen && <GlobalSearch onClose={() => setSearchOpen(false)} />}
    </>
  );
}

function TopIcon({ name, title, dot, badge, onClick, active }) {
  return (
    <button title={title} onClick={onClick}
      style={{
        width: 34, height: 34, borderRadius: 6, color: "var(--ink-3)",
        display: "flex", alignItems: "center", justifyContent: "center",
        position: "relative",
        background: active ? "var(--bg-active)" : "transparent",
      }}
      onMouseEnter={e => { if (!active) e.currentTarget.style.background = "var(--bg-hover)"; }}
      onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
    >
      <DashIcon name={name} size={15} />
      {dot && <span style={{
        position: "absolute", top: 8, right: 9, width: 6, height: 6,
        borderRadius: "50%", background: "var(--accent)",
        border: "1.5px solid var(--bg-page)",
      }} />}
      {badge != null && <span style={{
        position: "absolute", top: 4, right: 4,
        minWidth: 14, height: 14, padding: "0 4px", borderRadius: 7,
        background: "var(--danger)", color: "#fff",
        fontSize: 9, fontWeight: 600,
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        border: "1.5px solid var(--bg-page)",
      }}>{badge}</span>}
    </button>
  );
}

function QuickCreateMenu({ onClose }) {
  const items = [
    { icon: "users",  label: "新建客户", kbd: "C" },
    { icon: "flask",  label: "新建项目", kbd: "P" },
    { icon: "pen",    label: "新建报价", kbd: "Q" },
    { icon: "money",  label: "提交报销", kbd: "E" },
    { icon: "cart",   label: "新建客户订单" },
    { icon: "truck",  label: "新建采购订单" },
    { div: true },
    { icon: "pulse",  label: "记一笔 Action", kbd: "A" },
    { icon: "edit",   label: "写工作日报",     kbd: "D" },
    { icon: "check",  label: "创建任务",       kbd: "T" },
  ];
  return (
    <>
      <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 40 }} />
      <div style={{
        position: "absolute", top: "calc(100% + 6px)", right: 0,
        width: 240, background: "var(--bg-elev)",
        border: "1px solid var(--line)", borderRadius: 10,
        boxShadow: "0 12px 32px rgba(31,30,27,0.14)",
        padding: 6, zIndex: 50,
        animation: "scale-in 140ms ease-out",
      }}>
        <div style={{ padding: "8px 12px 4px", fontSize: 11, color: "var(--ink-3)", letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 500 }}>
          快速创建
        </div>
        {items.map((it, i) => it.div ? (
          <div key={i} style={{ height: 1, background: "var(--line)", margin: "4px 8px" }} />
        ) : (
          <button key={i} style={{
            width: "100%", display: "flex", alignItems: "center", gap: 10,
            padding: "8px 10px", borderRadius: 6, color: "var(--ink)",
            fontSize: 13, textAlign: "left",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
            onClick={onClose}
          >
            <span style={{ color: "var(--ink-3)" }}><DashIcon name={it.icon} size={14} /></span>
            <span style={{ flex: 1 }}>{it.label}</span>
            {it.kbd && <span style={{
              padding: "1px 5px", border: "1px solid var(--line)", borderRadius: 3,
              fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--ink-3)",
            }}>{it.kbd}</span>}
          </button>
        ))}
      </div>
    </>
  );
}

function NotificationsPanel({ onClose }) {
  const items = [
    { tone: "warn",    title: "采购订单 PO-2026-0103 待你审批", time: "2 小时前" },
    { tone: "info",    title: "孙杰 @ 你 在 QU-2026-0521",     time: "4 小时前" },
    { tone: "success", title: "出差报销 EXP-0511 已通过",       time: "今天 10:32" },
    { tone: "danger",  title: "广州宇洪 · 35 天未沟通",         time: "—" },
  ];
  const toneColor = { warn: "var(--warn)", info: "var(--info)", success: "var(--success)", danger: "var(--danger)" };
  return (
    <>
      <div onClick={onClose} style={{ position: "fixed", inset: 0, zIndex: 40 }} />
      <div style={{
        position: "absolute", top: "calc(100% + 6px)", right: 80,
        width: 360, background: "var(--bg-elev)",
        border: "1px solid var(--line)", borderRadius: 10,
        boxShadow: "0 12px 32px rgba(31,30,27,0.14)",
        zIndex: 50, animation: "scale-in 140ms ease-out",
        overflow: "hidden",
      }}>
        <div style={{
          padding: "12px 14px", display: "flex", alignItems: "center",
          borderBottom: "1px solid var(--line)",
        }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>通知</span>
          <span className="mono dim" style={{ marginLeft: 6, fontSize: 11 }}>3 未读</span>
          <span style={{ flex: 1 }} />
          <button style={{ fontSize: 12, color: "var(--accent)" }}>全部已读</button>
        </div>
        {items.map((it, i) => (
          <div key={i} style={{
            padding: "10px 14px", display: "flex", gap: 10, alignItems: "flex-start",
            borderBottom: i < items.length - 1 ? "1px solid var(--line-soft)" : "0",
            cursor: "pointer",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <span style={{ width: 6, height: 6, borderRadius: 3, marginTop: 6, background: toneColor[it.tone], flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 12.5, color: "var(--ink)", lineHeight: 1.4 }}>{it.title}</div>
              <div style={{ fontSize: 11, color: "var(--ink-4)", marginTop: 2 }}>{it.time}</div>
            </div>
          </div>
        ))}
        <button style={{
          width: "100%", padding: "10px", textAlign: "center",
          fontSize: 12, color: "var(--accent)", borderTop: "1px solid var(--line)",
        }}>查看全部 →</button>
      </div>
    </>
  );
}

function GlobalSearch({ onClose }) {
  const [q, setQ] = useState("");
  const ref = useRef();
  useEffect(() => { ref.current?.focus(); }, []);
  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, background: "rgba(31,30,27,0.35)",
      backdropFilter: "blur(2px)", zIndex: 100,
      display: "flex", justifyContent: "center", alignItems: "flex-start",
      paddingTop: "12vh",
      animation: "fade-in 140ms",
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: 640, maxWidth: "90vw",
        background: "var(--bg-elev)",
        border: "1px solid var(--line)", borderRadius: 12,
        boxShadow: "0 20px 60px rgba(31,30,27,0.20)",
        overflow: "hidden",
        animation: "scale-in 160ms ease-out",
      }}>
        <div style={{
          padding: "14px 18px", display: "flex", alignItems: "center", gap: 12,
          borderBottom: "1px solid var(--line)",
        }}>
          <DashIcon name="search" size={18} />
          <input ref={ref} value={q} onChange={e => setQ(e.target.value)}
            placeholder="搜索客户、项目、报价、SN、产品…"
            style={{
              flex: 1, border: 0, outline: 0, background: "transparent",
              fontSize: 16, color: "var(--ink)", fontFamily: "var(--font-sans)",
            }}
          />
          <kbd style={{
            padding: "2px 7px", border: "1px solid var(--line)", borderRadius: 4,
            background: "var(--bg-sunk)", color: "var(--ink-3)",
            fontFamily: "var(--font-mono)", fontSize: 11,
          }}>ESC</kbd>
        </div>
        <div style={{ maxHeight: 440, overflowY: "auto", padding: "8px 0" }}>
          {Object.entries(DASH.searchSuggest).map(([cat, list]) => (
            <div key={cat}>
              <div style={{
                padding: "8px 18px 4px", fontSize: 11, color: "var(--ink-3)",
                letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 500,
              }}>{cat}</div>
              {list.map((it, i) => (
                <button key={i} style={{
                  width: "100%", padding: "9px 18px",
                  display: "flex", alignItems: "center", gap: 12,
                  fontSize: 13, color: "var(--ink)", textAlign: "left",
                }}
                  onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                >
                  <span style={{ flex: 1 }}>{it.label}</span>
                  <span className="dim mono" style={{ fontSize: 11 }}>{it.sub}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
        <div style={{
          padding: "10px 18px", borderTop: "1px solid var(--line)",
          background: "var(--bg-sunk)",
          display: "flex", alignItems: "center", gap: 14,
          fontSize: 11, color: "var(--ink-3)",
        }}>
          <span><kbd style={kbdStyle}>↑↓</kbd> 选择</span>
          <span><kbd style={kbdStyle}>↵</kbd> 打开</span>
          <span><kbd style={kbdStyle}>Tab</kbd> 切换类型</span>
          <span style={{ flex: 1 }} />
          <span>Powered by PMA 全文索引</span>
        </div>
      </div>
    </div>
  );
}
const kbdStyle = {
  padding: "1px 5px", border: "1px solid var(--line)", borderRadius: 3,
  background: "var(--bg-elev)", fontFamily: "var(--font-mono)",
  fontSize: 10, marginRight: 4,
};

/* ─── 风险提醒条 (条件性) ──────────────────────────────────── */
function AlertBar({ alerts, onDismiss }) {
  if (!alerts.length) return null;
  return (
    <div style={{
      background: "linear-gradient(90deg, var(--warn-soft) 0%, var(--accent-tint) 100%)",
      borderBottom: "1px solid var(--warn-soft)",
      padding: "8px 24px",
      display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap",
      fontSize: 12.5,
    }}>
      <DashIcon name="alert" size={14} style={{ color: "var(--warn)" }} />
      <span style={{ color: "var(--ink-2)", fontWeight: 500 }}>需要关注</span>
      <div style={{ display: "flex", alignItems: "center", gap: 14, flex: 1, flexWrap: "wrap" }}>
        {alerts.map((a, i) => (
          <span key={i} style={{ display: "inline-flex", alignItems: "center", gap: 14 }}>
            {i > 0 && <span style={{ color: "var(--warn)", opacity: 0.4 }}>·</span>}
            <button style={{
              color: "var(--ink)", display: "inline-flex", alignItems: "center", gap: 4,
              fontWeight: 500,
            }}>
              {a.text}
              <DashIcon name="arrowRt" size={11} style={{ color: "var(--warn)" }} />
            </button>
          </span>
        ))}
      </div>
      <button onClick={onDismiss} style={{ color: "var(--ink-3)", padding: 2 }}>
        <DashIcon name="close" size={13} />
      </button>
    </div>
  );
}

Object.assign(window, { DashIcon, DashSidebar, DashTopbar, AlertBar });
