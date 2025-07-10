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

EXOS_MUSCU = ["Épaulé", "Arraché", "Soulevé de terre", "Squat", "Pull over"]
EXOS_PREPA = ["Médecine ball", "Passage de haies", "Série de médecine ball JB", "Gainage"]
EXOS_TECH = ["Lancers de balles", "Courses d’élan", "Point technique précis", "Lancers de javelots"]

TESTS_MAX_MUSCU = EXOS_MUSCU.copy()
TESTS_MAX_JAVELOT = [
    "Saut en longueur sans élan",
    "Éjection lancer de poids 4kg avant",
    "Éjection lancer de poids 4kg arrière",
    "Lancer médecine ball 4kg"
]
TEST_SAUT_HAUTEUR = "Saut en hauteur sans élan"

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

# ------------------- ONGLET SÉANCE -------------------

tab_seance, tab_tests = st.tabs(["Séance", "Tests max"])

with tab_seance:
    with st.form("formulaire_seance"):

        st.markdown("### 🏋️ Exercices réalisés")

        def input_reps_for_exos(exos):
            exos_reps = []
            for exo in exos:
                reps = st.text_input(f"Répétitions pour {exo}", key=f"reps_{exo}")
                exos_reps.append(f"{exo} ({reps})" if reps else exo)
            return exos_reps

        exercices_selectionnes = []
        exercices_reps = []
        autres_exos = ""

        if jour == "Lundi":
            exercices_selectionnes = st.multiselect("Exercices de musculation", EXOS_MUSCU)
            exercices_reps = input_reps_for_exos(exercices_selectionnes)

        elif jour in ["Mardi", "Jeudi"]:
            type_jour = st.radio("Type de séance", ["Prépa physique", "Technique", "Les deux"])
            options = []
            if type_jour in ["Prépa physique", "Les deux"]:
                options += EXOS_PREPA
            if type_jour in ["Technique", "Les deux"]:
                options += EXOS_TECH
            exercices_selectionnes = st.multiselect("Exercices réalisés", options)
            exercices_reps = input_reps_for_exos(exercices_selectionnes)

        else:
            autres_exos = st.text_area("Exercices réalisés (texte libre)")

        st.markdown("### 🩻 Ressenti / récupération")

        douleur_type = st.radio("Douleur ressentie", ["Aucune", "Musculaire", "Articulaire"], index=0)
        douleur_zone = st.text_input("Zone de douleur (si applicable)", disabled=douleur_type == "Aucune")

        sommeil = st.slider("🌙 Sommeil (0 à 10)", 0, 10, 5)
        hydratation = st.slider("💧 Hydratation (0 à 10)", 0, 10, 5)
        nutrition = st.slider("🍎 Nutrition (0 à 10)", 0, 10, 5)

        rpe = st.slider("🔥 Intensité (RPE 1 à 10)", 1, 10, 7)
        fatigue = st.slider("😩 Fatigue générale (1 reposé — 10 épuisé)", 1, 10, 5)

        notes = st.text_area("🗒️ Remarques / sensations")

        submitted = st.form_submit_button("💾 Enregistrer la séance")

        if submitted:
            exercices_str = "; ".join(exercices_reps) if exercices_reps else autres_exos

            if "data" not in st.session_state:
                st.session_state.data = []

            st.session_state.data.append({
                "Date": selected_date.strftime("%Y-%m-%d"),
                "Jour": jour,
                "Période": phase,
                "Séance": type_seance,
                "Exercices": exercices_str,
                "Douleur": douleur_type,
                "Zone douleur": douleur_zone,
                "Sommeil": sommeil,
                "Hydratation": hydratation,
                "Nutrition": nutrition,
                "RPE": rpe,
                "Fatigue": fatigue,
                "Notes": notes
            })

            st.success("✅ Séance enregistrée !")

# ------------------- ONGLET TESTS -------------------

with tab_tests:
    st.markdown("### 🧪 Tests max")
    tests_resultats = {}

    def input_test_result(test_name):
        return st.number_input(f"Résultat - {test_name}", min_value=0.0, step=0.1, format="%.2f")

    if jour == "Lundi":
        tests_selectionnes = st.multiselect("Tests muscu", TESTS_MAX_MUSCU)
        for test in tests_selectionnes:
            tests_resultats[test] = input_test_result(test)

    if jour in ["Mardi", "Jeudi"]:
        tests_selectionnes = st.multiselect("Tests explosivité / javelot", TESTS_MAX_JAVELOT)
        for test in tests_selectionnes:
            tests_resultats[test] = input_test_result(test)

    if st.checkbox("Ajouter test : Saut en hauteur sans élan"):
        tests_resultats[TEST_SAUT_HAUTEUR] = input_test_result(TEST_SAUT_HAUTEUR)

    if st.button("💾 Enregistrer les tests"):
        if "data" not in st.session_state:
            st.session_state.data = []

        entry = {
            "Date": selected_date.strftime("%Y-%m-%d"),
            "Jour": jour,
            "Période": phase,
            "Séance": type_seance
        }
        entry.update(tests_resultats)

        st.session_state.data.append(entry)
        st.success("✅ Tests enregistrés !")

# ------------------- HISTORIQUE + EXPORT -------------------

if "data" in st.session_state and st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("📊 Historique des entrées")
    st.dataframe(df)

    st.download_button(
        "⬇️ Télécharger en Excel",
        data=df.to_excel(index=False),
        file_name="carnet_suivi.xlsx",
mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
