/* ─────────────────────────────────────────────────────────────
   PMA · 仪表盘 · 主 App + 角色化布局 + Tweaks
   ───────────────────────────────────────────────────────────── */

/* 7 张卡 (todo / kpi / funnel / projects / quotes / expense / worklog)
   按角色重排顺序。worklog 永远在最末(它是宽列)。
   Row 1: 0,1,2 (3 列, 角色化权重)
   Row 2: 3,4   (2 列, 1.05fr / 0.95fr)
   Row 3: 5,6   (1fr / 1.7fr)
*/
const ROLE_LAYOUTS = {
  admin:  { label: "管理员",     order: ["todo", "kpi", "funnel", "projects", "quotes", "expense", "worklog"],
            row1w: "1.15fr 1fr 1.35fr" },
  sales:  { label: "销售",       order: ["todo", "kpi", "funnel", "projects", "quotes", "expense", "worklog"],
            row1w: "1.15fr 1fr 1.35fr" },
  sm:     { label: "方案经理",   order: ["todo", "quotes", "funnel", "projects", "kpi", "expense", "worklog"],
            row1w: "1fr 1.2fr 1.2fr" },
  finance:{ label: "财务",       order: ["todo", "expense", "kpi", "projects", "funnel", "quotes", "worklog"],
            row1w: "1fr 1.3fr 1fr" },
  ceo:    { label: "CEO / 管理", order: ["funnel", "kpi", "todo", "projects", "quotes", "expense", "worklog"],
            row1w: "1.5fr 0.95fr 0.95fr" },
};

function App() {
  const [t, setTweak] = useTweaks(/*EDITMODE-BEGIN*/{
    "role": "admin",
    "theme": "light",
    "density": "standard",
    "headlineFont": "serif",
    "showAlerts": true,
    "sidebarPinned": true
  }/*EDITMODE-END*/);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme",         t.theme);
    document.documentElement.setAttribute("data-density",       t.density);
    document.documentElement.setAttribute("data-headline-font", t.headlineFont);
  }, [t.theme, t.density, t.headlineFont]);

  const [alertsDismissed, setAlertsDismissed] = useState(false);
  const [currentNav, setCurrentNav] = useState("dashboard");

  const layout = ROLE_LAYOUTS[t.role] || ROLE_LAYOUTS.admin;
  const cardByKey = {
    todo:     <TodoCard />,
    kpi:      <KPICard />,
    funnel:   <FunnelCard />,
    projects: <ProjectsCard />,
    quotes:   <QuotesCard />,
    expense:  <ExpenseCard />,
    worklog:  <WorklogCard />,
  };
  const ord = layout.order;

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-page)" }}>
      <DashSidebar
        pinned={t.sidebarPinned}
        onPinToggle={() => setTweak("sidebarPinned", !t.sidebarPinned)}
        current={currentNav}
        onNavigate={setCurrentNav}
      />

      <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <DashTopbar />

        {t.showAlerts && !alertsDismissed && (
          <AlertBar alerts={DASH.alerts} onDismiss={() => setAlertsDismissed(true)} />
        )}

        <main style={{ flex: 1, padding: "32px 40px 60px", maxWidth: 1480, width: "100%", margin: "0 auto" }}>

          {/* Hero */}
          <div style={{ marginBottom: 28, display: "flex", alignItems: "flex-end", gap: 16, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 320 }}>
              <h1 style={{
                margin: 0, fontFamily: "var(--font-serif)",
                fontSize: 36, fontWeight: 500, letterSpacing: "-0.015em",
                color: "var(--ink)", lineHeight: 1.1,
              }}>
                晚上好,{DASH.currentUser.name}。
              </h1>
              <p style={{
                margin: "8px 0 0", fontSize: 14, color: "var(--ink-3)",
                lineHeight: 1.5,
              }}>
                你有 <b style={{ color: "var(--accent)" }}>{DASH.todos.length} 项待办</b> 等待处理 ·
                本季销售完成 <b style={{ color: "var(--ink)" }}>67%</b> ·
                视图角色:<b style={{ color: "var(--ink)" }}>{layout.label}</b>
              </p>
            </div>
            <Btn variant="ghost" size="sm" iconL="book">使用说明书</Btn>
            <Btn variant="soft" size="sm" iconL="sparkle">AI 周报</Btn>
          </div>

          {/* Row 1 (role-driven, 3 cards) */}
          <div style={{
            display: "grid", gridTemplateColumns: layout.row1w, gap: 20,
            marginBottom: 20, alignItems: "stretch",
          }}>
            {[ord[0], ord[1], ord[2]].map(k => (
              <div key={k} style={{ display: "contents" }}>{cardByKey[k]}</div>
            ))}
          </div>

          {/* Row 2 (2 cards) */}
          <div style={{
            display: "grid", gridTemplateColumns: "1.05fr 0.95fr", gap: 20,
            marginBottom: 20, alignItems: "stretch",
          }}>
            {[ord[3], ord[4]].map(k => (
              <div key={k} style={{ display: "contents" }}>{cardByKey[k]}</div>
            ))}
          </div>

          {/* Row 3 (2 cards, 1 : 1.7) */}
          <div style={{
            display: "grid", gridTemplateColumns: "1fr 1.7fr", gap: 20,
            alignItems: "stretch",
          }}>
            {[ord[5], ord[6]].map(k => (
              <div key={k} style={{ display: "contents" }}>{cardByKey[k]}</div>
            ))}
          </div>

          <footer style={{
            marginTop: 40, paddingTop: 18,
            borderTop: "1px solid var(--line-soft)",
            display: "flex", alignItems: "center", gap: 14,
            fontSize: 11.5, color: "var(--ink-4)",
          }}>
            <DashIcon name="star" size={12} />
            <span>团队 Skills 商店</span>
            <span style={{ color: "var(--ink-4)", opacity: 0.5 }}>—</span>
            <span>由 PMA Cowork 提供团队私有 skill</span>
            <span style={{ flex: 1 }} />
            <span className="mono">v3.0.3 · Build 2026-05-22</span>
          </footer>
        </main>
      </div>

      <TweaksPanel title="Tweaks · 仪表盘">
        <TweakSection label="角色视图">
          <TweakSelect
            label="当前角色"
            value={t.role}
            onChange={v => setTweak("role", v)}
            options={[
              { value: "admin",   label: "管理员" },
              { value: "sales",   label: "销售"   },
              { value: "sm",      label: "方案经理 SM" },
              { value: "finance", label: "财务"   },
              { value: "ceo",     label: "CEO / 管理层" },
            ]}
          />
        </TweakSection>

        <TweakSection label="外观">
          <TweakRadio
            label="主题"
            value={t.theme}
            onChange={v => setTweak("theme", v)}
            options={[{ value: "light", label: "Light" }, { value: "dark", label: "Dark" }]}
          />
          <TweakRadio
            label="标题字体"
            value={t.headlineFont}
            onChange={v => setTweak("headlineFont", v)}
            options={[{ value: "serif", label: "衬线" }, { value: "sans", label: "无衬线" }]}
          />
          <TweakRadio
            label="密度"
            value={t.density}
            onChange={v => setTweak("density", v)}
            options={[
              { value: "compact",  label: "紧凑" },
              { value: "standard", label: "标准" },
              { value: "cozy",     label: "宽松" },
            ]}
          />
        </TweakSection>

        <TweakSection label="布局">
          <TweakToggle label="显示风险提醒条" value={t.showAlerts} onChange={v => setTweak("showAlerts", v)} />
          <TweakToggle label="固定侧边栏" value={t.sidebarPinned} onChange={v => setTweak("sidebarPinned", v)} />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
