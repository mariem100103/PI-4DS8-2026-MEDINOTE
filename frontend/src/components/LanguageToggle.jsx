import { useLanguage } from "../context/LanguageContext.jsx";

export default function LanguageToggle({ className = "" }) {
  const { lang, setLang, t } = useLanguage();
  return (
    <div
      className={`inline-flex h-9 items-center gap-1 rounded-lg border border-slate-200 bg-white/80 p-0.5 shadow-sm dark:border-slate-600 dark:bg-slate-800/90 ${className}`}
      role="group"
      aria-label={t("common.language")}
    >
      <button
        type="button"
        onClick={() => setLang("fr")}
        className={`h-8 rounded-md px-3 py-0 text-sm font-semibold transition ${
          lang === "fr"
            ? "bg-[#2563eb] text-white shadow-sm"
            : "text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700"
        }`}
        aria-pressed={lang === "fr"}
      >
        FR
      </button>
      <button
        type="button"
        onClick={() => setLang("en")}
        className={`h-8 rounded-md px-3 py-0 text-sm font-semibold transition ${
          lang === "en"
            ? "bg-[#2563eb] text-white shadow-sm"
            : "text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700"
        }`}
        aria-pressed={lang === "en"}
      >
        EN
      </button>
    </div>
  );
}
