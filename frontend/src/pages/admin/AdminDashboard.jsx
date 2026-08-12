import { Link } from "react-router-dom";
import { Home, LayoutDashboard, LogOut, Users } from "lucide-react";
import { useAuth } from "../../context/AuthContextHybrid.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";
import logoMedinote from "../../assets/logoo.png";
import LanguageToggle from "../../components/LanguageToggle.jsx";

export default function AdminDashboard() {
  const { t } = useLanguage();
  const { user, logout, listUsers } = useAuth();
  const users = listUsers();

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f0f9ff] to-[#eef2ff] font-sans text-slate-800">
      <header className="border-b border-white/60 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <img
              src={logoMedinote}
              alt=""
              className="h-11 w-11 object-contain"
              width={44}
              height={44}
            />
            <div>
              <p className="text-lg font-bold text-slate-900">ALIA CRM</p>
              <p className="text-xs text-slate-500">
                {t("admin.dashboard.title")}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:border-[#2563eb]/40 hover:text-[#2563eb]"
            >
              <Home className="h-4 w-4 shrink-0" aria-hidden />
              {t("nav.home")}
            </Link>
            <span
              className="inline-flex items-center gap-1.5 rounded-lg border border-[#2563eb]/25 bg-blue-50/80 px-3 py-2 text-sm font-semibold text-[#1d4ed8]"
              aria-current="page"
            >
              <LayoutDashboard className="h-4 w-4 shrink-0" aria-hidden />
              {t("nav.dashboard")}
            </span>
            <span className="hidden text-sm text-slate-600 sm:inline">
              <span className="font-semibold text-slate-900">{user?.name}</span>
              <span className="mx-2 text-slate-300">·</span>
              {user?.email}
            </span>
            <LanguageToggle />
            <Link
              to="/persona"
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:border-[#2563eb]/40 hover:text-[#2563eb]"
            >
              {t("admin.dashboard.open_crm")}
            </Link>
            <button
              type="button"
              onClick={() => logout()}
              className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800"
            >
              <LogOut className="h-4 w-4" aria-hidden />
              {t("auth.logout")}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <div className="mb-8 flex items-center gap-2">
          <LayoutDashboard className="h-8 w-8 text-[#2563eb]" aria-hidden />
          <h1 className="text-2xl font-bold text-slate-900">
            {t("admin.dashboard.heading")}
          </h1>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              key: "users",
              value: users.length,
              labelKey: "admin.dashboard.kpi.users",
            },
            {
              key: "delegates",
              value: users.filter((u) => u.role === "delegate").length,
              labelKey: "admin.dashboard.kpi.delegates",
            },
            {
              key: "admins",
              value: users.filter((u) => u.role === "admin").length,
              labelKey: "admin.dashboard.kpi.admins",
            },
            {
              key: "visits",
              value: "4 142",
              labelKey: "admin.dashboard.kpi.visits_mock",
            },
          ].map((card) => (
            <article
              key={card.key}
              className="rounded-xl border border-slate-100 bg-white p-5 shadow-[0_4px_24px_rgba(0,0,0,0.06)]"
            >
              <p className="text-2xl font-bold text-[#2563eb]">{card.value}</p>
              <p className="mt-1 text-sm font-medium text-slate-600">
                {t(card.labelKey)}
              </p>
            </article>
          ))}
        </div>

        <section className="mt-10 rounded-xl border border-slate-100 bg-white p-6 shadow-[0_4px_24px_rgba(0,0,0,0.06)]">
          <div className="mb-4 flex items-center gap-2">
            <Users className="h-5 w-5 text-[#2563eb]" />
            <h2 className="text-lg font-semibold text-slate-900">
              {t("admin.dashboard.users_preview")}
            </h2>
          </div>
          <p className="text-sm text-slate-600">
            {t("admin.dashboard.users_hint")}
          </p>
          <ul className="mt-4 divide-y divide-slate-100">
            {users.slice(0, 5).map((u) => (
              <li
                key={u.id}
                className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm"
              >
                <span className="font-medium text-slate-900">{u.name}</span>
                <span className="text-slate-500">{u.email}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                    u.role === "admin"
                      ? "bg-violet-100 text-violet-800"
                      : "bg-emerald-100 text-emerald-800"
                  }`}
                >
                  {u.role === "admin"
                    ? t("auth.role.admin")
                    : t("auth.role.delegate")}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-4 text-xs text-slate-400">
            {t("admin.dashboard.full_users_later")}
          </p>
        </section>
      </main>
    </div>
  );
}
