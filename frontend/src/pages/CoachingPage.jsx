/**
 * pages/CoachingPage.jsx
 * Migration exacte de coaching_app.py (Streamlit) vers React.
 * Même scénarios, même niveaux, même logique de feedback.
 */

import { useState, useEffect, useRef } from "react";
import { Flag, Lightbulb, Loader2, PanelLeft, RotateCcw, Send, Target } from "lucide-react";
import { getScenarios, getLevels, sendMessage } from "../api/coachingApi";

// ── Helpers ────────────────────────────────────────────────────
function scoreColor(s) {
  if (s == null) return "#6b7280";
  if (s >= 7) return "#15803d";
  if (s >= 5) return "#854d0e";
  return "#991b1b";
}

function isFinalScore(feedback) {
  if (!feedback) return false;
  return ["🏆", "Points forts", "Impression générale", "NOTE FINALE", "bilan complet"].some(
    (kw) => feedback.includes(kw)
  );
}

function FeedbackBox({ feedback }) {
  if (!feedback) return null;
  if (isFinalScore(feedback)) {
    return (
      <div className="mt-2 ml-12 whitespace-pre-wrap rounded-xl border-2 border-emerald-500 bg-emerald-50 p-4 text-sm text-emerald-950 dark:border-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-100">
        <p className="mb-2 font-bold text-emerald-800 dark:text-emerald-300">Bilan de visite</p>
        {feedback}
      </div>
    );
  }
  return (
    <div className="mt-2 ml-12 whitespace-pre-wrap rounded-lg border-l-4 border-amber-400 bg-amber-50 px-4 py-3 text-sm text-slate-800 dark:bg-amber-950/30 dark:text-amber-100">
      <span className="font-bold text-amber-900 dark:text-amber-300">Coach : </span>
      {feedback}
    </div>
  );
}

// ── Composant principal ────────────────────────────────────────
export default function CoachingPage() {
  const [scenarios, setScenarios] = useState({});
  const [levels, setLevels] = useState({});
  const [scenarioKey, setScenarioKey] = useState("💬 Discussion libre");
  const [level, setLevel] = useState(1);
  const [history, setHistory] = useState([]);
  const [turns, setTurns] = useState(0);
  const [scores, setScores] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const bottomRef = useRef(null);

  // Charge scénarios + niveaux au démarrage
  useEffect(() => {
    getScenarios().then(setScenarios).catch(console.error);
    getLevels().then(setLevels).catch(console.error);
  }, []);

  // Initialise le chat quand le scénario change
  useEffect(() => {
    if (!scenarios[scenarioKey]) return;
    const sc = scenarios[scenarioKey];
    setHistory([{ role: "assistant", content: sc.doc_init, feedback: null }]);
    setTurns(0);
    setScores([]);
    setError(null);
  }, [scenarioKey, scenarios]);

  // Scroll vers le bas à chaque nouveau message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const sc = scenarios[scenarioKey];
  const lv = levels[String(level)];
  const isLibre = scenarioKey === "💬 Discussion libre";
  const avgScore = scores.length ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : null;
  const lastScore = scores.length ? scores[scores.length - 1] : null;

  const handleSend = async (userContent, forceFinal = false) => {
    if (!userContent.trim() && !forceFinal) return;
    setError(null);

    const newHistory = forceFinal
      ? [...history, { role: "user", content: userContent, feedback: null }]
      : [...history, { role: "user", content: userContent, feedback: null }];

    setHistory(newHistory);
    setTurns((t) => t + 1);
    setInput("");
    setLoading(true);

    try {
      const apiHistory = newHistory.map((m) => ({ role: m.role, content: m.content }));
      const res = await sendMessage(apiHistory, scenarioKey, level, forceFinal);
      setHistory((h) => [
        ...h,
        { role: "assistant", content: res.doc_reply, feedback: res.feedback },
      ]);
      if (res.score != null) setScores((s) => [...s, res.score]);
    } catch (e) {
      const msg = e.message || "";
      if (msg.includes("429") || msg.includes("rate_limit")) {
        setError("⏳ Limite atteinte. Attendez quelques secondes et réessayez.");
      } else if (msg.includes("401") || msg.includes("authentication")) {
        setError("🔑 Clé API invalide. Vérifiez GROQ_API_KEY_COACHING dans .env");
      } else {
        setError(`❌ Erreur : ${msg}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = () => {
    handleSend("Au revoir docteur, merci pour votre temps.", true);
  };

  const handleReset = () => {
    if (!sc) return;
    setHistory([{ role: "assistant", content: sc.doc_init, feedback: null }]);
    setTurns(0);
    setScores([]);
    setError(null);
  };

  if (!sc || !lv) {
    return (
      <div className="flex h-64 items-center justify-center gap-3 text-slate-500 dark:text-slate-400">
        <Loader2 className="h-8 w-8 animate-spin" aria-hidden />
        <span>Chargement…</span>
      </div>
    );
  }

  return (
    <div className="flex min-h-[min(680px,calc(100dvh-7rem))] max-h-[calc(100dvh-7rem)] overflow-hidden rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-gray-50)] dark:border-slate-600 dark:bg-slate-950">
      {/* ── SIDEBAR ── */}
      <div className={`${sidebarOpen ? "w-64" : "w-0"} flex-shrink-0 overflow-hidden transition-all duration-200`}>
        <div className="flex h-full w-64 flex-col overflow-y-auto border-r border-[var(--medical-gray-100)] bg-[var(--medical-white)] dark:border-slate-700 dark:bg-slate-900">
          <div className="space-y-4 p-4">
            {/* Niveau */}
            <div>
              <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                <Target className="h-3.5 w-3.5" aria-hidden />
                Niveau
              </p>
              {Object.entries(levels).map(([id, lv]) => (
                <button
                  key={id}
                  onClick={() => { setLevel(Number(id)); handleReset(); }}
                  className={`mb-1 w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                    level === Number(id)
                      ? "bg-[var(--medical-blue)]/15 font-semibold text-[var(--medical-blue-dark)] dark:bg-sky-500/20 dark:text-sky-200"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`}
                >
                  {lv.label}
                </button>
              ))}
            </div>

            <hr className="border-[var(--medical-gray-100)] dark:border-slate-700" />

            {/* Discussion libre — clé API inchangée */}
            <div>
              <p className="mb-2 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Discussion
              </p>
              <button
                type="button"
                onClick={() => setScenarioKey("💬 Discussion libre")}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                  scenarioKey === "💬 Discussion libre"
                    ? "bg-[var(--medical-blue)]/15 font-semibold text-[var(--medical-blue-dark)] dark:bg-sky-500/20 dark:text-sky-200"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                }`}
              >
                💬 Discussion libre
              </button>
            </div>

            <hr className="border-[var(--medical-gray-100)] dark:border-slate-700" />

            {/* Scénarios guidés — libellés backend */}
            <div>
              <p className="mb-2 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                Scénarios
              </p>
              {Object.keys(scenarios)
                .filter((k) => k !== "💬 Discussion libre")
                .map((key) => (
                  <button
                    type="button"
                    key={key}
                    onClick={() => setScenarioKey(key)}
                    className={`mb-1 w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                      scenarioKey === key
                        ? "bg-[var(--medical-blue)]/15 font-semibold text-[var(--medical-blue-dark)] dark:bg-sky-500/20 dark:text-sky-200"
                        : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                    }`}
                  >
                    {key}
                  </button>
                ))}
            </div>

            <hr className="border-[var(--medical-gray-100)] dark:border-slate-700" />

            <button
              type="button"
              onClick={handleReset}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              <RotateCcw className="h-4 w-4 shrink-0" aria-hidden />
              Recommencer
            </button>

            <hr className="border-[var(--medical-gray-100)] dark:border-slate-700" />

            {/* Hints */}
            <div>
              <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                <Lightbulb className="h-3.5 w-3.5" aria-hidden />
                Idées
              </p>
              {sc.hints.map((h, i) => (
                <p key={i} className="mb-1 text-xs text-slate-500 dark:text-slate-400">
                  • {h}
                </p>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── CONTENU PRINCIPAL ── */}
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-[var(--medical-gray-100)] bg-[var(--medical-white)] px-4 py-3 dark:border-slate-700 dark:bg-slate-900">
          <button
            type="button"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
            aria-label="Ouvrir ou fermer le panneau"
          >
            <PanelLeft className="h-5 w-5" aria-hidden />
          </button>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--medical-blue)]/15 text-xs font-bold text-[var(--medical-blue-dark)] dark:bg-sky-500/20 dark:text-sky-200">
            {sc.doc_initials}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
              {sc.doc_name} — {sc.doc_role}
              <span
                className={`ml-2 inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                  level === 1
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200"
                    : level === 2
                      ? "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200"
                      : "bg-rose-100 text-rose-800 dark:bg-rose-900/50 dark:text-rose-200"
                }`}
              >
                {lv.label}
              </span>
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400">{lv.description}</p>
          </div>

          {/* Stats */}
          <div className="ml-auto flex gap-4">
            {[
              { val: avgScore ? `${avgScore}/10` : "—", lbl: "Score moyen", color: scoreColor(avgScore) },
              { val: turns, lbl: "Échanges", color: null },
              { val: lastScore ? `${lastScore}/10` : "—", lbl: "Dernier score", color: scoreColor(lastScore) },
            ].map(({ val, lbl, color }) => (
              <div key={lbl} className="hidden text-center sm:block">
                <p
                  className={`text-lg font-bold ${color ? "" : "text-slate-900 dark:text-slate-100"}`}
                  style={color ? { color } : undefined}
                >
                  {val}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">{lbl}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Info discussion libre */}
        {isLibre && (
          <div className="mx-4 mt-3 flex items-center gap-2 rounded-xl border border-sky-200 bg-sky-50 px-4 py-2 text-sm text-sky-900 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-100">
            Discussion libre — parlez librement. Utilisez{" "}
            <strong className="font-semibold">Finir la discussion</strong> pour obtenir votre note finale.
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
          {history.map((msg, i) => (
            <div key={i}>
              {msg.role === "assistant" ? (
                <div className="flex items-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--medical-blue)]/15 text-xs font-bold text-[var(--medical-blue-dark)] dark:bg-sky-500/20 dark:text-sky-200">
                    {sc.doc_initials}
                  </div>
                  <div className="max-w-[75%] rounded-2xl border border-[var(--medical-gray-100)] bg-[var(--medical-white)] px-4 py-2.5 text-sm text-slate-800 shadow-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
                    {msg.content}
                  </div>
                </div>
              ) : (
                <div className="flex flex-row-reverse items-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200">
                    DM
                  </div>
                  <div className="max-w-[75%] rounded-2xl border border-sky-200 bg-sky-50 px-4 py-2.5 text-sm text-sky-950 dark:border-sky-800 dark:bg-sky-950/40 dark:text-sky-100">
                    {msg.content}
                  </div>
                </div>
              )}
              {msg.feedback && <FeedbackBox feedback={msg.feedback} />}
            </div>
          ))}

          {loading && (
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--medical-blue)]/15 text-xs font-bold text-[var(--medical-blue-dark)] dark:bg-sky-500/20 dark:text-sky-200">
                {sc.doc_initials}
              </div>
              <div className="flex items-center gap-2 rounded-2xl border border-[var(--medical-gray-100)] bg-[var(--medical-white)] px-4 py-2.5 text-sm text-slate-500 shadow-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-400">
                <Loader2 className="h-4 w-4 shrink-0 animate-spin" aria-hidden />
                Le médecin réfléchit…
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Zone de saisie */}
        <div className="space-y-2 border-t border-[var(--medical-gray-100)] bg-[var(--medical-white)] px-4 py-3 dark:border-slate-700 dark:bg-slate-900">
          {isLibre && (
            <button
              type="button"
              onClick={handleFinish}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--medical-gray-200)] px-4 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <Flag className="h-4 w-4 shrink-0" aria-hidden />
              Finir la discussion
            </button>
          )}
          <div className="flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend(input);
                }
              }}
              placeholder="Tapez ce que vous diriez au médecin… (Entrée pour envoyer)"
              rows={2}
              disabled={loading}
              className="medical-form flex-1 resize-none rounded-xl border border-[var(--medical-gray-200)] bg-[var(--medical-white)] px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[var(--medical-blue)] disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500"
            />
            <button
              type="button"
              onClick={() => handleSend(input)}
              disabled={loading || !input.trim()}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-[var(--medical-blue)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50 dark:bg-sky-600"
            >
              <Send className="h-4 w-4" aria-hidden />
              Envoyer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}