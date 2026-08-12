/**
 * api/correcteurApi.js
 * Toutes les requêtes vers le service /correcteur du backend FastAPI.
 */

const API_URL =
    import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Corriger un texte médical brut.
 * @param {string} texte
 * @returns {Promise<CorrectionResult>}
 */
export async function correctText(texte) {
    const res = await fetch(`${API_URL}/correcteur/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texte }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
    }
    return res.json();
}

/**
 * Transcrire + corriger un fichier audio.
 * @param {File} audioFile
 * @returns {Promise<CorrectionResult>}
 */
export async function correctAudio(audioFile) {
    const formData = new FormData();
    formData.append("file", audioFile);
    const res = await fetch(`${API_URL}/correcteur/audio`, {
        method: "POST",
        body: formData,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
    }
    return res.json();
}

/**
 * Vérifier l'integrite d'une note brute.
 * @param {string} rawNote
 * @returns {Promise<object>}
 */
export async function checkIntegrity(rawNote) {
    const res = await fetch(`${API_URL}/integrity/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_note: rawNote }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
    }
    return res.json();
}

/**
 * Calculer le score qualite d'une note brute.
 * @param {string} rawNote
 * @returns {Promise<object>}
 */
export async function scoreQuality(rawNote) {
    const res = await fetch(`${API_URL}/integrity/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_note: rawNote }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
    }
    return res.json();
}

/**
 * Generer un rapport structure.
 * @param {string} rawNote
 * @returns {Promise<object>}
 */
export async function generateReport(rawNote) {
    const res = await fetch(`${API_URL}/integrity/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_note: rawNote }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
    }
    return res.json();
}

/**
 * Récapitulatif integrite + qualite + rapport.
 * @param {string} rawNote
 * @returns {Promise<object>}
 */
export async function getIntegritySummary(rawNote) {
    const res = await fetch(`${API_URL}/integrity/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_note: rawNote }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
    }
    return res.json();
}

/**
 * Ajouter le rapport aux delegues reports (si PASS).
 * @param {string} rawNote
 * @returns {Promise<object>}
 */
export async function appendReport(rawNote) {
    const res = await fetch(`${API_URL}/integrity/append`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_note: rawNote }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
    }
    return res.json();
}

/**
 * Traitement par lot via CSV.
 * @param {File} file
 * @returns {Promise<object>}
 */
export async function batchProcess(file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/integrity/batch`, {
        method: "POST",
        body: formData,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
    }
    return res.json();
}