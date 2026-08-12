import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

const STORAGE_KEY = "alia_crm_language";

/** @type {Record<'fr' | 'en', Record<string, string>>} */
const translations = {
  fr: {
    // Commun (étendu au fil des pages)
    "common.loading": "Chargement…",
    "common.save": "Enregistrer",
    "common.cancel": "Annuler",
    "common.delete": "Supprimer",
    "common.edit": "Modifier",
    "common.search": "Rechercher",
    "common.language": "Langue",
    "common.theme.light": "Clair",
    "common.theme.dark": "Sombre",
    "common.theme.toggle_dark": "Passer en mode sombre",
    "common.theme.toggle_light": "Passer en mode clair",
    "common.backHome": "Retour à l’accueil",
    "common.send": "Envoyer",

    // Navigation (clés pour la sidebar — à brancher plus tard)
    "nav.home": "Accueil",
    "nav.sidebar_heading": "Fonctionnalités",
    "nav.dashboard": "Vue d'ensemble",
    "nav.persona": "Profils Médecins",
    "nav.heatmap": "Carte Visites",
    "nav.followup": "Planification",
    "nav.profile": "Profil",
    "nav.correcteur": "Rapports Visites",
    "nav.extraction": "Saisie Rapide",
    "nav.coaching": "Aide Terrain",
    "nav.chatbot": "Assistant Médicaments",
    "nav.rapport_extract": "Nouveau Rapport",
    "nav.rapport_history": "Historique",

    // Auth
    "auth.login": "Connexion",
    "auth.logout": "Déconnexion",
    "auth.register": "Créer un compte",
    "auth.email": "E-mail",
    "auth.password": "Mot de passe",
    "auth.name": "Nom complet",
    "auth.role": "Rôle",
    "auth.role.admin": "Administrateur",
    "auth.role.delegate": "Délégué",
    "auth.remember": "Se souvenir de moi",
    "auth.noAccount": "Pas encore de compte ?",
    "auth.hasAccount": "Déjà un compte ?",
    "auth.login_subtitle": "Connexion à votre espace Vital Labo Tunisia",
    "auth.register_subtitle": "Créer un compte délégué ou administrateur",
    "auth.register_submit": "Créer mon compte",
    "auth.password_confirm": "Confirmer le mot de passe",
    "auth.demo_hint":
      "Démo : les comptes fournis utilisent le mot de passe « demo123 » (ex. admin@vital-labo.tn).",
    "auth.error.invalid_credentials": "E-mail ou mot de passe incorrect.",
    "auth.error.account_suspended": "Compte suspendu",
    "auth.error.email_exists": "Cette adresse e-mail est déjà utilisée.",
    "auth.error.password_mismatch": "Les mots de passe ne correspondent pas.",
    "auth.error.password_short":
      "Le mot de passe doit contenir au moins 4 caractères.",

    "nav.admin": "Administration",

    "admin.dashboard.title": "Tableau de bord administrateur",
    "admin.dashboard.heading": "Vue d’ensemble",
    "admin.dashboard.open_crm": "Ouvrir le CRM",
    "admin.dashboard.kpi.users": "Utilisateurs",
    "admin.dashboard.kpi.delegates": "Délégués",
    "admin.dashboard.kpi.admins": "Administrateurs",
    "admin.dashboard.kpi.visits_mock": "Visites analysées (CRM)",
    "admin.dashboard.users_preview": "Utilisateurs",
    "admin.dashboard.users_hint":
      "Liste issue du stockage local (données mock).",
    "admin.dashboard.full_users_later":
      "L’écran complet de gestion des utilisateurs pourra être branché ici.",

    // Accueil
    "home.hero.title": "ALIA CRM",
    "home.hero.subtitle":
      "CRM alimenté par l’IA pour les délégués médicaux — Vital Labo Tunisia",
    "home.hero.slogan.visit": "Visitez plus intelligemment.",
    "home.hero.slogan.act": "Agissez plus vite.",
    "home.hero.slogan.sell": "Vendez mieux.",
    "home.hero.badge": "Plateforme délégués médicaux",
    "home.cta.start": "Commencer",
    "home.cta.learn": "En savoir plus",
    "home.features.title": "Fonctionnalités principales",
    "home.features.persona.title": "Moteur Persona",
    "home.features.persona.desc":
      "Segmentation des médecins en profils comportementaux (réceptifs, résistants, faible engagement).",
    "home.features.heatmap.title": "Carte de chaleur",
    "home.features.heatmap.desc":
      "Carte interactive des visites et de l’activité sur les régions tunisiennes.",
    "home.features.followup.title": "Suivi automatisé",
    "home.features.followup.desc":
      "Tâches de relance priorisées selon l’urgence (rouge, orange, vert).",
    "home.features.coach.title": "Coach vocal",
    "home.features.coach.desc":
      "Transcription des notes vocales et génération de rapports CRM assistée par IA.",
    "home.features.correcteur.title": "Correction de texte",
    "home.features.correcteur.desc":
      "Normalisation et nettoyage automatiques des comptes rendus de visite.",
    "home.features.reports.title": "Rapports intelligents",
    "home.features.reports.desc":
      "Rapports structurés, score qualité et assistant conversationnel.",
    "home.stats.title": "Chiffres clés",
    "home.stats.visits": "visites analysées",
    "home.stats.physicians": "médecins",
    "home.stats.regions": "régions tunisiennes",
    "home.stats.modules": "modules IA",
    "home.stats.visits.value": "4 142",
    "home.stats.physicians.value": "10",
    "home.stats.regions.value": "23",
    "home.stats.modules.value": "8",
    "home.steps.title": "Comment ça marche",
    "home.steps.one.title": "Visite terrain",
    "home.steps.one.desc":
      "Saisie ou dictée des notes après les consultations.",
    "home.steps.two.title": "Analyse IA",
    "home.steps.two.desc":
      "Extraction, persona, carte et contrôle qualité automatiques.",
    "home.steps.three.title": "Actions intelligentes",
    "home.steps.three.desc":
      "Relances, rapports et coaching pour optimiser la performance.",
    "home.footer.line": "ALIA CRM © 2026 — Vital Labo Tunisia",
    "home.login.wip": "La page de connexion arrive à l’étape suivante.",
    "home.nav.skip": "Accéder au CRM",

    "nav.reports_menu": "Rapports",
    "nav.history_menu": "Historique rapports",

    "shell.sidebar.platform": "Plateforme",
    "shell.sidebar.demo": "DEMO",
    "shell.sidebar.close": "Fermer",
    "shell.sidebar.navigation": "Navigation",
    "shell.sidebar.tip_title": "Conseil du jour",
    "shell.sidebar.tip_body":
      "Priorisez les médecins ROUGE pour maximiser l’impact des visites terrain.",
    "shell.sidebar.link_persona": "Carte Persona",
    "shell.sidebar.link_heatmap": "Carte de chaleur",
    "shell.sidebar.tagline": "Assistant intelligent délégués médicaux",

    "shell.topbar.menu": "Menu",
    "shell.topbar.open_menu": "Ouvrir le menu",
    "shell.topbar.dashboard": "Tableau de bord",
    "shell.topbar.subtitle":
      "ALIA CRM — suivi intelligent des interactions médecins",
    "shell.topbar.demo_mode": "Mode démo",

    "page.persona.title": "Profils médecins (Persona)",
    "page.persona.subtitle":
      "Analysez le profil comportemental et obtenez stratégie, objections et recommandations.",
    "page.persona.smart_card": "Carte intelligente",
    "page.persona.generating": "Génération en cours…",
    "page.persona.generate_btn": "Générer la carte d’intelligence",
    "page.persona.field.doctor": "Médecin",
    "page.persona.field.rating": "Niveau d’intérêt (1–10)",
    "page.persona.field.rating_value": "Valeur : {value}/10",
    "page.persona.field.effectiveness": "Efficacité perçue",
    "page.persona.field.side_effects": "Effets secondaires",
    "page.persona.field.benefits": "Bénéfices observés",
    "page.persona.field.benefits_ph":
      "Ex. : amélioration clinique, bonne observance…",
    "page.persona.field.side_detail": "Détail effets secondaires",
    "page.persona.field.side_detail_ph":
      "Ex. : nausées légères, fatigue…",
    "page.persona.stats.benefits_wc": "Mots (bénéfices)",
    "page.persona.stats.benefits_len": "Caractères (bénéfices)",
    "page.persona.stats.side_wc": "Mots (effets sec.)",
    "page.persona.stats.specialty": "Spécialité",
    "page.persona.opt_eff.very": "Très efficace",
    "page.persona.opt_eff.mod": "Modérément efficace",
    "page.persona.opt_eff.low": "Peu efficace",
    "page.persona.opt_side.light": "Effets secondaires légers",
    "page.persona.opt_side.mod": "Effets secondaires modérés",
    "page.persona.opt_side.severe": "Effets secondaires sévères",
    "page.persona.persona.highly_title": "Hautement réceptif",
    "page.persona.persona.high_hint":
      "Consolider avec données cliniques et prochaine visite planifiée.",
    "page.persona.persona.resist_title": "Forte résistance",
    "page.persona.persona.resist_hint":
      "Traiter les objections (tolérance, effets) avec preuves structurées.",
    "page.persona.persona.low_title": "Faible engagement",
    "page.persona.persona.low_hint":
      "Relancer : essai produit, événement médical ou escalation manager.",
    "page.persona.result.banner_title": "Carte d’intelligence médecin",
    "page.persona.result.doctor": "Médecin",
    "page.persona.result.specialty": "Spécialité",
    "page.persona.result.product": "Produit principal",
    "page.persona.result.persona_block": "Persona HCP",
    "page.persona.result.metrics":
      "Intérêt moyen : {avg}/5 · Visites : {visits} · Intérêt élevé : {proba}%",
    "page.persona.result.objection": "Objection fréquente",
    "page.persona.result.strategy": "Stratégie HCP",
    "page.persona.result.nba_com": "NBA — Recommandation commerciale",
    "page.persona.result.nba_risk": "NBA — Analyse du risque",
    "page.persona.result.label": "Libellé",
    "page.persona.result.actions": "Actions",
    "page.persona.empty_hint":
      "Générez une carte pour afficher le détail complet et les blocs NBA.",
    "page.persona.unknown": "Persona inconnu",

    "page.heatmap.title": "Carte de chaleur",
    "page.heatmap.subtitle":
      "Vue géographique des performances et priorisation des risques médecins.",
    "page.heatmap.loading": "Chargement des analyses de la carte…",
    "page.heatmap.kpi.total_visits": "Total des visites",
    "page.heatmap.kpi.physicians": "Médecins",
    "page.heatmap.kpi.avg_interest": "Intérêt moyen",
    "page.heatmap.kpi.pct_high": "% Intérêt élevé",
    "page.heatmap.kpi.top_region": "Top région",
    "page.heatmap.kpi.top_product": "Top produit",
    "page.heatmap.panel.title": "Panneau de lecture",
    "page.heatmap.panel.subtitle":
      "Résumé rapide des niveaux d’intérêt et de tendance.",
    "page.heatmap.legend.interest_level": "Niveau d’intérêt",
    "page.heatmap.legend.trend": "Tendance",
    "page.heatmap.legend.up": "Intérêt croissant",
    "page.heatmap.legend.down": "Intérêt décroissant",
    "page.heatmap.legend.stable": "Stable",
    "page.heatmap.band.vhigh": "Très élevé (&gt;=4/5)",
    "page.heatmap.band.high": "Élevé (3-4/5)",
    "page.heatmap.band.mid": "Moyen (2-3/5)",
    "page.heatmap.band.low": "Faible (&lt;2/5)",
    "page.heatmap.summary.visits": "Visites",
    "page.heatmap.summary.physicians": "Médecins",
    "page.heatmap.summary.avg": "Intérêt moyen",
    "page.heatmap.summary.high": "Intérêt élevé",
    "page.heatmap.map_card": "Carte Folium",
    "page.heatmap.map_iframe_title": "Carte de chaleur",
    "page.heatmap.table.physician": "Médecin",
    "page.heatmap.table.specialty": "Spécialité",
    "page.heatmap.table.region": "Région",
    "page.heatmap.table.score": "Score d’intérêt",
    "page.heatmap.table.trend": "Tendance",
    "page.heatmap.table.product": "Top produit",
    "page.heatmap.table.visits": "Visites",
    "page.heatmap.table.empty": "Aucune donnée disponible",
    "page.heatmap.risk.title": "Médecins à risque",
    "page.heatmap.risk.subtitle": "Intérêt moyen ≥ 3 avec tendance négative",
    "page.heatmap.potential.title": "Médecins à fort potentiel",
    "page.heatmap.potential.subtitle":
      "Intérêt moyen ≥ 3,5 avec tendance positive",

    "page.followup.title": "Tâches de suivi",
    "page.followup.subtitle":
      "Suivis médecins prioritaires et exports de planning.",
    "page.followup.export_csv": "Exporter CSV",
    "page.followup.export_ics": "Exporter ICS",
    "page.followup.loading": "Chargement des informations de suivi…",
    "page.followup.kpi.total_tasks": "Total des tâches",
    "page.followup.kpi.red": "ROUGE",
    "page.followup.kpi.orange": "ORANGE",
    "page.followup.kpi.green": "VERT",
    "page.followup.section_tasks": "Tâches prioritaires",
    "page.followup.search_placeholder": "Rechercher un médecin ou une action…",
    "page.followup.priority_all": "Toutes les priorités",
    "page.followup.empty.none": "Aucune tâche chargée.",
    "page.followup.empty.priority":
      "Aucune tâche pour la priorité sélectionnée.",
    "page.followup.empty.search": "Aucun résultat pour votre recherche.",
    "page.followup.due": "Échéance",
    "page.followup.date_unspecified": "Non spécifié",

    "page.correcteur.title": "Correcteur médical",
    "page.correcteur.subtitle": "Whisper-large-v3-turbo et Llama-3.3-70b via Groq",

    "page.chatbot.title": "Assistant médical IA",
    "page.chatbot.subtitle": "Votre assistant intelligent pour les médicaments",
    "page.chatbot.empty_hint": "Posez votre question sur un médicament",
    "page.chatbot.input_placeholder": "Posez votre question sur un médicament…",
    "page.chatbot.connection_error": "Erreur de connexion au serveur.",

    // Admin (placeholders)
    "admin.sidebar.dashboard": "Tableau de bord",
    "admin.sidebar.users": "Utilisateurs",
    "admin.sidebar.analytics": "Analytique",
    "admin.sidebar.settings": "Paramètres",
  },
  en: {
    "common.loading": "Loading…",
    "common.save": "Save",
    "common.cancel": "Cancel",
    "common.delete": "Delete",
    "common.edit": "Edit",
    "common.search": "Search",
    "common.language": "Language",
    "common.theme.light": "Light",
    "common.theme.dark": "Dark",
    "common.theme.toggle_dark": "Switch to dark mode",
    "common.theme.toggle_light": "Switch to light mode",
    "common.backHome": "Back to home",
    "common.send": "Send",

    "nav.home": "Home",
    "nav.sidebar_heading": "Features",
    "nav.dashboard": "Overview",
    "nav.persona": "Doctor Profiles",
    "nav.heatmap": "Visit Map",
    "nav.followup": "Planning",
    "nav.profile": "Profile",
    "nav.correcteur": "Visit Reports",
    "nav.extraction": "Quick Entry",
    "nav.coaching": "Field Support",
    "nav.chatbot": "Drug Assistant",
    "nav.rapport_extract": "New Report",
    "nav.rapport_history": "History",

    "auth.login": "Sign in",
    "auth.logout": "Sign out",
    "auth.register": "Create account",
    "auth.email": "Email",
    "auth.password": "Password",
    "auth.name": "Full name",
    "auth.role": "Role",
    "auth.role.admin": "Admin",
    "auth.role.delegate": "Delegate",
    "auth.remember": "Remember me",
    "auth.noAccount": "No account yet?",
    "auth.hasAccount": "Already have an account?",
    "auth.login_subtitle": "Sign in to your Vital Labo Tunisia workspace",
    "auth.register_subtitle": "Create a delegate or administrator account",
    "auth.register_submit": "Create account",
    "auth.password_confirm": "Confirm password",
    "auth.demo_hint":
      "Demo: seeded accounts use password « demo123 » (e.g. admin@vital-labo.tn).",
    "auth.error.invalid_credentials": "Invalid email or password.",
    "auth.error.account_suspended": "Account suspended",
    "auth.error.email_exists": "This email is already registered.",
    "auth.error.password_mismatch": "Passwords do not match.",
    "auth.error.password_short": "Password must be at least 4 characters.",

    "nav.admin": "Admin",

    "admin.dashboard.title": "Administrator dashboard",
    "admin.dashboard.heading": "Overview",
    "admin.dashboard.open_crm": "Open CRM",
    "admin.dashboard.kpi.users": "Users",
    "admin.dashboard.kpi.delegates": "Delegates",
    "admin.dashboard.kpi.admins": "Administrators",
    "admin.dashboard.kpi.visits_mock": "Visits analyzed (CRM)",
    "admin.dashboard.users_preview": "Users",
    "admin.dashboard.users_hint": "List from local storage (mock data).",
    "admin.dashboard.full_users_later":
      "Full user management screen can be wired here later.",

    "home.hero.title": "ALIA CRM",
    "home.hero.subtitle":
      "AI-powered CRM for medical sales representatives — Vital Labo Tunisia",
    "home.hero.slogan.visit": "Visit Smarter.",
    "home.hero.slogan.act": "Act Faster.",
    "home.hero.slogan.sell": "Sell Better.",
    "home.hero.badge": "Medical delegate platform",
    "home.cta.start": "Get started",
    "home.cta.learn": "Learn more",
    "home.features.title": "Key features",
    "home.features.persona.title": "Persona engine",
    "home.features.persona.desc":
      "Segment physicians into behavioral profiles (receptive, resistant, low engagement).",
    "home.features.heatmap.title": "Visit heat map",
    "home.features.heatmap.desc":
      "Interactive map of visits and activity across Tunisian regions.",
    "home.features.followup.title": "Follow-up automation",
    "home.features.followup.desc":
      "Prioritized follow-up tasks by urgency (red, orange, green).",
    "home.features.coach.title": "Voice coach",
    "home.features.coach.desc":
      "Voice note transcription and AI-assisted CRM report generation.",
    "home.features.correcteur.title": "Text correction",
    "home.features.correcteur.desc":
      "Automatic cleanup and standardization of visit notes.",
    "home.features.reports.title": "Smart reports",
    "home.features.reports.desc":
      "Structured reports, quality scoring, and conversational assistant.",
    "home.stats.title": "By the numbers",
    "home.stats.visits": "visits analyzed",
    "home.stats.physicians": "physicians",
    "home.stats.regions": "Tunisian regions",
    "home.stats.modules": "AI modules",
    "home.stats.visits.value": "4,142",
    "home.stats.physicians.value": "10",
    "home.stats.regions.value": "23",
    "home.stats.modules.value": "8",
    "home.steps.title": "How it works",
    "home.steps.one.title": "Field visit",
    "home.steps.one.desc": "Capture or dictate notes after consultations.",
    "home.steps.two.title": "AI analysis",
    "home.steps.two.desc":
      "Automatic extraction, persona, mapping, and quality control.",
    "home.steps.three.title": "Smart actions",
    "home.steps.three.desc":
      "Follow-ups, reports, and coaching to boost performance.",
    "home.footer.line": "ALIA CRM © 2026 — Vital Labo Tunisia",
    "home.login.wip": "Sign-in page comes in the next step.",
    "home.nav.skip": "Go to CRM",

    "nav.reports_menu": "Reports",
    "nav.history_menu": "Report history",

    "shell.sidebar.platform": "Platform",
    "shell.sidebar.demo": "DEMO",
    "shell.sidebar.close": "Close",
    "shell.sidebar.navigation": "Navigation",
    "shell.sidebar.tip_title": "Tip of the day",
    "shell.sidebar.tip_body":
      "Prioritize RED physicians to maximize impact on field visits.",
    "shell.sidebar.link_persona": "Persona card",
    "shell.sidebar.link_heatmap": "Heat map",
    "shell.sidebar.tagline": "Smart assistant for medical delegates",

    "shell.topbar.menu": "Menu",
    "shell.topbar.open_menu": "Open menu",
    "shell.topbar.dashboard": "Dashboard",
    "shell.topbar.subtitle":
      "ALIA CRM — smart tracking of physician interactions",
    "shell.topbar.demo_mode": "Demo mode",

    "page.persona.title": "Doctor profiles (Persona)",
    "page.persona.subtitle":
      "Assess behavioral profile and get strategy, objections, and next-best-actions.",
    "page.persona.smart_card": "Smart card",
    "page.persona.generating": "Generating…",
    "page.persona.generate_btn": "Generate intelligence card",
    "page.persona.field.doctor": "Physician",
    "page.persona.field.rating": "Interest level (1–10)",
    "page.persona.field.rating_value": "Value: {value}/10",
    "page.persona.field.effectiveness": "Perceived effectiveness",
    "page.persona.field.side_effects": "Side effects",
    "page.persona.field.benefits": "Observed benefits",
    "page.persona.field.benefits_ph":
      "E.g. clinical improvement, good adherence…",
    "page.persona.field.side_detail": "Side effects detail",
    "page.persona.field.side_detail_ph":
      "E.g. mild nausea, fatigue…",
    "page.persona.stats.benefits_wc": "Words (benefits)",
    "page.persona.stats.benefits_len": "Chars (benefits)",
    "page.persona.stats.side_wc": "Words (side fx)",
    "page.persona.stats.specialty": "Specialty",
    "page.persona.opt_eff.very": "Very effective",
    "page.persona.opt_eff.mod": "Moderately effective",
    "page.persona.opt_eff.low": "Low effectiveness",
    "page.persona.opt_side.light": "Mild side effects",
    "page.persona.opt_side.mod": "Moderate side effects",
    "page.persona.opt_side.severe": "Severe side effects",
    "page.persona.persona.highly_title": "Highly receptive",
    "page.persona.persona.high_hint":
      "Strengthen with clinical data and a scheduled follow-up visit.",
    "page.persona.persona.resist_title": "High resistance",
    "page.persona.persona.resist_hint":
      "Address objections (tolerance, side effects) with structured evidence.",
    "page.persona.persona.low_title": "Low engagement",
    "page.persona.persona.low_hint":
      "Re-engage: product trial, medical event, or manager escalation.",
    "page.persona.result.banner_title": "Physician intelligence card",
    "page.persona.result.doctor": "Physician",
    "page.persona.result.specialty": "Specialty",
    "page.persona.result.product": "Primary product",
    "page.persona.result.persona_block": "HCP persona",
    "page.persona.result.metrics":
      "Avg. interest: {avg}/5 · Visits: {visits} · High interest: {proba}%",
    "page.persona.result.objection": "Common objection",
    "page.persona.result.strategy": "HCP strategy",
    "page.persona.result.nba_com": "NBA — Commercial recommendation",
    "page.persona.result.nba_risk": "NBA — Risk analysis",
    "page.persona.result.label": "Label",
    "page.persona.result.actions": "Actions",
    "page.persona.empty_hint":
      "Generate a card to view full details and NBA blocks.",
    "page.persona.unknown": "Unknown persona",

    "page.heatmap.title": "Heat map",
    "page.heatmap.subtitle":
      "Geographic view of performance and physician risk prioritization.",
    "page.heatmap.loading": "Loading map analytics…",
    "page.heatmap.kpi.total_visits": "Total visits",
    "page.heatmap.kpi.physicians": "Physicians",
    "page.heatmap.kpi.avg_interest": "Average interest",
    "page.heatmap.kpi.pct_high": "% High interest",
    "page.heatmap.kpi.top_region": "Top region",
    "page.heatmap.kpi.top_product": "Top product",
    "page.heatmap.panel.title": "Reading panel",
    "page.heatmap.panel.subtitle":
      "Quick summary of interest levels and trends.",
    "page.heatmap.legend.interest_level": "Interest level",
    "page.heatmap.legend.trend": "Trend",
    "page.heatmap.legend.up": "Increasing interest",
    "page.heatmap.legend.down": "Decreasing interest",
    "page.heatmap.legend.stable": "Stable",
    "page.heatmap.band.vhigh": "Very high (&gt;=4/5)",
    "page.heatmap.band.high": "High (3-4/5)",
    "page.heatmap.band.mid": "Medium (2-3/5)",
    "page.heatmap.band.low": "Low (&lt;2/5)",
    "page.heatmap.summary.visits": "Visits",
    "page.heatmap.summary.physicians": "Physicians",
    "page.heatmap.summary.avg": "Avg. interest",
    "page.heatmap.summary.high": "High interest",
    "page.heatmap.map_card": "Folium map",
    "page.heatmap.map_iframe_title": "Heat map",
    "page.heatmap.table.physician": "Physician",
    "page.heatmap.table.specialty": "Specialty",
    "page.heatmap.table.region": "Region",
    "page.heatmap.table.score": "Interest score",
    "page.heatmap.table.trend": "Trend",
    "page.heatmap.table.product": "Top product",
    "page.heatmap.table.visits": "Visits",
    "page.heatmap.table.empty": "No data available",
    "page.heatmap.risk.title": "At-risk physicians",
    "page.heatmap.risk.subtitle": "Avg. interest ≥ 3 with negative trend",
    "page.heatmap.potential.title": "High-potential physicians",
    "page.heatmap.potential.subtitle":
      "Avg. interest ≥ 3.5 with positive trend",

    "page.followup.title": "Follow-up tasks",
    "page.followup.subtitle":
      "Priority physician follow-ups and calendar exports.",
    "page.followup.export_csv": "Export CSV",
    "page.followup.export_ics": "Export ICS",
    "page.followup.loading": "Loading follow-up information…",
    "page.followup.kpi.total_tasks": "Total tasks",
    "page.followup.kpi.red": "RED",
    "page.followup.kpi.orange": "ORANGE",
    "page.followup.kpi.green": "GREEN",
    "page.followup.section_tasks": "Priority tasks",
    "page.followup.search_placeholder": "Search for a physician or action…",
    "page.followup.priority_all": "All priorities",
    "page.followup.empty.none": "No tasks loaded.",
    "page.followup.empty.priority": "No tasks for the selected priority.",
    "page.followup.empty.search": "No results for your search.",
    "page.followup.due": "Due",
    "page.followup.date_unspecified": "Not specified",

    "page.correcteur.title": "Medical proofreader",
    "page.correcteur.subtitle": "Whisper-large-v3-turbo and Llama-3.3-70b via Groq",

    "page.chatbot.title": "Medical AI assistant",
    "page.chatbot.subtitle": "Your smart assistant for medicines",
    "page.chatbot.empty_hint": "Ask a question about a medicine",
    "page.chatbot.input_placeholder": "Ask a question about a medicine…",
    "page.chatbot.connection_error": "Could not connect to the server.",

    "admin.sidebar.dashboard": "Dashboard",
    "admin.sidebar.users": "Users",
    "admin.sidebar.analytics": "Analytics",
    "admin.sidebar.settings": "Settings",
  },
};

const LanguageContext = createContext(null);

function readStoredLang() {
  if (typeof window === "undefined") return "fr";
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw === "en" || raw === "fr") return raw;
  } catch {
    /* ignore */
  }
  return "fr";
}

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState(() => readStoredLang());

  const setLang = useCallback((next) => {
    const v = next === "en" ? "en" : "fr";
    setLangState(v);
    try {
      localStorage.setItem(STORAGE_KEY, v);
    } catch {
      /* ignore */
    }
  }, []);

  const t = useCallback(
    (key, vars) => {
      const table = translations[lang] || translations.fr;
      let s = table[key] ?? translations.fr[key] ?? key;
      if (vars && typeof s === "string") {
        Object.entries(vars).forEach(([k, val]) => {
          s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(val));
        });
      }
      return s;
    },
    [lang],
  );

  const value = useMemo(
    () => ({
      lang,
      setLang,
      t,
      isFr: lang === "fr",
      isEn: lang === "en",
    }),
    [lang, setLang, t],
  );

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return ctx;
}
