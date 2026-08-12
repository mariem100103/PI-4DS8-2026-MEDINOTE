const HISTORY_KEY = "consultation_history";
const MAX_ITEMS = 50;

export function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveHistory(items) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(items.slice(0, MAX_ITEMS)));
}

export function buildHistoryEntry(result, source) {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    date: new Date().toISOString(),
    source,
    category: result?.Catégorie || "Consultation",
    sentiment: result?.Sentiment || "neutre",
    doctors: Array.isArray(result?.Médecins) ? result.Médecins : [],
    drugs: Array.isArray(result?.Médicaments) ? result.Médicaments : [],
    summary: result?.Résumé || "",
  };
}

export function appendHistory(newEntries) {
  if (!Array.isArray(newEntries) || newEntries.length === 0) return loadHistory();
  const existing = loadHistory();
  const merged = [...newEntries, ...existing];
  saveHistory(merged);
  return merged.slice(0, MAX_ITEMS);
}

export function removeHistoryItem(itemId) {
  const existing = loadHistory();
  const updated = existing.filter((item) => item.id !== itemId);
  saveHistory(updated);
  return updated;
}

