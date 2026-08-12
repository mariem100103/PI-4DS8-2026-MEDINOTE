import { Link, useNavigate } from "react-router-dom";
import {
  Brain,
  CalendarClock,
  FileEdit,
  Layers,
  Map,
  Mic2,
  LogOut,
} from "lucide-react";
import { useLanguage } from "../context/LanguageContext.jsx";
import { useAuth } from "../context/AuthContextHybrid.jsx";
import LanguageToggle from "../components/LanguageToggle.jsx";
import ThemeToggle from "../components/ThemeToggle.jsx";
import { useTheme } from "../context/ThemeContext.jsx";
import logoMedinote from "../assets/logoo.png";

function cardSurfaceClass(isDark) {
  return (
    "rounded-xl border p-6 " +
    (isDark
      ? "border-slate-600 bg-slate-800 shadow-[0_8px_30px_rgba(0,0,0,0.55)] ring-1 ring-slate-500/30"
      : "border-slate-100 bg-white shadow-[0_4px_24px_rgba(15,23,42,0.08)]")
  );
}

export default function HomePage() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();
  const { isDark } = useTheme();

  const pageShell =
    "min-h-screen font-sans " +
    (isDark
      ? "bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-200"
      : "bg-gradient-to-br from-[#f0f9ff] to-[#eef2ff] text-slate-900");

  const features = [
    {
      icon: Brain,
      titleKey: "home.features.persona.title",
      descKey: "home.features.persona.desc",
    },
    {
      icon: Map,
      titleKey: "home.features.heatmap.title",
      descKey: "home.features.heatmap.desc",
    },
    {
      icon: CalendarClock,
      titleKey: "home.features.followup.title",
      descKey: "home.features.followup.desc",
    },
    {
      icon: Mic2,
      titleKey: "home.features.coach.title",
      descKey: "home.features.coach.desc",
    },
    {
      icon: FileEdit,
      titleKey: "home.features.correcteur.title",
      descKey: "home.features.correcteur.desc",
    },
    {
      icon: Layers,
      titleKey: "home.features.reports.title",
      descKey: "home.features.reports.desc",
    },
  ];

  const stats = [
    { valueKey: "home.stats.visits.value", labelKey: "home.stats.visits" },
    {
      valueKey: "home.stats.physicians.value",
      labelKey: "home.stats.physicians",
    },
    {
      valueKey: "home.stats.regions.value",
      labelKey: "home.stats.regions",
    },
    {
      valueKey: "home.stats.modules.value",
      labelKey: "home.stats.modules",
    },
  ];

  const steps = [
    {
      n: "1",
      titleKey: "home.steps.one.title",
      descKey: "home.steps.one.desc",
    },
    {
      n: "2",
      titleKey: "home.steps.two.title",
      descKey: "home.steps.two.desc",
    },
    {
      n: "3",
      titleKey: "home.steps.three.title",
      descKey: "home.steps.three.desc",
    },
  ];

  return (
    <div className={pageShell}>
      <header
        className={
          "sticky top-0 z-40 border-b backdrop-blur-md " +
          (isDark
            ? "border-slate-600 bg-slate-950 shadow-[0_1px_0_rgba(148,163,184,0.15)]"
            : "border-white/60 bg-white/70")
        }
      >
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <img
              src={logoMedinote}
              alt="MediNote"
              width={48}
              height={48}
              className={
                "h-12 w-12 shrink-0 rounded-xl object-contain shadow-sm ring-1 " +
                (isDark ? "ring-slate-600" : "ring-slate-100")
              }
            />
            <div>
              <p
                className={
                  "text-lg font-bold tracking-tight " +
                  (isDark ? "text-slate-100" : "text-slate-900")
                }
              >
                {t("home.hero.title")}
              </p>
              <p
                className={
                  "text-xs font-medium " +
                  (isDark ? "text-slate-400" : "text-slate-500")
                }
              >
                Vital Labo Tunisia
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3">
            <ThemeToggle compact />
            <LanguageToggle />
            {isAuthenticated && (
              <>
                <span
                  className={
                    "hidden max-w-[10rem] truncate border-l pl-3 text-sm md:inline " +
                    (isDark
                      ? "border-slate-600 text-slate-300"
                      : "border-slate-200/80 text-slate-600")
                  }
                  title={user?.email ?? ""}
                >
                  {user?.name ?? user?.email}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    navigate("/login", { replace: true });
                  }}
                  className={
                    "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-2 text-xs font-semibold shadow-sm transition sm:px-3 " +
                    (isDark
                      ? "border-slate-600 bg-slate-800 text-slate-200 hover:border-rose-400 hover:text-rose-300"
                      : "border-slate-200 bg-white text-slate-700 hover:border-rose-200 hover:text-rose-700")
                  }
                  title={t("auth.logout")}
                >
                  <LogOut className="h-3.5 w-3.5 shrink-0" aria-hidden />
                  <span className="hidden sm:inline">{t("auth.logout")}</span>
                </button>
              </>
            )}
            <Link
              to="/persona"
              className={
                "hidden rounded-lg border px-3 py-2 text-sm font-semibold shadow-sm transition sm:inline-flex " +
                (isDark
                  ? "border-slate-600 bg-slate-800 text-slate-200 hover:text-sky-400"
                  : "border-slate-200 bg-white text-slate-700 hover:border-[#2563eb]/40 hover:text-[#2563eb]")
              }
            >
              {t("home.nav.skip")}
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="mx-auto max-w-6xl px-4 pb-16 pt-12 sm:px-6 sm:pt-16">
          <p
            className={
              "mb-4 inline-flex items-center rounded-full px-4 py-1.5 text-xs font-semibold uppercase tracking-wide shadow-sm " +
              (isDark
                ? "bg-sky-950 text-sky-300 ring-1 ring-sky-400/35"
                : "bg-white/90 text-[#2563eb] ring-1 ring-blue-100")
            }
          >
            {t("home.hero.badge")}
          </p>
          <h1
            className={
              "max-w-3xl text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl " +
              (isDark ? "text-slate-100" : "text-slate-900")
            }
          >
            {t("home.hero.title")}
          </h1>
          <p
            className={
              "mt-6 max-w-2xl text-lg leading-relaxed sm:text-xl " +
              (isDark ? "text-slate-300" : "text-slate-600")
            }
          >
            {t("home.hero.subtitle")}
          </p>
          <p
            className={
              "mt-3 max-w-2xl text-sm font-extrabold tracking-tight sm:text-base"
            }
          >
            <span
              className={
                "inline-flex flex-wrap items-center gap-2 rounded-2xl border px-3 py-2 shadow-sm " +
                (isDark
                  ? "border-sky-500/30 bg-slate-900/60 text-slate-100"
                  : "border-blue-200/70 bg-white/70 text-slate-900")
              }
            >
              <span
                className={
                  "rounded-xl px-2.5 py-1 " +
                  (isDark
                    ? "bg-sky-500/15 text-sky-200 ring-1 ring-sky-400/25"
                    : "bg-blue-50 text-[#2563eb] ring-1 ring-blue-200/60")
                }
              >
                {t("home.hero.slogan.visit")}
              </span>
              <span
                className={
                  "rounded-xl px-2.5 py-1 " +
                  (isDark
                    ? "bg-emerald-500/15 text-emerald-200 ring-1 ring-emerald-400/25"
                    : "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200/60")
                }
              >
                {t("home.hero.slogan.act")}
              </span>
              <span
                className={
                  "rounded-xl px-2.5 py-1 " +
                  (isDark
                    ? "bg-violet-500/15 text-violet-200 ring-1 ring-violet-400/25"
                    : "bg-violet-50 text-violet-700 ring-1 ring-violet-200/60")
                }
              >
                {t("home.hero.slogan.sell")}
              </span>
            </span>
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link
              to="/login"
              className={
                "inline-flex items-center justify-center rounded-lg px-8 py-3 text-base font-semibold shadow-lg transition " +
                (isDark
                  ? "bg-sky-500 text-slate-950 shadow-[0_12px_40px_rgba(14,165,233,0.35)] hover:bg-sky-400"
                  : "bg-[#2563eb] text-white shadow-blue-500/30 hover:bg-blue-700")
              }
            >
              {t("home.cta.start")}
            </Link>
            <a
              href="#features"
              className={
                "inline-flex items-center justify-center rounded-lg border-2 px-8 py-3 text-base font-semibold shadow-sm transition " +
                (isDark
                  ? "border-slate-500 bg-slate-800 text-slate-100 hover:border-sky-500 hover:text-sky-300"
                  : "border-slate-200 bg-white text-slate-800 hover:border-[#2563eb]/50 hover:text-[#2563eb]")
              }
            >
              {t("home.cta.learn")}
            </a>
          </div>
        </section>

        {/* Features */}
        <section
          id="features"
          className={
            "scroll-mt-24 px-4 pb-16 sm:px-6 " +
            (isDark ? "bg-slate-950" : "bg-transparent")
          }
        >
          <div className="mx-auto max-w-6xl">
            <h2
              className={
                "text-center text-2xl font-bold sm:text-3xl " +
                (isDark ? "text-slate-100" : "text-slate-900")
              }
            >
              {t("home.features.title")}
            </h2>
            <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {features.map(({ icon: Icon, titleKey, descKey }) => (
                <article key={titleKey} className={cardSurfaceClass(isDark)}>
                  <div
                    className={
                      "mb-4 inline-flex rounded-lg p-3 " +
                      (isDark
                        ? "bg-sky-500/15 text-sky-300"
                        : "bg-blue-50 text-[#2563eb]")
                    }
                  >
                    <Icon className="h-6 w-6" aria-hidden />
                  </div>
                  <h3
                    className={
                      "text-lg font-bold " +
                      (isDark ? "text-slate-100" : "text-slate-900")
                    }
                  >
                    {t(titleKey)}
                  </h3>
                  <p
                    className={
                      "mt-2 text-sm leading-relaxed " +
                      (isDark ? "text-slate-200" : "text-slate-600")
                    }
                  >
                    {t(descKey)}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Stats */}
        <section
          id="stats"
          className={
            "border-y px-4 py-16 backdrop-blur-sm sm:px-6 " +
            (isDark
              ? "border-slate-600 bg-slate-900"
              : "border-white/80 bg-white/40")
          }
        >
          <div className="mx-auto max-w-6xl">
            <h2
              className={
                "text-center text-2xl font-bold sm:text-3xl " +
                (isDark ? "text-slate-100" : "text-slate-900")
              }
            >
              {t("home.stats.title")}
            </h2>
            <div className="mt-10 grid grid-cols-2 gap-4 lg:grid-cols-4">
              {stats.map(({ valueKey, labelKey }) => (
                <div
                  key={labelKey}
                  className={cardSurfaceClass(isDark) + " text-center"}
                >
                  <p
                    className={
                      "text-3xl font-extrabold sm:text-4xl " +
                      (isDark ? "text-sky-300" : "text-[#2563eb]")
                    }
                  >
                    {t(valueKey)}
                  </p>
                  <p
                    className={
                      "mt-2 text-sm font-medium " +
                      (isDark ? "text-slate-200" : "text-slate-600")
                    }
                  >
                    {t(labelKey)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How it works */}
        <section
          id="how"
          className={
            "scroll-mt-24 px-4 py-16 sm:px-6 " +
            (isDark ? "bg-slate-950" : "bg-transparent")
          }
        >
          <div className="mx-auto max-w-6xl">
            <h2
              className={
                "text-center text-2xl font-bold sm:text-3xl " +
                (isDark ? "text-slate-100" : "text-slate-900")
              }
            >
              {t("home.steps.title")}
            </h2>
            <div className="mt-12 grid gap-8 md:grid-cols-3">
              {steps.map(({ n, titleKey, descKey }) => (
                <div key={n} className={cardSurfaceClass(isDark)}>
                  <div
                    className={
                      "mb-4 flex h-12 w-12 items-center justify-center rounded-lg text-lg font-bold " +
                      (isDark
                        ? "bg-sky-500 text-slate-950"
                        : "bg-[#2563eb] text-white")
                    }
                  >
                    {n}
                  </div>
                  <h3
                    className={
                      "text-lg font-bold " +
                      (isDark ? "text-slate-100" : "text-slate-900")
                    }
                  >
                    {t(titleKey)}
                  </h3>
                  <p
                    className={
                      "mt-2 text-sm leading-relaxed " +
                      (isDark ? "text-slate-200" : "text-slate-600")
                    }
                  >
                    {t(descKey)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer
        className={
          "border-t px-4 py-8 text-center backdrop-blur-sm sm:px-6 " +
          (isDark
            ? "border-slate-600 bg-slate-950"
            : "border-slate-200/80 bg-white/60")
        }
      >
        <p
          className={
            "text-sm font-medium " +
            (isDark ? "text-slate-200" : "text-slate-600")
          }
        >
          {t("home.footer.line")}
        </p>
        <Link
          to="/persona"
          className={
            "mt-4 inline-block text-sm font-semibold hover:underline sm:hidden " +
            (isDark ? "text-sky-400" : "text-[#2563eb]")
          }
        >
          {t("home.nav.skip")}
        </Link>
      </footer>
    </div>
  );
}
