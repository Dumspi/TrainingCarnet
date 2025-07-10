import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

# ------------------- PARAMÈTRES FIXES -------------------

PHASES = [
    ("Prépa 1", date(2025, 9, 1), date(2025, 12, 31), "PPG/Technique", "PPG/Technique"),
    ("Pré-compétition janvier", date(2026, 1, 1), date(2026, 1, 31), "PPG/Technique", "Technique"),
    ("Compétition février", date(2026, 2, 1), date(2026, 2, 28), "Technique", "Technique"),
    ("Prépa 2", date(2026, 3, 1), date(2026, 4, 15), "PPG/Technique", "PPG/Technique"),
    ("Pré-compétition avril-mai", date(2026, 4, 16), date(2026, 5, 15), "PPG/Technique", "Technique"),
    ("Compétition mai-juillet", date(2026, 5, 16), date(2026, 7, 15), "Technique", "Technique"),
    ("Repos août", date(2026, 8, 1), date(2026, 8, 31), "Repos", "Repos"),
]

REGIMES = {
    9: "5x5",
    10: "5x5",
    11: "15 → 8 reps",
    12: "15 → 8 reps",
    1: "x5",
    2: "x3",
    3: "x10",
    4: "x6",
    5: "x5",
    6: "x3",
    7: "3 → 1 rep",
}

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

# ------------------- FONCTIONS -------------------

def get_phase(current_date):
    for phase, start, end, mardi, jeudi in PHASES:
        if start <= current_date <= end:
            return phase, mardi, jeudi
    return "Hors phase", "Repos", "Repos"

def get_regime(current_date, type_seance):
    if type_seance in ["Muscu", "Gym/Muscu/Mobilité"]:
        return REGIMES.get(current_date.month, "")
    return ""

# ------------------- INTERFACE -------------------

st.title("📘 Carnet de suivi d'entraînement - Javelot")

selected_date = st.date_input("📅 Choisis la date de la séance :", date.today())

day_name = selected_date.strftime("%A")
weekday = selected_date.weekday()

if weekday > 4:
    st.warning("Pas de séance prévue ce jour-là (week-end).")
    st.stop()

jour = JOURS[weekday]
phase, mardi_type, jeudi_type = get_phase(selected_date)

# Type de séance
if jour == "Lundi":
    type_seance = "Muscu"
elif jour == "Mardi":
    type_seance = mardi_type
elif jour == "Mercredi":
    type_seance = "Gym/Muscu/Mobilité"
elif jour == "Jeudi":
    type_seance = jeudi_type
else:
    type_seance = "Muscu"

regime = get_regime(selected_date, type_seance)

# ------------------- FORMULAIRE -------------------

st.subheader(f"📍 {jour} — {phase} — {type_seance}")
if regime:
    st.markdown(f"**Régime musculaire recommandé :** `{regime}`")

with st.form("formulaire_seance"):
    exercices = st.text_area("Exercices réalisés")
    charge_reps = st.text_input("Charges / Répétitions")
    rpe = st.slider("RPE / Intensité ressentie", 1, 10, 7)
    fatigue = st.slider("Fatigue générale (1 reposé — 10 cramé)", 1, 10, 5)
    notes = st.text_area("Remarques / sensations")

    submitted = st.form_submit_button("💾 Enregistrer la séance")

    if submitted:
        # Stockage dans session (pour test local, on peut ensuite sauvegarder ailleurs)
        if "data" not in st.session_state:
            st.session_state.data = []

        st.session_state.data.append({
            "Date": selected_date.strftime("%Y-%m-%d"),
            "Jour": jour,
            "Période": phase,
            "Séance": type_seance,
            "Régime musculaire": regime,
            "Exercices": exercices,
            "Charge / reps": charge_reps,
            "RPE": rpe,
            "Fatigue": fatigue,
            "Notes": notes
        })
        st.success("Séance enregistrée !")

# ------------------- TABLEAU + EXPORT -------------------

if "data" in st.session_state and st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("📊 Historique")
    st.dataframe(df)

    st.download_button("⬇️ Télécharger en Excel", data=df.to_excel(index=False), file_name="carnet_suivi.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
