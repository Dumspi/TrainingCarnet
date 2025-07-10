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
    "Squat", "Squat avec ceinture", "Demi-squat", "Pull over avec mouvement du bassin",
    "Pull over avec haltère", "Développé couché strict", "Développé couché avec mouvement du bassin",
    "Renfo ischios", "Renfo adducteurs", "Tirage nuque", "Tirage rowing", "Abdos",
    "Exos lombaires", "Renfo cheville", "Dips", "Vélo", "Rowing machine", "Lancer de médecine ball"
]

EXOS_PREPA = ["Médecine ball", "Passage de haies", "Série de médecine ball JB", "Gainage"]
EXOS_TECH = ["Lancers de balles", "Courses d’élan", "Point technique précis", "Lancers de javelots"]

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

# ---------- SAISIE MUSCU ----------
if type_seance == "Muscu":
    with st.form("form_muscu"):
        st.markdown("### 🏋️ Exercices de musculation")
        selection = st.multiselect("Exercices effectués :", EXOS_MUSCU)
        exercices_reps = []

        for exo in selection:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{exo}**")
            with col2:
                charge = st.number_input(f"Charge ({exo})", min_value=0.0, step=2.5, key=f"charge_{exo}")
            with col3:
                reps = st.number_input(f"Répétitions ({exo})", min_value=0, step=1, key=f"reps_{exo}")
            exercices_reps.append(f"{exo} – {charge} kg x {reps} reps")

        sommeil = st.slider("🌙 Sommeil (0 = très mauvais, 10 = excellent)", 0, 10, 5)
        hydratation = st.slider("💧 Hydratation (0 à 10)", 0, 10, 5)
        nutrition = st.slider("🍎 Nutrition (0 à 10)", 0, 10, 5)
        rpe = st.slider("🔥 Intensité ressentie (RPE)", 1, 10, 7)
        fatigue = st.slider("😴 Fatigue générale (1 = reposé, 10 = épuisé)", 1, 10, 5)
        notes = st.text_area("Remarques complémentaires")

        submit = st.form_submit_button("💾 Enregistrer la séance")

        if submit:
            if "data" not in st.session_state:
                st.session_state.data = []

            st.session_state.data.append({
                "Date": selected_date.strftime("%Y-%m-%d"),
                "Jour": jour,
                "Phase": phase,
                "Type": type_seance,
                "Exercices": "; ".join(exercices_reps),
                "Sommeil": sommeil,
                "Hydratation": hydratation,
                "Nutrition": nutrition,
                "RPE": rpe,
                "Fatigue": fatigue,
                "Notes": notes
            })

            st.success("Séance enregistrée ✅")

# ---------- ONGLET DOULEUR ----------
st.markdown("### ⚠️ Douleur")
with st.form("formulaire_douleur"):
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
