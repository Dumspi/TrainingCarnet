import streamlit as st
import pandas as pd
from datetime import date

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

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

# Exercices proposés
EXOS_MUSCU = ["Épaulé", "Arraché", "Soulevé de terre", "Squat", "Pull over"]
EXOS_PREPA = ["Médecine ball", "Passage de haies", "Série de médecine ball JB", "Gainage"]
EXOS_TECH = ["Lancers de balles", "Courses d’élan", "Point technique précis", "Lancers de javelots"]

# Tests
TESTS_MAX_MUSCU = EXOS_MUSCU.copy()
TESTS_MAX_JAVELOT = [
    "Saut en longueur sans élan",
    "Éjection lancer de poids 4kg avant",
    "Éjection lancer de poids 4kg arrière",
    "Lancer médecine ball 4kg"
]
TEST_SAUT_HAUTEUR = "Saut en hauteur sans élan"

# ------------------- FONCTIONS -------------------

def get_phase(current_date):
    for phase, start, end, mardi, jeudi in PHASES:
        if start <= current_date <= end:
            return phase, mardi, jeudi
    return "Hors phase", "Repos", "Repos"


# ------------------- INTERFACE -------------------

st.title("📘 Carnet de suivi d'entraînement - Javelot")

selected_date = st.date_input("📅 Choisis la date de la séance :", date.today())
weekday = selected_date.weekday()

if weekday > 4:
    st.warning("Pas de séance prévue ce jour-là (week-end).")
    st.stop()

jour = JOURS[weekday]
phase, mardi_type, jeudi_type = get_phase(selected_date)

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

st.subheader(f"📍 {jour} — {phase} — {type_seance}")

# Onglets
tab_seance, tab_tests = st.tabs(["Séance", "Tests max"])

with tab_seance:
    with st.form("formulaire_seance"):

        # ------------------- EXERCICES RÉALISÉS -------------------
        st.markdown("### 🏋️ Exercices réalisés")

        def input_reps_for_exos(exos):
            exos_reps = []
            for exo in exos:
                reps = st.text_input(f"Répétitions pour {exo} (ex: 3x10)", key=f"reps_{exo}")
                exos_reps.append(f"{exo} ({reps})" if reps else exo)
            return exos_reps

        exercices_selectionnes = []
        exercices_reps = []
        exercices_libres = ""

        if jour == "Lundi":
            exercices_selectionnes = st.multiselect("Exercices de musculation", EXOS_MUSCU)
            exercices_reps = input_reps_for_exos(exercices_selectionnes)

        elif jour in ["Mardi", "Jeudi"]:
            choix_type = st.radio("Type de séance", ["Prépa physique", "Technique", "Les deux"])

            options = []
            if choix_type in ["Prépa physique", "Les deux"]:
                options += EXOS_PREPA
            if choix_type in ["Technique", "Les deux"]:
                options += EXOS_TECH

            exercices_selectionnes = st.multiselect("Exercices réalisés", options)
            exercices_reps = input_reps_for_exos(exercices_selectionnes)

        else:
            exercices_libres = st.text_area("Exercices réalisés (libre)")

        # Champ libre pour compléter
        autres_exos = st.text_area("Autres exercices / précisions")

        # ------------------- INFOS PHYSIQUES -------------------
        st.markdown("### 🩻 Ressenti / récupération")

        douleur_type = st.radio("Douleur ressentie", ["Aucune", "Musculaire", "Articulaire"], index=0)
        douleur_zone = st.text_input("Zone de douleur (si applicable)", disabled=douleur_type == "Aucun_
