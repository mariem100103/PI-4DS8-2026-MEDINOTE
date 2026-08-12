/**
 * pages/CorrecteurPage.jsx
 * Équivalent React complet de app.py (Streamlit).
 * Modes : saisie texte | import fichier audio
 */

import { useState, useRef, useEffect } from "react";
import { Loader2, Mic, PenLine, Trash2, FileAudio } from "lucide-react";
import {
  correctText,
  correctAudio,
  checkIntegrity,
  scoreQuality,
  generateReport,
  batchProcess,
  getIntegritySummary,
  appendReport,
} from "../api/correcteurApi";
import ResultCard from "../components/ResultCard";
import {
  FEATURE_PAGE_ROOT,
  FIELD_INPUT_CLASS,
  FeatureErrorBox,
  FeatureLoadingBanner,
} from "../components/FeaturePageChrome";
import { PageHeader } from "../components/ui";
import { useLanguage } from "../context/LanguageContext.jsx";

const PLACEHOLDER = `visite chez le dr martin cardiologue au CHU de lyon le 15/3/2025.
le medecin ma recu pendant 20 minute , il etais tres interesse par notre
novueau produit pour le traitment de l'hta . rdv prevu dans 6 semaines.`;

export default function CorrecteurPage() {
  const { t } = useLanguage();
  const [mode, setMode] = useState("text"); // "text" | "audio"
  const [texte, setTexte] = useState("");
  const [audioFile, setAudioFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastRawNote, setLastRawNote] = useState("");
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState(null);
  const [appendLoading, setAppendLoading] = useState(false);
  const [appendError, setAppendError] = useState(null);
  const [appendSuccess, setAppendSuccess] = useState(null);
  const [action, setAction] = useState(null);
  const [actionResult, setActionResult] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [batchFile, setBatchFile] = useState(null);
  const fileRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordedUrl, setRecordedUrl] = useState(null);
  const timer = useRecordingTimer(isRecording);

  const surfaceCard =
    "rounded-2xl border border-[var(--medical-gray-100)] bg-[var(--medical-white)] shadow-sm dark:border-slate-600 dark:bg-slate-800/70";
  const surfaceCardPad = `${surfaceCard} p-6 space-y-4`;
  const mutedText = "text-slate-600 dark:text-slate-300";
  const labelText = "block text-sm font-medium text-slate-700 dark:text-slate-200";

  const reset = () => { setResult(null); setError(null); };
  const resetSummary = () => {
    setSummary(null);
    setSummaryError(null);
    setSummaryLoading(false);
    setAppendLoading(false);
    setAppendError(null);
    setAppendSuccess(null);
  };
  const resetAction = () => {
    setActionResult(null);
    setActionError(null);
    setActionLoading(false);
    setAction(null);
    setBatchFile(null);
  };

  const getRawNote = () => {
    if (lastRawNote) return lastRawNote;
    if (result?.transcription_whisper) return result.transcription_whisper;
    if (result?.texte_original) return result.texte_original;
    return "";
  };

  const fetchSummary = async (rawNote) => {
    if (!rawNote) return;
    setSummaryLoading(true);
    setSummaryError(null);
    setSummary(null);
    try {
      const data = await getIntegritySummary(rawNote);
      setSummary(data);
    } catch (e) {
      setSummaryError(e.message);
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!texte.trim()) { setError("Veuillez saisir du texte."); return; }
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await correctText(texte);
      const raw = data.texte_original || texte;
      setResult(data);
      setLastRawNote(raw);
      resetAction();
      resetSummary();
      await fetchSummary(raw);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAudioSubmit = async () => {
    if (!audioFile) { setError("Veuillez sélectionner un fichier audio."); return; }
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await correctAudio(audioFile);
      setResult(data);
      const raw = data.transcription_whisper || data.texte_original || "";
      setLastRawNote(raw);
      resetAction();
      resetSummary();
      await fetchSummary(raw);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleModeChange = (m) => {
    setMode(m);
    reset();
    resetAction();
    resetSummary();
    setTexte("");
    setAudioFile(null);
    setRecordedBlob(null);
    setRecordedUrl(null);
    setIsRecording(false);
    setLastRawNote("");
  };

  const startRecording = async () => {
    setRecordedBlob(null);
    setRecordedUrl(null);
    chunksRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
        ? "audio/webm"
        : "audio/ogg";
      const mr = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mr;
      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const ext = mimeType.includes("ogg") ? "ogg" : "webm";
        const file = new File([blob], `enregistrement.${ext}`, { type: mimeType });
        const url = URL.createObjectURL(blob);
        setRecordedBlob(blob);
        setRecordedUrl(url);
        setAudioFile(file);
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start(250);
      setIsRecording(true);
    } catch (err) {
      setError("Impossible d'accéder au microphone.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleAppendReport = async () => {
    const rawNote = getRawNote();
    if (!rawNote) return;
    setAppendLoading(true);
    setAppendError(null);
    setAppendSuccess(null);
    try {
      const data = await appendReport(rawNote);
      setAppendSuccess(`Rapport ajoute. Total: ${data.reports_total}`);
    } catch (e) {
      setAppendError(e.message);
    } finally {
      setAppendLoading(false);
    }
  };

  const runAction = async (nextAction) => {
    setAction(nextAction);
    setActionResult(null);
    setActionError(null);

    if (nextAction === "batch") {
      setBatchFile(null);
      return;
    }

    const rawNote = getRawNote();
    if (!rawNote) {
      setActionError("Aucune note disponible pour l'analyse.");
      return;
    }

    setActionLoading(true);
    try {
      if (nextAction === "integrity") {
        const data = await checkIntegrity(rawNote);
        setActionResult(data);
      } else if (nextAction === "score") {
        const data = await scoreQuality(rawNote);
        setActionResult(data);
      } else if (nextAction === "report") {
        const data = await generateReport(rawNote);
        setActionResult(data);
      }
    } catch (e) {
      setActionError(e.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBatchFileChange = async (file) => {
    if (!file) return;
    setBatchFile(file);
    setActionLoading(true);
    setActionError(null);
    setActionResult(null);
    try {
      const data = await batchProcess(file);
      setActionResult(data);
    } catch (e) {
      setActionError(e.message);
    } finally {
      setActionLoading(false);
    }
  };

  const gradeColors = {
    A: "text-emerald-600",
    B: "text-green-600",
    C: "text-yellow-600",
    D: "text-orange-600",
    F: "text-red-600",
  };

  const correctionsList = result?.corrections_appliquees?.length
    ? result.corrections_appliquees
    : summary?.corrections_log || [];
  const standardsList = result?.standardisations?.length
    ? result.standardisations
    : summary?.standardisations || [];
  const alertItems = summary?.alerts || [];
  const errorAlerts = alertItems.filter((a) => a.severity === "ERROR");
  const warnAlerts = alertItems.filter((a) => a.severity === "WARNING");

  return (
    <div className={`${FEATURE_PAGE_ROOT} bg-[var(--medical-gray-50)] py-6 dark:bg-slate-950 md:py-8`}>
      <div className="mx-auto max-w-2xl px-2 sm:px-0">
        <PageHeader title={t("page.correcteur.title")} subtitle={t("page.correcteur.subtitle")} />

        {/* ── Mode toggle ── */}
        <div className="mb-6 flex overflow-hidden rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-white)] shadow-sm dark:border-slate-600 dark:bg-slate-800/70">
          {[
            { key: "text", label: "Saisie texte", Icon: PenLine },
            { key: "audio", label: "Entrée vocale", Icon: Mic },
          ].map(({ key, label, Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => handleModeChange(key)}
              className={`flex flex-1 items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors ${
                mode === key
                  ? "bg-[var(--medical-blue)] text-white dark:bg-sky-600"
                  : `${mutedText} hover:bg-slate-50 dark:hover:bg-slate-700/50`
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden />
              {label}
            </button>
          ))}
        </div>

        {/* ── Mode TEXTE ── */}
        {mode === "text" && (
          <div className={surfaceCardPad}>
            <label className={labelText}>
              Note médicale à corriger
            </label>
            <textarea
              value={texte}
              onChange={(e) => setTexte(e.target.value)}
              rows={8}
              placeholder={PLACEHOLDER}
              className={`medical-form resize-none ${FIELD_INPUT_CLASS} min-h-[180px]`}
            />
            <button
              type="button"
              onClick={handleTextSubmit}
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--medical-blue)] py-3 font-semibold text-white transition hover:opacity-90 disabled:opacity-50 dark:bg-sky-600"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                  Correction en cours…
                </>
              ) : (
                "Corriger le texte"
              )}
            </button>
          </div>
        )}

        {/* ── Mode AUDIO ── */}
        {mode === "audio" && (
          <div className={surfaceCardPad}>
            <label className={labelText}>
              Importer un fichier audio
            </label>

            {/* Drop zone */}
            <div
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") fileRef.current?.click();
              }}
              onClick={() => fileRef.current?.click()}
              className="cursor-pointer rounded-xl border-2 border-dashed border-slate-300 p-8 text-center transition hover:border-[var(--medical-blue)] hover:bg-sky-50/80 dark:border-slate-600 dark:hover:border-sky-500 dark:hover:bg-slate-800/80"
            >
              {audioFile ? (
                <p className="flex items-center justify-center gap-2 text-sm font-medium text-[var(--medical-blue-dark)] dark:text-sky-300">
                  <FileAudio className="h-5 w-5 shrink-0" aria-hidden />
                  {audioFile.name}
                </p>
              ) : (
                <>
                  <Mic className="mx-auto mb-2 h-10 w-10 text-slate-400 dark:text-slate-500" aria-hidden />
                  <p className={`text-sm ${mutedText}`}>
                    Cliquez ou glissez un fichier
                  </p>
                  <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                    mp3, wav, m4a, ogg, flac, webm
                  </p>
                </>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".mp3,.wav,.m4a,.ogg,.flac,.webm"
              className="hidden"
              onChange={(e) => { setAudioFile(e.target.files[0] || null); reset(); }}
            />

            {/* Lecteur audio inline */}
            {audioFile && (
              <audio
                controls
                src={URL.createObjectURL(audioFile)}
                className="w-full"
              />
            )}

            {/* Enregistrement micro */}
            <div className="space-y-3 rounded-xl border border-[var(--medical-gray-100)] p-4 dark:border-slate-600">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Enregistrer avec le microphone</p>
              <div className="flex items-center justify-between gap-4 px-2">
                <WaveformBars active={isRecording} />
                <span
                  className={`font-mono text-sm tabular-nums ${
                    isRecording ? "font-semibold text-red-600 dark:text-red-400" : "text-slate-400 dark:text-slate-500"
                  }`}
                >
                  {isRecording ? `● ${timer}` : recordedUrl ? "Enregistrement terminé" : "Prêt"}
                </span>
              </div>
              {!recordedUrl && (
                <button
                  type="button"
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`flex w-full items-center justify-center gap-2 rounded-xl py-3 font-semibold transition ${
                    isRecording
                      ? "bg-red-500 text-white hover:bg-red-600"
                      : "bg-slate-800 text-white hover:bg-slate-900 dark:bg-slate-700 dark:hover:bg-slate-600"
                  }`}
                >
                  {isRecording ? (
                    <>
                      <StopIcon className="h-4 w-4" />
                      Arrêter
                    </>
                  ) : (
                    <>
                      <MicIcon className="h-4 w-4" />
                      Démarrer
                    </>
                  )}
                </button>
              )}
              {recordedUrl && (
                <div className="space-y-3">
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200">
                    Enregistrement prêt
                  </div>
                  <audio controls src={recordedUrl} className="w-full" />
                  <button
                    type="button"
                    onClick={() => {
                      setRecordedBlob(null);
                      setRecordedUrl(null);
                      setAudioFile(null);
                    }}
                    className="flex w-full items-center justify-center gap-2 rounded-lg border border-[var(--medical-gray-200)] py-2 text-sm text-slate-600 transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden />
                    Supprimer et réenregistrer
                  </button>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleAudioSubmit}
              disabled={loading || !audioFile}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--medical-blue)] py-3 font-semibold text-white transition hover:opacity-90 disabled:opacity-50 dark:bg-sky-600"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                  Transcription et correction…
                </>
              ) : (
                <>
                  <Mic className="h-5 w-5 shrink-0" aria-hidden />
                  Transcrire et corriger
                </>
              )}
            </button>
          </div>
        )}

        {/* ── Erreur ── */}
        {error && (
          <FeatureErrorBox>
            {error}
          </FeatureErrorBox>
        )}

        {/* ── Résultat ── */}
        <ResultCard result={result} />

        {/* ── Synthese automatique ── */}
        {result && (
          <div className={`mt-6 p-5 ${surfaceCard}`}>
            {summaryLoading && (
              <FeatureLoadingBanner>
                <Loader2 className="h-5 w-5 shrink-0 animate-spin" aria-hidden />
                Analyse en cours…
              </FeatureLoadingBanner>
            )}

            {!summaryLoading && summaryError && (
              <FeatureErrorBox>{summaryError}</FeatureErrorBox>
            )}

            {!summaryLoading && summary && (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                      summary.status === "PASS"
                        ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200"
                        : "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200"
                    }`}
                  >
                    {summary.status}
                  </span>
                  <p className="text-sm text-slate-700 dark:text-slate-200">
                    Pénalité : <span className="font-semibold">{summary.penalty_score}</span>
                  </p>
                </div>

                <div>
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Champs en échec</p>
                  {summary.failed_fields?.length ? (
                    <ul className="list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                      {summary.failed_fields.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-slate-500 dark:text-slate-400">Aucun champ bloqué.</p>
                  )}
                </div>

                <div className="flex items-center gap-4">
                  <div
                    className={`text-5xl font-extrabold ${
                      gradeColors[summary.grade] || "text-slate-700 dark:text-slate-200"
                    }`}
                  >
                    {summary.grade}
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Score qualité</p>
                    <p className="text-2xl font-semibold text-slate-800 dark:text-slate-100">
                      {summary.quality_score}/100
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-xl border border-[var(--medical-gray-100)] bg-slate-50 p-4 dark:border-slate-600 dark:bg-slate-800/50">
                    <p className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-200">Alertes intégrité</p>
                    {alertItems.length === 0 && (
                      <p className="text-sm text-slate-500 dark:text-slate-400">Aucune alerte.</p>
                    )}
                    {alertItems.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {errorAlerts.map((a, i) => (
                          <span
                            key={`err-${i}`}
                            className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700"
                            title={a.message}
                          >
                            {a.field}
                          </span>
                        ))}
                        {warnAlerts.map((a, i) => (
                          <span
                            key={`warn-${i}`}
                            className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700"
                            title={a.message}
                          >
                            {a.field}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-white)] p-4 dark:border-slate-600 dark:bg-slate-900/40">
                    <p className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-200">Recommandations</p>
                    <ul className="max-h-40 list-disc overflow-auto pl-5 text-sm text-slate-600 dark:text-slate-300">
                      {summary.recommendations?.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-white)] p-4 dark:border-slate-600 dark:bg-slate-900/40">
                    <p className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-200">Corrections appliquées</p>
                    {correctionsList.length === 0 ? (
                      <p className="text-sm text-slate-500 dark:text-slate-400">Aucune correction.</p>
                    ) : (
                      <ul className="max-h-40 list-disc overflow-auto pl-5 text-sm text-slate-600 dark:text-slate-300">
                        {correctionsList.map((c, i) => (
                          <li key={i}>{c}</li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <div className="rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-white)] p-4 dark:border-slate-600 dark:bg-slate-900/40">
                    <p className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-200">Standardisations</p>
                    {standardsList.length === 0 ? (
                      <p className="text-sm text-slate-500 dark:text-slate-400">Aucune standardisation.</p>
                    ) : (
                      <ul className="max-h-40 list-disc overflow-auto pl-5 text-sm text-slate-600 dark:text-slate-300">
                        {standardsList.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>

                {summary.status === "PASS" && summary.draft_report && (
                  <div>
                    <p className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">Rapport généré</p>
                    <pre className="whitespace-pre-wrap rounded-xl border border-[var(--medical-gray-100)] bg-slate-50 p-3 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-200">
                      {summary.draft_report}
                    </pre>
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={handleAppendReport}
                    disabled={appendLoading || summary.status !== "PASS"}
                    className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 dark:bg-emerald-700"
                  >
                    {appendLoading ? (
                      <span className="inline-flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                        Ajout…
                      </span>
                    ) : (
                      "Ajouter au rapport"
                    )}
                  </button>
                  {appendSuccess && (
                    <p className="text-sm text-emerald-700 dark:text-emerald-400">{appendSuccess}</p>
                  )}
                  {appendError && (
                    <p className="text-sm text-red-700 dark:text-red-300">{appendError}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Actions avancées ── */}
        {result && (
          <div className="mt-6">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <button
                type="button"
                onClick={() => runAction("integrity")}
                className={`rounded-xl border py-2 text-sm font-semibold transition ${
                  action === "integrity"
                    ? "border-[var(--medical-blue)] bg-[var(--medical-blue)] text-white dark:border-sky-600 dark:bg-sky-600"
                    : "border-[var(--medical-gray-200)] bg-[var(--medical-white)] text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-200 dark:hover:bg-slate-700/50"
                }`}
              >
                Vérifier l&apos;intégrité
              </button>
              <button
                type="button"
                onClick={() => runAction("score")}
                className={`rounded-xl border py-2 text-sm font-semibold transition ${
                  action === "score"
                    ? "border-[var(--medical-blue)] bg-[var(--medical-blue)] text-white dark:border-sky-600 dark:bg-sky-600"
                    : "border-[var(--medical-gray-200)] bg-[var(--medical-white)] text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-200 dark:hover:bg-slate-700/50"
                }`}
              >
                Score qualité
              </button>
              <button
                type="button"
                onClick={() => runAction("report")}
                className={`rounded-xl border py-2 text-sm font-semibold transition ${
                  action === "report"
                    ? "border-[var(--medical-blue)] bg-[var(--medical-blue)] text-white dark:border-sky-600 dark:bg-sky-600"
                    : "border-[var(--medical-gray-200)] bg-[var(--medical-white)] text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-200 dark:hover:bg-slate-700/50"
                }`}
              >
                Générer rapport
              </button>
              <button
                type="button"
                onClick={() => runAction("batch")}
                className={`rounded-xl border py-2 text-sm font-semibold transition ${
                  action === "batch"
                    ? "border-[var(--medical-blue)] bg-[var(--medical-blue)] text-white dark:border-sky-600 dark:bg-sky-600"
                    : "border-[var(--medical-gray-200)] bg-[var(--medical-white)] text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-200 dark:hover:bg-slate-700/50"
                }`}
              >
                Traitement lot
              </button>
            </div>

            <div className={`mt-4 p-5 ${surfaceCard}`}>
              {actionLoading && (
                <FeatureLoadingBanner className="mt-0">
                  <Loader2 className="h-5 w-5 shrink-0 animate-spin" aria-hidden />
                  Traitement en cours…
                </FeatureLoadingBanner>
              )}

              {!actionLoading && action === "integrity" && actionResult && (
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        actionResult.status === "PASS"
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200"
                          : "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-200"
                      }`}
                    >
                      {actionResult.status}
                    </span>
                    <p className="text-sm text-slate-700 dark:text-slate-200">
                      Score pénalité : <span className="font-semibold">{actionResult.penalty_score}</span>
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Champs en échec</p>
                    {actionResult.failed_fields?.length ? (
                      <ul className="list-disc pl-5 text-sm text-slate-600 dark:text-slate-300">
                        {actionResult.failed_fields.map((f) => (
                          <li key={f}>{f}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-slate-500 dark:text-slate-400">Aucun champ bloqué.</p>
                    )}
                  </div>
                </div>
              )}

              {!actionLoading && action === "score" && actionResult && (
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-4">
                    <div
                      className={`text-5xl font-extrabold ${
                        gradeColors[actionResult.grade] || "text-slate-700 dark:text-slate-200"
                      }`}
                    >
                      {actionResult.grade}
                    </div>
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400">Score</p>
                      <p className="text-2xl font-semibold text-slate-800 dark:text-slate-100">
                        {actionResult.quality_score}/100
                      </p>
                    </div>
                  </div>
                  <div className="text-sm text-slate-600 dark:text-slate-300">
                    <p className="font-medium text-slate-700 dark:text-slate-200">Recommandations</p>
                    <ul className="list-disc pl-5">
                      {actionResult.recommendations?.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {!actionLoading && action === "report" && actionResult && (
                <div>
                  <p className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">Rapport généré</p>
                  <pre className="whitespace-pre-wrap rounded-xl border border-[var(--medical-gray-100)] bg-slate-50 p-3 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-200">
                    {actionResult.draft_report}
                  </pre>
                </div>
              )}

              {!actionLoading && action === "batch" && (
                <div className="space-y-3">
                  <label className={labelText}>
                    Importer un CSV
                  </label>
                  <input
                    type="file"
                    accept=".csv"
                    className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-sm dark:text-slate-300 dark:file:bg-slate-700 dark:file:text-slate-200"
                    onChange={(e) => handleBatchFileChange(e.target.files?.[0])}
                  />
                  {batchFile && (
                    <p className="text-xs text-slate-500 dark:text-slate-400">Fichier : {batchFile.name}</p>
                  )}
                  {actionResult?.processed !== undefined && (
                    <p className="text-sm text-slate-700 dark:text-slate-200">
                      {actionResult.processed} notes traitées
                    </p>
                  )}
                </div>
              )}

              {!actionLoading && actionError && (
                <div className="mt-3">
                  <FeatureErrorBox>{actionError}</FeatureErrorBox>
                </div>
              )}

              {!actionLoading && !action && (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Choisissez une action pour continuer.
                </p>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

function MicIcon({ className = "" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2H3v2a9 9 0 0 0 8 8.94V23h2v-2.06A9 9 0 0 0 21 12v-2h-2z" />
    </svg>
  );
}

function StopIcon({ className = "" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <rect x="4" y="4" width="16" height="16" rx="2" />
    </svg>
  );
}

function useRecordingTimer(isRecording) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!isRecording) {
      setSeconds(0);
      return;
    }
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [isRecording]);
  const mm = String(Math.floor(seconds / 60)).padStart(2, "0");
  const ss = String(seconds % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

function WaveformBars({ active }) {
  return (
    <div className="flex items-center gap-0.5 h-8">
      {Array.from({ length: 16 }).map((_, i) => (
        <div
          key={i}
          className={`w-1 rounded-full transition-all ${
            active ? "bg-red-500 animate-pulse" : "bg-gray-300"
          }`}
          style={{
            height: active ? `${20 + Math.sin(i * 0.8) * 14}px` : "6px",
            animationDelay: active ? `${i * 60}ms` : "0ms",
            animationDuration: active ? `${600 + (i % 3) * 200}ms` : "0ms",
          }}
        />
      ))}
    </div>
  );
}
