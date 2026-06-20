/* ─────────────────────────────────────────────────────────────
   PMA · 弹窗组件:
   - SupplierConfirmModal  供应商确认
   - UploadTestModal       上传测试报告
   - CreateShipmentModal   创建发货单
   ───────────────────────────────────────────────────────────── */

function ModalShell({ open, title, onClose, icon, children, footer, width = 560 }) {
  if (!open) return null;
  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}
      style={{
        position: "fixed", inset: 0, zIndex: 100,
        background: "rgba(31,30,27,0.32)",
        backdropFilter: "blur(2px)",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: 20,
        animation: "fade-in 180ms ease",
      }}
    >
      <div style={{
        width: "100%", maxWidth: width,
        maxHeight: "90vh", display: "flex", flexDirection: "column",
        background: "var(--bg-elev)",
        borderRadius: 12,
        boxShadow: "0 20px 60px rgba(0,0,0,0.15), 0 0 0 1px var(--line)",
        animation: "scale-in 200ms cubic-bezier(.2,.7,.2,1)",
        overflow: "hidden",
      }}>
        <header style={{
          padding: "18px 22px 12px",
          display: "flex", alignItems: "center", gap: 10,
        }}>
          {icon && (
            <span style={{
              width: 30, height: 30, borderRadius: 7,
              background: "var(--accent-tint)", color: "var(--accent)",
              display: "inline-flex", alignItems: "center", justifyContent: "center",
            }}>
              <Icon name={icon} size={16} />
            </span>
          )}
          <h3 className="serif" style={{
            margin: 0, fontSize: 18, fontWeight: 500, letterSpacing: "0.01em", flex: 1,
          }}>{title}</h3>
          <button onClick={onClose} style={{
            color: "var(--ink-3)", padding: 4, borderRadius: 6,
          }}>
            <Icon name="close" size={18} />
          </button>
        </header>
        <div style={{ padding: "8px 22px 16px", overflowY: "auto", flex: 1, minHeight: 0 }}>
          {children}
        </div>
        {footer && (
          <footer style={{
            padding: "10px 22px 18px",
            display: "flex", justifyContent: "flex-end", gap: 8,
          }}>
            {footer}
          </footer>
        )}
      </div>
    </div>
  );
}

/* ─── Info strip (used in modal headers) ───────────────────── */

function InfoStrip({ items }) {
  return (
    <div style={{
      background: "var(--bg-page)",
      border: "1px solid var(--line)",
      borderRadius: 8, padding: "14px 16px",
      display: "flex", flexDirection: "column", gap: 8,
    }}>
      {items.map((it, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
          <span className="dim" style={{ fontSize: 12 }}>{it.k}</span>
          <span style={{
            fontSize: 13, fontWeight: it.strong ? 600 : 500,
            color: it.strong ? "var(--ink)" : "var(--ink-2)",
            fontFamily: it.mono ? "var(--font-mono)" : "inherit",
          }}>{it.v}</span>
        </div>
      ))}
    </div>
  );
}

/* ─── Field label + input wrapper ──────────────────────────── */

function Field({ label, required, hint, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{
        display: "flex", alignItems: "baseline", gap: 4,
        fontSize: 12.5, fontWeight: 500, color: "var(--ink-2)", marginBottom: 8,
      }}>
        <span>{label}</span>
        {required && <span style={{ color: "var(--danger)" }}>*</span>}
        {hint && <span className="dim" style={{ fontSize: 11, fontWeight: 400, marginLeft: "auto" }}>{hint}</span>}
      </label>
      {children}
    </div>
  );
}

/* ─── File drop zone ───────────────────────────────────────── */

function DropZone({ accept = "PDF · JPG · PNG", maxSize = "10 MB", name = "文件" }) {
  const [hover, setHover] = useState(false);
  const [file, setFile] = useState(null);

  const onDrop = (e) => {
    e.preventDefault();
    setHover(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };
  const onPick = (e) => {
    const f = e.target.files[0];
    if (f) setFile(f);
  };

  if (file) {
    return (
      <div style={{
        border: "1px solid var(--line-2)", borderRadius: 8,
        padding: "12px 14px", display: "flex", alignItems: "center", gap: 12,
        background: "var(--bg-page)",
      }}>
        <span style={{
          width: 36, height: 36, borderRadius: 6,
          background: "var(--accent-tint)", color: "var(--accent)",
          display: "inline-flex", alignItems: "center", justifyContent: "center",
        }}><Icon name="file" size={18} /></span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</div>
          <div className="dim mono tab-num" style={{ fontSize: 11, marginTop: 2 }}>
            {(file.size / 1024).toFixed(1)} KB
          </div>
        </div>
        <button onClick={() => setFile(null)} style={{
          color: "var(--ink-3)", fontSize: 12, padding: "4px 10px",
          borderRadius: 4, border: "1px solid var(--line-2)",
        }}>移除</button>
      </div>
    );
  }

  return (
    <label
      onDragOver={(e) => { e.preventDefault(); setHover(true); }}
      onDragLeave={() => setHover(false)}
      onDrop={onDrop}
      style={{
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        gap: 8, padding: "32px 20px", borderRadius: 8,
        border: `1.5px dashed ${hover ? "var(--accent)" : "var(--line-2)"}`,
        background: hover ? "var(--accent-tint)" : "var(--bg-page)",
        cursor: "pointer", transition: "all 160ms",
        position: "relative",
      }}
    >
      <span style={{
        width: 40, height: 40, borderRadius: 10,
        background: hover ? "var(--accent)" : "var(--bg-sunk)",
        color: hover ? "#fff" : "var(--ink-3)",
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        transition: "all 160ms",
      }}>
        <Icon name="upload" size={18} />
      </span>
      <div style={{ fontSize: 13, color: "var(--ink-2)", marginTop: 2, fontWeight: 500 }}>
        点击或拖拽上传{name}
      </div>
      <div className="dim mono" style={{ fontSize: 11, letterSpacing: "0.04em" }}>
        {accept} · 最大 {maxSize}
      </div>
      <input type="file" onChange={onPick} style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer" }} />
    </label>
  );
}

/* ─── Supplier confirm modal ───────────────────────────────── */

function SupplierConfirmModal({ open, order, onClose }) {
  const [note, setNote] = useState("");
  return (
    <ModalShell
      open={open} onClose={onClose}
      title="供应商确认"
      icon="check"
      footer={<>
        <Btn variant="ghost" onClick={onClose}>取消</Btn>
        <Btn variant="accent" iconL="check">确认供应商已确认</Btn>
      </>}
    >
      <InfoStrip items={[
        { k: "PO 单号",   v: order?.id || "CG-2605-003", mono: true, strong: true },
        { k: "供应商",     v: order?.supplier || "长泽科技" },
        { k: "订单金额",   v: fmtCNY(order?.amount || 0), mono: true },
      ]} />
      <div style={{ height: 18 }} />
      <Field label="确认回执" required>
        <DropZone name="供应商盖章确认单" />
      </Field>
      <Field label="备注">
        <textarea
          value={note} onChange={e => setNote(e.target.value)}
          placeholder="可选备注信息"
          style={{
            width: "100%", minHeight: 64, padding: "10px 12px",
            border: "1px solid var(--line-2)", borderRadius: 6,
            background: "var(--bg-page)", fontSize: 13, resize: "vertical",
            outline: "none", fontFamily: "inherit", color: "var(--ink)",
          }}
        />
      </Field>
    </ModalShell>
  );
}

/* ─── Upload test report modal ─────────────────────────────── */

function UploadTestModal({ open, order, onClose }) {
  const [note, setNote] = useState("");
  return (
    <ModalShell
      open={open} onClose={onClose}
      title="上传测试报告"
      icon="flask"
      footer={<>
        <Btn variant="ghost" onClick={onClose}>取消</Btn>
        <Btn variant="accent" iconL="upload">提交测试报告</Btn>
      </>}
    >
      <InfoStrip items={[
        { k: "PO 单号",   v: order?.id || "CG-2605-003", mono: true, strong: true },
        { k: "当前阶段",   v: "测试" },
      ]} />
      <div style={{ height: 18 }} />
      <Field label="测试报告" required hint="可一次上传多个文件,合并存档">
        <DropZone name="测试报告文件" />
      </Field>
      <Field label="备注">
        <textarea
          value={note} onChange={e => setNote(e.target.value)}
          placeholder="可选备注信息"
          style={{
            width: "100%", minHeight: 64, padding: "10px 12px",
            border: "1px solid var(--line-2)", borderRadius: 6,
            background: "var(--bg-page)", fontSize: 13, resize: "vertical",
            outline: "none", fontFamily: "inherit", color: "var(--ink)",
          }}
        />
      </Field>
    </ModalShell>
  );
}

/* ─── Create shipment modal ────────────────────────────────── */

function CreateShipmentModal({ open, order, onClose }) {
  const [target, setTarget] = useState("customer"); // customer | warehouse
  const [customerOrder, setCustomerOrder] = useState("");
  const baseItems = order?.items || [
    { desc: "常规数字基站",   spec: "400-470 MHz, 25W",        model: "Mark3000BS",    code: "MN-0001", qty: 1 },
    { desc: "多信道分合路器", spec: "2 路, 400 MHz",            model: "FHJ400-2",      code: "MN-0002", qty: 1 },
    { desc: "数字智能信道机", spec: "400-470 MHz, 输出 25 W",   model: "Mark1000 MAX",  code: "MN-0003", qty: 1 },
  ];
  const items = baseItems.map(i => ({ ...i, arrived: i.qty || 0, shipped: 0, avail: i.qty || 1 }));

  const [qty, setQty]           = useState(() => Object.fromEntries(items.map((_, i) => [i, items[i].avail || 1])));
  const [snPrefix, setSnPrefix] = useState(() => Object.fromEntries(items.map((it, i) => [i, (it.model || "") + "-"])));
  const [snStart, setSnStart]   = useState(() => Object.fromEntries(items.map((_, i) => [i, "001"])));
  const [skipSn, setSkipSn]     = useState({});

  const totalQty = Object.values(qty).reduce((s, v) => s + (Number(v) || 0), 0);

  return (
    <ModalShell
      open={open} onClose={onClose}
      title="创建发货单"
      icon="truck"
      width={880}
      footer={<>
        <Btn variant="ghost" onClick={onClose}>取消</Btn>
        <Btn variant="accent" iconL="truck" disabled={totalQty === 0}>
          创建发货单 {totalQty > 0 && <span className="mono tab-num" style={{ opacity: 0.85 }}>· {totalQty} 件</span>}
        </Btn>
      </>}
    >
      {/* Destination toggle */}
      <Field label="发货去向">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {[
            { v: "customer",  label: "发给客户订单", sub: "出库 → 客户" },
            { v: "warehouse", label: "入公司仓库",   sub: "出库 → 自有仓" },
          ].map(opt => {
            const active = target === opt.v;
            return (
              <button key={opt.v} onClick={() => setTarget(opt.v)}
                style={{
                  padding: "12px 14px",
                  border: `1px solid ${active ? "var(--accent)" : "var(--line-2)"}`,
                  background: active ? "var(--accent-tint)" : "var(--bg-elev)",
                  borderRadius: 8, textAlign: "left",
                  display: "flex", alignItems: "center", gap: 10,
                  cursor: "pointer", transition: "all 120ms",
                }}>
                <span style={{
                  width: 16, height: 16, borderRadius: "50%",
                  border: `1.5px solid ${active ? "var(--accent)" : "var(--line-2)"}`,
                  position: "relative", flexShrink: 0,
                }}>
                  {active && <span style={{
                    position: "absolute", inset: 3, borderRadius: "50%", background: "var(--accent)"
                  }} />}
                </span>
                <div>
                  <div style={{ fontSize: 13.5, fontWeight: 500, color: "var(--ink)" }}>{opt.label}</div>
                  <div className="dim" style={{ fontSize: 11, marginTop: 1 }}>{opt.sub}</div>
                </div>
              </button>
            );
          })}
        </div>
      </Field>

      {target === "customer" && (
        <Field label="目标客户订单" required>
          <Select
            value={customerOrder} onChange={setCustomerOrder}
            options={[
              { value: "", label: "选择客户订单…" },
              { value: "SO202605-001", label: "SO202605-001 · 上海大展通信 · 待 16 件" },
              { value: "SO202605-002", label: "SO202605-002 · 上海大展通信 · 待 24 件" },
              { value: "SO202605-003", label: "SO202605-003 · 上海常森电子 · 待 268 件" },
            ]}
            style={{ width: "100%" }}
          />
        </Field>
      )}

      {/* Items */}
      <Field label="发货明细" hint={`${items.length} 项物料 · 本次共 ${totalQty} 件`}>
        <div style={{ border: "1px solid var(--line)", borderRadius: 8, overflow: "hidden", background: "var(--bg-elev)" }}>
          <table style={{ width: "100%", fontSize: 12.5, borderCollapse: "separate", borderSpacing: 0 }}>
            <thead>
              <tr style={{ background: "var(--bg-page)" }}>
                {[
                  { l: "产品",      w: "auto", a: "left" },
                  { l: "已发 / 可发", w: 96,     a: "center" },
                  { l: "本次发货",   w: 88,     a: "right" },
                  { l: "序列号(SN)", w: 280,   a: "left" },
                ].map((h, i) => (
                  <th key={i} style={{
                    textAlign: h.a, padding: "10px 14px 12px",
                    fontSize: 10.5, fontWeight: 500,
                    color: "var(--ink-4)", letterSpacing: "0.06em", textTransform: "uppercase",
                    width: h.w, whiteSpace: "nowrap",
                    borderBottom: "1px solid var(--line)",
                  }}>{h.l}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((it, i) => {
                const q = Number(qty[i]) || 0;
                const isSkip = !!skipSn[i];
                const startNum = Number(snStart[i] || 0);
                const pad     = (snStart[i] || "001").length;
                const endStr  = String(startNum + Math.max(q - 1, 0)).padStart(pad, "0");
                return (
                  <tr key={i} style={{ borderTop: i === 0 ? "0" : "1px solid var(--line-soft)" }}>
                    {/* Product */}
                    <td style={{ padding: "14px 14px", verticalAlign: "top" }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>{it.desc}</div>
                      <div className="mono" style={{ fontSize: 11.5, color: "var(--ink-3)", marginTop: 2 }}>{it.model}</div>
                      {it.spec && <div className="dim" style={{ fontSize: 11, marginTop: 3, lineHeight: 1.4 }}>{it.spec}</div>}
                    </td>

                    {/* 已发 / 可发 */}
                    <td style={{ padding: "14px 14px", textAlign: "center", verticalAlign: "top" }}>
                      <div className="mono tab-num" style={{ fontSize: 13, color: "var(--ink-2)" }}>
                        <span className="dim">{it.shipped}</span>
                        <span className="dim" style={{ margin: "0 4px" }}>/</span>
                        <span style={{ color: "var(--success)" }}>{it.avail}</span>
                      </div>
                    </td>

                    {/* Quantity input (plain) */}
                    <td style={{ padding: "14px 12px", textAlign: "right", verticalAlign: "top" }}>
                      <input
                        value={qty[i]}
                        onChange={e => {
                          const n = Math.max(0, Math.min(it.avail, Number(e.target.value) || 0));
                          setQty({ ...qty, [i]: n });
                        }}
                        className="mono tab-num"
                        style={{
                          width: 64, height: 30, padding: "0 8px", textAlign: "right",
                          border: "1px solid var(--line-2)", borderRadius: 4,
                          background: "var(--bg-elev)", outline: "none", fontSize: 13,
                        }}
                      />
                    </td>

                    {/* SN editor — inline, compact */}
                    <td style={{ padding: "14px 14px", verticalAlign: "top" }}>
                      {isSkip ? (
                        <div className="dim" style={{ fontSize: 12, paddingTop: 6 }}>无需序列号</div>
                      ) : (
                        <>
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <input
                              value={snPrefix[i]} onChange={e => setSnPrefix({ ...snPrefix, [i]: e.target.value })}
                              className="mono"
                              placeholder="前缀"
                              style={{
                                flex: 1, minWidth: 0, height: 30, padding: "0 8px",
                                border: "1px solid var(--line-2)", borderRadius: 4,
                                background: "var(--bg-elev)", outline: "none", fontSize: 12,
                              }}
                            />
                            <input
                              value={snStart[i]} onChange={e => setSnStart({ ...snStart, [i]: e.target.value })}
                              className="mono tab-num"
                              placeholder="起始"
                              style={{
                                width: 64, height: 30, padding: "0 8px",
                                border: "1px solid var(--line-2)", borderRadius: 4,
                                background: "var(--bg-elev)", outline: "none", fontSize: 12,
                              }}
                            />
                          </div>
                          {q > 0 && (
                            <div className="mono" style={{ fontSize: 10.5, color: "var(--ink-3)", marginTop: 5, letterSpacing: "0.02em" }}>
                              → {snPrefix[i]}{snStart[i]}
                              {q > 1 && <> … {snPrefix[i]}{endStr}</>}
                            </div>
                          )}
                        </>
                      )}
                      <label style={{
                        display: "inline-flex", alignItems: "center", gap: 5, marginTop: 6,
                        fontSize: 11, color: "var(--ink-3)", cursor: "pointer",
                        userSelect: "none",
                      }}>
                        <input
                          type="checkbox" checked={isSkip}
                          onChange={e => setSkipSn({ ...skipSn, [i]: e.target.checked })}
                          style={{ accentColor: "var(--accent)" }}
                        />
                        无序列号
                      </label>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Field>

      {/* Logistics */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <Field label="承运商">
          <Input placeholder="如:顺丰速运" style={{ width: "100%" }} />
        </Field>
        <Field label="运单号">
          <Input placeholder="如:SF1234567890" style={{ width: "100%" }} />
        </Field>
      </div>
    </ModalShell>
  );
}

/* ─── Quantity stepper ─────────────────────────────────────── */

function Stepper({ value, onChange, min = 0, max = 99 }) {
  const v = Number(value) || 0;
  const dec = () => onChange(Math.max(min, v - 1));
  const inc = () => onChange(Math.min(max, v + 1));
  return (
    <div style={{
      display: "inline-flex", alignItems: "center",
      border: "1px solid var(--line-2)", borderRadius: 6,
      background: "var(--bg-elev)", overflow: "hidden",
    }}>
      <button onClick={dec} style={{
        width: 28, height: 30, color: "var(--ink-3)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>−</button>
      <input
        value={v} onChange={e => onChange(Math.max(min, Math.min(max, Number(e.target.value) || 0)))}
        className="mono tab-num"
        style={{
          width: 44, height: 30, textAlign: "center", border: "0", outline: "none",
          borderLeft: "1px solid var(--line)", borderRight: "1px solid var(--line)",
          background: "transparent", fontSize: 13,
        }}
      />
      <button onClick={inc} style={{
        width: 28, height: 30, color: "var(--ink-3)",
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>+</button>
    </div>
  );
}

/* ─── File preview modal ───────────────────────────────────── */

function fmtFileSize(b) {
  if (b == null) return "";
  if (b < 1024) return b + " B";
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + " KB";
  return (b / 1024 / 1024).toFixed(1) + " MB";
}

const FILE_ICON = {
  pdf:  { icon: "file", color: "#A23B3B", tint: "#F0DAD8", label: "PDF" },
  zip:  { icon: "file", color: "#7A5AE0", tint: "#E2DCF5", label: "ZIP" },
  img:  { icon: "file", color: "#2F7155", tint: "#DCE8E0", label: "IMG" },
  jpg:  { icon: "file", color: "#2F7155", tint: "#DCE8E0", label: "JPG" },
  png:  { icon: "file", color: "#2F7155", tint: "#DCE8E0", label: "PNG" },
  doc:  { icon: "file", color: "#2A5F8F", tint: "#DDE6F1", label: "DOC" },
};

function FilePreviewModal({ open, title, stageLabel, files, onClose }) {
  const [activeIdx, setActiveIdx] = useState(0);
  useEffect(() => { setActiveIdx(0); }, [open]);
  const file = files?.[activeIdx];
  if (!open) return null;

  return (
    <ModalShell
      open={open} onClose={onClose}
      title={title || "附件预览"}
      icon="file"
      width={files?.length > 1 ? 820 : 580}
      footer={<>
        <Btn variant="ghost" onClick={onClose}>关闭</Btn>
        <Btn variant="accent" iconL="download">下载</Btn>
      </>}
    >
      {stageLabel && (
        <div style={{ marginBottom: 14 }}>
          <Pill tone="mute" size="md">
            阶段 · {stageLabel}
          </Pill>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: files?.length > 1 ? "200px 1fr" : "1fr", gap: 16, minHeight: 0 }}>
        {/* File list (when multiple) */}
        {files?.length > 1 && (
          <div style={{ borderRight: "1px solid var(--line)", paddingRight: 12 }}>
            <div className="mono dim" style={{ fontSize: 10.5, letterSpacing: "0.1em", marginBottom: 10 }}>
              文件 · {files.length}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {files.map((f, i) => {
                const ext = (f.type || f.name?.split(".").pop() || "").toLowerCase();
                const meta = FILE_ICON[ext] || FILE_ICON.doc;
                const active = i === activeIdx;
                return (
                  <button key={i} onClick={() => setActiveIdx(i)}
                    style={{
                      display: "flex", alignItems: "center", gap: 10,
                      padding: "8px 10px", borderRadius: 6,
                      textAlign: "left", background: active ? "var(--bg-active)" : "transparent",
                      border: active ? "1px solid var(--line-2)" : "1px solid transparent",
                    }}>
                    <span style={{
                      width: 26, height: 30, borderRadius: 4,
                      background: meta.tint, color: meta.color,
                      display: "inline-flex", alignItems: "center", justifyContent: "center",
                      fontSize: 9, fontWeight: 600, letterSpacing: "0.04em",
                      fontFamily: "var(--font-mono)",
                      flexShrink: 0,
                    }}>{meta.label}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, fontWeight: 500, color: "var(--ink-2)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{f.name}</div>
                      <div className="dim mono" style={{ fontSize: 10.5, marginTop: 1 }}>{fmtFileSize(f.size)}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Preview pane */}
        <div>
          <FilePreviewPane file={file} />
        </div>
      </div>
    </ModalShell>
  );
}

function FilePreviewPane({ file }) {
  if (!file) return <div className="dim" style={{ padding: 40, textAlign: "center" }}>无文件</div>;
  const ext = (file.type || file.name?.split(".").pop() || "").toLowerCase();
  const meta = FILE_ICON[ext] || FILE_ICON.doc;
  return (
    <div>
      <div style={{
        background: "var(--bg-page)",
        border: "1px dashed var(--line-2)",
        borderRadius: 8,
        height: 320, display: "flex",
        alignItems: "center", justifyContent: "center",
        flexDirection: "column", gap: 10,
        position: "relative",
      }}>
        <div style={{
          width: 56, height: 70, borderRadius: 8,
          background: meta.tint, color: meta.color,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 14, letterSpacing: "0.05em",
        }}>{meta.label}</div>
        <div className="dim" style={{ fontSize: 12 }}>文件预览(示意)</div>
      </div>

      <div style={{
        marginTop: 14, padding: "10px 14px",
        background: "var(--bg-page)", borderRadius: 8, border: "1px solid var(--line)",
        display: "flex", alignItems: "center", gap: 12,
      }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {file.name}
          </div>
          <div className="dim mono tab-num" style={{ fontSize: 11, marginTop: 2 }}>
            {fmtFileSize(file.size)}
          </div>
        </div>
        <Btn variant="ghost" size="sm" iconL="download">下载</Btn>
      </div>
    </div>
  );
}

Object.assign(window, {
  SupplierConfirmModal, UploadTestModal, CreateShipmentModal,
  FilePreviewModal, fmtFileSize,
});
