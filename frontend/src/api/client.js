// src/api/client.js — CRM Médical

const API = (
    import.meta.env.VITE_API_URL || "").trim();

function buildUrl(path) {
    if (!API) return path; // utilise le proxy CRA (package.json)
    return `${API}${path}`;
}

function networkMessage() {
    return "Impossible de joindre le backend (Failed to fetch). Vérifie que l'API FastAPI tourne sur http://localhost:8000.";
}

async function post(path, body, isFormData = false) {
    const headers = isFormData ? {} : { "Content-Type": "application/json" };
    let resp;
    try {
        resp = await fetch(buildUrl(path), {
            method: "POST",
            headers,
            body: isFormData ? body : JSON.stringify(body),
        });
    } catch {
        throw new Error(networkMessage());
    }
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || "Erreur serveur");
    }
    return resp.json();
}

async function get(path) {
    let resp;
    try {
        resp = await fetch(buildUrl(path));
    } catch {
        throw new Error(networkMessage());
    }
    if (!resp.ok) throw new Error(resp.statusText);
    return resp.json();
}

// ── Analyse ──────────────────────────────────────────────────────

export const analyzeText = (text) =>
    post("/analyze/text", { text });

export const analyzeMulti = (text, split_notes = false) =>
    post("/analyze/multi", { text, split_notes });

// ── OCR ──────────────────────────────────────────────────────────

export const ocrImage = (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return post("/ocr/image", fd, true);
};

export const ocrPdf = (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return post("/ocr/pdf", fd, true);
};

// ── Données ──────────────────────────────────────────────────────

export const getStats = () => get("/data/stats");
export const searchMedicament = (q) => get(`/data/medicaments?q=${encodeURIComponent(q)}`);
export const healthCheck = () => get("/health");
// Dev: use Vite proxy (same origin). Prod: set VITE_API_URL or default to local API.
const BASE_URL =
    import.meta.env.VITE_API_URL ?
    import.meta.env.VITE_API_URL :
    (
        import.meta.env.DEV ? "" : "http://localhost:8000");

async function request(endpoint, options = {}) {
    const response = await fetch(`${BASE_URL}${endpoint}`, options);

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
            `API ${response.status} ${response.statusText}: ${
        errorText || "Erreur inconnue"
      }`
        );
    }

    return response;
}

export async function predictPersona(payload) {
    const response = await request("/persona/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    return response.json();
}

export async function getHeatmapMap() {
    const response = await request("/heatmap/map");
    return response.text();
}

export async function getHeatmapKpis() {
    const response = await request("/heatmap/kpis");
    return response.json();
}

export async function getAtRiskAndPotential() {
    const response = await request("/heatmap/at-risk");
    return response.json();
}

export async function getFollowupTasks(params = {}) {
    const searchParams = new URLSearchParams();

    if (params.medecin) searchParams.set("medecin", params.medecin);
    if (params.priorite) searchParams.set("priorite", params.priorite);
    if (params.min_interet !== undefined && params.min_interet !== null) {
        searchParams.set("min_interet", String(params.min_interet));
    }

    const query = searchParams.toString();
    const endpoint = query ? `/followup/tasks?${query}` : "/followup/tasks";
    const response = await request(endpoint);
    return response.json();
}

export async function getFollowupKpis() {
    const response = await request("/followup/kpis");
    return response.json();
}

export function getFollowupCsvExportUrl() {
    return `${BASE_URL}/followup/export/csv`;
}

export function getFollowupIcsExportUrl() {
    return `${BASE_URL}/followup/export/ics`;
}