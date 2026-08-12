import React, { useMemo, useState } from "react";
import { Trash2 } from "lucide-react";
import TextAnalyze from "./TextAnalyze";
import ImageOcr from "./ImageOcr";
import PdfAnalyze from "./PdfAnalyze";
import {
  appendHistory, buildHistoryEntry,
  loadHistory, removeHistoryItem, saveHistory,
} from "../utils/history";

// ─────────────────────────────────────────────────────────────
// Design tokens — thème blanc/clair style ALIA CRM
// ─────────────────────────────────────────────────────────────
const T = {
  bg:        "var(--medical-gray-50)",
  surface:   "var(--medical-white)",
  surfaceHov:"var(--medical-primary-light)",
  border:    "var(--medical-gray-100)",
  borderFoc: "var(--medical-primary-medium)",
  accent:    "var(--medical-primary)",
  accentSoft:"rgba(0,102,204,0.10)",
  accent2:   "var(--medical-success)",
  accent2Soft:"rgba(16,185,129,0.10)",
  text:      "var(--medical-gray-900)",
  textMid:   "var(--medical-gray-500)",
  muted:     "var(--medical-gray-500)",
  danger:    "var(--medical-danger)",
  dangerSoft:"rgba(239,68,68,0.08)",
  radius:    12,
  font:      "Inter, 'Segoe UI', sans-serif",
  fontHead:  "Inter, 'Segoe UI', sans-serif",
  shadow:    "0 1px 4px rgba(0,102,204,0.06), 0 4px 16px rgba(0,102,204,0.04)",
  shadowMd:  "0 2px 8px rgba(0,102,204,0.08), 0 8px 32px rgba(0,102,204,0.05)",
};

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────
const TABS = [
  { id: "text",  label: "Texte",  icon: "✍️" },
  { id: "image", label: "Image",  icon: "🖼️" },
  { id: "pdf",   label: "PDF",    icon: "📄" },
];

const BADGE_COLOR = {
  text:  { bg: "rgba(0,102,204,0.10)",  color: "var(--medical-primary)",      label: "✍️ texte"  },
  image: { bg: "rgba(16,185,129,0.10)", color: "var(--medical-success)",      label: "🖼️ image"  },
  pdf:   { bg: "rgba(245,158,11,0.10)", color: "var(--medical-warning)",      label: "📄 pdf"    },
};

// ─────────────────────────────────────────────────────────────
// Styles inline
// ─────────────────────────────────────────────────────────────
const S = {
  layout: {
    display: "grid",
    gridTemplateColumns: "260px 1fr",
    height: "min(920px, calc(100dvh - 7rem))",
    maxHeight: "calc(100dvh - 7rem)",
    fontFamily: T.font,
    background: T.bg,
    color: T.text,
    overflow: "hidden",
    borderRadius: 12,
    border: `1px solid ${T.border}`,
  },

  /* ── SIDEBAR ── */
  sidebar: {
    background: T.surface,
    borderRight: `1px solid ${T.border}`,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    boxShadow: "1px 0 0 var(--medical-gray-100)",
  },
  sidebarHeader: {
    padding: "20px 18px 16px",
    borderBottom: `1px solid ${T.border}`,
  },
  logoRow: {
    display: "flex", alignItems: "center", gap: 10, marginBottom: 3,
  },
  logoIcon: {
    width: 34, height: 34,
    background: `linear-gradient(135deg, ${T.accent}, ${T.accent2})`,
    borderRadius: 9,
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 15, flexShrink: 0,
    boxShadow: "0 2px 8px rgba(91,123,255,0.25)",
  },
  logoName: {
    fontFamily: T.fontHead, fontWeight: 800, fontSize: 17,
    color: T.text, letterSpacing: -0.3,
  },
  logoSub: {
    fontSize: 10.5, color: T.muted, marginLeft: 44,
    letterSpacing: "0.5px", textTransform: "uppercase", fontWeight: 500,
  },

  sidebarBody: {
    flex: 1, overflowY: "auto", padding: "14px 10px",
  },
  histTitle: {
    fontSize: 10, fontWeight: 700,
    color: T.muted, letterSpacing: "1px", textTransform: "uppercase",
    marginBottom: 8, padding: "0 6px",
  },
  histEmpty: {
    textAlign: "center", padding: "28px 12px",
    color: T.muted, fontSize: 12.5, lineHeight: 1.7,
  },
  histCard: (hovered) => ({
    background: hovered ? T.surfaceHov : T.surface,
    border: `1px solid ${hovered ? T.borderFoc + "55" : T.border}`,
    borderRadius: T.radius,
    padding: "9px 11px",
    marginBottom: 6,
    cursor: "pointer",
    position: "relative",
    transition: "all 0.15s ease",
    boxShadow: hovered ? "0 2px 8px rgba(91,123,255,0.08)" : "none",
  }),
  histBadge: (source) => ({
    display: "inline-flex", alignItems: "center", gap: 3,
    fontSize: 9.5, fontWeight: 700,
    padding: "2px 7px", borderRadius: 20,
    marginBottom: 4,
    textTransform: "uppercase", letterSpacing: "0.3px",
    background: (BADGE_COLOR[source] || BADGE_COLOR.text).bg,
    color:      (BADGE_COLOR[source] || BADGE_COLOR.text).color,
  }),
  histCategory: { fontSize: 12.5, fontWeight: 500, color: T.text, marginBottom: 1 },
  histDate:     { fontSize: 10.5, color: T.muted },
  histDel: (hovered) => ({
    position: "absolute", top: 8, right: 8,
    background: hovered ? T.dangerSoft : "none",
    border: "none", cursor: "pointer",
    color: hovered ? T.danger : T.muted,
    fontSize: 15, padding: "1px 5px",
    borderRadius: 6, lineHeight: 1,
    transition: "all 0.15s",
  }),

  sidebarFooter: {
    padding: "10px 12px 14px", borderTop: `1px solid ${T.border}`,
  },
  btnClear: {
    width: "100%", padding: "8px",
    background: T.dangerSoft,
    border: `1px solid rgba(245,101,101,0.15)`,
    borderRadius: 9, color: T.danger,
    fontFamily: T.font, fontSize: 12, fontWeight: 600,
    cursor: "pointer",
    transition: "background 0.15s",
  },

  /* ── MAIN ── */
  main: {
    display: "flex", flexDirection: "column",
    overflow: "hidden", background: T.bg,
  },
  mainInner: {
    display: "flex", flexDirection: "column", height: "100%",
  },

  topbar: {
    padding: "22px 28px 0",
    display: "flex", alignItems: "flex-start", justifyContent: "space-between",
    borderBottom: `1px solid ${T.border}`,
    paddingBottom: 18,
    background: T.surface,
    boxShadow: T.shadow,
  },
  pageTitle: {
    fontFamily: T.fontHead, fontSize: 22, fontWeight: 800,
    letterSpacing: -0.4, lineHeight: 1, color: T.text,
  },
  pageTitleAccent: {
    background: `linear-gradient(90deg, ${T.accent}, ${T.accent2})`,
    WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
  },
  pageSub: { fontSize: 12.5, color: T.muted, marginTop: 3, fontWeight: 400 },

  statusPill: {
    display: "flex", alignItems: "center", gap: 6,
    background: "rgba(16,185,129,0.08)",
    border: "1px solid rgba(16,185,129,0.2)",
    borderRadius: 20, padding: "5px 12px",
    fontSize: 12, color: "var(--medical-success)", fontWeight: 600,
  },
  dot: {
    width: 7, height: 7, borderRadius: "50%",
    background: T.accent2,
    boxShadow: `0 0 0 2px rgba(16,185,129,0.2)`,
  },

  /* ── TABS ── */
  tabNav: {
    margin: "0 28px",
    display: "flex", gap: 2,
    borderBottom: `1px solid ${T.border}`,
    background: "transparent",
  },
  tabBtn: (active) => ({
    height: 44, padding: "0 18px",
    border: "none",
    borderBottom: active ? `2px solid ${T.accent}` : "2px solid transparent",
    background: "transparent",
    color: active ? T.accent : T.muted,
    fontFamily: T.font, fontSize: 13, fontWeight: active ? 700 : 500,
    cursor: "pointer",
    transition: "all 0.18s",
    display: "flex", alignItems: "center", gap: 6,
    whiteSpace: "nowrap",
    marginBottom: -1,
  }),

  /* ── CONTENT ── */
  contentArea: {
    flex: 1,
    padding: "22px 28px 22px",
    overflowY: "auto",
    background: T.bg,
  },
  panel: {
    background: T.surface,
    border: `1px solid ${T.border}`,
    borderRadius: 16, padding: 26,
    minHeight: 300,
    boxShadow: T.shadow,
    animation: "fadeUp 0.25s ease both",
  },
};

// ─────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────
function PulsingDot() {
  const [opacity, setOpacity] = React.useState(1);
  React.useEffect(() => {
    const id = setInterval(() => setOpacity(o => o === 1 ? 0.35 : 1), 1000);
    return () => clearInterval(id);
  }, []);
  return <div style={{ ...S.dot, opacity, transition: "opacity 1s" }} />;
}

function HistCard({ item, onDelete }) {
  const [hCard,  setHCard]  = React.useState(false);
  const [hDel,   setHDel]   = React.useState(false);
  const [dying,  setDying]  = React.useState(false);

  const handleDelete = (e) => {
    e.stopPropagation();
    setDying(true);
    setTimeout(() => onDelete(item.id), 200);
  };

  const src  = item.source || "text";
  const badge = (BADGE_COLOR[src] || BADGE_COLOR.text).label;
  const date  = item.date
    ? new Date(item.date).toLocaleString("fr-FR", {
        hour: "2-digit", minute: "2-digit",
        day: "2-digit", month: "2-digit",
      })
    : "";

  return (
    <div
      style={{
        ...S.histCard(hCard),
        opacity: dying ? 0 : 1,
        transform: dying ? "translateX(-10px)" : "none",
        transition: "opacity 0.2s, transform 0.2s, all 0.15s ease",
      }}
      onMouseEnter={() => setHCard(true)}
      onMouseLeave={() => setHCard(false)}
    >
      <span style={S.histBadge(src)}>{badge}</span>
      <div style={S.histCategory}>{item.category || "Note médicale"}</div>
      {date && <div style={S.histDate}>{date}</div>}
      <button
        style={S.histDel(hDel)}
        onMouseEnter={() => setHDel(true)}
        onMouseLeave={() => setHDel(false)}
        onClick={handleDelete}
        title="Supprimer"
      >×</button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Main component
// ─────────────────────────────────────────────────────────────
export default function ExtractionPage() {
  const [tab,     setTab]     = useState("text");
  const [history, setHistory] = useState(() => loadHistory());

  const onSaveHistory = (results, source) => {
    const entries = (results || []).map((r) => buildHistoryEntry(r, source));
    const updated = appendHistory(entries);
    setHistory(updated);
  };

  const clearHistory = () => { saveHistory([]); setHistory([]); };

  const deleteHistoryEntry = (id) => {
    const updated = removeHistoryItem(id);
    setHistory(updated);
  };

  const historyPreview = useMemo(() => history.slice(0, 8), [history]);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700;800&display=swap');
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--medical-gray-100); border-radius: 4px; }
      `}</style>

      <div style={S.layout}>

        {/* ── SIDEBAR ── */}
        <aside style={S.sidebar}>
          <div style={S.sidebarBody}>
            <div style={S.histTitle}>Historique récent</div>

            {historyPreview.length === 0 ? (
              <div style={S.histEmpty}>
                Aucune analyse<br />pour le moment
              </div>
            ) : (
              historyPreview.map((item) => (
                <HistCard key={item.id} item={item} onDelete={deleteHistoryEntry} />
              ))
            )}
          </div>

          <div style={S.sidebarFooter}>
            <button type="button" style={S.btnClear} onClick={clearHistory}>
              <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 6 }}>
                <Trash2 size={14} aria-hidden />
                Vider l&apos;historique
              </span>
            </button>
          </div>
        </aside>

        {/* ── MAIN ── */}
        <main style={S.main}>
          <div style={S.mainInner}>

            {/* Topbar */}
            <div style={S.topbar}>
              <div>
                <div style={S.pageTitle}>
                  Extraction{" "}
                  <span style={S.pageTitleAccent}>intelligente</span>
                </div>
                <div style={S.pageSub}>Analyse automatique des notes médicales par IA</div>
              </div>
              <div style={S.statusPill}>
                <PulsingDot />
                Modèle actif
              </div>
            </div>

            {/* Tab nav */}
            <div style={{ background: T.surface, paddingLeft: 28, paddingRight: 28, borderBottom: `1px solid ${T.border}` }}>
              <div style={{ display: "flex", gap: 2 }}>
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    style={S.tabBtn(tab === t.id)}
                    onClick={() => setTab(t.id)}
                  >
                    <span>{t.icon}</span>
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Content panels */}
            <div style={S.contentArea}>
              <div style={S.panel} key={tab}>
                {tab === "text"  && <TextAnalyze  onSaveHistory={onSaveHistory} />}
                {tab === "image" && <ImageOcr     onSaveHistory={onSaveHistory} />}
                {tab === "pdf"   && <PdfAnalyze   onSaveHistory={onSaveHistory} />}
              </div>
            </div>

          </div>
        </main>
      </div>
    </>
  );
}