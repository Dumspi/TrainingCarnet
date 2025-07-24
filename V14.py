import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import json

# ---------- CONFIG GOOGLE SHEETS ----------
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = '1JrfYOXXajQFjl_wMqHpM4qJfBkgZiUO2VtTiPuwhmEk'
SHEET_SEANCE = 'Feuille 1'
SHEET_MAXS = 'Maxs'

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
    "Pull over avec haltère", "Développé couché strict", "Développé couché avec mouvement du bassin"
]

EXOS_TESTS = [
    "Watt max vélo", "Saut en longueur sans élan",
    "Lancer de medecine ball de 4kg en touche",
    "Lancer de poids avant 4kg", "Lancer de poids arrière 4kg",
    "Lancer de javelot sans élan", "Lancer de javelot sur un hop"
]

# ---------- INTERFACE PRINCIPALE ----------
st.set_page_config(page_title="Carnet Team Lancers", layout="centered")
st.sidebar.title("👤 Sélection du profil")
athlete = st.sidebar.selectbox("Sélectionne l'athlète :", ATHLETES, key="select_athlete")

st.title("📘 Carnet de suivi - Team Lancers")
selected_date = st.date_input("🗕️ Choisis la date :", date.today())
weekday = selected_date.weekday()
jour = JOURS[weekday]

# ---------- ONGLET PRINCIPAL ----------
tab_seance, tab_sensations, tab_maxs = st.tabs(["🖍️ Muscu", "🛌 Sensations", "🔺 Maxs"])

with tab_seance:
    with st.form("form_muscu"):
        exercices = []
        selected_exos = st.multiselect("Exercices muscu :", EXOS_MUSCU)

        if selected_exos:
            for exo in selected_exos:
                col1, col2, col3 = st.columns(3)
                with col1:
                    charge = st.number_input(f"Charge ({exo})", min_value=0.0, step=0.5, key=f"charge_{exo}")
                with col2:
                    reps = st.number_input(f"Répétitions ({exo})", min_value=0, step=1, key=f"reps_{exo}")
                with col3:
                    series = st.number_input(f"Séries ({exo})", min_value=0, step=1, key=f"series_{exo}")
                exercices.append(f"{exo} – {charge}kg x {reps} x {series}")

        submit = st.form_submit_button("✅ Enregistrer")
        if submit:
            new_row = [
                athlete,
                selected_date.strftime("%Y-%m-%d"),
                jour,
                "Muscu",
                "; ".join(exercices),
                "", "", "", "", "", ""
            ]
            df, sheet = load_sheet(SHEET_ID, SHEET_SEANCE)
            append_row_to_sheet(sheet, new_row)
            st.success("Séance enregistrée ✅")

with tab_sensations:
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
            df, sheet = load_sheet(SHEET_ID, SHEET_SEANCE)
            append_row_to_sheet(sheet, new_row)
            st.success("Sensations enregistrées ✅")

with tab_maxs:
    st.subheader("📝 Enregistrement des maxs")
    with st.form("form_max"):
        selected_maxs = st.multiselect("Exercice testé :", EXOS_MUSCU + EXOS_TESTS)
        max_entries = []

        for exo in selected_maxs:
            if "watt" in exo.lower():
                unite = "Watts"
            elif "saut" in exo.lower() or "lancer" in exo.lower():
                unite = "m"
            else:
                unite = "kg"

            valeur = st.number_input(f"{exo} ({unite})", min_value=0.0, step=0.1, key=f"max_{exo}")
            max_entries.append(f"{exo} : {valeur} {unite}")

        submit_max = st.form_submit_button("✅ Enregistrer le test")
        if submit_max:
            new_row = [
                athlete,
                selected_date.strftime("%Y-%m-%d"),
                jour,
                "Max",
                "; ".join(max_entries),
                "", "", "", "", "", ""
            ]
            df, sheet = load_sheet(SHEET_ID, SHEET_MAXS)
            append_row_to_sheet(sheet, new_row)
            st.success("Max enregistré ✅")

    st.subheader("📊 Historique des maxs")
    df_maxs, _ = load_sheet(SHEET_ID, SHEET_MAXS)
    athlète_filtré = st.selectbox("🔎 Filtrer par athlète :", ATHLETES, key="filtre_max")
    df_filtré = df_maxs[df_maxs["Athlète"] == athlète_filtré]

    if df_filtré.empty:
        st.info("Aucun max enregistré pour cet athlète.")
    else:
        st.dataframe(df_filtré)
