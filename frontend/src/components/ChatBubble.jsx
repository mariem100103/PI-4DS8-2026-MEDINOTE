function ChatBubble({ role, content }) {
  const isUser = role === "user"

  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start"
    }}>
      <div style={{
        maxWidth: "75%",
        padding: "10px 14px",
        borderRadius: isUser ? "12px 12px 2px 12px" : "12px 12px 12px 2px",
        backgroundColor: isUser ? "var(--medical-primary)" : "var(--medical-gray-50)",
        color: isUser ? "white" : "var(--medical-gray-900)",
        fontSize: "14px",
        lineHeight: "1.6",
        whiteSpace: "pre-wrap"
      }}>
        {content}
      </div>
    </div>
  )
}

export default ChatBubble
