from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import pandas as pd
from datetime import datetime, timedelta
import io, os

router = APIRouter()

def load_data():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "data", "visits_ready_clean_FR.csv")
    return pd.read_csv(csv_path)

def get_priority(niveau):
    if niveau >= 4: return "ROUGE", 14, "🔴"
    elif niveau == 3: return "ORANGE", 21, "🟡"
    else: return "VERT", 30, "🟢"

def generate_tasks(df):
    tasks = []
    # Stable unique ids (hash % 9999 collides often with ~4k rows → broken React lists / filters).
    for ordinal, (idx, row) in enumerate(df.iterrows()):
        priorite, delai, emoji = get_priority(row['niveau_interet'])
        date_rappel = datetime.now() + timedelta(days=delai)
        tasks.append({
            "id"          : f"TASK-{ordinal:05d}-{idx}",
            "medecin"     : row['nom_medecin'],
            "specialite"  : row['specialite_medecin'],
            "medicament"  : row['medicament'],
            "region"      : row.get('region_clean', '—'),
            "action"      : row['prochaine_action'],
            "objection"   : row.get('objection_clean', '—'),
            "interet"     : int(row['niveau_interet']),
            "priorite"    : priorite,
            "emoji"       : emoji,
            "delai_jours" : delai,
            "date_rappel" : date_rappel.strftime("%d/%m/%Y"),
            "statut"      : "À faire",
        })
    return tasks

@router.get("/tasks")
async def get_tasks(
    medecin: str   = "Tous",
    priorite: str  = "Toutes",
    min_interet: int = 1
):
    df = load_data()
    priorite = (priorite or "Toutes").strip().upper()
    if priorite in ("TOUTES", "ALL", "*"):
        priorite = "Toutes"
    if medecin   != "Tous":    df = df[df['nom_medecin']    == medecin]
    if priorite  != "Toutes":
        niveau_map = {"ROUGE": [4,5], "ORANGE": [3], "VERT": [1,2]}
        niveaux = niveau_map.get(priorite, [1,2,3,4,5])
        df = df[df['niveau_interet'].isin(niveaux)]
    df = df[df['niveau_interet'] >= min_interet]

    tasks = generate_tasks(df)
    order = {"ROUGE": 0, "ORANGE": 1, "VERT": 2}
    tasks.sort(key=lambda x: order.get(x['priorite'], 3))

    return {
        "total"       : len(tasks),
        "nb_rouge"    : sum(1 for t in tasks if t['priorite'] == 'ROUGE'),
        "nb_orange"   : sum(1 for t in tasks if t['priorite'] == 'ORANGE'),
        "nb_vert"     : sum(1 for t in tasks if t['priorite'] == 'VERT'),
        "tasks"       : tasks
    }

@router.get("/kpis")
async def get_kpis():
    df = load_data()
    tasks = generate_tasks(df)
    return {
        "total"         : len(tasks),
        "nb_rouge"      : sum(1 for t in tasks if t['priorite'] == 'ROUGE'),
        "nb_orange"     : sum(1 for t in tasks if t['priorite'] == 'ORANGE'),
        "nb_vert"       : sum(1 for t in tasks if t['priorite'] == 'VERT'),
        "nb_medecins"   : df['nom_medecin'].nunique(),
    }

@router.get("/export/csv")
async def export_csv():
    df = load_data()
    tasks = generate_tasks(df)
    tasks_df = pd.DataFrame(tasks)
    output = io.StringIO()
    tasks_df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=followup_tasks.csv"}
    )

@router.get("/export/ics")
async def export_ics():
    df = load_data()
    tasks = generate_tasks(df)
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ALIA-CRM//FR"]
    for t in tasks:
        date_iso = (datetime.now() + timedelta(days=t['delai_jours'])).strftime("%Y%m%d")
        lines += [
            "BEGIN:VEVENT",
            f"UID:{t['id']}@alia-crm",
            f"DTSTART;VALUE=DATE:{date_iso}",
            f"SUMMARY:{t['emoji']} {t['medecin']} — {t['medicament']}",
            f"DESCRIPTION:Action: {t['action']}\\nPriorité: {t['priorite']}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    ics_content = "\n".join(lines)
    return StreamingResponse(
        io.BytesIO(ics_content.encode('utf-8')),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=alia_crm_tasks.ics"}
    )

@router.get("/health")
async def health():
    return {"status": "ok", "module": "Follow-up Automation — Sawsen"}