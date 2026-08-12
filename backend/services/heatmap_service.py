from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, MarkerCluster, Fullscreen, MiniMap
import colorsys
import tempfile, os

router = APIRouter()

# ── GPS Tunisie ──────────────────────────────────────────────────────
GPS = {
    'Tunis'       : (36.8065, 10.1815),
    'Sfax'        : (34.7406, 10.7603),
    'Sousse'      : (35.8245, 10.6346),
    'Bizerte'     : (37.2744,  9.8739),
    'Monastir'    : (35.7643, 10.8113),
    'Nabeul'      : (36.4513, 10.7357),
    'Ariana'      : (36.8625, 10.1956),
    'Ben Arous'   : (36.7531, 10.2282),
    'Manouba'     : (36.8089, 10.0986),
    'Gabès'       : (33.8881, 10.0975),
    'Kairouan'    : (35.6781, 10.0964),
    'Gafsa'       : (34.4250,  8.7842),
    'Médenine'    : (33.3549, 10.5055),
    'Jendouba'    : (36.5011,  8.7757),
    'Kasserine'   : (35.1676,  8.8365),
    'Zaghouan'    : (36.4029, 10.1429),
    'Siliana'     : (36.0847,  9.3708),
    'Sidi Bouzid' : (35.0382,  9.4858),
    'Tataouine'   : (32.9211, 10.4511),
    'Tozeur'      : (33.9197,  8.1335),
    'Kébili'      : (33.7050,  8.9650),
    'Béja'        : (36.7256,  9.1817),
    'Le Kef'      : (36.1675,  8.7147),
}

GRADIENT = {
    '0.0': '#313695', '0.25': '#74add1',
    '0.5': '#fee090', '0.75': '#f46d43', '1.0': '#d73027'
}

def load_data():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                            "data", "visits_ready_clean_FR.csv")
    df = pd.read_csv(csv_path)
    df['latitude']  = df['region_clean'].map(lambda r: GPS.get(r, (34.0, 9.5))[0])
    df['longitude'] = df['region_clean'].map(lambda r: GPS.get(r, (34.0, 9.5))[1])

    rng = np.random.default_rng(seed=42)
    doctor_offsets = {
        doc: (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05))
        for doc in df['nom_medecin'].unique()
    }
    df['latitude']  += df['nom_medecin'].map(lambda d: doctor_offsets[d][0])
    df['longitude'] += df['nom_medecin'].map(lambda d: doctor_offsets[d][1])
    df['heat_score'] = df['niveau_interet']

    df['visit_idx'] = df.groupby('nom_medecin').cumcount()
    total = df.groupby('nom_medecin')['visit_idx'].transform('max') + 1
    df['visit_pct'] = df['visit_idx'] / total
    early = df[df['visit_pct'] < 0.33].groupby('nom_medecin')['niveau_interet'].mean()
    late  = df[df['visit_pct'] > 0.67].groupby('nom_medecin')['niveau_interet'].mean()
    trend = (late - early).rename('interet_trend')
    df = df.join(trend, on='nom_medecin')
    return df

@router.get("/map", response_class=HTMLResponse)
async def get_map(
    specialite: str = "Toutes",
    produit: str    = "Tous",
    region: str     = "Toutes",
    min_interet: int = 1
):
    df = load_data()

    # Filtres
    if specialite != "Toutes":
        df = df[df['specialite_medecin'] == specialite]
    if produit != "Tous":
        df = df[df['medicament'] == produit]
    if region != "Toutes":
        df = df[df['region_clean'] == region]
    df = df[df['niveau_interet'] >= min_interet]

    if df.empty:
        return "<h3>Aucune donnée pour ces filtres</h3>"

    # Carte Folium
    m = folium.Map(location=[34.8, 9.8], zoom_start=7, tiles='CartoDB positron')
    Fullscreen(position='topright').add_to(m)
    MiniMap(toggle_display=True).add_to(m)

    # Couche 1 : HeatMap
    heat_data = [[r['latitude'], r['longitude'], r['heat_score']]
                 for _, r in df.iterrows()]
    HeatMap(heat_data, name='🔥 Heatmap',
            min_opacity=0.35, radius=28, blur=18,
            gradient=GRADIENT).add_to(m)

    # Couche 2 : Cercles régions
    region_layer = folium.FeatureGroup(name='🗺️ Régions')
    reg_stats = df.groupby('region_clean').agg(
        nb=('nom_medecin','count'),
        avg=('niveau_interet','mean')
    ).reset_index()
    max_nb = reg_stats['nb'].max()
    for _, r in reg_stats.iterrows():
        radius = 15000 * (r['nb'] / max_nb) ** 0.5
        norm   = (r['avg'] - 1) / 4
        h      = (1 - norm) * 0.66
        rgb    = colorsys.hsv_to_rgb(h, 0.8, 0.9)
        hex_c  = '#{:02x}{:02x}{:02x}'.format(*[int(x*255) for x in rgb])
        gps_loc = GPS.get(r['region_clean'], (34, 9.5))
        folium.Circle(
            location=gps_loc, radius=radius,
            color=hex_c, fill=True, fill_opacity=0.25, weight=2,
            tooltip=f"<b>{r['region_clean']}</b><br>{r['nb']} visites | {r['avg']:.2f}/5"
        ).add_to(region_layer)
    region_layer.add_to(m)

    # Couche 3 : Marqueurs médecins
    cluster_layer = folium.FeatureGroup(name='👨‍⚕️ Médecins')
    doc_sum = df.groupby('nom_medecin').agg(
        specialite    = ('specialite_medecin', 'first'),
        region        = ('region_clean', lambda x: x.value_counts().index[0]),
        nb_visites    = ('nom_medecin', 'count'),
        avg_interet   = ('niveau_interet', 'mean'),
        top_produit   = ('medicament', lambda x: x.value_counts().index[0]),
        trend         = ('interet_trend', 'first'),
    ).reset_index()

    offsets = {
        doc: (i * 0.06 - 0.3, (i % 3) * 0.06 - 0.09)
        for i, doc in enumerate(doc_sum['nom_medecin'])
    }
    doc_sum['lat'] = doc_sum.apply(
        lambda r: GPS.get(r['region'], (34.0, 9.5))[0] + offsets[r['nom_medecin']][0], axis=1)
    doc_sum['lon'] = doc_sum.apply(
        lambda r: GPS.get(r['region'], (34.0, 9.5))[1] + offsets[r['nom_medecin']][1], axis=1)

    def marker_color(avg):
        if avg >= 4.0: return 'red'
        if avg >= 3.0: return 'orange'
        return 'blue'

    def trend_icon(v):
        if pd.isna(v): return '➡️'
        return '📈' if v > 0.3 else '📉' if v < -0.3 else '➡️'

    for _, r in doc_sum.iterrows():
        popup_html = f"""
        <div style="font-family:Arial;width:220px;padding:10px">
            <b>👨‍⚕️ {r['nom_medecin']}</b><br>
            🏥 {r['specialite']}<br>
            📍 {r['region']}<br>
            💊 {r['top_produit']}<br>
            📅 {r['nb_visites']} visites<br>
            ⭐ {r['avg_interet']:.2f}/5<br>
            📈 Trend: {trend_icon(r['trend'])} ({r['trend']:+.2f})
        </div>"""
        folium.Marker(
            location=[r['lat'], r['lon']],
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"👨‍⚕️ {r['nom_medecin']} ({r['avg_interet']:.1f}/5)",
            icon=folium.Icon(color=marker_color(r['avg_interet']),
                             icon='plus-sign', prefix='glyphicon')
        ).add_to(cluster_layer)
    cluster_layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    tmp = os.path.join(tempfile.gettempdir(), 'heatmap.html')
    m.save(tmp)
    with open(tmp, 'r', encoding='utf-8') as f:
        return f.read()

@router.get("/kpis")
async def get_kpis():
    df = load_data()
    return {
        "total_visites"  : int(len(df)),
        "nb_medecins"    : int(df['nom_medecin'].nunique()),
        "avg_interet"    : round(float(df['niveau_interet'].mean()), 2),
        "pct_high"       : round(float((df['niveau_interet'] >= 4).mean() * 100), 1),
        "top_region"     : df['region_clean'].value_counts().index[0],
        "top_produit"    : df['medicament'].value_counts().index[0],
    }

@router.get("/at-risk")
async def get_at_risk():
    df = load_data()
    MIN_VISITES = 3
    doc_full = df.groupby('nom_medecin').agg(
        specialite  = ('specialite_medecin', 'first'),
        region      = ('region_clean', 'first'),
        nb_visites  = ('nom_medecin', 'count'),
        avg_interet = ('niveau_interet', 'mean'),
        trend       = ('interet_trend', 'first'),
        top_produit = ('medicament', lambda x: x.value_counts().index[0]),
    ).reset_index()

    at_risk = doc_full[
        (doc_full['nb_visites'] >= MIN_VISITES) &
        (doc_full['avg_interet'] >= 3.0) &
        (doc_full['trend'] < -0.3)
    ].sort_values('trend').head(10)

    top_potential = doc_full[
        (doc_full['nb_visites'] >= MIN_VISITES) &
        (doc_full['avg_interet'] >= 3.5) &
        (doc_full['trend'] > 0.2)
    ].sort_values(['avg_interet','trend'], ascending=False).head(10)

    return {
        "at_risk"       : at_risk.to_dict(orient='records'),
        "top_potential" : top_potential.to_dict(orient='records'),
    }

@router.get("/health")
async def health():
    return {"status": "ok", "module": "Heat Map — Sawsen"}