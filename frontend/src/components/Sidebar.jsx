import { useMemo } from "react";
import { NavLink } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext.jsx";

function Sidebar({ open = true, onClose }) {
  const { t } = useLanguage();
  const links = useMemo(
    () => [
      { to: "/persona", label: t("shell.sidebar.link_persona") },
      { to: "/heatmap", label: t("shell.sidebar.link_heatmap") },
      { to: "/followup", label: t("nav.followup") },
    ],
    [t],
  );

  return (
    <>
      <div
        className={`fixed inset-0 z-40 bg-slate-900/40 transition md:hidden ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={onClose}
      />

      <aside
        className={`fixed left-0 top-0 z-50 h-screen w-72 shrink-0 border-r border-slate-200 bg-white/90 p-6 backdrop-blur transition-transform md:sticky md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
      <div className="rounded-xl bg-slate-900 bg-gradient-to-r from-alia-primary-800 to-alia-secondary-800 p-4 text-slate-50 shadow-md">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-200">{t("shell.sidebar.platform")}</p>
            <h1 className="mt-1 text-2xl font-bold">ALIA CRM</h1>
            <p className="mt-1 text-xs text-slate-200">{t("shell.sidebar.tagline")}</p>
          </div>
          <div className="rounded-lg bg-white/10 px-2 py-1 text-xs font-semibold text-white/90">
            {t("shell.sidebar.demo")}
          </div>
        </div>
      </div>

      <div className="mt-4 flex justify-end md:hidden">
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"
        >
          {t("shell.sidebar.close")}
        </button>
      </div>

      <p className="mb-3 mt-8 text-xs font-semibold uppercase tracking-wide text-slate-400">
        {t("shell.sidebar.navigation")}
      </p>
      <nav className="flex flex-col gap-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `rounded-lg px-4 py-2 text-sm font-medium transition ${
                isActive
                  ? "bg-slate-100 bg-alia-primary-100 text-slate-900 text-alia-primary-900 shadow-sm"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`
            }
            onClick={() => onClose?.()}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-8 rounded-xl border border-slate-200 border-alia-primary-100 bg-slate-50 bg-alia-primary-50 p-4">
        <p className="text-sm font-semibold text-slate-900 text-alia-primary-900">{t("shell.sidebar.tip_title")}</p>
        <p className="mt-1 text-xs text-slate-700 text-alia-primary-800">
          {t("shell.sidebar.tip_body")}
        </p>
      </div>
      </aside>
    </>
  );
}

export default Sidebar;
