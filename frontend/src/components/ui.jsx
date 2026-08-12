function PageHeader({ title, subtitle }) {
  return (
    <header className="mb-6">
      <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
      <p className="mt-2 text-slate-600 dark:text-slate-400">{subtitle}</p>
    </header>
  );
}

function Skeleton({ className = "" }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-slate-300/70 ${className}`}
      aria-hidden="true"
    />
  );
}

function Icon({ name, className = "h-5 w-5" }) {
  const common = {
    className,
    fill: "none",
    viewBox: "0 0 24 24",
    xmlns: "http://www.w3.org/2000/svg",
  };

  if (name === "map") {
    return (
      <svg {...common} stroke="currentColor" strokeWidth="1.8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 18 3.5 20V6l5.5-2m0 14 6-2m-6 2V4m6 12 5.5 2V4L15 2m0 14V2" />
      </svg>
    );
  }
  if (name === "tasks") {
    return (
      <svg {...common} stroke="currentColor" strokeWidth="1.8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 6h12M9 12h12M9 18h12" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.5 6.5 5 8l2.5-3M3.5 12.5 5 14l2.5-3M3.5 18.5 5 20l2.5-3" />
      </svg>
    );
  }
  if (name === "spark") {
    return (
      <svg {...common} stroke="currentColor" strokeWidth="1.8">
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 2 3 14h7l-1 8 10-12h-7l1-8Z" />
      </svg>
    );
  }
  return null;
}

function SectionCard({ title, subtitle, children, className = "", tone = "light" }) {
  const isDark = tone === "dark";
  return (
    <section
      className={`rounded-xl border p-4 shadow-sm ${
        isDark
          ? "border-slate-700 bg-slate-900 text-slate-100"
          : "border-slate-200 bg-white text-slate-900 dark:border-slate-600 dark:bg-slate-800/60 dark:text-slate-100"
      } ${className}`}
    >
      {(title || subtitle) && (
        <div className="mb-3">
          {title && (
            <h3
              className={`text-lg font-semibold ${
                isDark ? "text-slate-50" : "text-slate-900 dark:text-slate-100"
              }`}
            >
              {title}
            </h3>
          )}
          {subtitle && (
            <p className={`mt-1 text-sm ${isDark ? "text-slate-300" : "text-slate-500 dark:text-slate-400"}`}>
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </section>
  );
}

function KpiCard({ title, value, accent = "text-slate-900", dark = false }) {
  return (
    <article
      className={`rounded-xl border p-4 shadow-sm ${
        dark
          ? "border-slate-200 bg-slate-900 bg-gradient-to-r from-alia-primary-900 to-alia-secondary-800 text-slate-50"
          : "border-slate-200 bg-white"
      }`}
    >
      <p className={`text-sm ${dark ? "text-slate-100" : "text-slate-600"}`}>{title}</p>
      <p className={`mt-2 text-2xl font-semibold ${dark ? "text-slate-50" : accent}`}>{value}</p>
    </article>
  );
}

function Badge({ children, tone = "neutral" }) {
  const tones = {
    neutral: "bg-slate-100 text-slate-700",
    success: "bg-emerald-100 text-emerald-800",
    warning: "bg-amber-100 text-amber-800",
    danger: "bg-rose-100 text-rose-800",
    info: "bg-alia-primary-100 text-alia-primary-800",
  };

  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${tones[tone] || tones.neutral}`}>
      {children}
    </span>
  );
}

function PrimaryButton({ children, className = "", ...props }) {
  return (
    <button
      {...props}
      className={`rounded-lg bg-slate-900 bg-alia-primary-700 px-5 py-2 font-medium text-white shadow-sm transition hover:bg-slate-800 hover:bg-alia-primary-800 disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
    >
      {children}
    </button>
  );
}

export { Badge, Icon, KpiCard, PageHeader, PrimaryButton, SectionCard, Skeleton };
