import { useMemo, useState } from "react";
import {
  CheckCircle2,
  ShieldAlert,
  UserRoundMinus,
  Sparkles,
  Stethoscope,
  Star,
  Pill,
  AlertTriangle,
  Activity,
} from "lucide-react";
import { predictPersona } from "../api/client";
import { PageHeader, PrimaryButton, SectionCard, Skeleton } from "../components/ui";
import { useLanguage } from "../context/LanguageContext.jsx";

const effectivenessMap = {
  "Tres efficace": 3,
  "Moderement efficace": 2,
  "Peu efficace": 1,
};

const sideEffectsMap = {
  "Effets secondaires legers": 1,
  "Effets secondaires moderes": 2,
  "Effets secondaires severes": 3,
};

const EFFECTIVENESS_VALUES = Object.keys(effectivenessMap);
const SIDE_EFFECT_VALUES = Object.keys(sideEffectsMap);

const EFFECTIVENESS_LABEL_KEY = {
  "Tres efficace": "page.persona.opt_eff.very",
  "Moderement efficace": "page.persona.opt_eff.mod",
  "Peu efficace": "page.persona.opt_eff.low",
};

const SIDE_LABEL_KEY = {
  "Effets secondaires legers": "page.persona.opt_side.light",
  "Effets secondaires moderes": "page.persona.opt_side.mod",
  "Effets secondaires severes": "page.persona.opt_side.severe",
};

const doctors = [
  { name: "Dr Ahmed Ben Youssef", specialty: "Cardiologie", product: "Accutane" },
  { name: "Dr Leila Trabelsi", specialty: "Medecine generale", product: "Concor" },
  { name: "Dr Karim Mansouri", specialty: "Diabetologie", product: "Metformine" },
  { name: "Dr Nadia Hamdi", specialty: "Neurologie", product: "Keppra" },
];

const specialtyEncoders = {
  Cardiologie: 0,
  "Medecine generale": 1,
  Diabetologie: 2,
  Neurologie: 3,
};

const personaCardDefs = [
  {
    id: "highly-receptive",
    titleEn: "Highly Receptive",
    titleKey: "page.persona.persona.highly_title",
    hintKey: "page.persona.persona.high_hint",
    cardClass:
      "border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950/40",
    Icon: CheckCircle2,
    iconClass: "text-emerald-600 dark:text-emerald-400",
  },
  {
    id: "high-resistance",
    titleEn: "High Resistance",
    titleKey: "page.persona.persona.resist_title",
    hintKey: "page.persona.persona.resist_hint",
    cardClass: "border-rose-200 bg-rose-50 dark:border-rose-900 dark:bg-rose-950/40",
    Icon: ShieldAlert,
    iconClass: "text-rose-600 dark:text-rose-400",
  },
  {
    id: "low-engagement",
    titleEn: "Low Engagement",
    titleKey: "page.persona.persona.low_title",
    hintKey: "page.persona.persona.low_hint",
    cardClass:
      "border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-950/40",
    Icon: UserRoundMinus,
    iconClass: "text-orange-600 dark:text-orange-400",
  },
];

const initialValues = {
  doctor_name: doctors[0].name,
  rating: 7,
  effectiveness: "Moderement efficace",
  side_effects: "Effets secondaires legers",
  benefits: "",
  side_review: "",
};

function isSamePersona(predicted, cardTitleEn) {
  const normalize = (value) =>
    String(value || "")
      .toLowerCase()
      .replace(/[^a-z\s]/g, "")
      .trim();

  const p = normalize(predicted);
  const c = normalize(cardTitleEn);
  return p.includes("highly receptive")
    ? c.includes("highly receptive")
    : p.includes("high resistance")
    ? c.includes("high resistance")
    : p.includes("low engagement")
    ? c.includes("low engagement")
    : false;
}

function PersonaCard() {
  const { t } = useLanguage();
  const [formValues, setFormValues] = useState(initialValues);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const selectedDoctor = useMemo(
    () => doctors.find((doctor) => doctor.name === formValues.doctor_name) ?? doctors[0],
    [formValues.doctor_name],
  );

  const displayedCards = useMemo(
    () =>
      personaCardDefs.map((card) => {
        const active = isSamePersona(response?.persona, card.titleEn);
        return { ...card, active };
      }),
    [response],
  );

  const wordCount = (text) =>
    String(text || "")
      .trim()
      .split(/\s+/)
      .filter(Boolean).length;

  const getPersonaLabel = (persona) => {
    const matched = personaCardDefs.find((card) => isSamePersona(persona, card.titleEn));
    return matched ? t(matched.titleKey) : t("page.persona.unknown");
  };

  const handleFieldChange = (field, value) => {
    setFormValues((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResponse(null);

    const effectivenessScore = effectivenessMap[formValues.effectiveness] ?? 2;
    const sideEffectsScore = sideEffectsMap[formValues.side_effects] ?? 1;
    const benefitsWords = wordCount(formValues.benefits);
    const sideWords = wordCount(formValues.side_review);
    const specialtyEnc = specialtyEncoders[selectedDoctor.specialty] ?? 0;

    const payload = {
      physician_name: formValues.doctor_name,
      doctor_visit_count: Number(formValues.rating) * 40,
      specialty_visit_count: Number(formValues.rating) * 20,
      product_visit_count: Number(formValues.rating) * 12,
      reponse_wc: benefitsWords,
      reponse_len: String(formValues.benefits || "").length,
      resume_visite_wc: sideWords,
      commentaire_visite_wc: benefitsWords + sideWords,
      specialite_medecin_enc: specialtyEnc,
      medicament_enc: effectivenessScore - 1,
      type_visite_enc: sideEffectsScore >= 2 ? 1 : 0,
      objectif_visite_enc: effectivenessScore >= 2 ? 1 : 2,
    };

    try {
      const result = await predictPersona(payload);
      setResponse({
        persona: result.persona ?? result.persona_name ?? "Unknown",
        strategy: result.strategy ?? "N/A",
        objection: result.objection ?? "N/A",
        high_interest_proba: result.high_interest_proba ?? result.proba ?? "N/A",
        nbaCommercial:
          effectivenessScore >= 2
            ? {
                label: "Potentiel a developper",
                actions: [
                  "Laisser une documentation explicative",
                  "Prevoir un appel de suivi dans 2 semaines",
                ],
              }
            : {
                label: "Activation prioritaire",
                actions: [
                  "Programmer une visite de demonstration",
                  "Partager des cas cliniques adaptes",
                ],
              },
        nbaRisk:
          sideEffectsScore >= 3
            ? {
                label: "Risque eleve",
                actions: [
                  "Adapter rapidement les conditions de prise",
                  "Prevoir un suivi medical rapproche",
                ],
              }
            : sideEffectsScore === 2
            ? {
                label: "Risque modere",
                actions: [
                  "Adapter les conditions de prise (dose, moment)",
                  "Prevoir un suivi medical rapproche",
                ],
              }
            : {
                label: "Risque faible",
                actions: [
                  "Maintenir le schema de suivi actuel",
                  "Rappeler les bonnes pratiques d'observance",
                ],
              },
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-slate-900 outline-none transition " +
    "focus:border-[var(--medical-primary)] focus:ring-2 focus:ring-[var(--medical-primary-light)] " +
    "dark:border-slate-600 dark:bg-slate-900/60 dark:text-slate-100";

  const labelClass =
    "mb-2 flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200";

  return (
    <div className="persona-page mx-auto max-w-7xl px-1">
      <PageHeader title={t("page.persona.title")} subtitle={t("page.persona.subtitle")} />

      <form
        onSubmit={handleSubmit}
        className="medical-form mt-6 max-w-5xl border border-[var(--medical-gray-100)] shadow-[var(--shadow-md)] dark:border-slate-600 dark:bg-slate-900/40"
      >
        <div className="grid gap-5 md:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="persona-doctor">
              <Stethoscope className="h-4 w-4 text-[var(--medical-primary)]" aria-hidden />
              {t("page.persona.field.doctor")}
            </label>
            <select
              id="persona-doctor"
              value={formValues.doctor_name}
              onChange={(event) => handleFieldChange("doctor_name", event.target.value)}
              className={inputClass}
            >
              {doctors.map((doctor) => (
                <option key={doctor.name} value={doctor.name}>
                  {doctor.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass} htmlFor="persona-rating">
              <Star className="h-4 w-4 text-[var(--medical-primary)]" aria-hidden />
              {t("page.persona.field.rating")}
            </label>
            <input
              id="persona-rating"
              type="range"
              min={1}
              max={10}
              step={1}
              value={formValues.rating}
              onChange={(event) => handleFieldChange("rating", Number(event.target.value))}
              className="w-full accent-[var(--medical-primary)]"
            />
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              {t("page.persona.field.rating_value", { value: formValues.rating })}
            </p>
          </div>
          <div>
            <label className={labelClass} htmlFor="persona-eff">
              <Pill className="h-4 w-4 text-[var(--medical-primary)]" aria-hidden />
              {t("page.persona.field.effectiveness")}
            </label>
            <select
              id="persona-eff"
              value={formValues.effectiveness}
              onChange={(event) => handleFieldChange("effectiveness", event.target.value)}
              className={inputClass}
            >
              {EFFECTIVENESS_VALUES.map((key) => (
                <option key={key} value={key}>
                  {t(EFFECTIVENESS_LABEL_KEY[key])}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass} htmlFor="persona-side">
              <AlertTriangle className="h-4 w-4 text-[var(--medical-warning)]" aria-hidden />
              {t("page.persona.field.side_effects")}
            </label>
            <select
              id="persona-side"
              value={formValues.side_effects}
              onChange={(event) => handleFieldChange("side_effects", event.target.value)}
              className={inputClass}
            >
              {SIDE_EFFECT_VALUES.map((key) => (
                <option key={key} value={key}>
                  {t(SIDE_LABEL_KEY[key])}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-6 grid gap-5 md:grid-cols-2">
          <div>
            <label className={labelClass} htmlFor="persona-benefits">
              <CheckCircle2 className="h-4 w-4 text-[var(--medical-success)]" aria-hidden />
              {t("page.persona.field.benefits")}
            </label>
            <textarea
              id="persona-benefits"
              value={formValues.benefits}
              onChange={(event) => handleFieldChange("benefits", event.target.value)}
              rows={3}
              className={inputClass}
              placeholder={t("page.persona.field.benefits_ph")}
            />
          </div>
          <div>
            <label className={labelClass} htmlFor="persona-side-detail">
              <Activity className="h-4 w-4 text-[var(--medical-primary)]" aria-hidden />
              {t("page.persona.field.side_detail")}
            </label>
            <textarea
              id="persona-side-detail"
              value={formValues.side_review}
              onChange={(event) => handleFieldChange("side_review", event.target.value)}
              rows={3}
              className={inputClass}
              placeholder={t("page.persona.field.side_detail_ph")}
            />
          </div>
        </div>

        <div className="mt-6 grid gap-3 rounded-xl border border-[var(--medical-gray-100)] bg-[var(--medical-gray-50)] p-4 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800/50 dark:text-slate-200 md:grid-cols-4">
          <p>
            {t("page.persona.stats.benefits_wc")}:{" "}
            <span className="font-semibold text-[var(--medical-primary-dark)] dark:text-sky-400">
              {wordCount(formValues.benefits)}
            </span>
          </p>
          <p>
            {t("page.persona.stats.benefits_len")}:{" "}
            <span className="font-semibold text-[var(--medical-primary-dark)] dark:text-sky-400">
              {String(formValues.benefits || "").length}
            </span>
          </p>
          <p>
            {t("page.persona.stats.side_wc")}:{" "}
            <span className="font-semibold text-[var(--medical-primary-dark)] dark:text-sky-400">
              {wordCount(formValues.side_review)}
            </span>
          </p>
          <p>
            {t("page.persona.stats.specialty")}:{" "}
            <span className="font-semibold text-[var(--medical-primary-dark)] dark:text-sky-400">
              {selectedDoctor.specialty}
            </span>
          </p>
        </div>

        <div className="mt-6">
          <PrimaryButton type="submit" disabled={loading} className="inline-flex items-center gap-2">
            <Sparkles className="h-5 w-5 shrink-0" aria-hidden />
            {loading ? t("page.persona.generating") : t("page.persona.generate_btn")}
          </PrimaryButton>
        </div>
      </form>

      {error && (
        <p
          className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-800 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-200"
          role="alert"
        >
          {error}
        </p>
      )}

      {loading && (
        <div className="mt-6 space-y-4">
          <SectionCard title={t("page.persona.smart_card")}>
            <Skeleton className="h-6 w-64" />
            <Skeleton className="mt-4 h-24 w-full" />
          </SectionCard>
          <div className="grid gap-4 md:grid-cols-3">
            <SectionCard>
              <Skeleton className="h-6 w-40" />
              <Skeleton className="mt-3 h-12 w-full" />
            </SectionCard>
            <SectionCard>
              <Skeleton className="h-6 w-40" />
              <Skeleton className="mt-3 h-12 w-full" />
            </SectionCard>
            <SectionCard>
              <Skeleton className="h-6 w-40" />
              <Skeleton className="mt-3 h-12 w-full" />
            </SectionCard>
          </div>
        </div>
      )}

      {response && (
        <SectionCard className="mt-6 space-y-4" tone="dark">
          <div className="rounded-xl border border-slate-600/80 bg-slate-800/50 p-4 transition hover:border-[var(--medical-primary-medium)]">
            <p className="flex items-center gap-2 text-base font-semibold text-slate-50">
              <Stethoscope className="h-5 w-5 text-sky-400" aria-hidden />
              {t("page.persona.result.banner_title")}
            </p>
            <p className="mt-3 text-slate-200">
              <span className="font-medium text-slate-400">{t("page.persona.result.doctor")}:</span>{" "}
              {formValues.doctor_name}
            </p>
            <p className="mt-1 text-slate-200">
              <span className="font-medium text-slate-400">{t("page.persona.result.specialty")}:</span>{" "}
              {selectedDoctor.specialty}
            </p>
            <p className="mt-1 text-slate-200">
              <span className="font-medium text-slate-400">{t("page.persona.result.product")}:</span>{" "}
              {selectedDoctor.product}
            </p>
          </div>

          <div className="rounded-xl border border-slate-600/80 bg-slate-800/50 p-4 transition hover:border-[var(--medical-primary-medium)]">
            <p className="font-semibold text-slate-50">
              {t("page.persona.result.persona_block")}: {getPersonaLabel(response.persona)}
            </p>
            <p className="mt-2 text-slate-200">
              {t("page.persona.result.metrics", {
                avg: (Number(formValues.rating) / 2).toFixed(2),
                visits: Number(formValues.rating) * 40,
                proba: response.high_interest_proba,
              })}
            </p>
            <p className="mt-2 text-slate-200">
              <span className="font-medium text-slate-400">{t("page.persona.result.objection")}:</span>{" "}
              {response.objection}
            </p>
            <p className="mt-2 text-slate-200">
              <span className="font-medium text-slate-400">{t("page.persona.result.strategy")}:</span>{" "}
              {response.strategy}
            </p>
          </div>

          <div className="rounded-xl border border-slate-600/80 bg-slate-800/50 p-4 transition hover:border-[var(--medical-primary-medium)]">
            <p className="font-semibold text-slate-50">{t("page.persona.result.nba_com")}</p>
            <p className="mt-2 text-slate-200">
              <span className="font-medium text-slate-400">{t("page.persona.result.label")}:</span>{" "}
              {response.nbaCommercial.label}
            </p>
            <p className="mt-2 font-medium text-slate-300">{t("page.persona.result.actions")}</p>
            <ul className="mt-1 list-disc space-y-1 pl-6 text-slate-200">
              {response.nbaCommercial.actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl border border-slate-600/80 bg-slate-800/50 p-4 transition hover:border-[var(--medical-primary-medium)]">
            <p className="font-semibold text-slate-50">{t("page.persona.result.nba_risk")}</p>
            <p className="mt-2 text-slate-200">
              <span className="font-medium text-slate-400">{t("page.persona.result.label")}:</span>{" "}
              {response.nbaRisk.label}
            </p>
            <p className="mt-2 font-medium text-slate-300">{t("page.persona.result.actions")}</p>
            <ul className="mt-1 list-disc space-y-1 pl-6 text-slate-200">
              {response.nbaRisk.actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </div>
        </SectionCard>
      )}

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {displayedCards.map((card) => {
          const CardIcon = card.Icon;
          return (
            <article
              key={card.id}
              className={`rounded-xl border p-5 shadow-sm transition dark:shadow-black/20 ${card.cardClass} ${
                card.active
                  ? "ring-2 ring-[var(--medical-primary)] ring-offset-2 ring-offset-[var(--medical-gray-50)] dark:ring-sky-500 dark:ring-offset-slate-950"
                  : "opacity-90"
              }`}
            >
              <div className="flex items-start gap-3">
                <CardIcon className={`mt-0.5 h-6 w-6 shrink-0 ${card.iconClass}`} aria-hidden />
                <div>
                  <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {t(card.titleKey)}
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                    {t(card.hintKey)}
                  </p>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      {!response && (
        <p className="mt-6 text-sm text-slate-600 dark:text-slate-400">{t("page.persona.empty_hint")}</p>
      )}
    </div>
  );
}

export default PersonaCard;
