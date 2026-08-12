/**
 * components/ResultCard.jsx
 * Équivalent React de la fonction show_result() de app.py (Streamlit).
 */

import { useState } from "react";

export default function ResultCard({ result }) {
  const [showCorrections, setShowCorrections] = useState(false);
  const [showStandards, setShowStandards] = useState(false);

  if (!result) return null;

  const confidence = Math.round(result.score_confiance * 100);
  const confidenceColor =
    confidence >= 85
      ? "text-emerald-600 dark:text-emerald-400"
      : confidence >= 65
        ? "text-amber-600 dark:text-amber-400"
        : "text-red-500 dark:text-red-400";

  const kpiCard =
    "rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-white)] p-4 text-center shadow-sm dark:border-slate-600 dark:bg-slate-800/70";

  return (
    <div className="mt-6 space-y-4">
      <hr className="border-[var(--medical-gray-100)] dark:border-slate-600" />

      {/* ── KPIs ── */}
      <div className="grid grid-cols-3 gap-4">
        <div className={kpiCard}>
          <p className="mb-1 text-xs text-slate-500 dark:text-slate-400">Confiance</p>
          <p className={`text-2xl font-bold ${confidenceColor}`}>{confidence}%</p>
        </div>
        <div className={kpiCard}>
          <p className="mb-1 text-xs text-slate-500 dark:text-slate-400">Temps</p>
          <p className="text-2xl font-bold text-[var(--medical-primary)] dark:text-sky-400">
            {Math.round(result.temps_ms)} ms
          </p>
        </div>
        <div className={kpiCard}>
          <p className="mb-1 text-xs text-slate-500 dark:text-slate-400">Corrections</p>
          <p className="text-2xl font-bold text-violet-600 dark:text-violet-400">
            {result.corrections_appliquees.length}
          </p>
        </div>
      </div>

      {/* ── Type + modèle ── */}
      <div className="rounded-xl border border-sky-200 bg-sky-50 p-4 dark:border-sky-800 dark:bg-sky-950/40">
        <h3 className="font-semibold text-sky-900 dark:text-sky-100">{result.type_document}</h3>
        <p className="mt-1 text-xs text-sky-600 dark:text-sky-400">Modèle : {result.modele}</p>
      </div>

      {/* ── Transcription Whisper ── */}
      {result.transcription_whisper && (
        <div className="rounded-xl border border-[var(--medical-gray-100)] bg-slate-50 p-4 dark:border-slate-600 dark:bg-slate-900/50">
          <p className="mb-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
            Transcription Whisper (texte brut)
          </p>
          <p className="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">
            {result.transcription_whisper}
          </p>
        </div>
      )}

      {/* ── Texte corrigé ── */}
      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
          Texte corrigé
        </label>
        <textarea
          readOnly
          value={result.texte_corrige}
          rows={8}
          className="w-full resize-none rounded-xl border border-slate-300 bg-[var(--medical-white)] p-3 text-sm text-slate-800 focus:outline-none dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-100"
        />
      </div>

      {/* ── Corrections ── */}
      {result.corrections_appliquees.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-[var(--medical-gray-100)] dark:border-slate-600">
          <button
            type="button"
            onClick={() => setShowCorrections(!showCorrections)}
            className="flex w-full items-center justify-between bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:bg-slate-800/80 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <span>Corrections appliquées ({result.corrections_appliquees.length})</span>
            <span aria-hidden>{showCorrections ? "▲" : "▼"}</span>
          </button>
          {showCorrections && (
            <ul className="space-y-1 bg-[var(--medical-white)] px-4 py-3 text-sm text-slate-600 dark:bg-slate-900/40 dark:text-slate-300">
              {result.corrections_appliquees.map((c, i) => (
                <li key={i}>• {c}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* ── Standardisations ── */}
      {result.standardisations.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-[var(--medical-gray-100)] dark:border-slate-600">
          <button
            type="button"
            onClick={() => setShowStandards(!showStandards)}
            className="flex w-full items-center justify-between bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:bg-slate-800/80 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            <span>Standardisations médicales ({result.standardisations.length})</span>
            <span aria-hidden>{showStandards ? "▲" : "▼"}</span>
          </button>
          {showStandards && (
            <ul className="space-y-1 bg-[var(--medical-white)] px-4 py-3 text-sm text-slate-600 dark:bg-slate-900/40 dark:text-slate-300">
              {result.standardisations.map((s, i) => (
                <li key={i}>• {s}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
