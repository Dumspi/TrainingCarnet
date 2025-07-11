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

EXOS_MUSCU = [
    "Épaulé", "Épaulé avec bandes", "Arraché", "Arraché avec bandes", "Arraché force",
    "Squat", "Squat avec ceinture", "Demi-squat", "Demi-squat avec ceintures", "Pull over avec mouvement du bassin",
    "Pull over avec haltère", "Développé couché strict", "Développé couché avec mouvement du bassin",
    "Renfo ischios", "Renfo adducteurs", "Tirage nuque", "Tirage rowing", "Abdos",
    "Exos lombaires", "Renfo cheville", "Dips", "Vélo", "Rowing machine", "Lancer de medecine ball", "poulie javelot"
]

EXOS_PREPA = ["Medecine ball", " Série passages de haies", "Série de medecine ball JB", "Gainage", "séries exos javelot avec barre olympique"]
EXOS_TECH = ["Lancers de balles 400g", "Lancers de balles 500g", "Lancers de balles 600g", "Lancers de balles 700g", 
             "Lancers de balles 800g", "Lancers de balles 900g", "Lancers de balles 1Kg", "Lancers de balles 1Kg200", 
             "Lancers de balles 1Kg500", "Lancers de balles 2Kg", "Courses d’élan", "Courses d'élan avec lattes", "Série de courses d'élan Yann", 
             "Lancers de javelots"]

TESTS_MAX_MUSCU = EXOS_MUSCU
TESTS_MAX_JAVELOT = [
    "Saut en longueur sans élan", "Éjection lancer de poids 4kg avant",
    "Éjection lancer de poids 4kg arrière", "Lancer médecine ball 4kg"
]
TEST_SAUT_HAUTEUR = "Saut en hauteur sans élan"

ZONES_DOULEUR = [
    "Épaule droite", "Épaule gauche", "Coude droit", "Coude gauche", "Poignet droit", "Poignet gauche",
    "Dos haut", "Bas du dos", "Hanche droite", "Hanche gauche", "Genou droit", "Genou gauche",
    "Cheville droite", "Cheville gauche", "Cuisses", "Ischio-jambiers", "Mollets"
]

# ---------- FONCTIONS ----------

def get_phase(current_date):
    for phase, start, end, mardi, jeudi in PHASES:
        if start <= current_date <= end:
            return phase, mardi, jeudi
    return "", "PPG/Technique", "PPG/Technique"

# ---------- INTERFACE ----------

st.set_page_config(page_title="Carnet Javelot", layout="centered")
st.title("📘 Carnet de suivi - Javelot")

selected_date = st.date_input("📅 Choisis la date :", date.today())
if not isinstance(selected_date, date):
    st.error("La date sélectionnée est invalide.")
    st.stop()

weekday = selected_date.weekday()
if weekday > 4:
    st.warning("Aucune séance prévue le week-end.")
    st.stop()

jour = JOURS[weekday]
phase, mardi_type, jeudi_type = get_phase(selected_date)
type_seance = "Muscu" if jour in ["Lundi", "Mercredi", "Vendredi"] else (mardi_type if jour == "Mardi" else jeudi_type)

st.subheader(f"📍 {jour} — {phase} — {type_seance}")

# ---------- ONGLETS ----------
tab_seance, tab_douleur, tab_tests = st.tabs(["📝 Séance", "⚠️ Douleur", "🧪 Tests max"])

# ---------- ONGLET SÉANCE ----------

with tab_seance:
              # 🔁 EN DEHORS DU FORMULAIRE pour garder sélection réactive
selection = []
if jour in ["Lundi", "Mercredi", "Vendredi"]:
    selection = st.multiselect("Exercices muscu réalisés :", EXOS_MUSCU)

with st.form("formulaire_seance"):
    exercices_reps = []

    if jour in ["Lundi", "Mercredi", "Vendredi"]:
        exos_details = {}
        for exo in selection:
            st.markdown(f"**{exo}**")
            col1, col2, col3 = st.columns(3)
            with col1:
                charge = st.number_input(f"Charge (kg) pour {exo}", min_value=0.0, step=0.5, key=f"charge_{exo}")
            with col2:
                reps = st.number_input(f"Répétitions pour {exo}", min_value=0, step=1, key=f"reps_{exo}")
            with col3:
                series = st.number_input(f"Séries pour {exo}", min_value=0, step=1, key=f"series_{exo}")
            exos_details[exo] = {
                "charge": charge,
                "repetitions": reps,
                "series": series
            }

        for exo, vals in exos_details.items():
            exercices_reps.append(f"{exo} – {vals['charge']} kg x {vals['repetitions']} reps x {vals['series']} séries")

    elif jour in ["Mardi", "Jeudi"]:
        st.markdown("#### Préparation Physique")
        prepa_selection = st.multiselect("Exercices prépa physique :", EXOS_PREPA, key="prepa_exos")
        prepa_comment = st.text_area("Commentaires prépa physique :", key="prepa_comment")

        st.markdown("#### Technique")
        tech_selection = st.multiselect("Exercices technique :", EXOS_TECH, key="tech_exos")
        tech_comment = st.text_area("Commentaires technique :", key="tech_comment")

        exercices_reps = prepa_selection + tech_selection

    else:
        autres_exos = st.text_area("Exercices réalisés (libre)")

    # Autres infos générales
    sommeil = st.slider("🌙 Sommeil (0 = très mauvais, 10 = excellent)", 0, 10, 5)
    hydratation = st.slider("💧 Hydratation (0 à 10)", 0, 10, 5)
    nutrition = st.slider("🍎 Nutrition (0 à 10)", 0, 10, 5)
    rpe = st.slider("🔥 Intensité ressentie (RPE)", 1, 10, 7)
    fatigue = st.slider("😴 Fatigue générale (1 = reposé, 10 = épuisé)", 1, 10, 5)
    notes = st.text_area("Remarques complémentaires")

    submit = st.form_submit_button("💾 Enregistrer la séance")

    if submit:
        exos_final = "; ".join(exercices_reps) if exercices_reps else autres_exos

        if jour in ["Mardi", "Jeudi"]:
            if prepa_comment:
                exos_final += f"\nPrépa physique – Commentaires : {prepa_comment}"
            if tech_comment:
                exos_final += f"\nTechnique – Commentaires : {tech_comment}"

        if "data" not in st.session_state:
            st.session_state.data = []

        st.session_state.data.append({
            "Date": selected_date.strftime("%Y-%m-%d"),
            "Jour": jour,
            "Phase": phase,
            "Type": type_seance,
            "Exercices": exos_final,
            "Sommeil": sommeil,
            "Hydratation": hydratation,
            "Nutrition": nutrition,
            "RPE": rpe,
            "Fatigue": fatigue,
            "Notes": notes
        })

        st.success("Séance enregistrée avec succès ✅")

# ---------- ONGLET DOULEUR ----------
with tab_douleur:
    with st.form("formulaire_douleur"):
        st.markdown("### ⚠️ Douleur")

        type_douleur = st.selectbox("Type de douleur :", ["Aucune", "Musculaire", "Articulaire", "Tendineuse"], key="type_douleur")

        zones_selectionnees = []
        autre_zone = ""

        if type_douleur != "Aucune":
            zones_selectionnees = st.multiselect("Zones concernées :", ZONES_DOULEUR, key="zones_douleur")
            autre_zone = st.text_input("Autre zone non listée :", key="autre_zone")

        zone_douleur_finale = ", ".join(zones_selectionnees)
        if autre_zone.strip():
            zone_douleur_finale += (", " if zone_douleur_finale else "") + autre_zone.strip()

        commentaire_douleur = st.text_area("Commentaires douleur / sensations")

        submit_douleur = st.form_submit_button("💾 Enregistrer la douleur")

        if submit_douleur:
            if "data" not in st.session_state:
                st.session_state.data = []

            st.session_state.data.append({
                "Date": selected_date.strftime("%Y-%m-%d"),
                "Jour": jour,
                "Phase": phase,
                "Type": type_seance,
                "Douleur": type_douleur,
                "Zones douleur": zone_douleur_finale,
                "Commentaire douleur": commentaire_douleur
            })

            st.success("Douleur enregistrée ✅")

# ---------- ONGLET TESTS ----------
with tab_tests:
    st.markdown("### 🧪 Tests de performance")
    tests = {}

    def saisir_test(label):
        return st.number_input(f"{label} :", min_value=0.0, step=0.1, key=f"test_{label}")

    if jour in ["Lundi", "Mercredi", "Vendredi"]:
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

        st.session_state.data.append({
            "Date": selected_date.strftime("%Y-%m-%d"),
            "Jour": jour,
            "Phase": phase,
            "Type": type_seance,
            "Tests": tests
        })
        st.success("Tests enregistrés ✅")

# ---------- AFFICHAGE DONNÉES ----------
if "data" in st.session_state and st.session_state.data:
    st.markdown("## 📊 Données enregistrées")
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df)
