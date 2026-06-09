/* ─────────────────────────────────────────────────────────────
   PMA · 仪表盘 · 卡片组件
   每个卡片都有 header (title + action) + body + 可选 footer
   ───────────────────────────────────────────────────────────── */

/* ── 通用 Card 容器 ─────────────────────────────────────────── */
function Card({ title, subtitle, action, children, padding = 22, style }) {
  return (
    <section style={{
      background: "var(--bg-elev)",
      border: "1px solid var(--line)",
      borderRadius: 12,
      display: "flex", flexDirection: "column",
      overflow: "hidden",
      ...style,
    }}>
      {(title || action) && (
        <header style={{
          padding: `18px ${padding}px 14px`,
          display: "flex", alignItems: "center", gap: 12,
        }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            {title && (
              <h3 style={{
                margin: 0, fontFamily: "var(--font-serif)",
                fontSize: 17, fontWeight: 500, letterSpacing: "0.005em",
                lineHeight: 1.2, color: "var(--ink)",
              }}>{title}</h3>
            )}
            {subtitle && (
              <div style={{ marginTop: 3, fontSize: 12, color: "var(--ink-3)" }}>{subtitle}</div>
            )}
          </div>
          {action}
        </header>
      )}
      <div style={{ padding: `0 ${padding}px ${padding}px`, flex: 1, minWidth: 0 }}>
        {children}
      </div>
    </section>
  );
}

const SectionLabel = ({ children, action }) => (
  <div style={{
    display: "flex", alignItems: "baseline", gap: 10,
    margin: "0 4px 14px",
  }}>
    <h2 className="serif" style={{
      margin: 0, fontSize: 22, fontWeight: 500, letterSpacing: "-0.005em",
      color: "var(--ink)",
    }}>{children}</h2>
    {action}
  </div>
);

/* ─────────────────────────────────────────────────────────────
   Row 1 · CARD A: 我的待办
   ───────────────────────────────────────────────────────────── */
function TodoCard() {
  const [tab, setTab] = useState("all");
  const filtered = DASH.todos.filter(t => tab === "all" || t.type === tab);
  const counts = DASH.todos.reduce((a, t) => { a[t.type] = (a[t.type] || 0) + 1; return a; }, {});
  const tabs = [
    { k: "all",       label: "全部",   n: DASH.todos.length, tone: "neutral" },
    { k: "approval",  label: "待审批", n: counts.approval || 0, tone: "warn" },
    { k: "quotation", label: "待确认", n: counts.quotation || 0, tone: "info" },
    { k: "mention",   label: "@我的", n: counts.mention || 0, tone: "accent" },
    { k: "action",    label: "Action", n: counts.action || 0, tone: "danger" },
  ];

  return (
    <Card
      title="我的待办"
      subtitle={
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
          <span>共 {DASH.todos.length} 项</span>
          <span style={{ width: 4, height: 4, background: "var(--ink-4)", borderRadius: 2 }} />
          <span style={{ color: "var(--danger)" }}>{DASH.todos.filter(t => t.urgent).length} 紧急</span>
        </span>
      }
      action={<Btn variant="bare" size="sm" iconR="arrowRt">全部待办</Btn>}
    >
      {/* Tabs */}
      <div style={{
        display: "flex", gap: 4, marginBottom: 14, padding: 3,
        background: "var(--bg-sunk)", borderRadius: 8,
      }}>
        {tabs.map(t => (
          <button key={t.k} onClick={() => setTab(t.k)}
            style={{
              flex: 1, padding: "5px 8px", borderRadius: 6,
              fontSize: 11.5, fontWeight: 500,
              color: tab === t.k ? "var(--ink)" : "var(--ink-3)",
              background: tab === t.k ? "var(--bg-elev)" : "transparent",
              boxShadow: tab === t.k ? "0 1px 2px rgba(31,30,27,0.06)" : "none",
              display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 5,
              transition: "background 120ms",
            }}>
            <span>{t.label}</span>
            <span className="tab-num" style={{
              padding: "0 5px", fontSize: 10,
              borderRadius: 4, background: tab === t.k ? "var(--bg-sunk)" : "transparent",
              color: "var(--ink-3)",
            }}>{t.n}</span>
          </button>
        ))}
      </div>

      {/* List */}
      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 0 }}>
        {filtered.slice(0, 5).map((t, i) => (
          <li key={t.id} style={{
            padding: "11px 6px", display: "flex", gap: 12, alignItems: "flex-start",
            borderTop: i === 0 ? "0" : "1px solid var(--line-soft)",
            cursor: "pointer", position: "relative",
            transition: "background 100ms", borderRadius: 6,
          }}
            onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <Pill tone={t.tone} size="md" dot>{t.typeLabel}</Pill>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 13, color: "var(--ink)", lineHeight: 1.35,
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                fontWeight: 500,
              }}>{t.title}</div>
              <div style={{
                fontSize: 11.5, color: "var(--ink-3)", marginTop: 3,
                display: "flex", alignItems: "center", gap: 8,
              }}>
                <span>{t.meta}</span>
                {t.who !== "—" && <>
                  <span style={{ color: "var(--ink-4)" }}>·</span>
                  <span>{t.who}</span>
                </>}
                {t.when !== "—" && <>
                  <span style={{ color: "var(--ink-4)" }}>·</span>
                  <span>{t.when}</span>
                </>}
              </div>
            </div>
            {t.urgent && (
              <span title="紧急" style={{
                color: "var(--danger)", marginTop: 2, fontSize: 10,
              }}>●</span>
            )}
          </li>
        ))}
      </ul>

      {filtered.length > 5 && (
        <button style={{
          marginTop: 8, padding: "8px 0", width: "100%",
          fontSize: 12, color: "var(--accent)", fontWeight: 500,
          borderTop: "1px solid var(--line-soft)",
        }}>显示其余 {filtered.length - 5} 项</button>
      )}
    </Card>
  );
}

/* ─────────────────────────────────────────────────────────────
   Row 1 · CARD B: 我的 KPI
   ───────────────────────────────────────────────────────────── */
function KPICard() {
  const { salesGoal, quoteWin, activeCust, budget } = DASH.kpis;
  const pct = (v, t) => Math.min(100, Math.round(v / t * 100));

  const items = [
    { ...salesGoal, pct: pct(salesGoal.value, salesGoal.target),
      display: fmtCNY(salesGoal.value).replace(".00",""), of: fmtCNY(salesGoal.target).replace(".00",""),
      tone: "var(--accent)", delta: "+12%", deltaTone: "var(--success)" },
    { ...quoteWin, pct: quoteWin.value,
      display: quoteWin.value + "%", of: "目标 100%",
      tone: "var(--success)", delta: "+5pp", deltaTone: "var(--success)" },
    { ...activeCust, pct: pct(activeCust.value, activeCust.target),
      display: activeCust.value + " 户", of: activeCust.target + " 户",
      tone: "var(--info)", delta: "持平", deltaTone: "var(--ink-3)" },
    { ...budget, pct: pct(budget.value, budget.target),
      display: fmtCNY(budget.value).replace(".00",""), of: fmtCNY(budget.target).replace(".00",""),
      tone: "var(--warn)", delta: "+8%", deltaTone: "var(--warn)" },
  ];

  return (
    <Card
      title="我的 KPI"
      subtitle="本季度 · 同比上季度"
      action={<button title="刷新" style={{ color: "var(--ink-3)", padding: 4 }}><DashIcon name="refresh" size={13} /></button>}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {items.map((it, i) => (
          <div key={i}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 5 }}>
              <span style={{ fontSize: 12, color: "var(--ink-3)" }}>{it.label}</span>
              <span style={{ flex: 1 }} />
              <span style={{
                fontSize: 10.5, fontWeight: 500, padding: "1px 6px",
                borderRadius: 3,
                color: it.deltaTone,
                background: it.deltaTone === "var(--success)" ? "var(--success-soft)"
                          : it.deltaTone === "var(--warn)" ? "var(--warn-soft)" : "var(--bg-sunk)",
              }}>{it.delta}</span>
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 6 }}>
              <span className="tab-num" style={{
                fontFamily: "var(--font-serif)", fontSize: 22, fontWeight: 500,
                color: "var(--ink)", letterSpacing: "-0.01em",
              }}>{it.display}</span>
              <span className="dim" style={{ fontSize: 11 }}>/ {it.of}</span>
              <span style={{ flex: 1 }} />
              <span className="mono tab-num" style={{ fontSize: 11.5, color: it.tone, fontWeight: 500 }}>
                {it.pct}%
              </span>
            </div>
            <div style={{ height: 3, background: "var(--bg-sunk)", borderRadius: 2, overflow: "hidden" }}>
              <div style={{
                width: it.pct + "%", height: "100%",
                background: it.tone, borderRadius: 2,
                transition: "width 600ms cubic-bezier(.2,.7,.2,1)",
              }} />
            </div>
          </div>
        ))}
      </div>

      {/* Today's micro-stats */}
      <div style={{
        marginTop: 18, padding: "12px 0 0",
        borderTop: "1px solid var(--line-soft)",
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 4,
      }}>
        <div style={{ fontSize: 10.5, color: "var(--ink-3)", gridColumn: "1 / -1", marginBottom: 2 }}>
          今日 · {new Date().toLocaleDateString("zh-CN", { month: "numeric", day: "numeric" })}
        </div>
        {[
          { n: DASH.todayStats.newCust,   l: "新客户" },
          { n: DASH.todayStats.newQuote,  l: "新报价" },
          { n: DASH.todayStats.newAction, l: "Action" },
          { n: DASH.todayStats.newOrder,  l: "新订单" },
        ].map((s, i) => (
          <div key={i} style={{
            display: "flex", flexDirection: "column", gap: 1,
            paddingLeft: i === 0 ? 0 : 8,
            borderLeft: i === 0 ? "0" : "1px solid var(--line-soft)",
          }}>
            <span className="tab-num" style={{ fontSize: 16, fontWeight: 600, color: "var(--ink)" }}>{s.n}</span>
            <span style={{ fontSize: 10.5, color: "var(--ink-3)" }}>{s.l}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

/* ─────────────────────────────────────────────────────────────
   Row 1 · CARD C: 快速操作
   ───────────────────────────────────────────────────────────── */
function QuickActionsCard() {
  const primary = [
    { icon: "users", label: "新客户",   sub: "录入潜在客户" },
    { icon: "pen",   label: "新报价",   sub: "起草新报价单" },
    { icon: "pulse", label: "记 Action", sub: "客户跟进沟通" },
    { icon: "money", label: "提报销",   sub: "费用申请审批" },
  ];
  const secondary = [
    { icon: "flask",  label: "新建项目" },
    { icon: "cart",   label: "客户订单" },
    { icon: "truck",  label: "采购单"   },
    { icon: "edit",   label: "写日报"   },
    { icon: "check",  label: "新任务"   },
    { icon: "users",  label: "排会议"   },
  ];

  return (
    <Card
      title="快速操作"
      subtitle="按 ⌘+N 唤起菜单"
      action={<Pill tone="accent">销售常用</Pill>}
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {primary.map((a, i) => (
          <button key={i} style={{
            padding: "14px 14px", textAlign: "left",
            background: "var(--bg-sunk)", border: "1px solid transparent",
            borderRadius: 10,
            display: "flex", flexDirection: "column", gap: 8,
            transition: "all 140ms",
          }}
            onMouseEnter={e => {
              e.currentTarget.style.background = "var(--accent-tint)";
              e.currentTarget.style.borderColor = "var(--accent-soft)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = "var(--bg-sunk)";
              e.currentTarget.style.borderColor = "transparent";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: "var(--bg-elev)", color: "var(--accent)",
              display: "flex", alignItems: "center", justifyContent: "center",
              border: "1px solid var(--line)",
            }}><DashIcon name={a.icon} size={16} /></div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>{a.label}</div>
              <div style={{ fontSize: 11, color: "var(--ink-3)", marginTop: 2 }}>{a.sub}</div>
            </div>
          </button>
        ))}
      </div>

      <div style={{
        marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--line-soft)",
      }}>
        <div style={{ fontSize: 11, color: "var(--ink-3)", marginBottom: 8, letterSpacing: "0.04em" }}>
          其他动作
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {secondary.map((a, i) => (
            <button key={i} style={{
              padding: "5px 10px", borderRadius: 6,
              border: "1px solid var(--line)", background: "var(--bg-elev)",
              fontSize: 12, color: "var(--ink-2)",
              display: "inline-flex", alignItems: "center", gap: 5,
            }}
              onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
              onMouseLeave={e => e.currentTarget.style.background = "var(--bg-elev)"}
            >
              <DashIcon name={a.icon} size={12} style={{ color: "var(--ink-3)" }} />
              {a.label}
            </button>
          ))}
        </div>
      </div>
    </Card>
  );
}

Object.assign(window, { Card, SectionLabel, TodoCard, KPICard, QuickActionsCard });
