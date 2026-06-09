/* ─────────────────────────────────────────────────────────────
   PMA · Toast + Inline validation system
   ───────────────────────────────────────────────────────────── */

const ToastContext = React.createContext(null);

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const idRef = useRef(0);

  const push = useCallback((t) => {
    const id = ++idRef.current;
    const toast = {
      id,
      tone: t.tone || "info",
      title: t.title || "",
      desc: t.desc || "",
      duration: t.duration ?? 3200,
    };
    setToasts(arr => [...arr, toast]);
    if (toast.duration > 0) {
      setTimeout(() => setToasts(arr => arr.filter(x => x.id !== id)), toast.duration);
    }
    return id;
  }, []);
  const dismiss = useCallback((id) => setToasts(arr => arr.filter(x => x.id !== id)), []);

  // expose to global
  useEffect(() => {
    window.toast = {
      info:    (title, desc) => push({ tone: "info",    title, desc }),
      success: (title, desc) => push({ tone: "success", title, desc }),
      warn:    (title, desc) => push({ tone: "warn",    title, desc }),
      error:   (title, desc) => push({ tone: "error",   title, desc }),
    };
  }, [push]);

  return (
    <ToastContext.Provider value={{ push, dismiss }}>
      {children}
      <ToastStack toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

const useToast = () => React.useContext(ToastContext);

function ToastStack({ toasts, onDismiss }) {
  return (
    <div style={{
      position: "fixed", top: 32, left: 0, right: 0,
      display: "flex", flexDirection: "column", alignItems: "center", gap: 10,
      pointerEvents: "none", zIndex: 2000,
    }}>
      {toasts.map((t, i) => (
        <ToastItem key={t.id} toast={t} onDismiss={() => onDismiss(t.id)} index={i} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onDismiss }) {
  const tone = toast.tone;
  const meta = {
    info:    { bg: "#1A2F49", fg: "#FFFFFF", accent: "#7AB5F0", icon: "info"   },
    success: { bg: "#2F5A45", fg: "#FFFFFF", accent: "#85E0B2", icon: "check"  },
    warn:    { bg: "#7A4914", fg: "#FFFFFF", accent: "#F2B96F", icon: "clock"  },
    error:   { bg: "#7A2C2C", fg: "#FFFFFF", accent: "#F08080", icon: "cancel" },
  }[tone] || {};

  return (
    <div
      role="status"
      style={{
        pointerEvents: "auto",
        minWidth: 360, maxWidth: 520,
        display: "flex", alignItems: "flex-start", gap: 14,
        background: meta.bg, color: meta.fg,
        border: "1px solid rgba(255,255,255,0.08)",
        boxShadow: "0 24px 60px rgba(31,30,27,0.30), 0 4px 12px rgba(31,30,27,0.18)",
        borderRadius: 12, padding: "16px 18px 16px 14px",
        animation: "toast-in 280ms cubic-bezier(.2,.7,.2,1)",
        position: "relative", overflow: "hidden",
      }}
    >
      {/* Left accent bar */}
      <span style={{
        position: "absolute", left: 0, top: 0, bottom: 0,
        width: 4, background: meta.accent,
      }} />
      <span style={{
        width: 30, height: 30, borderRadius: 8, flexShrink: 0,
        background: `${meta.accent}22`,
        color: meta.accent,
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        marginLeft: 4,
      }}>
        <Icon name={meta.icon} size={16} />
      </span>
      <div style={{ flex: 1, minWidth: 0, paddingTop: 2 }}>
        <div style={{ fontSize: 14.5, fontWeight: 600, lineHeight: 1.35, letterSpacing: "0.01em" }}>{toast.title}</div>
        {toast.desc && <div style={{ fontSize: 12.5, marginTop: 4, lineHeight: 1.5, color: "rgba(255,255,255,0.78)" }}>{toast.desc}</div>}
      </div>
      <button onClick={onDismiss} style={{
        color: "rgba(255,255,255,0.55)", padding: 4, borderRadius: 4, flexShrink: 0,
        transition: "color 120ms",
      }}
        onMouseEnter={e => e.currentTarget.style.color = "#fff"}
        onMouseLeave={e => e.currentTarget.style.color = "rgba(255,255,255,0.55)"}
        title="关闭">
        <Icon name="close" size={14} />
      </button>
    </div>
  );
}

/* Inline field error markup */
function FieldError({ children }) {
  if (!children) return null;
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      marginTop: 6, color: "var(--danger)", fontSize: 11.5,
    }}>
      <span style={{ display: "inline-flex" }}>
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h0"/>
        </svg>
      </span>
      {children}
    </div>
  );
}

Object.assign(window, { ToastProvider, useToast, FieldError });
