/* PMA · 库存调整 & Excel 导入弹窗 */

/* ─── Adjust stock ─────────────────────────────────────────── */

function AdjustStockModal({ open, row, companyName, onClose, onSubmit }) {
  const [mode, setMode] = useState("in"); // in | out | set
  const [delta, setDelta] = useState(1);
  const [target, setTarget] = useState("");
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [err, setErr] = useState({});

  useEffect(() => {
    if (open) { setMode("in"); setDelta(1); setTarget(""); setReason(""); setNote(""); setErr({}); }
  }, [open]);

  const cur = row?.qty ?? 0;
  const newQty =
    mode === "in"  ? cur + Number(delta || 0) :
    mode === "out" ? cur - Number(delta || 0) :
                     Number(target || 0);
  const diff = newQty - cur;

  const submit = () => {
    const e = {};
    if (mode === "set" && target === "") e.target = "请填写目标值";
    if ((mode === "in" || mode === "out") && (!delta || Number(delta) <= 0)) e.delta = "数量必须大于 0";
    if (!reason) e.reason = "请选择原因";
    setErr(e);
    if (Object.keys(e).length) {
      window.toast?.warn?.("无法调整", Object.values(e)[0]);
      return;
    }
    window.toast?.success?.("库存已调整", `${row?.name} · ${cur} → ${newQty}`);
    onSubmit?.();
    onClose();
  };

  return (
    <ModalShell
      open={open} onClose={onClose}
      title="调整库存"
      icon="settings"
      width={520}
      footer={<>
        <Btn variant="ghost" onClick={onClose}>取消</Btn>
        <Btn variant="accent" iconL="check" onClick={submit}>确认调整</Btn>
      </>}
    >
      {/* Header strip */}
      <div style={{
        background: "var(--bg-page)", border: "1px solid var(--line)",
        borderRadius: 10, padding: "14px 16px", marginBottom: 18,
      }}>
        <div className="mono dim" style={{ fontSize: 10.5, letterSpacing: "0.12em", marginBottom: 6 }}>
          产品 · 当前公司
        </div>
        <div style={{ fontSize: 13.5, color: "var(--ink-2)", marginBottom: 6 }}>
          {row?.name} <span className="mono dim" style={{ fontSize: 12, marginLeft: 6 }}>{row?.model}</span>
        </div>
        <div className="dim" style={{ fontSize: 11.5, marginBottom: 8 }}>{companyName}</div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
          <span className="dim" style={{ fontSize: 12 }}>当前库存</span>
          <span className="mono tab-num serif" style={{ fontSize: 26, fontWeight: 500, color: "var(--accent)" }}>{cur}</span>
          <span className="dim" style={{ fontSize: 12 }}>{row?.unit}</span>
        </div>
      </div>

      {/* Mode segmented control */}
      <Field label="调整方式">
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 0,
          padding: 3, background: "var(--bg-page)", borderRadius: 8,
          border: "1px solid var(--line-2)",
        }}>
          {[
            { v: "in",  l: "入库 (+)", color: "var(--success)" },
            { v: "out", l: "出库 (−)", color: "var(--danger)"  },
            { v: "set", l: "设值 (=)", color: "var(--accent)"  },
          ].map(opt => {
            const active = mode === opt.v;
            return (
              <button key={opt.v} onClick={() => setMode(opt.v)}
                style={{
                  padding: "8px 0", borderRadius: 6,
                  background: active ? "var(--bg-elev)" : "transparent",
                  color: active ? opt.color : "var(--ink-3)",
                  fontSize: 13, fontWeight: active ? 600 : 500,
                  boxShadow: active ? "0 1px 3px rgba(31,30,27,0.08)" : "none",
                  transition: "all 140ms",
                }}>
                {opt.l}
              </button>
            );
          })}
        </div>
      </Field>

      {/* Input */}
      {mode === "set" ? (
        <Field label="目标值" required>
          <input
            type="number" value={target} onChange={e => setTarget(e.target.value)}
            placeholder="设置后的数量"
            className="mono tab-num"
            style={{
              width: "100%", height: 36, padding: "0 12px",
              border: `1px solid ${err.target ? "var(--danger)" : "var(--line-2)"}`,
              borderRadius: 6, fontSize: 14, background: "var(--bg-elev)", outline: "none",
            }}/>
          <div className="dim" style={{ fontSize: 11, marginTop: 5 }}>
            直接设为该绝对值,系统记录差异({diff >= 0 ? "+" : ""}{diff})
          </div>
          <FieldError>{err.target}</FieldError>
        </Field>
      ) : (
        <Field label={mode === "in" ? "入库数量" : "出库数量"} required>
          <input
            type="number" value={delta} onChange={e => setDelta(e.target.value)}
            min="1"
            className="mono tab-num"
            style={{
              width: "100%", height: 36, padding: "0 12px",
              border: `1px solid ${err.delta ? "var(--danger)" : "var(--line-2)"}`,
              borderRadius: 6, fontSize: 14, background: "var(--bg-elev)", outline: "none",
            }}/>
          <div className="dim" style={{ fontSize: 11, marginTop: 5 }}>
            调整后:<span className="mono tab-num" style={{ color: "var(--ink-2)" }}>{cur} → {newQty}</span>
          </div>
          <FieldError>{err.delta}</FieldError>
        </Field>
      )}

      <Field label="原因" required>
        <Select value={reason} onChange={(v) => { setReason(v); setErr(e => ({...e, reason: undefined})); }}
          options={[{ value: "", label: "请选择…" }, ...window.PMA_INV.ADJUST_REASONS]}
          style={{ width: "100%", borderColor: err.reason ? "var(--danger)" : undefined }}/>
        <FieldError>{err.reason}</FieldError>
      </Field>

      <Field label="备注">
        <textarea value={note} onChange={e => setNote(e.target.value)}
          placeholder="补充说明(可选)"
          style={{
            width: "100%", minHeight: 60, padding: "10px 12px",
            border: "1px solid var(--line-2)", borderRadius: 6,
            background: "var(--bg-page)", fontSize: 13, resize: "vertical",
            outline: "none", fontFamily: "inherit", color: "var(--ink)",
          }}/>
      </Field>
    </ModalShell>
  );
}

/* ─── Excel import ─────────────────────────────────────────── */

function ExcelImportModal({ open, onClose }) {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [hover, setHover] = useState(false);

  useEffect(() => { if (open) { setStep(1); setFile(null); } }, [open]);

  return (
    <ModalShell
      open={open} onClose={onClose}
      title="Excel 导入"
      icon="upload"
      width={680}
      footer={<>
        <Btn variant="ghost" onClick={onClose}>取消</Btn>
        {step === 1 ? (
          <Btn variant="accent" iconR="arrowRt" disabled={!file} onClick={() => setStep(2)}>
            下一步 · 预览校验
          </Btn>
        ) : (
          <>
            <Btn variant="ghost" onClick={() => setStep(1)}>上一步</Btn>
            <Btn variant="accent" iconL="check" onClick={() => {
              window.toast?.success?.("已导入", `${file?.name} · 8 条记录已合并入库`);
              onClose();
            }}>确认导入</Btn>
          </>
        )}
      </>}
    >
      {/* Stepper */}
      <div style={{ display: "flex", alignItems: "center", gap: 0, marginBottom: 22 }}>
        {[
          { n: 1, l: "上传文件" },
          { n: 2, l: "预览校验" },
        ].flatMap((s, i, arr) => {
          const active = step === s.n;
          const done   = step > s.n;
          const els = [];
          if (i > 0) {
            els.push(<div key={`line-${i}`} style={{ flex: 1, height: 1, background: done || active ? "var(--ink-2)" : "var(--line-2)", margin: "0 8px" }} />);
          }
          els.push(
            <div key={`step-${s.n}`} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{
                width: 24, height: 24, borderRadius: "50%",
                background: done ? "var(--ink)" : active ? "var(--accent)" : "var(--bg-page)",
                color: done || active ? "#fff" : "var(--ink-4)",
                border: !done && !active ? "1px solid var(--line-2)" : "0",
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                fontSize: 11, fontWeight: 600, fontFamily: "var(--font-mono)",
              }}>{done ? "✓" : s.n}</span>
              <span style={{ fontSize: 13, color: active ? "var(--ink)" : "var(--ink-3)", fontWeight: active ? 500 : 400 }}>{s.l}</span>
            </div>
          );
          return els;
        })}
      </div>

      {step === 1 && (
        <>
          <div style={{
            padding: "10px 14px", borderRadius: 8,
            background: "var(--info-soft)", color: "var(--info)",
            fontSize: 12.5, lineHeight: 1.55, marginBottom: 16,
            display: "flex", gap: 10, alignItems: "flex-start",
          }}>
            <span style={{ flexShrink: 0, marginTop: 1 }}><Icon name="info" size={14} /></span>
            <span>
              Excel 必含列:<strong>MN 号 / 公司名 / 数量</strong>(可选:单位、存储位置、最低库存、最高库存、备注)。导入语义 = 设值,会覆盖现有库存。
            </span>
          </div>

          {file ? (
            <div style={{
              border: "1px solid var(--line-2)", borderRadius: 10,
              padding: "14px 16px", display: "flex", alignItems: "center", gap: 14,
              background: "var(--bg-page)",
            }}>
              <span style={{
                width: 42, height: 42, borderRadius: 8,
                background: "var(--success-soft)", color: "var(--success)",
                display: "inline-flex", alignItems: "center", justifyContent: "center",
              }}><Icon name="file" size={20} /></span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13.5, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</div>
                <div className="mono dim tab-num" style={{ fontSize: 11.5, marginTop: 2 }}>{fmtFileSize(file.size)}</div>
              </div>
              <button onClick={() => setFile(null)} style={{
                padding: "5px 10px", border: "1px solid var(--line-2)", borderRadius: 4,
                fontSize: 12, color: "var(--ink-3)",
              }}>移除</button>
            </div>
          ) : (
            <label
              onDragOver={e => { e.preventDefault(); setHover(true); }}
              onDragLeave={() => setHover(false)}
              onDrop={e => { e.preventDefault(); setHover(false); const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
              style={{
                display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                gap: 10, padding: "50px 20px", borderRadius: 10,
                border: `1.5px dashed ${hover ? "var(--accent)" : "var(--line-2)"}`,
                background: hover ? "var(--accent-tint)" : "var(--bg-page)",
                cursor: "pointer", position: "relative", transition: "all 140ms",
              }}>
              <span style={{
                width: 48, height: 48, borderRadius: 12,
                background: hover ? "var(--accent)" : "var(--bg-sunk)",
                color: hover ? "#fff" : "var(--ink-3)",
                display: "inline-flex", alignItems: "center", justifyContent: "center",
              }}><Icon name="upload" size={22} /></span>
              <div style={{ fontSize: 14, fontWeight: 500, color: "var(--ink)" }}>
                点击选择文件 <span className="dim">或 拖拽到此处</span>
              </div>
              <div className="dim mono" style={{ fontSize: 11.5 }}>支持 .xlsx / .xls 格式</div>
              <input type="file" accept=".xlsx,.xls"
                onChange={e => { const f = e.target.files[0]; if (f) setFile(f); }}
                style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer" }}/>
            </label>
          )}

          <div style={{ marginTop: 14, textAlign: "center" }}>
            <button style={{
              color: "var(--accent)", fontSize: 12.5, padding: "6px 12px",
              display: "inline-flex", alignItems: "center", gap: 5,
            }}>
              <Icon name="download" size={12} /> 下载导入模板
            </button>
          </div>
        </>
      )}

      {step === 2 && (
        <PreviewTable />
      )}
    </ModalShell>
  );
}

function PreviewTable() {
  const sample = [
    { mn: "HYTD4MA",   company: "和源通信(上海)股份有限公司", qty: 120, old: 100, status: "ok",    msg: "" },
    { mn: "HYPSMXI40", company: "和源通信(上海)股份有限公司", qty: 5,   old: 2,   status: "ok",    msg: "" },
    { mn: "BC4I2X4NN", company: "和源通信(上海)股份有限公司", qty: 95,  old: 101, status: "warn",  msg: "数量减少" },
    { mn: "UNKNOWN-1", company: "和源通信(上海)股份有限公司", qty: 10,  old: null,status: "err",   msg: "MN 号不存在" },
  ];
  const ok = sample.filter(r => r.status === "ok").length;
  const warn = sample.filter(r => r.status === "warn").length;
  const err = sample.filter(r => r.status === "err").length;
  return (
    <div>
      <div style={{ display: "flex", gap: 14, marginBottom: 14, fontSize: 12.5 }}>
        <Pill tone="success" dot>{ok} 条正常</Pill>
        {warn > 0 && <Pill tone="warn" dot>{warn} 条变更较大</Pill>}
        {err > 0 && <Pill tone="danger" dot>{err} 条异常</Pill>}
      </div>
      <div style={{ border: "1px solid var(--line)", borderRadius: 8, overflow: "hidden", background: "var(--bg-elev)" }}>
        <table style={{ width: "100%", fontSize: 12.5, borderCollapse: "separate", borderSpacing: 0 }}>
          <thead>
            <tr>
              {["MN 号", "公司", "新数量", "原数量", "状态"].map((h, i) => (
                <th key={i} style={{
                  textAlign: i === 2 || i === 3 ? "right" : "left",
                  padding: "10px 14px 12px", fontSize: 10, fontWeight: 500,
                  color: "var(--ink-4)", letterSpacing: "0.08em", textTransform: "uppercase",
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sample.map((r, i) => (
              <tr key={i} style={{ borderTop: "1px solid var(--line-soft)" }}>
                <td style={{ padding: "10px 14px" }} className="mono">{r.mn}</td>
                <td style={{ padding: "10px 14px", color: "var(--ink-2)", fontSize: 12 }}>{r.company}</td>
                <td style={{ padding: "10px 14px", textAlign: "right" }} className="mono tab-num">{r.qty}</td>
                <td style={{ padding: "10px 14px", textAlign: "right" }} className="mono tab-num dim">{r.old ?? "—"}</td>
                <td style={{ padding: "10px 14px" }}>
                  {r.status === "ok"   && <Pill tone="success">就绪</Pill>}
                  {r.status === "warn" && <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><Pill tone="warn">需确认</Pill><span className="dim" style={{ fontSize: 11 }}>{r.msg}</span></span>}
                  {r.status === "err"  && <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}><Pill tone="danger">异常</Pill><span style={{ fontSize: 11, color: "var(--danger)" }}>{r.msg}</span></span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

Object.assign(window, { AdjustStockModal, ExcelImportModal });
