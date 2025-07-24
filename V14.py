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
        headers = ["Athlète", "Date", "Jour", "Type", "Catégorie", "Exercice", "Valeur", "Unité", "Commentaire"]
        sheet.append_row(headers)
    sheet.append_row(row)

# ---------- PARAMÈTRES ----------
ATHLETES = ["Joffrey", "Marie", "Dorine", "Fabien", "Yann", "Lucile", "Arthur", "Baptiste"]
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

EXOS_MUSCU = [
    "Épaulé", "Épaulé avec bandes", "Arraché", "Arraché avec bandes", "Arraché force",
    "Squat", "Squat avec ceinture", "Demi-squat", "Pull over avec mouvement du bassin",
    "Pull over avec haltère", "Développé couché strict", "Développé couché avec mouvement du bassin"
]

PERF_PHYSIQUE = [
    ("Watt max vélo", "Watt"),
    ("Saut en longueur sans élan", "m")
]

LANCERS = [
    ("Lancer de medecine ball de 4kg en touche", "m"),
    ("Lancer de poids avant 4kg", "m"),
    ("Lancer de poids arrière 4kg", "m"),
    ("Lancer de javelot sans élan", "m"),
    ("Lancer de javelot sur un hop", "m")
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
            "",
            "; ".join(exercices),
            "", "", "", "", ""
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
                "",
                sommeil, hydratation, nutrition, rpe, fatigue, notes
            ]
            df, sheet = load_sheet(SHEET_ID, SHEET_NAME)
            append_row_to_sheet(sheet, new_row)
            st.success("Sensations enregistrées ✅")

with tab_maxs:
    with st.form("form_maxs"):
        st.subheader("🏋️‍♀️ Maxs Musculation")
        maxs_muscu = {}
        for exo in EXOS_MUSCU:
            val = st.number_input(f"{exo} (kg)", min_value=0.0, step=0.5, key=f"max_{exo}")
            if val > 0:
                maxs_muscu[exo] = val

        st.subheader("🚴‍♂️ Performances physiques")
        perf_physique = {}
        for nom, unite in PERF_PHYSIQUE:
            val = st.number_input(f"{nom} ({unite})", min_value=0.0, step=0.1, key=f"perf_{nom}")
            if val > 0:
                perf_physique[nom] = (val, unite)

        st.subheader("🏹 Maxs Lancers")
        maxs_lancers = {}
        for nom, unite in LANCERS:
            val = st.number_input(f"{nom} ({unite})", min_value=0.0, step=0.1, key=f"lancer_{nom}")
            if val > 0:
                maxs_lancers[nom] = (val, unite)

        commentaire = st.text_area("🗒️ Commentaire général (facultatif)")

        submit = st.form_submit_button("✅ Enregistrer les maxs")
        if submit:
            df, sheet = load_sheet(SHEET_ID, SHEET_NAME)

            for exo, val in maxs_muscu.items():
                row = [athlete, selected_date.strftime("%Y-%m-%d"), jour, "Max", "Muscu", exo, val, "kg", commentaire]
                append_row_to_sheet(sheet, row)

            for nom, (val, unite) in perf_physique.items():
                row = [athlete, selected_date.strftime("%Y-%m-%d"), jour, "Max", "Perf physique", nom, val, unite, commentaire]
                append_row_to_sheet(sheet, row)

            for nom, (val, unite) in maxs_lancers.items():
                row = [athlete, selected_date.strftime("%Y-%m-%d"), jour, "Max", "Lancer", nom, val, unite, commentaire]
                append_row_to_sheet(sheet, row)

            st.success("Maxs enregistrés ✅")
