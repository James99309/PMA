/* PMA · 库存管理 屏幕 */

const _INV = window.PMA_INV;

/* ─── Inventory main screen ────────────────────────────────── */

function InventoryScreen({ onOpenGlobal, onOpenAdjust, onOpenImport }) {
  const [companyId, setCompanyId] = useState("heyuan");
  const [tab, setTab] = useState("stock"); // stock | tx
  const [query, setQuery] = useState("");
  const [pickerOpen, setPickerOpen] = useState(false);

  const company = _INV.COMPANIES.find(c => c.id === companyId);
  const stockRows = _INV.STOCK.filter(s => !query || s.name.includes(query) || s.model.toLowerCase().includes(query.toLowerCase()));
  const txRows = _INV.TX.filter(t => !query || t.product.includes(query) || t.model.toLowerCase().includes(query.toLowerCase()));

  const stats = useMemo(() => {
    const totalQty = _INV.STOCK.reduce((s, x) => s + x.qty, 0);
    return [
      { k: "在册产品", v: _INV.STOCK.length, icon: "cube"  },
      { k: "总数量",   v: totalQty,         icon: "box"   },
      { k: "本月流水", v: _INV.TX.length,   icon: "chart" },
    ];
  }, []);

  return (
    <div style={{ padding: "32px 40px 80px", maxWidth: 1480, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <div className="mono dim" style={{ fontSize: 11, letterSpacing: "0.15em", marginBottom: 8 }}>
            INVENTORY · 库存管理
          </div>
          <h1 className="serif" style={{
            margin: 0, fontSize: 40, fontWeight: 500,
            letterSpacing: "-0.01em", lineHeight: 1.1,
          }}>库存</h1>
          <p style={{ margin: "10px 0 0", color: "var(--ink-3)", fontSize: 14, maxWidth: 560 }}>
            实时查看各公司库存数量与变动记录,支持手动调整、Excel 批量导入。
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Btn variant="ghost" iconL="history" onClick={onOpenGlobal}>全局流水</Btn>
          <Btn variant="ghost" iconL="upload" onClick={onOpenImport}>Excel 导入</Btn>
        </div>
      </div>

      {/* Company picker bar */}
      <div style={{
        position: "relative",
        background: "var(--bg-elev)", border: "1px solid var(--line)",
        borderRadius: 12, padding: "16px 20px",
        display: "flex", alignItems: "center", gap: 14,
        marginBottom: 24, cursor: "pointer",
      }}
      onClick={() => setPickerOpen(o => !o)}
      onMouseEnter={e => e.currentTarget.style.borderColor = "var(--line-2)"}
      onMouseLeave={e => e.currentTarget.style.borderColor = "var(--line)"}
      >
        <span style={{
          width: 44, height: 44, borderRadius: 10,
          background: "var(--accent-tint)", color: "var(--accent)",
          display: "inline-flex", alignItems: "center", justifyContent: "center",
        }}><Icon name={company?.kindIcon || "factory"} size={20} /></span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="mono dim" style={{ fontSize: 10.5, letterSpacing: "0.12em", marginBottom: 3 }}>当前查看库存</div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 17, fontWeight: 600, color: "var(--ink)" }}>{company?.name}</span>
            <Pill tone="mute">{company?.kind}</Pill>
          </div>
        </div>
        <span style={{ color: "var(--ink-3)", display: "inline-flex", transform: pickerOpen ? "rotate(180deg)" : "none", transition: "transform 200ms" }}>
          <Icon name="chevd" size={16} />
        </span>

        {pickerOpen && (
          <CompanyPicker
            companies={_INV.COMPANIES} currentId={companyId}
            onPick={(id) => { setCompanyId(id); setPickerOpen(false); }}
            onClose={() => setPickerOpen(false)}
          />
        )}
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 24 }}>
        {stats.map(s => (
          <div key={s.k} style={{
            background: "var(--bg-elev)", border: "1px solid var(--line)",
            borderRadius: 12, padding: "20px 22px",
            display: "flex", alignItems: "center", gap: 16,
          }}>
            <span style={{
              width: 36, height: 36, borderRadius: 8,
              background: "var(--bg-sunk)", color: "var(--ink-3)",
              display: "inline-flex", alignItems: "center", justifyContent: "center",
            }}><Icon name={s.icon} size={18} /></span>
            <div>
              <div className="serif" style={{ fontSize: 32, fontWeight: 500, lineHeight: 1, letterSpacing: "-0.01em", fontVariantNumeric: "tabular-nums" }}>{s.v}</div>
              <div className="dim" style={{ fontSize: 12, marginTop: 6 }}>{s.k}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs + search */}
      <div style={{
        borderTop: "1px solid var(--line)", borderBottom: "1px solid var(--line)",
        display: "flex", alignItems: "center", marginBottom: 14,
      }}>
        {[
          { k: "stock", l: "库存", c: stockRows.length, icon: "box"   },
          { k: "tx",    l: "流水", c: txRows.length,    icon: "history" },
        ].map(t => {
          const active = tab === t.k;
          return (
            <button key={t.k} onClick={() => setTab(t.k)} style={{
              padding: "14px 18px", display: "flex", alignItems: "baseline", gap: 8,
              color: active ? "var(--ink)" : "var(--ink-3)",
              borderBottom: active ? "1.5px solid var(--ink)" : "1.5px solid transparent",
              marginBottom: -1, fontSize: 13, fontWeight: active ? 500 : 400,
            }}>
              <Icon name={t.icon} size={13} />
              <span>{t.l}</span>
              <span className="mono tab-num" style={{ fontSize: 11, color: active ? "var(--ink-2)" : "var(--ink-4)" }}>{t.c}</span>
            </button>
          );
        })}
        <div style={{ flex: 1 }} />
        <Input iconL="search" placeholder="搜产品/MN号…" value={query} onChange={e => setQuery(e.target.value)} style={{ width: 240 }} />
      </div>

      {tab === "stock"
        ? <StockTable rows={stockRows} onAdjust={onOpenAdjust} />
        : <TxTable rows={txRows} mode="company" />}
    </div>
  );
}

function CompanyPicker({ companies, currentId, onPick, onClose }) {
  const [q, setQ] = useState("");
  const filtered = companies.filter(c => !q || c.name.includes(q));
  useEffect(() => {
    const h = e => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div
      onClick={e => e.stopPropagation()}
      style={{
        position: "absolute", top: "100%", left: 12, marginTop: 6,
        width: 380, background: "var(--bg-elev)",
        border: "1px solid var(--line)", borderRadius: 10,
        boxShadow: "0 20px 40px rgba(31,30,27,0.12)",
        zIndex: 30, overflow: "hidden",
        animation: "scale-in 180ms cubic-bezier(.2,.7,.2,1)",
      }}>
      <div style={{ padding: 10, borderBottom: "1px solid var(--line)" }}>
        <Input autoFocus iconL="search" placeholder="搜索公司…"
          value={q} onChange={e => setQ(e.target.value)} style={{ width: "100%" }}/>
      </div>
      <div style={{ maxHeight: 340, overflowY: "auto", padding: 6 }}>
        {filtered.map(c => {
          const active = c.id === currentId;
          return (
            <button key={c.id} onClick={() => onPick(c.id)}
              style={{
                width: "100%", padding: "8px 10px", borderRadius: 6,
                display: "flex", alignItems: "center", gap: 10,
                background: active ? "var(--accent-tint)" : "transparent",
                textAlign: "left", marginBottom: 1,
              }}
              onMouseEnter={e => { if (!active) e.currentTarget.style.background = "var(--bg-hover)"; }}
              onMouseLeave={e => { if (!active) e.currentTarget.style.background = "transparent"; }}
            >
              <span style={{ color: active ? "var(--accent)" : "var(--ink-3)" }}>
                <Icon name={c.kindIcon} size={14} />
              </span>
              <span style={{ flex: 1, fontSize: 13, color: active ? "var(--accent-ink)" : "var(--ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.name}</span>
              <span className="mono tab-num dim" style={{ fontSize: 11 }}>{c.total} 件</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function StockTable({ rows, onAdjust }) {
  return (
    <div style={{ background: "var(--bg-elev)", border: "1px solid var(--line)", borderRadius: 10, overflow: "hidden" }}>
      <table style={{ width: "100%", fontSize: 13, borderCollapse: "separate", borderSpacing: 0 }}>
        <thead>
          <tr>
            {[
              { l: "产品",     a: "left" },
              { l: "数量",     a: "right" },
              { l: "最后变动", a: "left" },
              { l: "",         a: "right", w: 90 },
            ].map((h, i) => (
              <th key={i} style={{
                textAlign: h.a, padding: "12px 18px",
                fontSize: 10.5, fontWeight: 500, color: "var(--ink-4)",
                letterSpacing: "0.08em", textTransform: "uppercase", width: h.w,
                borderBottom: "1px solid var(--line)",
              }}>{h.l}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id} style={{ borderTop: i === 0 ? "0" : "1px solid var(--line-soft)" }}>
              <td style={{ padding: "14px 18px" }}>
                <div style={{ fontSize: 13.5, color: "var(--ink)", fontWeight: 500 }}>{r.name}</div>
                <div className="mono dim" style={{ fontSize: 11.5, marginTop: 2 }}>{r.model}</div>
              </td>
              <td style={{ padding: "14px 18px", textAlign: "right" }}>
                <span className="mono tab-num" style={{ fontSize: 15, fontWeight: 600, color: "var(--ink)" }}>{r.qty}</span>
                <span className="dim" style={{ fontSize: 11, marginLeft: 4 }}>{r.unit}</span>
              </td>
              <td style={{ padding: "14px 18px" }}>
                {r.last ? (
                  <>
                    <div style={{ fontSize: 12.5, color: "var(--ink-2)" }}>
                      <span className="mono tab-num">{r.last.date.slice(5)}</span>
                      <span style={{ margin: "0 6px", color: "var(--ink-4)" }}>·</span>
                      <span style={{ color: r.last.delta > 0 ? "var(--success)" : "var(--danger)" }}>
                        {r.last.type} {r.last.delta > 0 ? "+" : ""}{r.last.delta}
                      </span>
                    </div>
                    <div className="dim" style={{ fontSize: 11.5, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 560 }}>{r.last.note}</div>
                  </>
                ) : <span className="dim" style={{ fontSize: 12 }}>—</span>}
              </td>
              <td style={{ padding: "14px 18px", textAlign: "right" }}>
                <Btn variant="ghost" size="sm" iconL="settings" onClick={() => onAdjust(r)}>调整</Btn>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TxTable({ rows, mode }) {
  // mode: "company" (no company col) | "global" (with company col)
  const cols = mode === "global"
    ? ["时间", "公司", "产品", "类型", "变动", "变化", "关联 / 备注", "操作人"]
    : ["时间", "产品", "类型", "变动", "变化", "关联 / 备注", "操作人"];
  return (
    <div style={{ background: "var(--bg-elev)", border: "1px solid var(--line)", borderRadius: 10, overflow: "auto" }}>
      <table style={{ width: "100%", minWidth: 920, fontSize: 13, borderCollapse: "separate", borderSpacing: 0 }}>
        <thead>
          <tr>
            {cols.map((h, i) => {
              const isNum = h === "变动" || h === "变化";
              return (
                <th key={i} style={{
                  textAlign: isNum ? "right" : "left", padding: "12px 16px",
                  fontSize: 10.5, fontWeight: 500, color: "var(--ink-4)",
                  letterSpacing: "0.08em", textTransform: "uppercase",
                  whiteSpace: "nowrap", borderBottom: "1px solid var(--line)",
                }}>{h}</th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const isIn = r.delta > 0;
            return (
              <tr key={i} style={{ borderTop: i === 0 ? "0" : "1px solid var(--line-soft)" }}>
                <td style={{ padding: "13px 16px", whiteSpace: "nowrap" }} className="mono tab-num dim">{r.time}</td>
                {mode === "global" && (
                  <td style={{ padding: "13px 16px", whiteSpace: "nowrap" }}>
                    <div style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                      <span style={{ color: "var(--ink-3)" }}><Icon name={r.companyIcon} size={12} /></span>
                      <span style={{ color: "var(--ink-2)", fontSize: 12.5 }}>{r.company}</span>
                    </div>
                  </td>
                )}
                <td style={{ padding: "13px 16px" }}>
                  <div style={{ color: "var(--ink)", fontSize: 13 }}>{r.product}</div>
                  <div className="mono dim" style={{ fontSize: 11, marginTop: 1 }}>{r.model}</div>
                </td>
                <td style={{ padding: "13px 16px" }}>
                  <Pill tone={isIn ? "success" : "danger"}>{r.type}</Pill>
                </td>
                <td style={{ padding: "13px 16px", textAlign: "right", whiteSpace: "nowrap" }}>
                  <span className="mono tab-num" style={{ fontSize: 13.5, fontWeight: 600, color: isIn ? "var(--success)" : "var(--danger)" }}>
                    {isIn ? "+" : ""}{r.delta}
                  </span>
                </td>
                <td style={{ padding: "13px 16px", textAlign: "right", whiteSpace: "nowrap" }} className="mono tab-num dim">
                  {r.from} <span style={{ margin: "0 4px" }}>→</span> <span style={{ color: "var(--ink-2)" }}>{r.to}</span>
                </td>
                <td style={{ padding: "13px 16px" }}>
                  {r.ref && <div style={{ color: "var(--accent)", fontSize: 12.5, fontWeight: 500 }}>{r.ref}</div>}
                  <div className="dim" style={{ fontSize: 11.5, marginTop: r.ref ? 2 : 0, lineHeight: 1.45, maxWidth: 460 }}>{r.note}</div>
                </td>
                <td style={{ padding: "13px 16px" }} className="dim">{r.op}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Global flow screen ───────────────────────────────────── */

function GlobalFlowScreen({ onBack }) {
  const [start, setStart] = useState("2026-05-01");
  const [end, setEnd] = useState("2026-05-23");
  const [company, setCompany] = useState("");
  const [type, setType]       = useState("");
  const [src, setSrc]         = useState("");
  const [q, setQ]             = useState("");

  const rows = _INV.TX_GLOBAL;
  const txnCount = rows.length;
  const inCount  = rows.filter(r => r.delta > 0).reduce((s, r) => s + r.delta, 0);
  const outCount = rows.filter(r => r.delta < 0).reduce((s, r) => s + Math.abs(r.delta), 0);
  const activeCo = new Set(rows.map(r => r.company)).size;

  return (
    <div style={{ padding: "32px 40px 80px", maxWidth: 1480, margin: "0 auto" }}>
      <div style={{ marginBottom: 16, display: "flex", alignItems: "center", gap: 14 }}>
        <button onClick={onBack} style={{
          color: "var(--ink-3)", display: "inline-flex", alignItems: "center", gap: 4, fontSize: 13,
          padding: "4px 8px", borderRadius: 6, marginLeft: -8,
        }}
          onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
        >
          <Icon name="back" size={13} /> 库存管理
        </button>
        <span style={{ color: "var(--ink-4)" }}>/</span>
        <h1 className="serif" style={{ margin: 0, fontSize: 26, fontWeight: 500, letterSpacing: "-0.005em" }}>全局流水</h1>
        <Pill tone="accent" dot size="lg">厂商管理员</Pill>
      </div>
      <p style={{ margin: "0 0 22px", color: "var(--ink-3)", fontSize: 13.5, maxWidth: 760 }}>
        跨公司库存变动审计视图,经销商 / 客户用户不可见。用于异常监测、月度统计。
      </p>

      {/* KPIs */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 18 }}>
        {[
          { k: "本月流水笔数", v: txnCount,            tone: "ink"     },
          { k: "本月入库",     v: "+ " + inCount,      tone: "success" },
          { k: "本月出库",     v: "- " + outCount,     tone: "danger"  },
          { k: "活跃公司",     v: activeCo + " / " + _INV.COMPANIES.length, tone: "ink" },
        ].map((s, i) => (
          <div key={i} style={{
            background: "var(--bg-elev)", border: "1px solid var(--line)",
            borderRadius: 10, padding: "16px 18px",
          }}>
            <div className="dim" style={{ fontSize: 11.5, marginBottom: 6 }}>{s.k}</div>
            <div className="serif tab-num" style={{
              fontSize: 26, fontWeight: 500, lineHeight: 1.05, letterSpacing: "-0.01em",
              color: s.tone === "success" ? "var(--success)" : s.tone === "danger" ? "var(--danger)" : "var(--ink)",
              fontVariantNumeric: "tabular-nums",
            }}>{s.v}</div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div style={{
        background: "var(--bg-elev)", border: "1px solid var(--line)",
        borderRadius: 10, padding: "12px 14px",
        display: "flex", alignItems: "center", gap: 10, marginBottom: 16, flexWrap: "wrap",
      }}>
        <input type="date" value={start} onChange={e => setStart(e.target.value)}
          style={{ height: 32, padding: "0 10px", border: "1px solid var(--line-2)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 12.5, background: "var(--bg-elev)", outline: "none" }}/>
        <span className="dim" style={{ fontSize: 12 }}>至</span>
        <input type="date" value={end} onChange={e => setEnd(e.target.value)}
          style={{ height: 32, padding: "0 10px", border: "1px solid var(--line-2)", borderRadius: 6, fontFamily: "var(--font-mono)", fontSize: 12.5, background: "var(--bg-elev)", outline: "none" }}/>
        <Select value={company} onChange={setCompany}
          options={[{ value: "", label: "全部公司" }, ..._INV.COMPANIES.map(c => ({ value: c.id, label: c.name }))]}
          style={{ minWidth: 180 }}/>
        <Select value={type} onChange={setType}
          options={[{ value: "", label: "全部类型" }, "入库", "出库", "调整"]}
          style={{ minWidth: 110 }}/>
        <Select value={src} onChange={setSrc}
          options={[{ value: "", label: "全部来源" }, "采购订单", "发货单", "手动调整", "Excel 导入"]}
          style={{ minWidth: 120 }}/>
        <Input placeholder="搜产品 / 单据 / 备注…" value={q} onChange={e => setQ(e.target.value)} style={{ flex: 1, minWidth: 200 }}/>
        <Btn variant="accent">应用</Btn>
      </div>

      <TxTable rows={rows} mode="global" />
    </div>
  );
}

Object.assign(window, { InventoryScreen, GlobalFlowScreen });
