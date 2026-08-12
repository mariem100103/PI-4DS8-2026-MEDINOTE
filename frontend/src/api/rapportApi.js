const API_URL =
    import.meta.env.VITE_API_URL || "http://localhost:8000";


async function handleResponse(response) {
    if (!response.ok) {
        const text = await response.text();
        throw new Error(text);
    }

    const contentType = response.headers.get("content-type");

    if (contentType && contentType.includes("application/json")) {
        return response.json();
    }

    return response;
}

export async function uploadRapport(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_URL}/reports/upload`, {
        method: "POST",
        body: formData,
    });

    return handleResponse(response);
}

export async function updateTexteExtrait(reportId, texteExtrait) {
    const response = await fetch(`${API_URL}/reports/${reportId}/extracted-text`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            extracted_text: texteExtrait,
        }),
    });

    return handleResponse(response);
}

export async function formatRapport(reportId) {
    const response = await fetch(`${API_URL}/reports/${reportId}/format`, {
        method: "POST",
    });

    return handleResponse(response);
}

export async function getRapport(reportId) {
    const response = await fetch(`${API_URL}/reports/${reportId}`);
    return handleResponse(response);
}

export async function updateRapport(reportId, rapportJson) {
    const response = await fetch(`${API_URL}/reports/${reportId}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            data: rapportJson,
        }),
    });

    return handleResponse(response);
}

export async function exportRapportXlsx(reportId) {
    const response = await fetch(`${API_URL}/reports/${reportId}/export-xlsx`, {
        method: "POST",
    });

    return handleResponse(response);
}

export function downloadRapportXlsx(reportId) {
    window.open(`${API_URL}/reports/${reportId}/download-xlsx`, "_blank");
}

export async function getRapports() {
    const response = await fetch(`${API_URL}/reports`);
    return handleResponse(response);
}

export async function deleteRapport(reportId, reason = "Supprimé depuis interface") {
    const formData = new FormData();
    formData.append("reason", reason);

    const response = await fetch(`${API_URL}/reports/${reportId}`, {
        method: "DELETE",
        body: formData,
    });

    return handleResponse(response);
}