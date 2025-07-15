import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

# ---------- CONFIG GOOGLE SHEETS ----------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '1JrfYOXXajQFjl_wMqHpM4qJfBkgZiUO2VtTiPuwhmEk'
SHEET_NAME = 'Feuille 1'

@st.cache_resource
def get_gsheet_client():
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def load_sheet(sheet_id, sheet_name):
    client = get_gsheet_client()
    sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df, sheet

def append_row_to_sheet(sheet, row):
    if not sheet.get_all_values():
        headers = ["Date", "Jour", "Phase", "Type", "Exercices", "Sommeil", "Hydratation", "Nutrition", "RPE", "Fatigue", "Notes", "Athlète"]
        sheet.append_row(headers)
    sheet.append_row(row)

# ---------- PARAMÈTRES ----------
ATHLETES = ["Joffrey", "Marie", "Dorine", "Fabien", "Yann", "Lucile", "Arthur", "Baptiste"]

PHASES = [
    ("Prépa 1", date(2025, 9, 1), date(2025, 12, 31), "PPG/Technique", "PPG/Technique"),
    ("Pré-compétition janvier", date(2026, 1, 1), date(2026, 1, 31), "PPG/Technique", "Technique"),
    ("Compétition février", date(2026, 2, 1), date(2026, 2, 28), "Technique", "Technique"),
    ("Prépa 2", date(2026, 3, 1), date(2026, 4, 15), "PPG/Technique", "PPG/Technique"),
    ("Pré-compétition avril-mai", date(2026, 4, 16), date(2026, 5, 15), "PPG/Technique", "Technique"),
    ("Compétition mai-juillet", date(2026, 5, 16), date(2026, 7, 15), "Technique", "Technique"),
]

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

EXOS_MUSCU = [
    "Épaulé", "Épaulé avec bandes", "Arraché", "Arraché avec bandes", "Arraché force",
    "Squat", "Squat avec ceinture", "Demi-squat", "Pull over avec mouvement du bassin",
    "Pull over avec haltère", "Développé couché strict", "Développé couché avec mouvement du bassin",
    "Renfo ischios", "Renfo adducteurs", "Tirage nuque", "Tirage rowing", "Abdos",
    "Exos lombaires", "Renfo cheville", "Dips", "Vélo", "Rowing machine", "Lancer de medecine ball"
]

EXOS_PREPA = ["Médecine ball", "Passage de haies", "Série de médecine ball JB", "Gainage"]
EXOS_TECH = ["Lancers de balles", "Courses d’élan", "Point technique précis", "Lancers de javelots"]

ZONES_DOULEUR = [
    "Épaule droite", "Épaule gauche", "Coude droit", "Coude gauche", "Poignet droit", "Poignet gauche",
    "Dos haut", "Bas du dos", "Hanche droite", "Hanche gauche", "Genou droit", "Genou gauche",
    "Cheville droite", "Cheville gauche", "Cuisses", "Ischio-jambiers", "Mollets"
]

def get_phase(current_date):
    for phase, start, end, mardi, jeudi in PHASES:
        if start <= current_date <= end:
            return phase, mardi, jeudi
    return "", "PPG/Technique", "PPG/Technique"

# ---------- INTERFACE ----------
st.set_page_config(page_title="Carnet Javelot", layout="centered")
st.sidebar.title("👤 Sélection du profil")
athlete = st.sidebar.selectbox("Sélectionne l'athlète :", ATHLETES, key="select_athlete")

st.title("📘 Carnet de suivi - Javelot")

selected_date = st.date_input("📅 Choisis la date :", date.today())
weekday = selected_date.weekday()
if weekday > 4:
    st.warning("Aucune séance prévue le week-end.")
    st.stop()

jour = JOURS[weekday]
phase, mardi_type, jeudi_type = get_phase(selected_date)
type_seance = "Muscu" if jour in ["Lundi", "Mercredi", "Vendredi"] else (mardi_type if jour == "Mardi" else jeudi_type)
st.subheader(f"📍 {jour} — {phase} — {type_seance}")

# ---------- ONGLET SÉANCE ----------
tab_seance, tab_douleur = st.tabs(["📝 Séance", "⚠️ Douleur"])

with tab_seance:
    with st.form("form_seance"):
        exercices = []
        autres_exos = ""
        prepa_comment = ""
        tech_comment = ""

        if jour in ["Lundi", "Mercredi", "Vendredi"]:
            selection = st.multiselect("Exercices muscu :", EXOS_MUSCU)
            for exo in selection:
                col1, col2, col3 = st.columns(3)
                with col1:
                    charge = st.number_input(f"Charge ({exo})", min_value=0.0, step=0.5, key=f"charge_{exo}")
                with col2:
                    reps = st.number_input(f"Répétitions ({exo})", min_value=0, step=1, key=f"reps_{exo}")
                with col3:
                    series = st.number_input(f"Séries ({exo})", min_value=0, step=1, key=f"series_{exo}")
                exercices.append(f"{exo} – {charge}kg x {reps} x {series}")
        elif jour in ["Mardi", "Jeudi"]:
            prepa = st.multiselect("Prépa physique :", EXOS_PREPA)
            prepa_comment = st.text_area("Commentaire prépa")
            tech = st.multiselect("Technique :", EXOS_TECH)
            tech_comment = st.text_area("Commentaire technique")
            exercices = prepa + tech
        else:
            autres_exos = st.text_area("Autres exercices")

        sommeil = st.slider("🌙 Sommeil", 0, 10, 5)
        hydratation = st.slider("💧 Hydratation", 0, 10, 5)
        nutrition = st.slider("🍎 Nutrition", 0, 10, 5)
        rpe = st.slider("🔥 RPE", 1, 10, 7)
        fatigue = st.slider("😴 Fatigue", 1, 10, 5)
        notes = st.text_area("🗒️ Notes")

        submit = st.form_submit_button("✅ Enregistrer")

        if submit:
            exos_final = "; ".join(exercices) if exercices else autres_exos
            if prepa_comment:
                exos_final += f"\nPrépa : {prepa_comment}"
            if tech_comment:
                exos_final += f"\nTechnique : {tech_comment}"

            new_row = [
                selected_date.strftime("%Y-%m-%d"), jour, phase, type_seance, exos_final,
                sommeil, hydratation, nutrition, rpe, fatigue, notes, athlete
            ]
            df, sheet = load_sheet(SHEET_ID, SHEET_NAME)
            append_row_to_sheet(sheet, new_row)
            st.success("Séance enregistrée ✅")
            df, _ = load_sheet(SHEET_ID, SHEET_NAME)
            st.dataframe(df)

# ---------- ONGLET DOULEUR ----------
with tab_douleur:
    with st.form("form_douleur"):
        type_douleur = st.selectbox("Type de douleur", ["Aucune", "Musculaire", "Articulaire", "Tendineuse"])
        zones = []
        autre = ""
        if type_douleur != "Aucune":
            zones = st.multiselect("Zones :", ZONES_DOULEUR)
            autre = st.text_input("Autre zone")
        commentaire = st.text_area("Commentaires")

        submit_d = st.form_submit_button("✅ Enregistrer douleur")

        if submit_d:
            zone_str = ", ".join(zones)
            if autre.strip():
                zone_str += (", " if zone_str else "") + autre.strip()
            new_row = [
                selected_date.strftime("%Y-%m-%d"), jour, phase, "Douleur", f"{type_douleur} : {zone_str}",
                "", "", "", "", "", commentaire, athlete
            ]
            df, sheet = load_sheet(SHEET_ID, SHEET_NAME)
            append_row_to_sheet(sheet, new_row)
            st.success("Douleur enregistrée ✅")
            df, _ = load_sheet(SHEET_ID, SHEET_NAME)
            st.dataframe(df)

# ---------- EXPORT CSV ----------
df, _ = load_sheet(SHEET_ID, SHEET_NAME)
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📁 Télécharger CSV", csv, "carnet_javelot.csv", "text/csv")
