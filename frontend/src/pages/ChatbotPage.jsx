import { useState, useRef, useEffect } from "react";
import { Loader2, Send } from "lucide-react";
import ChatBubble from "../components/ChatBubble";
import { sendMessage } from "../api/chatbotApi";
import { useLanguage } from "../context/LanguageContext.jsx";
import { PageHeader } from "../components/ui";
import { FEATURE_PAGE_ROOT, FIELD_INPUT_CLASS } from "../components/FeaturePageChrome.jsx";

const examples = [
  "Parle-moi du Doliprane",
  "Quel est le prix du Brufen ?",
  "Trouve une alternative moins chère",
  "Quelle est la DCI de l'Efferalgan ?",
];

function ChatbotPage() {
  const { t } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;

    const userMessage = { role: "user", content: text };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await sendMessage(text);
      setMessages([...newMessages, { role: "assistant", content: response }]);
    } catch {
      setMessages([
        ...newMessages,
        { role: "assistant", content: t("page.chatbot.connection_error") },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={FEATURE_PAGE_ROOT}>
      <PageHeader title={t("page.chatbot.title")} subtitle={t("page.chatbot.subtitle")} />

      <div className="mx-auto mt-6 max-w-[780px] rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-white)] shadow-[var(--shadow-md)] dark:border-slate-600 dark:bg-slate-800/60">
        <div className="flex max-h-[min(420px,55vh)] flex-col gap-3 overflow-y-auto p-5">
          {messages.length === 0 && (
            <div className="mt-8 text-center">
              <p className="mb-5 text-sm text-slate-600 dark:text-slate-400">
                {t("page.chatbot.empty_hint")}
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {examples.map((ex, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setInput(ex)}
                    className="rounded-full border border-[var(--medical-primary-medium)] bg-[var(--medical-primary-light)] px-3.5 py-1.5 text-xs font-semibold text-[var(--medical-primary)] transition hover:opacity-90 dark:border-sky-700 dark:bg-sky-950/50 dark:text-sky-300"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <ChatBubble key={i} role={msg.role} content={msg.content} />
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-xl rounded-bl-sm border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-600 dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-400">
                <Loader2 className="h-4 w-4 shrink-0 animate-spin" aria-hidden />
                {t("common.loading")}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-[var(--medical-gray-100)] dark:border-slate-600" />

        <div className="flex flex-wrap gap-2 p-4 sm:flex-nowrap">
          <input
            type="text"
            className={`${FIELD_INPUT_CLASS} min-h-[44px] flex-1`}
            placeholder={t("page.chatbot.input_placeholder")}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            aria-label={t("page.chatbot.title")}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-[var(--medical-primary)] px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-sky-600 dark:text-slate-950"
          >
            <Send className="h-4 w-4" aria-hidden />
            {t("common.send")}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatbotPage;
