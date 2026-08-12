import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  uploadRapport,
  updateTexteExtrait,
  formatRapport,
  updateRapport,
  exportRapportXlsx,
  downloadRapportXlsx,
  getRapport,
} from "../api/rapportApi.js";

export default function RapportExtractionPage() {
  const { reportId: reportIdParam } = useParams();

  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [fileType, setFileType] = useState("");

  const [reportId, setReportId] = useState(null);
  const [texteExtrait, setTexteExtrait] = useState("");
  const [rapport, setRapport] = useState(null);

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const isEditMode = Boolean(reportIdParam);

  useEffect(() => {
    async function chargerRapportPourModification() {
      if (!reportIdParam) return;

      setLoading(true);
      setMessage("");

      try {
        const data = await getRapport(reportIdParam);

        setReportId(data.id);
        setTexteExtrait(data.extracted_text || "");
        setRapport(data.report_json || null);

        if (data.report_json) setStep(3);
        else if (data.extracted_text) setStep(2);
        else setStep(1);

        setMessage("Rapport chargé avec succès.");
      } catch (error) {
        setMessage("Erreur de chargement : " + error.message);
      } finally {
        setLoading(false);
      }
    }

    chargerRapportPourModification();
  }, [reportIdParam]);

  function choisirFichier(event) {
    const selectedFile = event.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
    setFileType(selectedFile.type);

    setReportId(null);
    setTexteExtrait("");
    setRapport(null);
    setStep(1);
    setMessage("");
  }

  async function lancerExtraction() {
    if (!file) return;

    setLoading(true);
    setMessage("");

    try {
      const result = await uploadRapport(file);

      setReportId(result.report_id);
      setTexteExtrait(result.extracted_text || "");
      setStep(2);
      setMessage("Texte extrait avec succès.");
    } catch (error) {
      setMessage("Erreur d’importation : " + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function genererRapport() {
    if (!reportId || !texteExtrait.trim()) return;

    setLoading(true);
    setMessage("");

    try {
      await updateTexteExtrait(reportId, texteExtrait);

      const result = await formatRapport(reportId);

      setRapport(result.data);
      setStep(3);
      setMessage("Rapport généré avec succès.");
    } catch (error) {
      setMessage("Erreur de génération : " + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function sauvegarderRapport() {
    if (!reportId || !rapport) return;

    setLoading(true);
    setMessage("");

    try {
      const result = await updateRapport(reportId, rapport);

      setRapport(result.data);
      setMessage("Rapport enregistré avec succès.");
    } catch (error) {
      setMessage("Erreur d’enregistrement : " + error.message);
    } finally {
      setLoading(false);
    }
  }

  async function exporterXlsx() {
    if (!reportId || !rapport) return;

    setLoading(true);
    setMessage("");

    try {
      await updateRapport(reportId, rapport);
      await exportRapportXlsx(reportId);
      downloadRapportXlsx(reportId);

      setMessage("Export XLSX lancé.");
    } catch (error) {
      setMessage("Erreur export XLSX : " + error.message);
    } finally {
      setLoading(false);
    }
  }

  function exporterPdf() {
    window.print();
  }

  function updateField(field, value) {
    setRapport((prev) => ({
      ...prev,
      [field]: value,
    }));
  }

  function updateProduct(index, field, value) {
    setRapport((prev) => {
      const produits = [...(prev.produits_presentes || [])];

      produits[index] = {
        ...produits[index],
        [field]: field === "nombre_echantillons" ? Number(value || 0) : value,
      };

      return {
        ...prev,
        produits_presentes: produits,
      };
    });
  }

  function resetPage() {
    setFile(null);
    setPreviewUrl("");
    setFileType("");
    setReportId(null);
    setTexteExtrait("");
    setRapport(null);
    setStep(1);
    setMessage("");
  }

  return (
    <main className="page rapport-page">
      {message && <div className="toast">{message}</div>}

      <header className="page-header rapport-header">
        <div>
          <h1>{isEditMode ? "Modifier un rapport" : "Rapport de visite"}</h1>
          <p>
            {isEditMode
              ? "Modifiez le texte extrait, vérifiez les champs puis exportez le rapport."
              : "Importez un PDF ou une image scannée, vérifiez le texte, puis générez le rapport."}
          </p>
        </div>

        <div className="header-badge">Document → Rapport</div>
      </header>

      <div className="steps professional-steps">
        <Step active={step >= 1} number="1" label="Importer" />
        <div className="step-line" />
        <Step active={step >= 2} number="2" label="Vérifier" />
        <div className="step-line" />
        <Step active={step >= 3} number="3" label="Générer" />
      </div>

      <section className="three-columns rapport-workspace">
        <div className="card workflow-card">
          <div className="card-title-row">
            <h2>Importer le document</h2>
          </div>

          <p className="card-description">
            Formats acceptés : PDF, PNG, JPG, JPEG.
          </p>

          <label className="upload-zone">
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={choisirFichier}
              className="hidden-file-input"
            />
            <span>Sélectionner un fichier</span>
          </label>

          <div className="preview-box">
            {!previewUrl && !isEditMode && (
              <p>Aucun document sélectionné.</p>
            )}

            {!previewUrl && isEditMode && (
              <p>Rapport existant chargé depuis l’historique.</p>
            )}

            {previewUrl && fileType.startsWith("image/") && (
              <img src={previewUrl} alt="Aperçu" className="preview-image" />
            )}

            {previewUrl && fileType === "application/pdf" && (
              <iframe
                src={previewUrl}
                title="Aperçu PDF"
                className="preview-pdf"
              />
            )}
          </div>

          <button
            className="btn primary"
            onClick={lancerExtraction}
            disabled={!file || loading}
          >
            {loading ? "Importation..." : "Importer"}
          </button>

          {file && (
            <button className="btn secondary" onClick={resetPage}>
              Nouveau fichier
            </button>
          )}
        </div>

        <div className="card workflow-card">
          <div className="card-title-row">
            <h2>Texte extrait</h2>
          </div>

          <p className="card-description">
            Corrigez le texte si nécessaire avant de générer le rapport.
          </p>

          <textarea
            className="text-editor"
            value={texteExtrait}
            onChange={(e) => setTexteExtrait(e.target.value)}
            placeholder="Le texte extrait apparaîtra ici..."
          />

          <button
            className="btn primary"
            onClick={genererRapport}
            disabled={!reportId || !texteExtrait.trim() || loading}
          >
            {loading ? "Génération..." : "Générer"}
          </button>
        </div>

        <div className="card workflow-card">
          <div className="card-title-row">
            <h2>Rapport généré</h2>
          </div>

          <p className="card-description">
            Vérifiez le rapport puis exportez-le au format souhaité.
          </p>

          <div className="report-preview-container">
            {!rapport && (
              <p className="empty-text">Le rapport généré apparaîtra ici.</p>
            )}

            {rapport && <RapportPreview rapport={rapport} />}
          </div>

          {rapport && (
            <div className="action-row professional-actions">
              <button className="btn dark" onClick={sauvegarderRapport}>
                Enregistrer
              </button>

              <button className="btn pdf-btn" onClick={exporterPdf}>
                Exporter PDF
              </button>

              <button className="btn success" onClick={exporterXlsx}>
                Exporter XLSX
              </button>
            </div>
          )}
        </div>
      </section>

      {rapport && (
        <section className="card form-section">
          <div className="section-header">
            <h2>Champs du rapport</h2>
            <p>Vous pouvez modifier les informations avant l’export final.</p>
          </div>

          <div className="form-grid">
            <Input
              label="Nom prospect"
              value={rapport.nom_prospect || ""}
              onChange={(value) => updateField("nom_prospect", value)}
            />

            <Input
              label="Date visite"
              value={rapport.date_visite || ""}
              onChange={(value) => updateField("date_visite", value)}
            />

            <Input
              label="Objectif visite"
              value={rapport.objectif_visite || ""}
              onChange={(value) => updateField("objectif_visite", value)}
            />

            <Input
              label="Nombre échantillons"
              type="number"
              value={rapport.nombre_echantillons || ""}
              onChange={(value) =>
                updateField("nombre_echantillons", Number(value || 0))
              }
            />

            <Input
              label="Nom superviseur"
              value={rapport.nom_superviseur || ""}
              onChange={(value) => updateField("nom_superviseur", value)}
            />

            <Input
              label="Nombre patients présents"
              type="number"
              value={rapport.nombre_patients_presents || ""}
              onChange={(value) =>
                updateField("nombre_patients_presents", Number(value || 0))
              }
            />

            <Input
              label="Gadget"
              value={rapport.gadget || ""}
              onChange={(value) => updateField("gadget", value)}
            />

            <Input
              label="Date relance"
              value={rapport.date_relance || ""}
              onChange={(value) => updateField("date_relance", value)}
            />
          </div>

          <TextArea
            label="Commentaire"
            value={rapport.commentaire || ""}
            onChange={(value) => updateField("commentaire", value)}
          />

          <TextArea
            label="Opportunités"
            value={rapport.opportunites || ""}
            onChange={(value) => updateField("opportunites", value)}
          />

          <TextArea
            label="Remarque générale"
            value={rapport.remarque_generale || ""}
            onChange={(value) => updateField("remarque_generale", value)}
          />

          <TextArea
            label="Prochaine étape"
            value={rapport.prochaine_etape || ""}
            onChange={(value) => updateField("prochaine_etape", value)}
          />

          <h3>Produits présentés</h3>

          {(rapport.produits_presentes || []).map((product, index) => (
            <div className="product-card" key={index}>
              <div className="form-grid">
                <Input
                  label="Produit"
                  value={product.nom || ""}
                  onChange={(value) => updateProduct(index, "nom", value)}
                />

                <Input
                  label="Nombre échantillons"
                  type="number"
                  value={product.nombre_echantillons || ""}
                  onChange={(value) =>
                    updateProduct(index, "nombre_echantillons", value)
                  }
                />
              </div>

              <TextArea
                label="Commentaire produit"
                value={product.commentaire || ""}
                onChange={(value) => updateProduct(index, "commentaire", value)}
              />

              <TextArea
                label="Opportunités produit"
                value={product.opportunites || ""}
                onChange={(value) => updateProduct(index, "opportunites", value)}
              />
            </div>
          ))}
        </section>
      )}
    </main>
  );
}

function Step({ active, number, label }) {
  return (
    <div className="step">
      <div className={active ? "step-circle active" : "step-circle"}>
        {active ? "✓" : number}
      </div>
      <span>{label}</span>
    </div>
  );
}

function Input({ label, value, onChange, type = "text" }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

function TextArea({ label, value, onChange }) {
  return (
    <label className="field full">
      <span>{label}</span>
      <textarea value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

function RapportPreview({ rapport }) {
  const produits = rapport.produits_presentes || [];

  return (
    <div id="print-report" className="rapport-document">
      <h1>RAPPORT DE VISITE MÉDICALE</h1>
      <p className="subtitle">Rapport généré par MediNote</p>

      <div className="info-grid">
        <Info label="Nom du prospect" value={rapport.nom_prospect} />
        <Info label="Date" value={rapport.date_visite} />
        <Info label="Superviseur" value={rapport.nom_superviseur} />
        <Info label="Patients présents" value={rapport.nombre_patients_presents} />
        <Info label="Date de relance" value={rapport.date_relance} />
        <Info label="Gadget" value={rapport.gadget} />
      </div>

      <Section title="Objectif de la visite">
        {rapport.objectif_visite || "Non mentionné"}
      </Section>

      <Section title="Produits présentés">
        {produits.length === 0 ? (
          <p>Non mentionné</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Produit</th>
                <th>Commentaire</th>
                <th>Opportunités</th>
                <th>Concurrents</th>
                <th>Échantillons</th>
              </tr>
            </thead>

            <tbody>
              {produits.map((product, index) => (
                <tr key={index}>
                  <td>{product.nom || "-"}</td>
                  <td>{product.commentaire || "-"}</td>
                  <td>{product.opportunites || "-"}</td>
                  <td>
                    {(product.benchmarking_concurrents || []).join(", ") || "-"}
                  </td>
                  <td>{product.nombre_echantillons ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Section>

      <Section title="Commentaire">
        {rapport.commentaire || "Non mentionné"}
      </Section>

      <Section title="Opportunités">
        {rapport.opportunites || "Non mentionné"}
      </Section>

      <Section title="Remarque générale">
        {rapport.remarque_generale || "Non mentionné"}
      </Section>

      <Section title="Prochaine étape">
        {rapport.prochaine_etape || "Non mentionné"}
      </Section>
    </div>
  );
}

function Info({ label, value }) {
  return (
    <div className="info-box">
      <span>{label}</span>
      <strong>{value || "Non mentionné"}</strong>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="rapport-section">
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  );
}