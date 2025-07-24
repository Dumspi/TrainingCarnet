import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import json

# ---------- CONFIG GOOGLE SHEETS ----------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '1JrfYOXXajQFjl_wMqHpM4qJfBkgZiUO2VtTiPuwhmEk'
SHEET_NAME = 'Feuille 1'

@st.cache_resource
def get_gsheet_client():
    try:
        with open("credentials.json", "r", encoding="utf-8") as f:
            creds_data = json.load(f)
        creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"⛔ Erreur lors du chargement de credentials.json : {e}")
        st.stop()

def load_sheet(sheet_id, sheet_name):
    client = get_gsheet_client()
    sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df, sheet

def append_row_to_sheet(sheet, row):
    if not sheet.get_all_values():
        headers = ["Athlète", "Date", "Jour", "Type", "Exercices", "Sommeil", "Hydratation", "Nutrition", "RPE", "Fatigue", "Notes"]
        sheet.append_row(headers)
    sheet.append_row(row)

# ---------- PARAMÈTRES ----------
ATHLETES = ["Joffrey", "Marie", "Dorine", "Fabien", "Yann", "Lucile", "Arthur", "Baptiste"]
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

EXOS_MUSCU = [
    "Épaulé", "Épaulé avec bandes", "Arraché", "Arraché avec bandes", "Arraché force",
    "Squat", "Squat avec ceinture", "Demi-squat", "Pull over avec mouvement du bassin",
    "Pull over avec haltère", "Développé couché strict", "Développé couché avec mouvement du bassin",
    "Renfo ischios", "Renfo adducteurs", "Tirage nuque", "Tirage rowing", "Abdos",
    "Exos lombaires", "Renfo cheville", "Dips", "Vélo", "Rowing machine", "Lancer de medecine ball"
]

# ---------- INTERFACE PRINCIPALE ----------
st.set_page_config(page_title="Carnet Team Lancers", layout="centered")
st.sidebar.title("👤 Sélection du profil")
athlete = st.sidebar.selectbox("Sélectionne l'athlète :", ATHLETES, key="select_athlete")

st.title("📘 Carnet de suivi - Team Lancers")
selected_date = st.date_input("🗕️ Choisis la date :", date.today())
weekday = selected_date.weekday()
jour = JOURS[weekday]

# ---------- ONGLET SÉANCE MUSCU ----------
tab_seance, tab_sensations, tab_maxs = st.tabs(["🖍️ Muscu", "🛌 Sensations", "🔺 Maxs"])

with tab_seance:
    st.subheader("💪 Séance de muscu")
    exercices = []
    selected_exos = st.multiselect("Exercices muscu :", EXOS_MUSCU)

    for exo in selected_exos:
        col1, col2, col3 = st.columns(3)
        with col1:
            charge = st.number_input(f"Charge ({exo})", min_value=0.0, step=0.5, key=f"charge_{exo}")
        with col2:
            reps = st.number_input(f"Répétitions ({exo})", min_value=0, step=1, key=f"reps_{exo}")
        with col3:
            series = st.number_input(f"Séries ({exo})", min_value=0, step=1, key=f"series_{exo}")
        exercices.append(f"{exo} – {charge}kg x {reps} x {series}")

    if st.button("✅ Enregistrer la séance"):
        new_row = [
            athlete,
            selected_date.strftime("%Y-%m-%d"),
            jour,
            "Muscu",
            "; ".join(exercices),
            "", "", "", "", "", ""
        ]
        df, sheet = load_sheet(SHEET_ID, SHEET_NAME)
        append_row_to_sheet(sheet, new_row)
        st.success("Séance enregistrée ✅")

with tab_sensations:
    st.subheader("🧘 Suivi des sensations")
    with st.form("form_sensations"):
        sommeil = st.slider("🌙 Sommeil", 0, 10, 5)
        hydratation = st.slider("💧 Hydratation", 0, 10, 5)
        nutrition = st.slider("🍎 Nutrition", 0, 10, 5)
        rpe = st.slider("🔥 RPE", 1, 10, 7)
        fatigue = st.slider("🛌 Fatigue", 1, 10, 5)
        notes = st.text_area("📒 Notes")

        submit2 = st.form_submit_button("✅ Enregistrer")
        if submit2:
            new_row = [
                athlete,
                selected_date.strftime("%Y-%m-%d"),
                jour,
                "Sensations",
                "",
                sommeil, hydratation, nutrition, rpe, fatigue, notes
            ]
            df, sheet = load_sheet(SHEET_ID, SHEET_NAME)
            append_row_to_sheet(sheet, new_row)
            st.success("Sensations enregistrées ✅")

with tab_maxs:
    st.subheader("🔺 Enregistrement des maxs")
    st.markdown("**À venir** : Ajout des tests mensuels de performance (exos muscu, explosivité, etc.)")
