/**
 * api/coachingApi.js
 * Toutes les requêtes vers le service /coaching du backend FastAPI.
 */

const API_URL =
    import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function getScenarios() {
    const res = await fetch(`${API_URL}/coaching/scenarios`);
    if (!res.ok) throw new Error(`Erreur ${res.status}`);
    return res.json();
}

export async function getLevels() {
    const res = await fetch(`${API_URL}/coaching/levels`);
    if (!res.ok) throw new Error(`Erreur ${res.status}`);
    return res.json();
}

/**
 * Envoyer un message au médecin simulé.
 * @param {Array} history - [{role, content}]
 * @param {string} scenarioKey
 * @param {number} level
 * @param {boolean} forceFinalScore
 */
export async function sendMessage(history, scenarioKey, level, forceFinalScore = false) {
    const res = await fetch(`${API_URL}/coaching/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            history,
            scenario_key: scenarioKey,
            level,
            force_final_score: forceFinalScore,
        }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erreur serveur ${res.status}`);
    }
    return res.json();
}