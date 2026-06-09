/* ─────────────────────────────────────────────────────────────
   PMA · 采购订单 · 列表页 + 详情页 + 弹窗
   ───────────────────────────────────────────────────────────── */

const { ORDERS, STAGES, STATUS_META, SUPPLIERS, STATUS_COUNTS } = window.PMA_DATA;

/* ╔═══════════════════════════════════════════════════════════╗
   ║  LIST SCREEN                                              ║
   ╚═══════════════════════════════════════════════════════════╝ */

const FILTERS = [
  { key: "all",     label: "全部",   count: STATUS_COUNTS.all },
  { key: "pending", label: "待确认", count: STATUS_COUNTS.pending },
  { key: "produce", label: "生产中", count: STATUS_COUNTS.produce },
  { key: "shipped", label: "已发货", count: STATUS_COUNTS.shipped },
  { key: "stored",  label: "已入库", count: STATUS_COUNTS.stored },
  { key: "overdue", label: "超期",   count: STATUS_COUNTS.overdue },
];

function ListScreen({ onOpenOrder, headlineFont, onNewOrder }) {
  const [filter, setFilter]   = useState("all");
  const [query, setQuery]     = useState("");
  const [supplier, setSupplier] = useState("");

  const rows = useMemo(() => {
    return ORDERS.filter(o => {
      if (filter === "pending" && !["待审批", "待确认"].includes(o.status)) return false;
      if (filter === "produce" && o.status !== "生产中") return false;
      if (filter === "shipped" && o.status !== "已发货") return false;
      if (filter === "stored"  && o.status !== "已入库") return false;
      if (filter === "overdue" && !o.overdue) return false;
      if (supplier && o.supplier !== supplier) return false;
      if (query && !o.id.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });
  }, [filter, query, supplier]);

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: "calc(100vh - 56px)",
      padding: "32px 40px 24px", maxWidth: 1480, margin: "0 auto",
      width: "100%",
    }}>
      {/* Page header */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 24, flexShrink: 0 }}>
        <div>
          <div className="mono dim" style={{ fontSize: 11, letterSpacing: "0.15em", marginBottom: 8 }}>
            PURCHASE · 采购管理
          </div>
          <h1 className="serif" style={{
            margin: 0, fontSize: 40, fontWeight: 500,
            letterSpacing: "-0.01em", lineHeight: 1.1,
          }}>采购订单</h1>
          <p style={{ margin: "10px 0 0", color: "var(--ink-3)", fontSize: 14, maxWidth: 560 }}>
            管理从供应商下单、生产到验收入库的完整生命周期。
          </p>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <Btn variant="ghost" iconL="download">导出</Btn>
          <Btn variant="primary" iconL="plus" onClick={onNewOrder}>新建采购订单</Btn>
        </div>
      </div>

      {/* Filter tabs (replaces big stat cards) */}
      <div style={{
        borderTop: "1px solid var(--line)",
        borderBottom: "1px solid var(--line)",
        display: "flex", alignItems: "center", gap: 0,
        marginBottom: 16, flexShrink: 0,
        overflowX: "auto",
      }}>
        {FILTERS.map(f => {
          const active = filter === f.key;
          return (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              style={{
                padding: "16px 18px",
                display: "flex", alignItems: "baseline", gap: 10,
                position: "relative",
                color: active ? "var(--ink)" : "var(--ink-3)",
                borderBottom: active ? "1.5px solid var(--ink)" : "1.5px solid transparent",
                marginBottom: -1,
                transition: "color 120ms",
                whiteSpace: "nowrap",
              }}
              onMouseEnter={e => { if (!active) e.currentTarget.style.color = "var(--ink-2)"; }}
              onMouseLeave={e => { if (!active) e.currentTarget.style.color = "var(--ink-3)"; }}
            >
              <span style={{ fontSize: 13, fontWeight: active ? 500 : 400 }}>{f.label}</span>
              <span className="tab-num mono" style={{
                fontSize: 11,
                color: active ? "var(--ink-2)" : "var(--ink-4)",
              }}>{f.count}</span>
            </button>
          );
        })}
        <div style={{ flex: 1 }} />
        <div className="dim" style={{ fontSize: 12, paddingRight: 4 }}>
          共 <span className="mono tab-num" style={{ color: "var(--ink-2)" }}>{rows.length}</span> 条
        </div>
      </div>

      {/* Filter row */}
      <div style={{ display: "flex", gap: 10, marginBottom: 18, alignItems: "center", flexShrink: 0 }}>
        <Input
          iconL="search" placeholder="搜索订单号…"
          value={query} onChange={e => setQuery(e.target.value)}
          style={{ width: 280 }}
        />
        <Select
          value={supplier} onChange={setSupplier}
          options={SUPPLIERS}
          placeholder="全部供应商"
          style={{ minWidth: 160 }}
        />
        <Select
          value="" onChange={() => {}}
          options={["全部测试状态", "已上传测试报告", "未上传"]}
          style={{ minWidth: 140 }}
        />
        <Select
          value="" onChange={() => {}}
          options={["所有订单类型", "渠道订单", "备货订单"]}
          style={{ minWidth: 140 }}
        />
        <div style={{ flex: 1 }} />
        <button style={{
          height: 34, padding: "0 10px", color: "var(--ink-3)",
          fontSize: 12.5, display: "inline-flex", alignItems: "center", gap: 4,
        }}>
          <Icon name="filter" size={13} /> 更多筛选
        </button>
      </div>

      {/* Table */}
      <OrderTable rows={rows} onOpenOrder={onOpenOrder} />
    </div>
  );
}

function OrderTable({ rows, onOpenOrder }) {
  return (
    <div style={{
      background: "var(--bg-elev)",
      border: "1px solid var(--line)",
      borderRadius: 10, overflow: "auto",
      flex: 1, minHeight: 0,
    }}>
      <table style={{ width: "100%", minWidth: 920, fontSize: 13, borderCollapse: "separate", borderSpacing: 0 }}>
        <thead>
          <tr style={{ background: "var(--bg-elev)" }}>
            {["PO 单号", "供应商", "类型", "金额", "进度", "状态", "测试", "交期"].map((h, i) => (
              <th key={h} style={{
                textAlign: i === 3 ? "right" : "left",
                padding: "14px 16px",
                fontSize: 11, fontWeight: 500,
                color: "var(--ink-3)",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                whiteSpace: "nowrap",
                position: "sticky", top: 0, zIndex: 2,
                background: "var(--bg-elev)",
                borderBottom: "1px solid var(--line)",
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((o, idx) => (
            <OrderRow key={o.id} order={o} isLast={idx === rows.length - 1} onOpen={() => onOpenOrder(o.id)} />
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={8} style={{ padding: "60px 16px", textAlign: "center", color: "var(--ink-3)" }}>
                没有符合筛选条件的订单
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function OrderRow({ order, isLast, onOpen }) {
  const meta = STATUS_META[order.status] || { tone: "neutral", label: order.status };
  const cellBorder = isLast ? "0" : "1px solid var(--line-soft)";
  const cellStyle = {
    padding: "0 16px",
    borderBottom: cellBorder,
  };
  return (
    <tr
      onClick={onOpen}
      style={{
        height: "var(--row-h, 52px)",
        cursor: "pointer", transition: "background 100ms",
      }}
      onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
      onMouseLeave={e => e.currentTarget.style.background = "transparent"}
    >
      <td style={{ ...cellStyle, whiteSpace: "nowrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="mono" style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)", letterSpacing: "0.01em" }}>
            {order.id}
          </span>
          {order.overdue && <Pill tone="danger" size="md">超期</Pill>}
        </div>
      </td>
      <td style={{ ...cellStyle, whiteSpace: "nowrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "var(--ink-2)" }}>{order.supplier}</span>
        </div>
      </td>
      <td style={{ ...cellStyle, color: "var(--ink-3)", fontSize: 12.5, whiteSpace: "nowrap" }}>
        {order.type}
      </td>
      <td style={{ ...cellStyle, textAlign: "right", whiteSpace: "nowrap" }}>
        <span className="mono tab-num" style={{ color: order.amount ? "var(--ink)" : "var(--ink-4)", fontSize: 13 }}>
          {fmtCNY(order.amount)}
        </span>
      </td>
      <td style={cellStyle}>
        <Progress value={order.progress} width={90} />
      </td>
      <td style={cellStyle}>
        <Pill tone={meta.tone} dot>{meta.label}</Pill>
      </td>
      <td style={cellStyle}>
        <span title={order.test ? "已上传测试报告" : "未上传"} style={{
          color: order.test ? "var(--success)" : "var(--ink-4)",
          display: "inline-flex",
        }}>
          <Icon name={order.test ? "check" : "clock"} size={14} />
        </span>
      </td>
      <td style={{ ...cellStyle, whiteSpace: "nowrap" }}>
        <span className="mono tab-num" style={{
          color: order.due ? (order.overdue ? "var(--danger)" : "var(--ink-2)") : "var(--ink-4)",
          fontSize: 12.5,
        }}>
          {order.due ? order.due.slice(5) : "—"}
        </span>
      </td>
    </tr>
  );
}

/* ╔═══════════════════════════════════════════════════════════╗
   ║  DETAIL SCREEN                                            ║
   ╚═══════════════════════════════════════════════════════════╝ */

function DetailScreen({ orderId, onBack, onOpenModal, timelinePos }) {
  const order = ORDERS.find(o => o.id === orderId) || ORDERS.find(o => o.id === "CG-2601-001");
  const meta = STATUS_META[order.status] || { tone: "neutral", label: order.status };
  const approvalStatus = order.approval?.status || "approved";
  const isApprovalPending = approvalStatus === "pending";
  const items = order.items || [];

  const [preview, setPreview] = useState(null); // { stageKey, stageLabel, files }
  const openPreview = (stageKey, stageLabel, files) => setPreview({ stageKey, stageLabel, files });
  const closePreview = () => setPreview(null);

  return (
    <div style={{ padding: "32px 40px 80px", maxWidth: 1400, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 28 }}>
        <div>
          <div className="mono dim" style={{ fontSize: 11, letterSpacing: "0.15em", marginBottom: 8 }}>
            PURCHASE ORDER · {order.type}
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
            <h1 className="serif mono" style={{
              margin: 0, fontSize: 40, fontWeight: 500,
              letterSpacing: "-0.005em", lineHeight: 1.1,
              fontFamily: "var(--font-mono)", fontVariantNumeric: "tabular-nums",
            }}>{order.id}</h1>
            <Pill tone={meta.tone} dot size="lg">{meta.label}</Pill>
          </div>
          <div style={{ marginTop: 10, color: "var(--ink-3)", fontSize: 13, display: "flex", gap: 18 }}>
            <span>供应商 · <span style={{ color: "var(--ink-2)" }}>{order.supplier}</span></span>
            <span style={{ color: "var(--line-2)" }}>|</span>
            <span>创建于 <span className="mono tab-num" style={{ color: "var(--ink-2)" }}>{order.created}</span></span>
            {order.due && <>
              <span style={{ color: "var(--line-2)" }}>|</span>
              <span>交期 <span className="mono tab-num" style={{ color: "var(--ink-2)" }}>{order.due}</span></span>
            </>}
          </div>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <Btn variant="ghost" iconL="back" onClick={onBack}>返回</Btn>
          <Btn variant="ghost" iconL="download">导出 PO</Btn>
          <Btn variant="ghost" iconL="edit">编辑</Btn>
        </div>
      </div>

      {/* Approval flow (always shown above execution) */}
      <ApprovalFlow approval={order.approval} defaultOpen={isApprovalPending} />

      {/* Execution stage strip */}
      {timelinePos === "top" && (
        <div style={{ marginTop: 14 }}>
          <StageStrip order={order} sticky onAction={onOpenModal} dimmed={isApprovalPending} onPreview={openPreview} />
        </div>
      )}

      {/* Two-column body */}
      <div style={{
        marginTop: 24,
        display: timelinePos === "side" ? "grid" : "block",
        gridTemplateColumns: timelinePos === "side" ? "1fr 320px" : "1fr",
        gap: 24,
        alignItems: "start",
      }}>
        {/* MAIN */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Current action card */}
          <CurrentActionCard order={order} onAction={onOpenModal} />

          {/* Basic info */}
          <Section title="基本信息" action={<Btn variant="bare" size="sm" iconL="edit">编辑</Btn>}>
            <InfoGrid cols={4} items={[
              { k: "供应商",     v: order.supplier },
              { k: "订单日期",   v: order.created, mono: true },
              { k: "需求日期",   v: order.needBy || order.due || "—", mono: true },
              { k: "订单类别",   v: order.type },
              { k: "贸易术语",   v: order.incoterm || "EXW" },
              { k: "运输方式",   v: order.transport || "汽运" },
              { k: "付款条件",   v: order.payment || "T/T 30%" },
              { k: "交货地点",   v: order.location || "上海市浦东新区" },
              { k: "创建者",     v: order.creator },
              { k: "创建时间",   v: order.created, mono: true },
              { k: "更新时间",   v: order.due || order.created, mono: true },
              { k: "订单金额",   v: fmtCNY(order.amount), mono: true, strong: true },
            ]} />
          </Section>

          {/* Order items */}
          <Section
            title={`订单明细`}
            subtitle={<span className="mono tab-num">{items.length} 项 · 共 {items.reduce((s,i)=>s+i.qty,0)} 套</span>}
          >
            <ItemTable items={items} />
          </Section>

          {/* Shipments */}
          <Section title="发货记录" subtitle={
            order.shipments?.length > 0
              ? <span className="mono tab-num">{order.shipments.length} 次发货</span>
              : null
          } action={
            order.stage >= 4 && order.shipments?.length > 0
              ? <Btn variant="bare" size="sm" iconL="plus">新增发货单</Btn>
              : null
          }>
            <ShipmentList shipments={order.shipments || []} canCreate={order.stage >= 4} onCreate={() => onOpenModal("ship")} />
          </Section>
        </div>

        {/* SIDE — only shown when timeline is on the right rail */}
        {timelinePos === "side" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16, position: "sticky", top: 80 }}>
            <StageStripVertical order={order} onAction={onOpenModal} dimmed={isApprovalPending} onPreview={openPreview} />
            {isApprovalPending && <ApprovalCard order={order} />}
          </div>
        )}

        {/* Inline approval card when timeline is on top (since no side rail) */}
        {timelinePos === "top" && isApprovalPending && (
          <div style={{ marginTop: 20 }}>
            <ApprovalCard order={order} />
          </div>
        )}
      </div>

      {/* File preview modal */}
      <FilePreviewModal
        open={!!preview}
        title={preview ? `${preview.stageLabel} · 附件` : ""}
        stageLabel={preview?.stageLabel}
        files={preview?.files}
        onClose={closePreview}
      />
    </div>
  );
}

/* ─── Section wrapper ──────────────────────────────────────── */

function Section({ title, subtitle, action, children, compact }) {
  return (
    <section style={{
      background: "var(--bg-elev)",
      border: "1px solid var(--line)",
      borderRadius: 10,
      overflow: "hidden",
    }}>
      <header style={{
        padding: compact ? "12px 16px" : "18px 22px 14px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <h3 className="serif" style={{
            margin: 0,
            fontSize: compact ? 14 : 16,
            fontWeight: 500, letterSpacing: "0.01em",
          }}>{title}</h3>
          {subtitle && <span className="dim" style={{ fontSize: 12 }}>{subtitle}</span>}
        </div>
        {action}
      </header>
      <div>{children}</div>
    </section>
  );
}

/* ─── Approval flow ─────────────────────────────────────────
   Separate from execution. Collapsed when approved, expanded
   when pending or rejected.
   ───────────────────────────────────────────────────────── */

function ApprovalFlow({ approval, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen !== false);
  if (!approval) return null;

  const status = approval.status; // pending | approved | rejected
  const nodes  = approval.nodes || [];
  const currentIdx = nodes.findIndex(n => n.status === "current");

  const statusMeta = {
    approved: { tone: "success", label: "已通过", icon: "check" },
    pending:  { tone: "warn",    label: "审批中", icon: "clock" },
    rejected: { tone: "danger",  label: "已驳回", icon: "cancel" },
  }[status] || { tone: "neutral", label: status };

  return (
    <section style={{
      background: "var(--bg-elev)",
      border: "1px solid var(--line)",
      borderRadius: 10, overflow: "hidden",
    }}>
      {/* Header bar */}
      <header style={{
        padding: "12px 18px",
        display: "flex", alignItems: "center", gap: 12,
        borderBottom: open ? "1px solid var(--line)" : "0",
        background: status === "pending" ? "var(--warn-soft)" : "transparent",
        transition: "background 200ms",
      }}>
        <span className="mono" style={{
          fontSize: 10.5, letterSpacing: "0.14em",
          color: "var(--ink-3)", textTransform: "uppercase",
        }}>APPROVAL · 审批流</span>
        <Pill tone={statusMeta.tone} dot>{statusMeta.label}</Pill>

        {status === "approved" && (
          <>
            <span className="dim" style={{ fontSize: 12 }}>·</span>
            <span style={{ fontSize: 12, color: "var(--ink-3)" }}>
              历时 <span className="mono tab-num">{approval.duration ?? 0}</span> 天 · 经
              <span style={{ color: "var(--ink-2)", margin: "0 4px" }}>{nodes.length}</span>
              个节点
            </span>
            <div style={{ display: "flex", marginLeft: 4, gap: -6 }}>
              {nodes.map((n, i) => (
                <span key={i} style={{ marginLeft: i === 0 ? 0 : -6, border: "1.5px solid var(--bg-elev)", borderRadius: "50%" }}>
                  <Avatar name={n.name} size={20} />
                </span>
              ))}
            </div>
          </>
        )}
        {status === "pending" && (
          <>
            <span className="dim" style={{ fontSize: 12 }}>·</span>
            <span style={{ fontSize: 12, color: "var(--warn)" }}>
              当前节点
              <span style={{ color: "var(--ink-2)", margin: "0 4px", fontWeight: 500 }}>
                {nodes[currentIdx]?.role}
              </span>
              ({nodes[currentIdx]?.name})
            </span>
          </>
        )}

        <div style={{ flex: 1 }} />
        <button onClick={() => setOpen(!open)}
          style={{
            color: "var(--ink-3)", fontSize: 12,
            display: "inline-flex", alignItems: "center", gap: 4,
            padding: "4px 8px", borderRadius: 4,
          }}
        >
          {open ? "收起" : "展开"}
          <span style={{ display: "inline-flex", transition: "transform 180ms", transform: open ? "rotate(180deg)" : "rotate(0)" }}>
            <Icon name="chevd" size={12} />
          </span>
        </button>
      </header>

      {/* Body */}
      {open && (
        <div style={{ padding: "20px 22px" }}>
          <div style={{ display: "flex", alignItems: "stretch", justifyContent: "space-between" }}>
            {nodes.flatMap((n, i) => {
              const isDone    = n.status === "done";
              const isCurrent = n.status === "current";
              const els = [];
              if (i > 0) {
                const prevDone = nodes[i - 1].status === "done";
                els.push(
                  <div key={`l-${i}`} style={{
                    flex: 1, alignSelf: "flex-start", height: 1, marginTop: 15,
                    background: prevDone && (isDone || isCurrent) ? "var(--ink-2)" : "var(--line-2)",
                    margin: "15px 4px 0",
                  }} />
                );
              }
              els.push(
                <div key={`n-${i}`} style={{
                  display: "flex", flexDirection: "column", alignItems: "center",
                  gap: 6, minWidth: 110, position: "relative", textAlign: "center",
                }}>
                  <div style={{
                    width: 30, height: 30, borderRadius: "50%",
                    background: isDone ? "var(--ink)"
                              : isCurrent ? "var(--warn)"
                              : "var(--bg-page)",
                    color: isDone || isCurrent ? "#fff" : "var(--ink-4)",
                    border: !isDone && !isCurrent ? "1px solid var(--line-2)" : "0",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    boxShadow: isCurrent ? "0 0 0 4px var(--warn-soft)" : "none",
                  }}>
                    {isDone ? <Icon name="check" size={13} /> : isCurrent ? <Icon name="clock" size={12} /> : <Icon name="user" size={12} />}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--ink-3)" }}>{n.role}</div>
                  <div style={{ fontSize: 12.5, fontWeight: 500, color: isCurrent ? "var(--warn)" : isDone ? "var(--ink)" : "var(--ink-3)" }}>
                    {n.name}
                  </div>
                  {n.date && (
                    <div className="mono tab-num dim" style={{ fontSize: 10.5 }}>{n.date.slice(5)}</div>
                  )}
                  {isCurrent && !n.date && (
                    <div className="mono dim" style={{ fontSize: 10.5 }}>等待审批</div>
                  )}
                  {!isDone && !isCurrent && (
                    <div className="mono dim" style={{ fontSize: 10.5 }}>—</div>
                  )}
                  {n.action && isDone && (
                    <div className="dim" style={{ fontSize: 10.5, marginTop: -2 }}>{n.action}</div>
                  )}
                </div>
              );
              return els;
            })}
          </div>
        </div>
      )}
    </section>
  );
}

/* ─── Helpers ──────────────────────────────────────────────── */

function historyByStage(order, stageKey) {
  return order?.history?.find(h => h.stage === stageKey);
}

function getStageAttachments(order, stageKey) {
  return historyByStage(order, stageKey)?.attachments || [];
}

const ATTACH_LABEL_BY_STAGE = {
  confirm: "查看确认单",
  prep:    "查看备料单",
  produce: "查看生产单",
  test:    "查看测试报告",
  ship:    "查看发货单",
  receive: "查看入库单",
};

/* ─── Stage strip (horizontal, compact, sticky) ────────────── */

function StageStrip({ order, sticky, onAction, dimmed, onPreview }) {
  const currentIdx = order.stage;
  return (
    <div style={{
      background: "var(--bg-elev)",
      border: "1px solid var(--line)",
      borderRadius: 10,
      padding: "20px 24px",
      opacity: dimmed ? 0.55 : 1,
      transition: "opacity 240ms",
      ...(sticky ? {
        position: "sticky", top: 72, zIndex: 20,
        boxShadow: "0 4px 16px rgba(31,30,27,0.04)",
      } : {}),
    }}>
      {dimmed && (
        <div className="dim" style={{ fontSize: 11.5, marginBottom: 12, letterSpacing: "0.04em" }}>
          ⓘ 待审批通过后进入执行阶段
        </div>
      )}
      <div style={{
        display: "flex", alignItems: "stretch", justifyContent: "space-between",
        gap: 0, position: "relative",
      }}>
        {STAGES.flatMap((s, i) => {
          const isDone    = i < currentIdx;
          const isCurrent = i === currentIdx;
          const isFuture  = i > currentIdx;
          const history   = order.history?.[i];

          const elements = [];
          if (i > 0) {
            elements.push(
              <div key={`line-${i}`} style={{
                flex: 1, alignSelf: "flex-start", height: 1, marginTop: 18,
                background: isDone || isCurrent ? "var(--ink-2)" : "var(--line)",
              }} />
            );
          }
          elements.push(
            <div key={`node-${s.key}`} style={{
              display: "flex", flexDirection: "column", alignItems: "center",
              gap: 8, minWidth: 92, position: "relative",
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: "50%",
                background: isCurrent ? "var(--accent)"
                          : isDone    ? "var(--ink)"
                          :              "var(--bg-page)",
                color: isCurrent || isDone ? "#fff" : "var(--ink-4)",
                border: isFuture ? "1px solid var(--line-2)" : "0",
                display: "flex", alignItems: "center", justifyContent: "center",
                boxShadow: isCurrent ? "0 0 0 4px var(--accent-tint)" : "none",
                transition: "all 200ms",
              }}>
                {isDone ? <Icon name="check" size={16} /> : <Icon name={STAGE_ICON[s.key]} size={15} />}
              </div>
              <div style={{ textAlign: "center", lineHeight: 1.3, display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
                <div style={{
                  fontSize: 12.5, fontWeight: isCurrent ? 500 : 400,
                  color: isCurrent ? "var(--accent)" : isDone ? "var(--ink)" : "var(--ink-4)",
                }}>{s.label}</div>
                <div className="mono tab-num" style={{
                  fontSize: 10, color: "var(--ink-4)", letterSpacing: "0.02em",
                }}>
                  {historyByStage(order, s.key)?.date ? historyByStage(order, s.key).date.slice(5) : isCurrent ? "进行中" : "—"}
                </div>
                {isDone && getStageAttachments(order, s.key).length > 0 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onPreview?.(s.key, s.label, getStageAttachments(order, s.key));
                    }}
                    title="查看附件"
                    style={{
                      marginTop: 2,
                      display: "inline-flex", alignItems: "center", gap: 4,
                      padding: "1px 6px", borderRadius: 99,
                      background: "var(--bg-page)", border: "1px solid var(--line)",
                      color: "var(--ink-2)", fontSize: 10.5,
                    }}>
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                    </svg>
                    <span className="mono tab-num">{getStageAttachments(order, s.key).length}</span>
                  </button>
                )}
              </div>
            </div>
          );
          return elements;
        })}
      </div>
    </div>
  );
}

/* ─── Stage strip vertical (side rail variant) ─────────────── */

function StageStripVertical({ order, onAction, dimmed, onPreview }) {
  const currentIdx = order.stage;
  return (
    <div style={{
      background: "var(--bg-elev)",
      border: "1px solid var(--line)",
      borderRadius: 10,
      padding: "20px 18px",
      opacity: dimmed ? 0.55 : 1,
    }}>
      <div className="mono dim" style={{ fontSize: 11, letterSpacing: "0.12em", marginBottom: 14 }}>
        EXECUTION · 执行阶段
      </div>
      {dimmed && (
        <div className="dim" style={{ fontSize: 11.5, marginBottom: 14, padding: "8px 10px", background: "var(--bg-sunk)", borderRadius: 6 }}>
          待审批通过后开始
        </div>
      )}
      {STAGES.map((s, i) => {
        const isDone    = i < currentIdx;
        const isCurrent = i === currentIdx;
        const history   = historyByStage(order, s.key);
        const attachments = getStageAttachments(order, s.key);
        return (
          <div key={s.key} style={{
            display: "grid", gridTemplateColumns: "28px 1fr",
            gap: 10, position: "relative", paddingBottom: 14,
          }}>
            {i < STAGES.length - 1 && (
              <div style={{
                position: "absolute", left: 13.5, top: 28, bottom: -2,
                width: 1, background: isDone ? "var(--ink-2)" : "var(--line)",
              }} />
            )}
            <div style={{
              width: 28, height: 28, borderRadius: "50%", zIndex: 1,
              background: isCurrent ? "var(--accent)" : isDone ? "var(--ink)" : "var(--bg-page)",
              color: isCurrent || isDone ? "#fff" : "var(--ink-4)",
              border: !isCurrent && !isDone ? "1px solid var(--line-2)" : "0",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              {isDone ? <Icon name="check" size={13} /> : <Icon name={STAGE_ICON[s.key]} size={12} />}
            </div>
            <div style={{ paddingTop: 4 }}>
              <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 8 }}>
                <div style={{
                  fontSize: 13,
                  fontWeight: isCurrent ? 500 : 400,
                  color: isCurrent ? "var(--accent)" : isDone ? "var(--ink)" : "var(--ink-3)",
                }}>{s.label}</div>
                <div className="mono tab-num" style={{ fontSize: 11, color: "var(--ink-4)" }}>
                  {history?.date ? history.date.slice(5) : isCurrent ? "进行中" : "—"}
                </div>
              </div>
              {history?.by && (
                <div className="dim" style={{ fontSize: 11, marginTop: 3 }}>{history.by}</div>
              )}
              {attachments.length > 0 && (
                <button onClick={() => onPreview?.(s.key, s.label, attachments)}
                  style={{
                    marginTop: 6,
                    display: "inline-flex", alignItems: "center", gap: 5,
                    padding: "3px 8px", borderRadius: 4,
                    background: "var(--bg-page)", border: "1px solid var(--line-2)",
                    color: "var(--ink-2)", fontSize: 11.5,
                  }}>
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                  </svg>
                  {ATTACH_LABEL_BY_STAGE[s.key] || "查看附件"}
                  {attachments.length > 1 && <span className="mono dim" style={{ fontSize: 10 }}>· {attachments.length}</span>}
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Current action card (next-step focus) ─────────────────── */

function CurrentActionCard({ order, onAction }) {
  const isApprovalPending = order.approval?.status === "pending";

  // Approval phase
  if (isApprovalPending) {
    const currentNode = order.approval?.nodes?.find(n => n.status === "current");
    return (
      <div style={{
        background: "linear-gradient(180deg, var(--warn-soft) 0%, var(--bg-elev) 100%)",
        border: "1px solid var(--warn-soft)",
        borderRadius: 10, padding: "20px 24px",
        display: "flex", alignItems: "center", justifyContent: "space-between", gap: 24,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, flex: 1, minWidth: 0 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 10,
            background: "var(--warn)", color: "#fff",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
          }}>
            <Icon name="clock" size={20} />
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <span className="mono dim" style={{ fontSize: 11, letterSpacing: "0.12em" }}>当前节点</span>
              <span style={{ fontSize: 16, fontWeight: 500, color: "var(--ink)" }}>
                {currentNode?.role} 审批 — {currentNode?.name}
              </span>
            </div>
            <div style={{ marginTop: 4, color: "var(--ink-2)", fontSize: 13 }}>
              审批通过后将进入「供应商确认」阶段。
            </div>
            <div className="dim" style={{ marginTop: 2, fontSize: 12 }}>
              如需催办,可通过站内消息提醒审批人。
            </div>
          </div>
        </div>
        <Btn variant="bare" size="md">催办</Btn>
      </div>
    );
  }

  // Execution phase
  const currentStage = STAGES[order.stage];
  if (!currentStage) return null;

  const actionMap = {
    confirm: { label: "上传供应商确认单", action: "supplier-confirm", desc: "等待供应商盖章确认订单",      hint: "确认完成后将进入备料环节" },
    prep:    { label: "标记备料完成",     action: null,                desc: "采购部正在准备物料",        hint: "供应商可开始生产" },
    produce: { label: "完成生产",          action: null,                desc: "供应商正在生产订单中的物料", hint: "完成后进入测试" },
    test:    { label: "上传测试报告",     action: "upload-test",       desc: "需要上传 QA 测试报告",     hint: "通过后即可发货" },
    ship:    { label: "创建发货单",       action: "ship",              desc: "可向客户订单或公司仓库发货", hint: "可分多次发货" },
    receive: { label: "确认入库",         action: null,                desc: "仓库验收中",               hint: "全部物料入库后流程关闭" },
  };
  const a = actionMap[currentStage.key] || {};
  const isOpen = order.status === "已入库" || order.stage >= STAGES.length;

  if (isOpen) return null;

  return (
    <div style={{
      background: "linear-gradient(180deg, var(--accent-tint) 0%, var(--bg-elev) 100%)",
      border: "1px solid var(--accent-soft)",
      borderRadius: 10, padding: "20px 24px",
      display: "flex", alignItems: "center", justifyContent: "space-between", gap: 24,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 16, flex: 1, minWidth: 0 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 10,
          background: "var(--accent)", color: "#fff",
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0,
        }}>
          <Icon name={STAGE_ICON[currentStage.key]} size={20} />
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <span className="mono dim" style={{ fontSize: 11, letterSpacing: "0.12em" }}>当前阶段</span>
            <span style={{ fontSize: 16, fontWeight: 500, color: "var(--ink)" }}>{currentStage.label}</span>
          </div>
          <div style={{ marginTop: 4, color: "var(--ink-2)", fontSize: 13 }}>{a.desc}</div>
          <div className="dim" style={{ marginTop: 2, fontSize: 12 }}>{a.hint}</div>
        </div>
      </div>
      {a.action && (
        <Btn variant="accent" iconR="arrowRt" onClick={() => onAction(a.action)} size="lg">
          {a.label}
        </Btn>
      )}
    </div>
  );
}

/* ─── Info grid ────────────────────────────────────────────── */

function InfoGrid({ items, cols = 4 }) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: `repeat(${cols}, 1fr)`,
      padding: "8px 22px 22px",
      rowGap: 20, columnGap: 24,
    }}>
      {items.map((it, i) => (
        <div key={i}>
          <div className="dim" style={{ fontSize: 11.5, marginBottom: 5, letterSpacing: "0.04em" }}>{it.k}</div>
          <div style={{
            fontSize: 13.5, color: "var(--ink)",
            fontFamily: it.mono ? "var(--font-mono)" : "inherit",
            fontVariantNumeric: it.mono ? "tabular-nums" : "normal",
            fontWeight: it.strong ? 600 : 400,
          }}>{it.v}</div>
        </div>
      ))}
    </div>
  );
}

/* ─── Item table ───────────────────────────────────────────── */

function ItemTable({ items }) {
  if (!items.length) return <Empty icon="cube" label="无明细" />;
  const total = items.reduce((s, i) => s + i.qty * i.price, 0);
  return (
    <table style={{ width: "100%", fontSize: 13, borderCollapse: "separate", borderSpacing: 0 }}>
      <thead>
        <tr>
          {[
            { l: "产品", a: "left" },
            { l: "型号", a: "left" },
            { l: "产品编号", a: "left" },
            { l: "数量", a: "right" },
            { l: "单价", a: "right" },
            { l: "金额", a: "right" },
          ].map((h, i) => (
            <th key={i} style={{
              textAlign: h.a, padding: "8px 22px 10px",
              fontSize: 10.5, fontWeight: 500,
              color: "var(--ink-4)",
              letterSpacing: "0.08em", textTransform: "uppercase",
            }}>{h.l}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {items.map((it, i) => (
          <tr key={i}>
            <td style={{ padding: "16px 22px", maxWidth: 320, borderTop: "1px solid var(--line-soft)", verticalAlign: "top" }}>
              <div style={{ fontWeight: 500, fontSize: 13.5 }}>{it.desc}</div>
              {it.spec && <div className="dim" style={{ fontSize: 11.5, marginTop: 4, lineHeight: 1.4 }}>{it.spec}</div>}
            </td>
            <td style={{ padding: "16px 22px", borderTop: "1px solid var(--line-soft)", verticalAlign: "top" }} className="mono"><span style={{ fontSize: 12.5 }}>{it.model}</span></td>
            <td style={{ padding: "16px 22px", borderTop: "1px solid var(--line-soft)", verticalAlign: "top" }} className="mono dim"><span style={{ fontSize: 12 }}>{it.code}</span></td>
            <td style={{ padding: "16px 22px", textAlign: "right", borderTop: "1px solid var(--line-soft)", verticalAlign: "top" }} className="mono tab-num">{it.qty} <span className="dim" style={{ fontSize: 11 }}>{it.unit}</span></td>
            <td style={{ padding: "16px 22px", textAlign: "right", borderTop: "1px solid var(--line-soft)", verticalAlign: "top" }} className="mono tab-num">{fmtCNY(it.price)}</td>
            <td style={{ padding: "16px 22px", textAlign: "right", fontWeight: 500, borderTop: "1px solid var(--line-soft)", verticalAlign: "top" }} className="mono tab-num">{fmtCNY(it.qty * it.price)}</td>
          </tr>
        ))}
        <tr>
          <td colSpan={3} style={{ padding: "16px 22px", color: "var(--ink-3)", fontSize: 12, letterSpacing: "0.05em", borderTop: "1px solid var(--line)" }}>合计</td>
          <td style={{ padding: "16px 22px", textAlign: "right", borderTop: "1px solid var(--line)" }} className="mono tab-num">{items.reduce((s,i)=>s+i.qty,0)}</td>
          <td style={{ borderTop: "1px solid var(--line)" }}></td>
          <td style={{ padding: "16px 22px", textAlign: "right", fontWeight: 600, fontSize: 14, borderTop: "1px solid var(--line)" }} className="mono tab-num">{fmtCNY(total)}</td>
        </tr>
      </tbody>
    </table>
  );
}

/* ─── Shipment list ─────────────────────────────────────────── */

function ShipmentList({ shipments, canCreate, onCreate }) {
  const [expanded, setExpanded] = useState(new Set());
  const toggle = (id) => setExpanded(s => {
    const n = new Set(s);
    if (n.has(id)) n.delete(id); else n.add(id);
    return n;
  });

  if (!shipments.length) {
    return (
      <Empty
        icon="truck"
        label={canCreate ? "尚未发货" : "尚未发货"}
        sub={canCreate ? "可立即创建发货单" : "订单进入「待发货」阶段后可创建发货单"}
        cta={canCreate ? <Btn variant="accent" iconL="plus" onClick={onCreate} size="md">创建发货单</Btn> : null}
      />
    );
  }
  return (
    <table style={{ width: "100%", fontSize: 13, borderCollapse: "separate", borderSpacing: 0 }}>
      <thead>
        <tr>
          {["", "发货单号", "目标", "数量", "状态", "日期"].map((h, i) => (
            <th key={i} style={{
              textAlign: i === 3 ? "right" : "left",
              padding: "8px 20px 10px", fontSize: 10.5, fontWeight: 500,
              color: "var(--ink-4)", letterSpacing: "0.08em", textTransform: "uppercase",
              width: i === 0 ? 32 : undefined,
            }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {shipments.map((s, i) => {
          const isExpanded = expanded.has(s.id);
          const isLast = i === shipments.length - 1;
          return (
            <ShipmentRow
              key={s.id}
              shipment={s}
              isExpanded={isExpanded}
              onToggle={() => toggle(s.id)}
              isLast={isLast}
            />
          );
        })}
      </tbody>
    </table>
  );
}

function ShipmentRow({ shipment, isExpanded, onToggle, isLast }) {
  const cellBorder = isExpanded ? "0" : (isLast ? "0" : "1px solid var(--line-soft)");
  const topBorder = "1px solid var(--line-soft)";
  return (
    <>
      <tr
        onClick={onToggle}
        style={{ cursor: "pointer", transition: "background 100ms" }}
        onMouseEnter={e => e.currentTarget.style.background = "var(--bg-hover)"}
        onMouseLeave={e => e.currentTarget.style.background = "transparent"}
      >
        <td style={{ padding: "14px 20px", borderTop: topBorder, color: "var(--ink-3)" }}>
          <span style={{
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            width: 18, height: 18, transition: "transform 200ms",
            transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
          }}>
            <Icon name="chev" size={12} />
          </span>
        </td>
        <td style={{ padding: "14px 20px", borderTop: topBorder }} className="mono">
          <span style={{ color: "var(--accent)", fontWeight: 500 }}>{shipment.id}</span>
        </td>
        <td style={{ padding: "14px 20px", borderTop: topBorder }}>
          <div style={{ color: "var(--ink)" }}>{shipment.target}</div>
          {shipment.targetSub && <div className="mono dim" style={{ fontSize: 11, marginTop: 2 }}>{shipment.targetSub}</div>}
        </td>
        <td style={{ padding: "14px 20px", textAlign: "right", borderTop: topBorder }} className="mono tab-num">
          {shipment.qty}
        </td>
        <td style={{ padding: "14px 20px", borderTop: topBorder }}>
          <Pill tone="success" dot>{shipment.status}</Pill>
        </td>
        <td style={{ padding: "14px 20px", borderTop: topBorder }} className="mono tab-num dim">
          {shipment.date}
        </td>
      </tr>
      {isExpanded && (
        <tr style={{ background: "var(--bg-page)" }}>
          <td colSpan={6} style={{
            padding: "16px 24px 18px",
          }}>
            <ShipmentDetail shipment={shipment} />
          </td>
        </tr>
      )}
    </>
  );
}

function ShipmentDetail({ shipment }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      {/* Logistics info */}
      <div style={{
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
        gap: 12, padding: "8px 0",
      }}>
        {[
          { k: "承运商",   v: shipment.carrier || "—" },
          { k: "运单号",   v: shipment.waybill || "—", mono: true },
          { k: "发货数量", v: shipment.qty + " 套", mono: true },
          { k: "签收日期", v: shipment.date, mono: true },
        ].map((it, idx) => (
          <div key={idx}>
            <div className="dim" style={{ fontSize: 11, marginBottom: 3, letterSpacing: "0.04em" }}>{it.k}</div>
            <div style={{
              fontSize: 13, color: "var(--ink)",
              fontFamily: it.mono ? "var(--font-mono)" : "inherit",
              fontVariantNumeric: it.mono ? "tabular-nums" : "normal",
            }}>{it.v}</div>
          </div>
        ))}
      </div>

      {/* Item breakdown */}
      {shipment.items && shipment.items.length > 0 && (
        <div style={{
          background: "var(--bg-elev)",
          border: "1px solid var(--line)",
          borderRadius: 8, overflow: "hidden",
        }}>
          <div style={{
            padding: "10px 14px", borderBottom: "1px solid var(--line)",
            display: "flex", alignItems: "center", gap: 8,
          }}>
            <span className="mono dim" style={{ fontSize: 10.5, letterSpacing: "0.1em" }}>本次发货明细 · {shipment.items.length} 项</span>
          </div>
          <table style={{ width: "100%", fontSize: 12.5 }}>
            <thead>
              <tr style={{ background: "var(--bg-page)" }}>
                {["产品", "型号", "数量", "SN 段"].map((h, idx) => (
                  <th key={h} style={{
                    textAlign: idx === 2 ? "right" : "left",
                    padding: "8px 14px", fontSize: 10, fontWeight: 500,
                    color: "var(--ink-3)", letterSpacing: "0.08em", textTransform: "uppercase",
                    borderBottom: "1px solid var(--line)",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {shipment.items.map((it, idx) => (
                <tr key={idx} style={{
                  borderBottom: idx === shipment.items.length - 1 ? "0" : "1px solid var(--line-soft)",
                }}>
                  <td style={{ padding: "10px 14px", color: "var(--ink-2)" }}>{it.desc}</td>
                  <td style={{ padding: "10px 14px" }} className="mono dim">{it.model}</td>
                  <td style={{ padding: "10px 14px", textAlign: "right" }} className="mono tab-num">{it.qty}</td>
                  <td style={{ padding: "10px 14px" }} className="mono dim">{it.sn || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ─── Meta list ────────────────────────────────────────────── */

function MetaList({ items }) {
  return (
    <div style={{ padding: "10px 16px" }}>
      {items.map((it, i) => (
        <div key={i} style={{
          display: "flex", justifyContent: "space-between", alignItems: "baseline",
          padding: "8px 0", borderBottom: i === items.length - 1 ? "0" : "1px solid var(--line)",
        }}>
          <span className="dim" style={{ fontSize: 12 }}>{it.k}</span>
          <span style={{
            fontSize: 12.5,
            color: it.strong ? "var(--ink)" : "var(--ink-2)",
            fontWeight: it.strong ? 600 : 400,
            fontFamily: it.mono ? "var(--font-mono)" : "inherit",
          }}>{it.v}</span>
        </div>
      ))}
    </div>
  );
}

/* ─── History list ─────────────────────────────────────────── */

function HistoryList({ history }) {
  return (
    <div style={{ padding: "10px 16px 14px" }}>
      {history.map((h, i) => {
        const stage = STAGES.find(s => s.key === h.stage);
        return (
          <div key={i} style={{
            display: "grid", gridTemplateColumns: "auto 1fr auto",
            gap: 10, alignItems: "center", padding: "8px 0",
            borderBottom: i === history.length - 1 ? "0" : "1px dashed var(--line)",
          }}>
            <span style={{
              width: 20, height: 20, borderRadius: "50%",
              background: h.current ? "var(--accent-soft)" : "var(--bg-sunk)",
              color: h.current ? "var(--accent)" : "var(--ink-3)",
              display: "inline-flex", alignItems: "center", justifyContent: "center",
            }}>
              <Icon name={h.current ? "clock" : "check"} size={11} />
            </span>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 12.5, color: "var(--ink-2)" }}>
                {stage?.label}
                {h.attach && <span style={{ color: "var(--accent)", marginLeft: 6, fontSize: 11.5 }}>· {h.attach}</span>}
              </div>
              {h.by && <div className="dim" style={{ fontSize: 11, marginTop: 1 }}>{h.by}</div>}
            </div>
            <span className="mono tab-num dim" style={{ fontSize: 11 }}>
              {h.date ? h.date.slice(5) : "—"}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Empty state ───────────────────────────────────────────── */

function Empty({ icon, label, sub, cta }) {
  return (
    <div style={{
      padding: "44px 20px", textAlign: "center",
      display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
    }}>
      <div style={{
        width: 44, height: 44, borderRadius: 10,
        background: "var(--bg-sunk)", color: "var(--ink-4)",
        display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 4,
      }}>
        <Icon name={icon} size={20} />
      </div>
      <div style={{ color: "var(--ink-2)", fontSize: 13, fontWeight: 500 }}>{label}</div>
      {sub && <div className="dim" style={{ fontSize: 12, maxWidth: 320 }}>{sub}</div>}
      {cta && <div style={{ marginTop: 8 }}>{cta}</div>}
    </div>
  );
}

/* ─── Approval card (inline) ────────────────────────────────── */

function ApprovalCard({ order }) {
  const [note, setNote] = useState("");
  return (
    <Section title="部门负责人审批" subtitle={<Pill tone="warn">当前节点</Pill>} compact>
      <div style={{ padding: "14px 16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
          <Avatar name={order.approver || "郭"} size={32} />
          <div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>{order.approver || "郭小会"}</div>
            <div className="dim" style={{ fontSize: 11 }}>{order.approveStage || "部门负责人"}</div>
          </div>
        </div>
        <textarea
          value={note} onChange={e => setNote(e.target.value)}
          placeholder="审批意见…"
          style={{
            width: "100%", minHeight: 64, padding: "8px 10px",
            border: "1px solid var(--line-2)", borderRadius: 6,
            background: "var(--bg-page)", fontSize: 12.5, resize: "vertical",
            outline: "none", marginBottom: 10,
            fontFamily: "inherit", color: "var(--ink)",
          }}
        />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <Btn variant="primary" iconL="check" size="md">同意</Btn>
          <Btn variant="danger" iconL="cancel" size="md">驳回</Btn>
        </div>
      </div>
    </Section>
  );
}

Object.assign(window, {
  ListScreen, DetailScreen,
});
