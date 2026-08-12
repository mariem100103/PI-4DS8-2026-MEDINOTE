// src/pages/ImageOcr.jsx

import React, { useState, useRef } from "react";
import { ocrImage, analyzeText } from "../api/client";
import ResultCard from "../components/ResultCardMedical";

export default function ImageOcr({ onSaveHistory }) {
  const [files, setFiles]       = useState([]);
  const [ocrTexts, setOcrTexts] = useState({});
  const [loading, setLoading]   = useState({});
  const [result, setResult]     = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError]       = useState("");
  const inputRef = useRef();

  const handleFiles = (e) => {
    const selected = Array.from(e.target.files);
    setFiles(selected);
    setOcrTexts({});
    setResult(null);

    selected.forEach(async (file, idx) => {
      setLoading(prev => ({ ...prev, [idx]: true }));
      try {
        const data = await ocrImage(file);
        setOcrTexts(prev => ({ ...prev, [idx]: data.text || "" }));
      } catch (e) {
        setOcrTexts(prev => ({ ...prev, [idx]: "" }));
      } finally {
        setLoading(prev => ({ ...prev, [idx]: false }));
      }
    });
  };

  const handleAnalyze = async () => {
    const combined = Object.values(ocrTexts).join("\n\n");
    if (!combined.trim()) return;
    setAnalyzing(true);
    setError("");
    try {
      const data = await analyzeText(combined);
      setResult(data);
      onSaveHistory?.([data], `OCR (${files.length} image(s))`);
    } catch (e) {
      setError(e.message);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--medical-primary-dark)", marginBottom: 16 }}>
        🖼️ OCR — Images manuscrites
      </h2>

      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        style={{
          border: "2px dashed var(--medical-primary-medium)", borderRadius: 12,
          padding: "32px 24px", textAlign: "center",
          cursor: "pointer", background: "var(--medical-primary-light)",
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 32, marginBottom: 8 }}>📷</div>
        <div style={{ color: "var(--medical-primary)", fontWeight: 600 }}>
          Cliquez pour sélectionner des images (JPG, PNG)
        </div>
        <div style={{ color: "var(--medical-gray-500)", fontSize: 13, marginTop: 4 }}>
          Plusieurs fichiers acceptés
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png"
          multiple
          style={{ display: "none" }}
          onChange={handleFiles}
        />
      </div>

      {/* Images + OCR texts */}
      {files.map((file, idx) => (
        <div key={idx} style={{
          border: "1px solid var(--medical-gray-100)", borderRadius: 10,
          padding: 16, marginBottom: 16, background: "var(--medical-white)",
        }}>
          <div style={{ fontWeight: 600, marginBottom: 12, color: "var(--medical-gray-900)" }}>
            📷 {file.name}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <img
              src={URL.createObjectURL(file)}
              alt={file.name}
              style={{ width: "100%", borderRadius: 8, objectFit: "contain", maxHeight: 200 }}
            />
            <div>
              {loading[idx] ? (
                <div style={{ color: "var(--medical-gray-500)", fontSize: 13, paddingTop: 20 }}>
                  ⏳ OCR en cours...
                </div>
              ) : (
                <textarea
                  value={ocrTexts[idx] || ""}
                  onChange={e => setOcrTexts(prev => ({ ...prev, [idx]: e.target.value }))}
                  placeholder="Texte extrait par OCR..."
                  style={{
                    width: "100%", height: 150, padding: "8px 12px",
                    border: "1px solid var(--medical-gray-100)", borderRadius: 8,
                    fontFamily: "monospace", fontSize: 13, resize: "vertical",
                    boxSizing: "border-box",
                  }}
                />
              )}
              {ocrTexts[idx] && (
                <div style={{ fontSize: 11, color: "var(--medical-success)", marginTop: 4 }}>
                  ✅ Groq (Llama 4 Scout)
                </div>
              )}
            </div>
          </div>
        </div>
      ))}

      {Object.keys(ocrTexts).length > 0 && (
        <div style={{ display: "flex", justifyContent: "center", marginTop: 8 }}>
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
            {analyzing ? "⏳ Analyse..." : `🧠 Analyser les images (${files.length})`}
          </button>
        </div>
      )}

      {error && (
        <div style={{ background: "var(--medical-danger-light)", color: "var(--medical-danger)", borderRadius: 8, padding: "10px 16px", marginTop: 16 }}>
          ❌ {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 24 }}>
          <ResultCard result={result} source={`OCR (${files.length} image(s))`} />
        </div>
      )}
    </div>
  );
}
