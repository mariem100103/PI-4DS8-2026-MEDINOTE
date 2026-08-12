import { useEffect, useMemo, useState } from "react";
import { useLanguage } from "../context/LanguageContext.jsx";
import {
  getFollowupCsvExportUrl,
  getFollowupIcsExportUrl,
  getFollowupKpis,
  getFollowupTasks,
} from "../api/client";
import {
  FEATURE_PAGE_ROOT,
  FeatureKpiTile,
  FeatureErrorBox,
  FeatureLoadingBanner,
  FIELD_INPUT_CLASS,
} from "../components/FeaturePageChrome.jsx";
import { Loader2, ListChecks } from "lucide-react";
import { Badge, PageHeader, SectionCard, Skeleton } from "../components/ui";

function getValueByKeys(source, keys, fallback = "N/A") {
  for (const key of keys) {
    if (source && source[key] !== undefined && source[key] !== null) {
      return source[key];
    }
  }
  return fallback;
}

function normalizePriority(task) {
  const raw = String(
    getValueByKeys(
      task,
      ["priorite", "priority", "priority_level", "color", "risk_level", "level"],
      ""
    )
  ).toUpperCase();
  // Backend follow-up module uses FR labels: ROUGE / ORANGE / VERT
  if (raw === "ROUGE" || raw.includes("ROUGE") || raw.includes("RED")) return "ROUGE";
  if (raw === "ORANGE" || raw.includes("ORANGE")) return "ORANGE";
  if (raw === "VERT" || raw.includes("VERT") || raw.includes("GREEN")) return "VERT";
  // Fallback: niveau d'intérêt numérique (API ALIA)
  const interet = Number(
    getValueByKeys(task, ["interet", "niveau_interet", "interest_level"], NaN)
  );
  if (!Number.isNaN(interet)) {
    if (interet >= 4) return "ROUGE";
    if (interet === 3) return "ORANGE";
    return "VERT";
  }
  return "INCONNU";
}

function getPriorityClasses(priority) {
  if (priority === "ROUGE") {
    return "border-rose-200 bg-rose-50 dark:border-rose-900/60 dark:bg-rose-950/30";
  }
  if (priority === "ORANGE") {
    return "border-orange-200 bg-orange-50 dark:border-orange-900/60 dark:bg-orange-950/30";
  }
  if (priority === "VERT") {
    return "border-emerald-200 bg-emerald-50 dark:border-emerald-900/60 dark:bg-emerald-950/30";
  }
  return "border-slate-200 bg-slate-50 dark:border-slate-600 dark:bg-slate-800/50";
}

function getPriorityTone(priority) {
  if (priority === "ROUGE") return "danger";
  if (priority === "ORANGE") return "warning";
  if (priority === "VERT") return "success";
  return "neutral";
}

const EMPTY_TASKS = [];

function extractTasksPayload(tasksRes) {
  if (tasksRes == null) return EMPTY_TASKS;
  if (Array.isArray(tasksRes)) return tasksRes;
  if (Array.isArray(tasksRes.tasks)) return tasksRes.tasks;
  if (Array.isArray(tasksRes.data?.tasks)) return tasksRes.data.tasks;
  if (Array.isArray(tasksRes.data)) return tasksRes.data;
  return EMPTY_TASKS;
}

/** Lowercase + strip accents for tolerant search (médecin / medecin). */
function foldForSearch(value) {
  const s = String(value ?? "");
  try {
    return s
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  } catch {
    return s.toLowerCase();
  }
}

function FollowUp() {
  const { t } = useLanguage();
  const [tasksPayload, setTasksPayload] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [error, setError] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [loadingKpis, setLoadingKpis] = useState(true);
  const [loadingTasks, setLoadingTasks] = useState(true);

  useEffect(() => {
    const loadKpis = async () => {
      setError("");
      setLoadingKpis(true);
      try {
        const kpisRes = await getFollowupKpis();
        setKpis(kpisRes);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingKpis(false);
      }
    };
    loadKpis();
  }, []);

  useEffect(() => {
    const loadTasks = async () => {
      setError("");
      setLoadingTasks(true);
      try {
        // Full list once; priority + search are applied in the UI so behavior
        // does not depend on query-string filtering (cache / proxy / API quirks).
        const tasksRes = await getFollowupTasks({});
        setTasksPayload(tasksRes);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingTasks(false);
      }
    };
    loadTasks();
  }, []);

  const rawTasks = useMemo(() => extractTasksPayload(tasksPayload), [tasksPayload]);

  const mappedTasks = useMemo(
    () =>
      rawTasks.map((task, index) => ({
        id: getValueByKeys(task, ["id", "task_id"], `task-${index}`),
        physicianName: getValueByKeys(task, [
          "physician_name",
          "doctor_name",
          "medecin",
          "name",
          "nom_medecin",
        ]),
        taskLabel: getValueByKeys(task, [
          "task",
          "title",
          "action",
          "description",
          "prochaine_action",
        ]),
        dueDate: getValueByKeys(
          task,
          ["due_date", "date", "next_visit_date", "date_rappel"],
          t("page.followup.date_unspecified"),
        ),
        priority: normalizePriority(task),
        searchBlob: [
          getValueByKeys(task, [
            "physician_name",
            "doctor_name",
            "medecin",
            "name",
            "nom_medecin",
          ]),
          getValueByKeys(task, [
            "task",
            "title",
            "action",
            "description",
            "prochaine_action",
          ]),
          getValueByKeys(task, ["specialite", "specialite_medecin", "specialty"], ""),
          getValueByKeys(task, ["medicament", "medication", "product"], ""),
          getValueByKeys(task, ["region", "region_clean"], ""),
          getValueByKeys(task, ["objection", "objection_clean"], ""),
        ]
          .filter(Boolean)
          .join(" "),
      })),
    [rawTasks, t],
  );

  const priorityFiltered = useMemo(() => {
    if (priorityFilter === "ALL") return mappedTasks;
    return mappedTasks.filter((task) => task.priority === priorityFilter);
  }, [mappedTasks, priorityFilter]);

  const visibleTasks = useMemo(() => {
    const q = search.trim();
    if (!q) return priorityFiltered;
    const needle = foldForSearch(q);
    return priorityFiltered.filter((task) => foldForSearch(task.searchBlob).includes(needle));
  }, [priorityFiltered, search]);

  const kpiCards = useMemo(
    () => [
      {
        id: "total",
        title: t("page.followup.kpi.total_tasks"),
        value: getValueByKeys(kpis, ["total_tasks", "tasks_total", "total"], tasksPayload?.total ?? 0),
        valueClass: "",
      },
      {
        id: "red",
        title: t("page.followup.kpi.red"),
        value: getValueByKeys(kpis, ["red_count", "RED", "red", "nb_rouge"], tasksPayload?.nb_rouge ?? 0),
        valueClass: "!text-rose-600 dark:!text-rose-400",
      },
      {
        id: "orange",
        title: t("page.followup.kpi.orange"),
        value: getValueByKeys(kpis, ["orange_count", "ORANGE", "orange", "nb_orange"], tasksPayload?.nb_orange ?? 0),
        valueClass: "!text-orange-600 dark:!text-orange-400",
      },
      {
        id: "green",
        title: t("page.followup.kpi.green"),
        value: getValueByKeys(kpis, ["green_count", "GREEN", "green", "nb_vert"], tasksPayload?.nb_vert ?? 0),
        valueClass: "!text-emerald-600 dark:!text-emerald-400",
      },
    ],
    [kpis, tasksPayload, t],
  );

  return (
    <section className={FEATURE_PAGE_ROOT}>
      <PageHeader
        title={t("page.followup.title")}
        subtitle={t("page.followup.subtitle")}
      />

      <div className="mt-4 flex flex-wrap gap-3">
        <a
          href={getFollowupCsvExportUrl()}
          className="inline-flex items-center justify-center rounded-lg border border-transparent bg-[var(--medical-primary)] px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-95 dark:bg-sky-600 dark:text-slate-950"
        >
          {t("page.followup.export_csv")}
        </a>
        <a
          href={getFollowupIcsExportUrl()}
          className="inline-flex items-center justify-center rounded-lg border border-[var(--medical-gray-100)] bg-[var(--medical-white)] px-4 py-2.5 text-sm font-semibold text-[var(--medical-primary-dark)] shadow-sm transition hover:bg-[var(--medical-primary-light)] dark:border-slate-600 dark:bg-slate-800 dark:text-sky-300 dark:hover:bg-slate-700"
        >
          {t("page.followup.export_ics")}
        </a>
      </div>

      {error && <FeatureErrorBox>{error}</FeatureErrorBox>}

      {(loadingKpis || loadingTasks) && (
        <FeatureLoadingBanner>
          <Loader2 className="h-5 w-5 shrink-0 animate-spin" aria-hidden />
          {t("page.followup.loading")}
        </FeatureLoadingBanner>
      )}

      <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {loadingKpis
          ? Array.from({ length: 4 }).map((_, idx) => (
              <SectionCard key={idx}>
                <Skeleton className="h-4 w-28" />
                <Skeleton className="mt-3 h-8 w-24" />
              </SectionCard>
            ))
          : kpiCards.map((card) => (
              <FeatureKpiTile
                key={card.id}
                title={card.title}
                value={card.value}
                valueClassName={card.valueClass}
              />
            ))}
      </div>

      <SectionCard
        className="mt-6"
        title={
          <span className="inline-flex items-center gap-2 text-slate-900 dark:text-slate-100">
            <ListChecks className="h-5 w-5 shrink-0 text-[var(--medical-primary)] dark:text-sky-400" />
            {t("page.followup.section_tasks")}
          </span>
        }
      >
        <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex w-full flex-col gap-2 sm:flex-row sm:items-center">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={t("page.followup.search_placeholder")}
              className={`${FIELD_INPUT_CLASS} min-w-0 py-2`}
            />
            <select
              value={priorityFilter}
              onChange={(event) => setPriorityFilter(event.target.value)}
              className={`${FIELD_INPUT_CLASS} w-full shrink-0 sm:w-56`}
            >
              <option value="ALL">{t("page.followup.priority_all")}</option>
              <option value="ROUGE">ROUGE</option>
              <option value="ORANGE">ORANGE</option>
              <option value="VERT">VERT</option>
            </select>
          </div>
        </div>

        <div className="grid gap-3">
          {loadingTasks ? (
            <>
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </>
          ) : visibleTasks.length === 0 ? (
            <p className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-slate-600 dark:border-slate-600 dark:bg-slate-800/40 dark:text-slate-400">
              {mappedTasks.length === 0
                ? t("page.followup.empty.none")
                : priorityFiltered.length === 0
                  ? t("page.followup.empty.priority")
                  : t("page.followup.empty.search")}
            </p>
          ) : (
            visibleTasks.map((task, index) => (
              <article
                key={`${task.id}-${index}`}
                className={`rounded-lg border p-4 transition hover:-translate-y-0.5 hover:shadow-sm ${getPriorityClasses(task.priority)}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-slate-900 dark:text-slate-100">{task.physicianName}</p>
                    <p className="mt-1 break-words text-sm text-slate-800 dark:text-slate-200">
                      {task.taskLabel}
                    </p>
                    <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
                      {t("page.followup.due")}: {task.dueDate}
                    </p>
                  </div>
                  <Badge tone={getPriorityTone(task.priority)}>{task.priority}</Badge>
                </div>
              </article>
            ))
          )}
        </div>
      </SectionCard>
    </section>
  );
}

export default FollowUp;
