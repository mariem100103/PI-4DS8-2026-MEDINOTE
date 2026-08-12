// src/pages/TextAnalyze.jsx

import React, { useState } from "react";
import { analyzeText } from "../api/client";
import ResultCard from "../components/ResultCardMedical";

const PLACEHOLDER = `Exemples :

• Le patient présente des nausées suite à la prise de Doliprane 1000 mg.
• Amélioration sous Amoxicilline, pas d'effets secondaires.
• Dr. Martin prescrit Kardégic pour l'hypertension. Fatigue légère.`;

export default function TextAnalyze({ onSaveHistory }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!text.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await analyzeText(text);

      console.log("BACKEND RESPONSE:", data); // 🔍 debug

      const safeData = data || {}; // 🔐 anti-crash

      setResult(safeData);
      onSaveHistory?.([safeData], "Texte saisi");

    } catch (e) {
      setError(e?.message || "Erreur serveur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--medical-primary-dark)", marginBottom: 16 }}>
        ✍️ Analyse de texte
      </h2>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={PLACEHOLDER}
        style={{
          width: "100%",
          minHeight: 200,
          padding: "12px 16px",
          border: "1.5px solid var(--medical-gray-100)",
          borderRadius: 10,
          fontFamily: "monospace",
          fontSize: 14,
          resize: "vertical",
          outline: "none",
          boxSizing: "border-box",
        }}
      />

      <div style={{ display: "flex", justifyContent: "center", marginTop: 12 }}>
        <button
          onClick={handleAnalyze}
          disabled={loading || !text.trim()}
          style={{
            background: loading ? "var(--medical-primary-medium)" : "var(--medical-primary)",
            color: "white",
            border: "none",
            borderRadius: 8,
            padding: "10px 32px",
            fontWeight: 600,
            fontSize: 15,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "⏳ Analyse en cours..." : "🔍 Analyser"}
        </button>
      </div>

      {error && (
        <div
          style={{
            background: "var(--medical-danger-light)",
            color: "var(--medical-danger)",
            borderRadius: 8,
            padding: "10px 16px",
            marginTop: 16,
          }}
        >
          ❌ {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 24 }}>
          <ResultCard result={result} source="Texte saisi" />
        </div>
      )}
    </div>
  );
}