// src/components/ResultCard.jsx — VERSION FIXÉE

import React from "react";

const sentimentConfig = {
  positif: { bg: "var(--medical-success-light)", fg: "var(--medical-success)", emoji: "😊" },
  négatif: { bg: "var(--medical-danger-light)",  fg: "var(--medical-danger)",  emoji: "😟" },
  neutre:  { bg: "var(--medical-gray-50)",       fg: "var(--medical-gray-500)", emoji: "😐" },
};

function Badge({ label, bg, fg }) {
  return (
    <span
      style={{
        display: "inline-block",
        background: bg,
        color: fg,
        borderRadius: 20,
        padding: "4px 14px",
        fontSize: 13,
        margin: 3,
        fontWeight: 500,
      }}
    >
      {label}
    </span>
  );
}

export default function ResultCard({ result, source = "", visitIdx = null }) {
  if (!result) return null;

  // ✅ SAFE DEFAULTS (IMPORTANT FIX)
  const {
    Médicaments = [],
    Médecins = [],
    Effets = {},
    Sentiment = "neutre",
    Catégorie = "—",
    Résumé = "",
    Fiche_visite = {},
  } = result || {};

  const meds = Array.isArray(Médicaments) ? Médicaments : [];
  const docs = Array.isArray(Médecins) ? Médecins : [];
  const effets = Effets && typeof Effets === "object" ? Effets : {};
  const fiche = Fiche_visite && typeof Fiche_visite === "object" ? Fiche_visite : {};

  const sent = sentimentConfig[Sentiment] || sentimentConfig.neutre;

  const ficheEntries = Object.entries(fiche).filter(
    ([, v]) => v != null && String(v).trim() !== ""
  );

  return (
    <div style={{
      border: "1.5px solid var(--medical-gray-100)",
      borderRadius: 14,
      overflow: "hidden",
      boxShadow: "0 2px 12px rgba(0,102,204,0.08)",
      marginBottom: 24,
    }}>

      {/* HEADER */}
      <div style={{
        background: "linear-gradient(135deg, var(--medical-primary), var(--medical-primary-medium))",
        padding: "14px 20px",
        color: "white",
        display: "flex",
        justifyContent: "space-between",
      }}>
        <div>
          {visitIdx && (
            <div style={{ fontSize: 11, opacity: 0.7 }}>
              Visite {visitIdx}
            </div>
          )}

          <div style={{ fontSize: 15, fontWeight: 700 }}>
            {docs.length > 0 ? docs.join(" · ") : source || "Note médicale"}
          </div>
        </div>

        <span style={{
          background: "rgba(255,255,255,0.18)",
          borderRadius: 20,
          padding: "3px 14px",
          fontSize: 12,
        }}>
          {Catégorie}
        </span>
      </div>

      {/* BODY */}
      <div style={{ padding: "16px 20px" }}>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

          {/* MEDICAMENTS */}
          <div>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
              💊 Médicaments
            </div>

            {meds.length > 0 ? (
              meds.map((m) => (
                <Badge key={m} label={m} bg="var(--medical-primary-light)" fg="var(--medical-primary)" />
              ))
            ) : (
              <span style={{ color: "var(--medical-gray-500)", fontSize: 13 }}>
                Aucun détecté
              </span>
            )}
          </div>

          {/* SENTIMENT */}
          <div>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
              😊 Sentiment
            </div>

            <div style={{
              background: sent.bg,
              color: sent.fg,
              borderRadius: 8,
              padding: "8px 14px",
              display: "inline-block",
            }}>
              {sent.emoji}{" "}
              {Sentiment.charAt(0).toUpperCase() + Sentiment.slice(1)}
            </div>
          </div>

        </div>

        {/* EFFETS */}
        <div style={{ marginTop: 14 }}>
          <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
            ⚠️ Effets secondaires
          </div>

          {Object.keys(effets).length > 0 ? (
            Object.entries(effets).map(([k, v]) => (
              <Badge
                key={k}
                label={`⚠️ ${k}`}
                bg="#FEF3C7"
                fg="#B45309"
              />
            ))
          ) : (
            <span style={{ color: "var(--medical-gray-500)", fontSize: 13 }}>
              Aucun identifié
            </span>
          )}
        </div>

        {/* FICHE */}
        {ficheEntries.length > 0 && (
          <div style={{
            marginTop: 14,
            background: "var(--medical-gray-50)",
            padding: 12,
            borderRadius: 10,
          }}>
            <strong>📋 Fiche visite</strong>

            {ficheEntries.map(([k, v]) => (
              <div key={k} style={{ marginTop: 6 }}>
                <b>{k}:</b> {v}
              </div>
            ))}
          </div>
        )}

        {/* RESUME */}
        <div style={{ marginTop: 16 }}>
          <div style={{ fontWeight: 600, fontSize: 13 }}>
            📝 Résumé
          </div>

          <div style={{
            background: "var(--medical-primary-light)",
            padding: 12,
            borderRadius: 8,
            marginTop: 6,
          }}>
            {Résumé || "Aucun résumé disponible"}
          </div>
        </div>

      </div>
    </div>
  );
}