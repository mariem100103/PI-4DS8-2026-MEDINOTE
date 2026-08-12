import { useState } from "react";
import {
  uploadReport,
  updateExtractedText,
  formatReport,
  updateReportJson,
  exportXlsx,
  downloadXlsxUrl,
} from "../api/reportApi";

export default function ImageToReport() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const [reportId, setReportId] = useState(null);
  const [extractedText, setExtractedText] = useState("");
  const [reportJson, setReportJson] = useState(null);

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    setFile(selected);

    if (selected && selected.type.startsWith("image/")) {
      setPreviewUrl(URL.createObjectURL(selected));
    } else {
      setPreviewUrl(null);
    }
  };

  const handleUpload = async () => {
    setLoading(true);
    try {
      const result = await uploadReport(file);
      setReportId(result.report_id);
      setExtractedText(result.extracted_text);
      setStep(2);
    } finally {
      setLoading(false);
    }
  };

  const handleFormat = async () => {
    setLoading(true);
    try {
      await updateExtractedText(reportId, extractedText);
      const result = await formatReport(reportId);
      setReportJson(result.data);
      setStep(3);
    } finally {
      setLoading(false);
    }
  };

  const handleJsonChange = (field, value) => {
    setReportJson((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSaveJson = async () => {
    const result = await updateReportJson(reportId, reportJson);
    setReportJson(result.data);
    alert("Report updated");
  };

  const handleExport = async () => {
    await updateReportJson(reportId, reportJson);
    await exportXlsx(reportId);
    window.open(downloadXlsxUrl(reportId), "_blank");
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Image / PDF to Report</h1>
          <p className="text-gray-500">
            Upload scanned or printed reports for AI processing
          </p>
        </div>

        <div className="flex items-center justify-center gap-6 mb-8">
          <StepCircle active={step >= 1} label="Upload" number="1" />
          <StepLine />
          <StepCircle active={step >= 2} label="Edit Text" number="2" />
          <StepLine />
          <StepCircle active={step >= 3} label="Format Report" number="3" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upload */}
          <div className="bg-white rounded-2xl shadow p-5">
            <h2 className="font-semibold mb-4">Upload File</h2>

            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="mb-4"
            />

            {previewUrl ? (
              <img
                src={previewUrl}
                alt="preview"
                className="rounded-xl border max-h-[450px] object-contain w-full"
              />
            ) : (
              <div className="border rounded-xl p-8 text-center text-gray-400">
                PDF or image preview
              </div>
            )}

            <button
              onClick={handleUpload}
              disabled={!file || loading}
              className="mt-4 w-full bg-blue-600 text-white rounded-xl py-3"
            >
              {loading ? "Processing..." : "Upload and Extract"}
            </button>
          </div>

          {/* Extracted text */}
          <div className="bg-white rounded-2xl shadow p-5">
            <h2 className="font-semibold mb-4">Extracted Text</h2>

            <textarea
              value={extractedText}
              onChange={(e) => setExtractedText(e.target.value)}
              className="w-full h-[450px] border rounded-xl p-4 font-mono text-sm"
              placeholder="Extracted text will appear here. You can modify it before formatting..."
            />

            <button
              onClick={handleFormat}
              disabled={!reportId || !extractedText || loading}
              className="mt-4 w-full bg-purple-600 text-white rounded-xl py-3"
            >
              {loading ? "Formatting..." : "Format with AI"}
            </button>
          </div>

          {/* Formatted report */}
          <div className="bg-white rounded-2xl shadow p-5">
            <h2 className="font-semibold mb-4">Formatted Report</h2>

            {!reportJson ? (
              <div className="border rounded-xl p-8 text-gray-400 h-[450px]">
                Formatted JSON report will appear here.
              </div>
            ) : (
              <div className="space-y-3 h-[450px] overflow-auto">
                <InputField
                  label="Nom prospect"
                  value={reportJson.nom_prospect || ""}
                  onChange={(v) => handleJsonChange("nom_prospect", v)}
                />

                <InputField
                  label="Date visite"
                  value={reportJson.date_visite || ""}
                  onChange={(v) => handleJsonChange("date_visite", v)}
                />

                <InputField
                  label="Objectif visite"
                  value={reportJson.objectif_visite || ""}
                  onChange={(v) => handleJsonChange("objectif_visite", v)}
                />

                <InputField
                  label="Commentaire"
                  value={reportJson.commentaire || ""}
                  onChange={(v) => handleJsonChange("commentaire", v)}
                />

                <InputField
                  label="Prochaine étape"
                  value={reportJson.prochaine_etape || ""}
                  onChange={(v) => handleJsonChange("prochaine_etape", v)}
                />

                <pre className="bg-green-50 border rounded-xl p-3 text-xs overflow-auto">
                  {JSON.stringify(reportJson, null, 2)}
                </pre>
              </div>
            )}

            {reportJson && (
              <div className="grid grid-cols-2 gap-3 mt-4">
                <button
                  onClick={handleSaveJson}
                  className="bg-gray-800 text-white rounded-xl py-3"
                >
                  Save Changes
                </button>

                <button
                  onClick={handleExport}
                  className="bg-green-600 text-white rounded-xl py-3"
                >
                  Export XLSX
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StepCircle({ active, label, number }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center text-white ${
          active ? "bg-green-600" : "bg-gray-300"
        }`}
      >
        {active ? "✓" : number}
      </div>
      <span className="font-medium">{label}</span>
    </div>
  );
}

function StepLine() {
  return <div className="h-[2px] bg-gray-300 w-24" />;
}

function InputField({ label, value, onChange }) {
  return (
    <label className="block">
      <span className="text-sm text-gray-600">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full border rounded-lg p-2 mt-1"
      />
    </label>
  );
}