import streamlit as st
import pandas as pd
from datetime import date

# ---------- PARAMÈTRES ----------

PHASES = [
    ("Prépa 1", date(2025, 9, 1), date(2025, 12, 31), "PPG/Technique", "PPG/Technique"),
    ("Pré-compétition janvier", date(2026, 1, 1), date(2026, 1, 31), "PPG/Technique", "Technique"),
    ("Compétition février", date(2026, 2, 1), date(2026, 2, 28), "Technique", "Technique"),
    ("Prépa 2", date(2026, 3, 1), date(2026, 4, 15), "PPG/Technique", "PPG/Technique"),
    ("Pré-compétition avril-mai", date(2026, 4, 16), date(2026, 5, 15), "PPG/Technique", "Technique"),
    ("Compétition mai-juillet", date(2026, 5, 16), date(2026, 7, 15), "Technique", "Technique"),
]

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

EXOS_MUSCU = ["Épaulé", "Arraché", "Soulevé de terre", "Squat", "Pull over"]
EXOS_PREPA = ["Médecine ball", "Passage de haies", "Série de médecine ball JB", "Gainage"]
EXOS_TECH = ["Lancers de balles", "Courses d’élan", "Point technique précis", "Lancers de javelots"]

TESTS_MAX_MUSCU = EXOS_MUSCU
TESTS_MAX_JAVELOT = [
    "Saut en longueur sans élan",
    "Éjection lancer de poids 4kg avant",
    "Éjection lancer de poids 4kg arrière",
    "Lancer médecine ball 4kg"
]
TEST_SAUT_HAUTEUR = "Saut en hauteur sans élan"

# ---------- FONCTIONS ----------

def get_phase(current_date):
    for phase, start, end, mardi, jeudi in PHASES:
        if start <= current_date <= end:
            return phase, mardi, jeudi
    return "", "PPG/Technique", "PPG/Technique"  # Valeurs par défaut

# ---------- INTERFACE ----------

st.set_page_config(page_title="Carnet Javelot", layout="centered")
st.title("📘 Carnet de suivi - Javelot")

selected_date = st.date_input("📅 Choisis la date :", date.today())

if isinstance(selected_date, date):
    weekday = selected_date.weekday()
else:
    st.error("La date sélectionnée est invalide.")
    st.stop()

if weekday > 4:
    st.warning("Aucune séance prévue le week-end.")
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

# ---------- TABS ----------

tab_seance, tab_tests = st.tabs(["📝 Séance", "🧪 Tests max"])

# ---------- SÉANCE ----------

with tab_seance:
    with st.form("formulaire_seance"):
        st.markdown("### 🏋️ Exercices réalisés")

        def saisie_exercices(exercices):
            resultats = []
            for exo in exercices:
                reps = st.text_input(f"{exo} – Répétitions :", key=f"reps_{exo}")
                resultats.append(f"{exo} ({reps})" if reps else exo)
            return resultats

        exercices_reps = []
        autres_exos = ""

        if jour == "Lundi":
            selection = st.multiselect("Exos muscu", EXOS_MUSCU)
            exercices_reps = saisie_exercices(selection)

        elif jour in ["Mardi", "Jeudi"]:
            choix = st.radio("Type de séance :", ["Prépa physique", "Technique", "Les deux"])
            options = []
            if choix in ["Prépa physique", "Les deux"]:
                options += EXOS_PREPA
            if choix in ["Technique", "Les deux"]:
                options += EXOS_TECH
            selection = st.multiselect("Exercices :", options)
            exercices_reps = saisie_exercices(selection)

        else:
            autres_exos = st.text_area("Exercices réalisés (libre)")

        st.markdown("### 💬 Ressenti & récupération")
        douleur = st.radio("Douleur ressentie :", ["Aucune", "Musculaire", "Articulaire"])
        zone_douleur = st.text_input("Zone de douleur :", disabled=(douleur == "Aucune"))
        sommeil = st.slider("🌙 Sommeil (0 = très mauvais, 10 = excellent)", 0, 10, 5)
        hydratation = st.slider("💧 Hydratation (0 à 10)", 0, 10, 5)
        nutrition = st.slider("🍎 Nutrition (0 à 10)", 0, 10, 5)
        rpe = st.slider("🔥 Intensité ressentie (RPE)", 1, 10, 7)
        fatigue = st.slider("😴 Fatigue générale (1 = reposé, 10 = épuisé)", 1, 10, 5)
        notes = st.text_area("Remarques complémentaires")

        submit = st.form_submit_button("💾 Enregistrer la séance")

        if submit:
            exos_final = "; ".join(exercices_reps) if exercices_reps else autres_exos
            if "data" not in st.session_state:
                st.session_state.data = []

            st.session_state.data.append({
                "Date": selected_date.strftime("%Y-%m-%d"),
                "Jour": jour,
                "Phase": phase,
                "Type": type_seance,
                "Exercices": exos_final,
                "Douleur": douleur,
                "Zone douleur": zone_douleur,
                "Sommeil": sommeil,
                "Hydratation": hydratation,
                "Nutrition": nutrition,
                "RPE": rpe,
                "Fatigue": fatigue,
                "Notes": notes
            })

            st.success("Séance enregistrée avec succès ✅")

# ---------- TESTS ----------

with tab_tests:
    st.markdown("### 🧪 Tests de performance")
    tests = {}

    def saisir_test(label):
        return st.number_input(f"{label} :", min_value=0.0, step=0.1)

    if jour == "Lundi":
        tests_choisis = st.multiselect("Tests muscu", TESTS_MAX_MUSCU)
        for test in tests_choisis:
            tests[test] = saisir_test(test)

    if jour in ["Mardi", "Jeudi"]:
        tests_choisis = st.multiselect("Tests explosivité", TESTS_MAX_JAVELOT)
        for test in tests_choisis:
            tests[test] = saisir_test(test)

    if st.checkbox("Inclure saut en hauteur sans élan"):
        tests[TEST_SAUT_HAUTEUR] = saisir_test(TEST_SAUT_HAUTEUR)

    if st.button("💾 Enregistrer les tests"):
        if "data" not in st.session_state:
            st.session_state.data = []

        enregistrement = {
            "Date": selected_date.strftime("%Y-%m-%d"),
            "Jour": jour,
            "Phase": phase,
            "Type": type_seance
        }
        enregistrement.update(tests)
        st.session_state.data.append(enregistrement)
        st.success("Tests enregistrés ✅")

# ---------- EXPORT ----------

if "data" in st.session_state and st.session_state.data:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("📊 Historique")
    st.dataframe(df)

    st.download_button(
        "⬇️ Télécharger l'historique (.xlsx)",
        data=df.to_excel(index=False),
        file_name="carnet_suivi.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
