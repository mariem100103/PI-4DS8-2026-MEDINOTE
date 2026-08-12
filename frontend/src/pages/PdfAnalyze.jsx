// src/pages/PdfAnalyze.jsx

import React, { useState, useRef } from "react";
import { ocrPdf, analyzeMulti } from "../api/client";
import ResultCard from "../components/ResultCardMedical";

function MultiSummaryBanner({ count, summary, filename }) {
  return (
    <div style={{
      background: "linear-gradient(135deg, var(--medical-primary), var(--medical-primary-medium))",
      borderRadius: 12, padding: "18px 24px", marginBottom: 20, color: "white",
    }}>
      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 10 }}>
        📄 {filename} — {count} visite{count > 1 ? "s" : ""} analysée{count > 1 ? "s" : ""}
      </div>
      <div style={{ display: "flex", gap: 32, flexWrap: "wrap", fontSize: 13, opacity: 0.92 }}>
        <span>👨‍⚕️ <b>{summary.all_doctors.length}</b> médecin{summary.all_doctors.length > 1 ? "s" : ""}</span>
        <span>💊 <b>{summary.all_drugs.length}</b> médicament{summary.all_drugs.length > 1 ? "s" : ""}</span>
        <span>😊 <b>{summary.positive}</b> positif{summary.positive > 1 ? "s" : ""}</span>
        <span>😟 <b>{summary.negative}</b> négatif{summary.negative > 1 ? "s" : ""}</span>
      </div>
    </div>
  );
}

export default function PdfAnalyze({ onSaveHistory }) {
  const [file, setFile]         = useState(null);
  const [rawText, setRawText]   = useState("");
  const [extracted, setExtracted] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [results, setResults]   = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError]       = useState("");
  const inputRef = useRef();

  const handleFile = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setRawText("");
    setExtracted(false);
    setResults(null);
    setError("");

    setExtracting(true);
    try {
      const data = await ocrPdf(f);
      setRawText(data.text);
      setExtracted(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setExtracting(false);
    }
  };

  const handleAnalyze = async () => {
    if (!rawText) return;
    setAnalyzing(true);
    setProgress(0);
    setError("");
    try {
      const data = await analyzeMulti(rawText, true);
      setResults(data);
      onSaveHistory?.(data?.notes || [], `PDF · ${file?.name || "document"}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--medical-primary-dark)", marginBottom: 16 }}>
        📄 Extraction depuis PDF
      </h2>

      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        style={{
          border: "2px dashed var(--medical-primary-medium)", borderRadius: 12,
          padding: "32px 24px", textAlign: "center",
          cursor: "pointer", background: "var(--medical-primary-light)", marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 32, marginBottom: 8 }}>📄</div>
        <div style={{ color: "var(--medical-primary)", fontWeight: 600 }}>
          {file ? file.name : "Cliquez pour sélectionner un PDF"}
        </div>
        {!file && (
          <div style={{ color: "var(--medical-gray-500)", fontSize: 13, marginTop: 4 }}>
            Supports le texte natif + OCR pour les pages scannées
          </div>
        )}
        <input ref={inputRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={handleFile} />
      </div>

      {extracting && (
        <div style={{ textAlign: "center", color: "var(--medical-primary)", fontSize: 14, padding: "12px 0" }}>
          ⏳ Extraction du texte en cours...
        </div>
      )}

      {extracted && rawText && (
        <div>
          <div style={{
            background: "var(--medical-success-light)", color: "var(--medical-success)",
            borderRadius: 8, padding: "8px 16px", marginBottom: 12, fontSize: 13,
          }}>
            ✅ {rawText.length} caractères extraits
          </div>

          <details style={{ marginBottom: 16 }}>
            <summary style={{ cursor: "pointer", fontWeight: 600, fontSize: 13, color: "var(--medical-gray-900)" }}>
              📄 Aperçu du texte brut
            </summary>
            <pre style={{
              background: "var(--medical-gray-50)", borderRadius: 8,
              padding: "12px", fontSize: 12, overflow: "auto",
              maxHeight: 200, marginTop: 8,
            }}>
              {rawText.slice(0, 1000)}{rawText.length > 1000 ? "..." : ""}
            </pre>
          </details>

          <div style={{ display: "flex", justifyContent: "center" }}>
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              style={{
                background: analyzing ? "var(--medical-primary-medium)" : "var(--medical-primary)",
                color: "white", border: "none", borderRadius: 8,
                padding: "10px 32px", fontWeight: 600, fontSize: 15,
                cursor: analyzing ? "not-allowed" : "pointer",
              }}
            >
              {analyzing ? "⏳ Analyse en cours..." : "🧠 Analyser le PDF"}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div style={{ background: "var(--medical-danger-light)", color: "var(--medical-danger)", borderRadius: 8, padding: "10px 16px", marginTop: 16 }}>
          ❌ {error}
        </div>
      )}

      {results && (
        <div style={{ marginTop: 24 }}>
          {results.count > 1 && (
            <MultiSummaryBanner
              count={results.count}
              summary={results.summary}
              filename={file?.name || "PDF"}
            />
          )}

          {results.count > 1 ? (
            <>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "var(--medical-primary-dark)", marginBottom: 16 }}>
                🗂️ Détail des {results.count} visites
              </h3>
              {results.notes.map((r, i) => (
                <ResultCard key={i} result={r} visitIdx={i + 1} source={file?.name} />
              ))}
            </>
          ) : (
            <ResultCard result={results.notes[0]} source={`PDF · ${file?.name}`} />
          )}
        </div>
      )}
    </div>
  );
}
