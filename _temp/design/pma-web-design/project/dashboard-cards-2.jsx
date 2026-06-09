/* ─────────────────────────────────────────────────────────────
   PMA · 仪表盘 · Row 2 + Row 3 卡片
   ───────────────────────────────────────────────────────────── */

/* ─────────────────────────────────────────────────────────────
   Row 2 · CARD A: 销售漏斗 (水平阶梯条 + 段间转化率)
   ───────────────────────────────────────────────────────────── */
function FunnelCard() {
  const max = DASH.funnel[0].amount;
  return (
    <Card
      title="销售漏斗"
      subtitle="当前在管销售机会全链路"
      action={
        <div style={{ display: "flex", gap: 6 }}>
          <Pill tone="success" size="md">转化 {DASH.funnelConversion}%</Pill>
          <Pill tone="info" size="md" dot>同比 +{DASH.funnelYoY}%</Pill>
        </div>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {DASH.funnel.map((s, i) => {
          const w = s.amount / max * 100;
          const next = DASH.funnel[i + 1];
          const drop = next ? Math.round((s.amount - next.amount) / s.amount * 100) : null;
          const isLast = i === DASH.funnel.length - 1;
          const tone = ["#C15F3C", "#D97757", "#B8742E", "#2A5F8F", "#2F7155"][i];
          return (
            <div key={s.stage}>
              <div style={{
                position: "relative",
                display: "flex", alignItems: "center", gap: 12,
                padding: "6px 0",
              }}>
                <span style={{
                  width: 56, fontSize: 12, fontWeight: 500, color: "var(--ink-2)",
                  textAlign: "right", letterSpacing: "0.02em",
                }}>{s.stage}</span>
                <div style={{ flex: 1, position: "relative", height: 34 }}>
                  <div style={{
                    width: w + "%", height: "100%", borderRadius: 6,
                    background: `linear-gradient(90deg, ${tone}88, ${tone})`,
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    padding: "0 12px", color: "#fff", minWidth: 90,
                    transition: "width 600ms cubic-bezier(.2,.7,.2,1)",
                  }}>
                    <span className="tab-num" style={{ fontSize: 12, fontWeight: 600 }}>
                      {s.count} 单
                    </span>
                    <span className="tab-num" style={{ fontSize: 11.5, opacity: 0.9 }}>
                      {fmtCNY(s.amount).replace(".00", "")}
                    </span>
                  </div>
                </div>
              </div>
              {!isLast && (
                <div style={{
                  display: "flex", alignItems: "center", gap: 12,
                  paddingLeft: 68, height: 12,
                }}>
                  <div style={{
                    height: 12, width: 1, borderLeft: "1px dashed var(--line-2)",
                    marginLeft: -2,
                  }} />
                  <span style={{ fontSize: 10.5, color: "var(--ink-3)" }}>
                    流失 <span className="tab-num" style={{ color: "var(--danger)" }}>{drop}%</span>
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{
        marginTop: 16, padding: "10px 12px",
        background: "var(--bg-sunk)", borderRadius: 8,
        display: "flex", alignItems: "center", gap: 14,
        fontSize: 11.5, color: "var(--ink-3)",
      }}>
        <DashIcon name="info" size={12} />
        <span>本季漏斗顶部健康,但 <b style={{ color: "var(--warn)" }}>"已确认 → 批价"</b> 流失 25%,建议关注 SM 排期。</span>
      </div>
    </Card>
  );
}

/* ─────────────────────────────────────────────────────────────
   Row 2 · CARD B: 我的项目 (进行中)
   ───────────────────────────────────────────────────────────── */
function ProjectsCard() {
  return (
    <Card
      title="我的项目"
      subtitle={
        <span>
          进行中 <b className="tab-num" style={{ color: "var(--ink)" }}>{DASH.projectCounts.active}</b>
          <span style={{ color: "var(--ink-4)" }}> · </span>
          即将到期 <b className="tab-num" style={{ color: "var(--danger)" }}>{DASH.projectCounts.dueSoon}</b>
        </span>
      }
      action={<Btn variant="bare" size="sm" iconR="arrowRt">全部项目</Btn>}
    >
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {DASH.projects.map((p, i) => (
          <li key={p.id} style={{
            padding: "10px 4px",
            borderTop: i === 0 ? "0" : "1px solid var(--line-soft)",
            display: "flex", flexDirection: "column", gap: 6,
            cursor: "pointer", borderRadius: 6,
            transition: "background 100ms",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <Pill tone={p.stageT} size="md">{p.stage}</Pill>
              <span style={{
                flex: 1, fontSize: 13, color: "var(--ink)", fontWeight: 500,
                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
              }}>{p.name}</span>
              {p.dueRed && (
                <span style={{
                  fontSize: 10.5, color: "var(--danger)", fontWeight: 500,
                  display: "inline-flex", alignItems: "center", gap: 4,
                }}>
                  <span style={{ width: 5, height: 5, background: "var(--danger)", borderRadius: 3 }} />
                  {p.dueIn}天到期
                </span>
              )}
            </div>
            <div style={{
              display: "flex", alignItems: "center", gap: 10,
              paddingLeft: 4,
            }}>
              <div style={{
                flex: 1, height: 3, background: "var(--bg-sunk)",
                borderRadius: 2, overflow: "hidden", maxWidth: 240,
              }}>
                <div style={{
                  width: p.progress + "%", height: "100%",
                  background: p.progress >= 50 ? "var(--accent)" : "var(--ink-3)",
                  borderRadius: 2,
                }} />
              </div>
              <span className="tab-num mono" style={{
                fontSize: 11, color: "var(--ink-3)", width: 36,
              }}>{p.progress}%</span>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

/* ─────────────────────────────────────────────────────────────
   Row 2 · CARD C: 我的报价 (按状态聚合)
   ───────────────────────────────────────────────────────────── */
function QuotesCard() {
  const { draft, awaitConfirm, awaitReply, expiring, wonThisMonth } = DASH.quoteCounts;
  const stats = [
    { k: "draft",        label: "草稿",     n: draft,        tone: "neutral" },
    { k: "awaitConfirm", label: "待确认",   n: awaitConfirm, tone: "warn",  hot: true },
    { k: "awaitReply",   label: "待回复",   n: awaitReply,   tone: "info" },
    { k: "expiring",     label: "即将到期", n: expiring,     tone: "danger", hot: true },
    { k: "won",          label: "本月成交", n: wonThisMonth, tone: "success" },
  ];
  return (
    <Card
      title="我的报价"
      subtitle="按状态聚合"
      action={<Btn variant="bare" size="sm" iconR="arrowRt">全部报价</Btn>}
    >
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 6,
        marginBottom: 14,
      }}>
        {stats.map(s => (
          <button key={s.k} style={{
            padding: "10px 6px", borderRadius: 8,
            background: "var(--bg-sunk)", border: "1px solid transparent",
            display: "flex", flexDirection: "column", alignItems: "center", gap: 3,
            position: "relative",
            transition: "all 140ms",
          }}
            onMouseEnter={e => { e.currentTarget.style.background = "var(--bg-hover)"; e.currentTarget.style.borderColor = "var(--line)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "var(--bg-sunk)"; e.currentTarget.style.borderColor = "transparent"; }}
          >
            {s.hot && s.n > 0 && (
              <span style={{
                position: "absolute", top: 5, right: 5,
                width: 6, height: 6, borderRadius: 3,
                background: s.tone === "danger" ? "var(--danger)" : "var(--warn)",
              }} />
            )}
            <span className="tab-num serif" style={{
              fontSize: 22, fontWeight: 500, color: "var(--ink)",
              fontFamily: "var(--font-serif)", lineHeight: 1,
            }}>{s.n}</span>
            <span style={{ fontSize: 10.5, color: "var(--ink-3)", letterSpacing: "0.02em" }}>{s.label}</span>
          </button>
        ))}
      </div>

      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {DASH.quotes.map((q, i) => (
          <li key={q.id} style={{
            padding: "9px 4px",
            borderTop: i === 0 ? "0" : "1px solid var(--line-soft)",
            display: "flex", alignItems: "center", gap: 10,
            cursor: "pointer", borderRadius: 6,
            transition: "background 100ms",
          }}
            onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}
          >
            <span className="mono" style={{
              fontSize: 11, color: "var(--ink-3)", width: 96, letterSpacing: 0,
            }}>{q.id}</span>
            <span style={{
              flex: 1, fontSize: 12.5, color: "var(--ink)",
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            }}>{q.title}</span>
            <span className="tab-num mono" style={{ fontSize: 12, color: "var(--ink-2)" }}>
              {fmtCNY(q.amount).replace(".00", "")}
            </span>
            <Pill tone={q.tone} size="md">{q.status}</Pill>
          </li>
        ))}
      </ul>
    </Card>
  );
}

/* ─────────────────────────────────────────────────────────────
   Row 3 · CARD A: 我的报销 (12 月折线 + 列表)
   ───────────────────────────────────────────────────────────── */
function ExpenseCard() {
  const { yearTotal, yearTotalLast, monthly, months, recent } = DASH.expense;
  const max = Math.max(...monthly, 1);
  const avg = monthly.reduce((a, b) => a + b, 0) / monthly.filter(v => v > 0).length;

  const points = monthly.map((v, i) => ({
    x: (i / (monthly.length - 1)) * 100,
    y: 100 - (v / max) * 95,
    v,
  }));
  const pathD = points.map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`)).join(" ");
  const areaD = pathD + ` L 100 100 L 0 100 Z`;
  const avgY = 100 - (avg / max) * 95;

  const yoY = ((yearTotal - yearTotalLast) / yearTotalLast * 100).toFixed(1);

  return (
    <Card
      title="我的报销"
      subtitle={`本年度 · 12 月趋势`}
      action={<Btn variant="ghost" size="sm" iconL="plus">提交报销</Btn>}
    >
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: "var(--ink-3)" }}>今年累计</span>
        <span className="tab-num" style={{
          fontFamily: "var(--font-serif)", fontSize: 30, fontWeight: 500,
          letterSpacing: "-0.01em", color: "var(--ink)",
        }}>{fmtCNY(yearTotal).replace(".00", "")}</span>
        <Pill tone={yoY > 0 ? "warn" : "success"} size="md">
          同比 {yoY > 0 ? "+" : ""}{yoY}%
        </Pill>
      </div>
      <div style={{ fontSize: 11, color: "var(--ink-4)", marginBottom: 14 }}>
        月均 {fmtCNY(avg).replace(".00", "")} · CNY 结算
      </div>

      {/* Chart */}
      <div style={{
        position: "relative", height: 100, marginBottom: 6,
        background: "linear-gradient(180deg, var(--bg-sunk) 0%, transparent 80%)",
        borderRadius: 6, padding: "4px 0",
      }}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none"
             style={{ width: "100%", height: "100%", display: "block" }}>
          <defs>
            <linearGradient id="exp-grad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.22" />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
            </linearGradient>
          </defs>
          <line x1="0" y1={avgY} x2="100" y2={avgY}
                stroke="var(--ink-4)" strokeWidth="0.4" strokeDasharray="1.4 1.4"
                vectorEffect="non-scaling-stroke" />
          <path d={areaD} fill="url(#exp-grad)" />
          <path d={pathD} fill="none" stroke="var(--accent)" strokeWidth="1.6"
                vectorEffect="non-scaling-stroke" strokeLinejoin="round" strokeLinecap="round" />
          {points.map((p, i) => p.v > 0 && (
            <circle key={i} cx={p.x} cy={p.y} r="0.9" fill="var(--bg-elev)"
              stroke="var(--accent)" strokeWidth="0.6"
              vectorEffect="non-scaling-stroke" />
          ))}
        </svg>
      </div>
      <div style={{
        display: "grid", gridTemplateColumns: `repeat(${months.length}, 1fr)`,
        fontSize: 9.5, color: "var(--ink-4)", marginBottom: 16,
        fontFamily: "var(--font-mono)",
      }}>
        {months.map((m, i) => (
          <span key={i} style={{ textAlign: "center" }}>{m.replace("月","")}</span>
        ))}
      </div>

      {/* Recent list */}
      <div style={{ fontSize: 11, color: "var(--ink-3)", marginBottom: 6, letterSpacing: "0.04em" }}>
        最近 3 笔
      </div>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {recent.map((e, i) => (
          <li key={e.id} style={{
            padding: "8px 4px",
            borderTop: i === 0 ? "0" : "1px solid var(--line-soft)",
            display: "flex", alignItems: "center", gap: 10,
            fontSize: 12.5,
          }}>
            <span className="mono" style={{ fontSize: 10.5, color: "var(--ink-4)", width: 70 }}>{e.id}</span>
            <span style={{ flex: 1, color: "var(--ink-2)" }}>{e.title}</span>
            <span className="tab-num" style={{ color: "var(--ink)", fontWeight: 500 }}>
              {fmtCNY(e.amount)}
            </span>
            <Pill tone={e.tone}>{e.status}</Pill>
          </li>
        ))}
      </ul>
    </Card>
  );
}

/* ─────────────────────────────────────────────────────────────
   Row 3 · CARD B: 工作记录流
   ───────────────────────────────────────────────────────────── */
function WorklogCard() {
  const [filter, setFilter] = useState("all");
  const filters = [
    { k: "all", label: "全部" },
    { k: "mine", label: "我的" },
    { k: "team", label: "团队" },
    { k: "mention", label: "@ 我的" },
  ];
  const filtered = DASH.worklog.filter(w => {
    if (filter === "mine") return w.who === "孙杰";
    if (filter === "mention") return w.mentioned;
    return true;
  });

  // Group by date
  const today = "2026-05-22";
  const yesterday = "2026-05-21";
  const grouped = filtered.reduce((acc, w) => {
    const key = w.date === today ? "今天" : w.date === yesterday ? "昨天" : w.date;
    (acc[key] = acc[key] || []).push(w);
    return acc;
  }, {});

  const unreadCount = DASH.worklog.filter(w => w.mentioned).length;

  return (
    <Card
      title="工作记录"
      subtitle={
        <span>
          团队最近动态
          {unreadCount > 0 && (
            <>
              <span style={{ color: "var(--ink-4)" }}> · </span>
              <span style={{ color: "var(--accent)" }}>@ 我的 {unreadCount} 条未读</span>
            </>
          )}
        </span>
      }
      action={
        <div style={{ display: "flex", gap: 4, padding: 3, background: "var(--bg-sunk)", borderRadius: 7 }}>
          {filters.map(f => (
            <button key={f.k} onClick={() => setFilter(f.k)}
              style={{
                padding: "4px 10px", fontSize: 11.5, fontWeight: 500,
                borderRadius: 5,
                color: filter === f.k ? "var(--ink)" : "var(--ink-3)",
                background: filter === f.k ? "var(--bg-elev)" : "transparent",
                boxShadow: filter === f.k ? "0 1px 2px rgba(31,30,27,0.06)" : "none",
              }}>{f.label}</button>
          ))}
        </div>
      }
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        {Object.entries(grouped).map(([date, list]) => (
          <div key={date}>
            <div style={{
              fontSize: 10.5, color: "var(--ink-3)",
              letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 500,
              padding: "0 0 8px",
              borderBottom: "1px solid var(--line-soft)",
              marginBottom: 4,
            }}>{date}</div>
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 2 }}>
              {list.map(w => (
                <li key={w.id} style={{
                  padding: "12px 4px", display: "flex", gap: 12,
                  position: "relative", borderRadius: 6,
                  background: w.mentioned ? "var(--accent-tint)" : "transparent",
                  borderLeft: w.mentioned ? "2px solid var(--accent)" : "2px solid transparent",
                  paddingLeft: w.mentioned ? 10 : 4,
                  marginLeft: w.mentioned ? -4 : 0,
                  cursor: "pointer",
                  transition: "background 100ms",
                }}
                  onMouseEnter={e => { if (!w.mentioned) e.currentTarget.style.background = "var(--bg-hover)"; }}
                  onMouseLeave={e => { if (!w.mentioned) e.currentTarget.style.background = "transparent"; }}
                >
                  <Avatar name={w.who} size={32} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
                      <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>{w.who}</span>
                      {w.customer !== "—" && (
                        <span style={{
                          fontSize: 11, padding: "1px 6px", borderRadius: 3,
                          background: "var(--bg-sunk)", color: "var(--ink-2)",
                        }}>{w.customer}</span>
                      )}
                      {w.project !== "—" && (
                        <span style={{
                          fontSize: 11, padding: "1px 6px", borderRadius: 3,
                          background: "var(--info-soft)", color: "var(--info)",
                        }}>{w.project}</span>
                      )}
                      <span style={{ flex: 1 }} />
                      <span style={{ fontSize: 11, color: "var(--ink-4)" }}>{w.time}</span>
                    </div>
                    <p style={{
                      margin: 0, fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.6,
                      display: "-webkit-box",
                      WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden",
                    }}>{w.text}</p>
                    {w.replies > 0 && (
                      <div style={{
                        marginTop: 6, fontSize: 11, color: "var(--ink-3)",
                        display: "inline-flex", alignItems: "center", gap: 5,
                      }}>
                        <DashIcon name="chat" size={11} />
                        <span>{w.replies} 条回复</span>
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <button style={{
        marginTop: 14, padding: "10px", width: "100%",
        fontSize: 12, color: "var(--ink-3)", fontWeight: 500,
        background: "var(--bg-sunk)", borderRadius: 6,
      }}>加载更早记录…</button>
    </Card>
  );
}

Object.assign(window, { FunnelCard, ProjectsCard, QuotesCard, ExpenseCard, WorklogCard });
