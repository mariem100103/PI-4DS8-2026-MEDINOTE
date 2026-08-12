import { useEffect, useMemo, useState } from "react";
import {
  Loader2,
  Map,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { getAtRiskAndPotential, getHeatmapKpis, getHeatmapMap } from "../api/client";
import {
  FEATURE_PAGE_ROOT,
  FeatureKpiTile,
} from "../components/FeaturePageChrome.jsx";
import { Badge, PageHeader, SectionCard, Skeleton } from "../components/ui";
import { useLanguage } from "../context/LanguageContext.jsx";

function getValueByKeys(source, keys, fallback = "N/A") {
  for (const key of keys) {
    if (source && source[key] !== undefined && source[key] !== null) {
      return source[key];
    }
  }
  return fallback;
}

function formatNumber(value) {
  if (value === "N/A") return value;
  const numeric = Number(value);
  return Number.isNaN(numeric) ? value : numeric.toLocaleString();
}

function formatPercent(value) {
  if (value === "N/A") return value;
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return value;
  return `${numeric.toFixed(1)}%`;
}

function extractTablesData(riskData) {
  return {
    atRisk:
      riskData?.at_risk_physicians ??
      riskData?.at_risk ??
      riskData?.atRiskPhysicians ??
      [],
    topPotential:
      riskData?.top_potential_physicians ??
      riskData?.top_potential ??
      riskData?.topPotentialPhysicians ??
      [],
  };
}

function getTrendClass(trendValue) {
  const trend = Number(trendValue);
  if (Number.isNaN(trend)) return "neutral";
  if (trend > 0.2) return "success";
  if (trend < -0.2) return "danger";
  return "warning";
}

function LegendDot({ className }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 shrink-0 rounded-full ${className}`}
      aria-hidden
    />
  );
}

function PhysiciansTable({ title, subtitle, rows }) {
  const { t } = useLanguage();
  return (
    <SectionCard title={title} subtitle={subtitle}>
      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-600">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-600 dark:bg-slate-800/70 dark:text-slate-300">
              <th className="px-3 py-2.5 font-semibold">
                {t("page.heatmap.table.physician")}
              </th>
              <th className="px-3 py-2.5 font-semibold">
                {t("page.heatmap.table.specialty")}
              </th>
              <th className="px-3 py-2.5 font-semibold">
                {t("page.heatmap.table.region")}
              </th>
              <th className="px-3 py-2.5 font-semibold">
                {t("page.heatmap.table.score")}
              </th>
              <th className="px-3 py-2.5 font-semibold">
                {t("page.heatmap.table.trend")}
              </th>
              <th className="px-3 py-2.5 font-semibold">
                {t("page.heatmap.table.product")}
              </th>
              <th className="px-3 py-2.5 font-semibold">
                {t("page.heatmap.table.visits")}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={7}
                  className="px-3 py-6 text-center text-slate-500 dark:text-slate-400"
                >
                  {t("page.heatmap.table.empty")}
                </td>
              </tr>
            ) : (
              rows.map((row, index) => (
                <tr
                  key={`${title}-${index}`}
                  className="border-b border-slate-100 transition hover:bg-slate-50/80 dark:border-slate-700 dark:hover:bg-slate-800/40"
                >
                  <td className="px-3 py-2.5 text-slate-900 dark:text-slate-100">
                    {getValueByKeys(row, [
                      "physician_name",
                      "name",
                      "medecin",
                      "doctor_name",
                      "nom_medecin",
                    ])}
                  </td>
                  <td className="px-3 py-2.5 text-slate-700 dark:text-slate-300">
                    {getValueByKeys(row, [
                      "specialty",
                      "specialite",
                      "specialty_name",
                      "specialite_medecin",
                    ])}
                  </td>
                  <td className="px-3 py-2.5 text-slate-700 dark:text-slate-300">
                    {getValueByKeys(row, ["region", "region_clean"])}
                  </td>
                  <td className="px-3 py-2.5 font-medium text-[var(--medical-primary-dark)] dark:text-sky-400">
                    {getValueByKeys(row, [
                      "interest_score",
                      "high_interest_proba",
                      "score",
                      "probability",
                      "avg_interet",
                    ])}
                  </td>
                  <td className="px-3 py-2.5">
                    <Badge tone={getTrendClass(getValueByKeys(row, ["trend"], "N/A"))}>
                      {getValueByKeys(row, ["trend"], "N/A")}
                    </Badge>
                  </td>
                  <td className="px-3 py-2.5 text-slate-700 dark:text-slate-300">
                    {getValueByKeys(row, ["top_produit", "top_product", "produit"], "N/A")}
                  </td>
                  <td className="px-3 py-2.5 text-slate-700 dark:text-slate-300">
                    {getValueByKeys(row, [
                      "visits",
                      "visit_count",
                      "doctor_visit_count",
                      "nb_visites",
                    ])}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}

function HeatMap() {
  const { t } = useLanguage();
  const [kpis, setKpis] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [mapHtml, setMapHtml] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setError("");
      setLoading(true);
      try {
        const [kpiRes, riskRes, mapRes] = await Promise.all([
          getHeatmapKpis(),
          getAtRiskAndPotential(),
          getHeatmapMap(),
        ]);
        setKpis(kpiRes);
        setRiskData(riskRes);
        setMapHtml(mapRes);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const { atRisk, topPotential } = extractTablesData(riskData);
  const kpiCards = useMemo(
    () => [
      {
        id: "total_visits",
        title: t("page.heatmap.kpi.total_visits"),
        value: formatNumber(
          getValueByKeys(kpis, ["total_visits", "total_visites", "visits_total", "visit_count"]),
        ),
      },
      {
        id: "physicians",
        title: t("page.heatmap.kpi.physicians"),
        value: formatNumber(
          getValueByKeys(kpis, ["physicians", "total_physicians", "physician_count", "nb_medecins"]),
        ),
      },
      {
        id: "avg_interest",
        title: t("page.heatmap.kpi.avg_interest"),
        value: formatNumber(
          getValueByKeys(kpis, ["avg_interest", "average_interest", "interest_avg", "avg_interet"]),
        ),
      },
      {
        id: "pct_high",
        title: t("page.heatmap.kpi.pct_high"),
        value: formatPercent(
          getValueByKeys(kpis, [
            "high_interest_pct",
            "percent_high_interest",
            "high_interest_percentage",
            "pct_high",
          ]),
        ),
      },
      {
        id: "top_region",
        title: t("page.heatmap.kpi.top_region"),
        value: getValueByKeys(kpis, ["top_region"], "N/A"),
      },
      {
        id: "top_product",
        title: t("page.heatmap.kpi.top_product"),
        value: getValueByKeys(kpis, ["top_produit", "top_product"], "N/A"),
      },
    ],
    [kpis, t],
  );

  return (
    <div className={`heatmap-page ${FEATURE_PAGE_ROOT}`}>
      <PageHeader title={t("page.heatmap.title")} subtitle={t("page.heatmap.subtitle")} />

      {loading && (
        <div
          className="mt-4 flex items-center gap-3 rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-primary-light)] px-4 py-3 text-sm font-medium text-[var(--medical-primary-dark)] dark:border-slate-600 dark:bg-slate-800/90 dark:text-sky-300"
          role="status"
          aria-live="polite"
        >
          <Loader2 className="h-5 w-5 shrink-0 animate-spin opacity-90" aria-hidden />
          {t("page.heatmap.loading")}
        </div>
      )}

      {error && (
        <p
          className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-800 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200"
          role="alert"
        >
          {error}
        </p>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {loading
          ? Array.from({ length: 6 }).map((_, idx) => (
              <SectionCard key={idx}>
                <Skeleton className="h-4 w-28" />
                <Skeleton className="mt-3 h-8 w-40" />
              </SectionCard>
            ))
          : kpiCards.map((card) => (
              <FeatureKpiTile key={card.id} title={card.title} value={card.value} />
            ))}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-[minmax(0,280px)_1fr]">
        <SectionCard
          title={t("page.heatmap.panel.title")}
          subtitle={t("page.heatmap.panel.subtitle")}
        >
          <div className="mt-4 space-y-3">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              {t("page.heatmap.legend.interest_level")}
            </p>
            <div className="space-y-2 text-sm">
              <p className="flex items-center gap-2.5 text-slate-600 dark:text-slate-300">
                <LegendDot className="bg-red-500 shadow-sm ring-1 ring-red-500/30" />
                {t("page.heatmap.band.vhigh")}
              </p>
              <p className="flex items-center gap-2.5 text-slate-600 dark:text-slate-300">
                <LegendDot className="bg-orange-500 shadow-sm ring-1 ring-orange-500/30" />
                {t("page.heatmap.band.high")}
              </p>
              <p className="flex items-center gap-2.5 text-slate-600 dark:text-slate-300">
                <LegendDot className="bg-amber-400 shadow-sm ring-1 ring-amber-400/40" />
                {t("page.heatmap.band.mid")}
              </p>
              <p className="flex items-center gap-2.5 text-slate-600 dark:text-slate-300">
                <LegendDot className="bg-blue-500 shadow-sm ring-1 ring-blue-500/30" />
                {t("page.heatmap.band.low")}
              </p>
            </div>
          </div>

          <div className="mt-5 space-y-3">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              {t("page.heatmap.legend.trend")}
            </p>
            <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
              <p className="flex items-center gap-2.5">
                <TrendingUp className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                {t("page.heatmap.legend.up")}
              </p>
              <p className="flex items-center gap-2.5">
                <TrendingDown className="h-4 w-4 shrink-0 text-rose-600 dark:text-rose-400" />
                {t("page.heatmap.legend.down")}
              </p>
              <p className="flex items-center gap-2.5">
                <Minus className="h-4 w-4 shrink-0 text-slate-500 dark:text-slate-400" />
                {t("page.heatmap.legend.stable")}
              </p>
            </div>
          </div>

          {!loading && (
            <div className="mt-5 rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-gray-50)] p-3 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800/60 dark:text-slate-200">
              <p>
                <span className="font-medium text-slate-500 dark:text-slate-400">
                  {t("page.heatmap.summary.visits")}
                </span>
                : {kpiCards[0].value}
              </p>
              <p className="mt-1">
                <span className="font-medium text-slate-500 dark:text-slate-400">
                  {t("page.heatmap.summary.physicians")}
                </span>
                : {kpiCards[1].value}
              </p>
              <p className="mt-1">
                <span className="font-medium text-slate-500 dark:text-slate-400">
                  {t("page.heatmap.summary.avg")}
                </span>
                : {kpiCards[2].value}/5
              </p>
              <p className="mt-1">
                <span className="font-medium text-slate-500 dark:text-slate-400">
                  {t("page.heatmap.summary.high")}
                </span>
                : {kpiCards[3].value}
              </p>
            </div>
          )}
        </SectionCard>

        <SectionCard
          title={
            <span className="inline-flex items-center gap-2 text-slate-900 dark:text-slate-100">
              <Map className="h-5 w-5 shrink-0 text-[var(--medical-primary)] dark:text-sky-400" />
              {t("page.heatmap.map_card")}
            </span>
          }
        >
          {loading && <Skeleton className="h-[520px] w-full rounded-xl" />}
          {!loading && (
            <iframe
              title={t("page.heatmap.map_iframe_title")}
              className="h-[520px] w-full rounded-xl border border-slate-200 bg-white dark:border-slate-600 dark:bg-slate-900"
              srcDoc={mapHtml}
            />
          )}
        </SectionCard>
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        {loading ? (
          <>
            <SectionCard title={t("page.heatmap.risk.title")} subtitle={t("page.heatmap.risk.subtitle")}>
              <Skeleton className="h-10 w-full" />
              <Skeleton className="mt-3 h-10 w-full" />
              <Skeleton className="mt-3 h-10 w-full" />
            </SectionCard>
            <SectionCard
              title={t("page.heatmap.potential.title")}
              subtitle={t("page.heatmap.potential.subtitle")}
            >
              <Skeleton className="h-10 w-full" />
              <Skeleton className="mt-3 h-10 w-full" />
              <Skeleton className="mt-3 h-10 w-full" />
            </SectionCard>
          </>
        ) : (
          <>
            <PhysiciansTable
              title={t("page.heatmap.risk.title")}
              subtitle={t("page.heatmap.risk.subtitle")}
              rows={atRisk}
            />
            <PhysiciansTable
              title={t("page.heatmap.potential.title")}
              subtitle={t("page.heatmap.potential.subtitle")}
              rows={topPotential}
            />
          </>
        )}
      </div>
    </div>
  );
}

export default HeatMap;
