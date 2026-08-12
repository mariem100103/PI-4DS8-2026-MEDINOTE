import { useLanguage } from "../context/LanguageContext.jsx";

function TopBar({ onOpenMenu }) {
  const { t } = useLanguage();
  return (
    <div className="sticky top-0 z-30 mb-6 rounded-xl border border-slate-200 bg-white/80 p-3 shadow-sm backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onOpenMenu}
            className="inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 md:hidden"
            aria-label={t("shell.topbar.open_menu")}
          >
            {t("shell.topbar.menu")}
          </button>
          <div>
            <p className="text-sm font-semibold text-slate-900">{t("shell.topbar.dashboard")}</p>
            <p className="text-xs text-slate-500">
              {t("shell.topbar.subtitle")}
            </p>
          </div>
        </div>

        <div className="hidden items-center gap-2 md:flex">
          <span className="rounded-full bg-alia-primary-100 px-3 py-1 text-xs font-semibold text-alia-primary-900">
            {t("shell.topbar.demo_mode")}
          </span>
        </div>
      </div>
    </div>
  );
}

export default TopBar;

