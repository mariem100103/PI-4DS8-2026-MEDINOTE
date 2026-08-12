const API_URL =
    import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function sendMessage(message) {
  const response = await fetch(`${API_URL}/chatbot/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history: [] })
  })
  const data = await response.json()
  return data.response
}
