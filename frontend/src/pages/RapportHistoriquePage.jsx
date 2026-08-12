import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import html2pdf from "html2pdf.js";

import {
  FileSpreadsheet,
  Trash2,
  RefreshCcw,
  FileText,
  Calendar,
  Pencil,
  FileDown,
} from "lucide-react";

import {
  getRapports,
  getRapport,
  deleteRapport,
  exportRapportXlsx,
  downloadRapportXlsx,
} from "../api/rapportApi.js";

export default function RapportHistoriquePage() {
  const navigate = useNavigate();

  const [rapports, setRapports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function chargerRapports() {
    setLoading(true);
    setMessage("");

    try {
      const data = await getRapports();
      setRapports(data);
    } catch (error) {
      setMessage("Erreur chargement historique: " + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function supprimerRapport(reportId) {
    const reason = prompt("Pourquoi supprimer ce rapport ?");
    if (!reason) return;

    try {
      await deleteRapport(reportId, reason);
      await chargerRapports();
    } catch (error) {
      setMessage("Erreur suppression: " + error.message);
    }
  }

  async function telechargerXlsx(report) {
    try {
      setMessage("Préparation XLSX...");

      if (!report.xlsx_path) {
        await exportRapportXlsx(report.id);
        await chargerRapports();
      }

      downloadRapportXlsx(report.id);
      setMessage("Téléchargement XLSX lancé.");
    } catch (error) {
      setMessage("Erreur téléchargement XLSX: " + error.message);
    }
  }

  async function telechargerPdf(reportId) {
    try {
      setMessage("Préparation PDF...");

      const fullReport = await getRapport(reportId);
      const rapportJson = fullReport.report_json;

      if (!rapportJson) {
        setMessage("Ce rapport n'a pas encore de JSON généré.");
        return;
      }

      const element = document.createElement("div");
      element.innerHTML = buildRapportPdfHtml(rapportJson);
      element.style.padding = "20px";
      element.style.background = "white";

      const filename = `${fullReport.name || "rapport"}.pdf`;

      const options = {
        margin: 10,
        filename,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
      };

      await html2pdf().set(options).from(element).save();

      setMessage("PDF téléchargé.");
    } catch (error) {
      setMessage("Erreur téléchargement PDF: " + error.message);
    }
  }

  useEffect(() => {
    chargerRapports();
  }, []);

  return (
    <main className="page">
      {message && <div className="toast">{message}</div>}

      <header className="page-header">
        <div>
          <h1>Historique des rapports</h1>
          <p>Tous les rapports générés sont sauvegardés ici.</p>
        </div>

        <button className="small-btn" onClick={chargerRapports}>
          <RefreshCcw size={16} />
          Actualiser
        </button>
      </header>

      <section className="card">
        <table className="history-table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Fichier original</th>
              <th>Source</th>
              <th>Status</th>
              <th>Date création</th>
              <th>Qualité</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {loading && (
              <tr>
                <td colSpan="6" className="empty-row">
                  Chargement...
                </td>
              </tr>
            )}

            {!loading && rapports.length === 0 && (
              <tr>
                <td colSpan="6" className="empty-row">
                  Aucun rapport trouvé.
                </td>
              </tr>
            )}

            {!loading &&
              rapports.map((rapport) => (
                <tr key={rapport.id}>
                  <td>
                    <div className="cell-with-icon">
                      <FileText size={18} />
                      <span>{rapport.name}</span>
                    </div>
                  </td>

                  <td>{rapport.original_filename}</td>

                  <td>
                    <span className="source-badge">{rapport.source_type}</span>
                  </td>

                  <td>
                    <span className="status">{rapport.status}</span>
                  </td>

                  <td>
                    <div className="cell-with-icon">
                      <Calendar size={16} />
                      <span>{rapport.created_at}</span>
                    </div>
                  </td>
<td>
  <span className={getQualityClass(rapport.qualite_rapport)}>
    {rapport.qualite_rapport || "non généré"}
  </span>
</td>
                  <td className="table-actions">
                    <button
                      className="icon-btn warning"
                      onClick={() => navigate(`/rapport/${rapport.id}/modifier`)}
                      title="Modifier rapport"
                    >
                      <Pencil size={17} />
                      {/* <span>Modifier</span> */}
                    </button>

                    <button
                      className="icon-btn pdf"
                      onClick={() => telechargerPdf(rapport.id)}
                      title="Télécharger PDF"
                    >
                      <FileDown size={17} />
                      <span>PDF</span>
                    </button>

                    <button
                      className="icon-btn success"
                      onClick={() => telechargerXlsx(rapport)}
                      title="Télécharger XLSX"
                    >
                      <FileSpreadsheet size={17} />
                      <span>XLSX</span>
                    </button>

                    <button
                      className="icon-btn danger"
                      onClick={() => supprimerRapport(rapport.id)}
                      title="Supprimer rapport"
                    >
                      <Trash2 size={17} />
                      {/* <span>Supprimer</span> */}
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}

function buildRapportPdfHtml(rapport) {
  const produits = rapport.produits_presentes || [];

  const produitsRows = produits
    .map(
      (p) => `
        <tr>
          <td>${p.nom || "-"}</td>
          <td>${p.commentaire || "-"}</td>
          <td>${p.opportunites || "-"}</td>
          <td>${(p.benchmarking_concurrents || []).join(", ") || "-"}</td>
          <td>${p.nombre_echantillons ?? "-"}</td>
        </tr>
      `
    )
    .join("");

  return `
    <div style="font-family: Arial, sans-serif; color: #0f172a; padding: 20px;">
      <h1 style="text-align:center; margin-bottom: 5px;">
        RAPPORT DE VISITE MÉDICALE
      </h1>

      <p style="text-align:center; color:#64748b; margin-bottom: 30px;">
        Rapport généré par MediNote AI
      </p>

      <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:25px;">
        ${infoBox("Nom du prospect", rapport.nom_prospect)}
        ${infoBox("Date", rapport.date_visite)}
        ${infoBox("Superviseur", rapport.nom_superviseur)}
        ${infoBox("Patients présents", rapport.nombre_patients_presents)}
        ${infoBox("Date de relance", rapport.date_relance)}
        ${infoBox("Gadget", rapport.gadget)}
      </div>

      ${section("Objectif de la visite", rapport.objectif_visite)}

      <h2 style="border-bottom:1px solid #cbd5e1; padding-bottom:6px;">
        Produits présentés
      </h2>

      <table style="width:100%; border-collapse:collapse; font-size:12px; margin-bottom:20px;">
        <thead>
          <tr style="background:#f1f5f9;">
            <th style="border:1px solid #cbd5e1; padding:8px;">Produit</th>
            <th style="border:1px solid #cbd5e1; padding:8px;">Commentaire</th>
            <th style="border:1px solid #cbd5e1; padding:8px;">Opportunités</th>
            <th style="border:1px solid #cbd5e1; padding:8px;">Concurrents</th>
            <th style="border:1px solid #cbd5e1; padding:8px;">Échantillons</th>
          </tr>
        </thead>
        <tbody>
          ${
            produitsRows ||
            `<tr><td colspan="5" style="border:1px solid #cbd5e1; padding:8px;">Non mentionné</td></tr>`
          }
        </tbody>
      </table>

      ${section("Commentaire", rapport.commentaire)}
      ${section("Opportunités", rapport.opportunites)}
      ${section("Benchmarking concurrents", (rapport.benchmarking_concurrents || []).join(", "))}
      ${section("Remarque générale", rapport.remarque_generale)}
      ${section("Prochaine étape", rapport.prochaine_etape)}
    </div>
  `;
}

function infoBox(label, value) {
  return `
    <div style="border:1px solid #e2e8f0; border-radius:10px; padding:12px;">
      <div style="font-size:12px; color:#64748b;">${label}</div>
      <div style="font-weight:700; margin-top:4px;">${value || "Non mentionné"}</div>
    </div>
  `;
}
function getQualityClass(quality) {
  if (quality === "excellent") return "quality-badge excellent";
  if (quality === "bon") return "quality-badge good";
  if (quality === "moyen") return "quality-badge medium";
  return "quality-badge bad";
}
function section(title, value) {
  return `
    <div style="margin-bottom:20px;">
      <h2 style="font-size:18px; border-bottom:1px solid #cbd5e1; padding-bottom:6px;">
        ${title}
      </h2>
      <p style="font-size:14px; line-height:1.6;">
        ${value || "Non mentionné"}
      </p>
    </div>
  `;
}