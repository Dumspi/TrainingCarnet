import streamlit as st
from datetime import datetime
from some_module import load_sheet, append_row_to_sheet  # adapte selon ton code

# Listes d'athlètes et exercices
ATHLETES = ["Joffrey", "Marie", "Dorine", "Fabien", "Yann", "Lucile", "Arthur", "Baptiste"]

EXOS_MUSCU = [
    "Épaulé", "Épaulé avec bandes", "Arraché", "Arraché avec bandes", "Arraché force",
    "Squat", "Squat avec ceinture", "Demi-squat", "Pull over avec mouvement du bassin",
    "Pull over avec haltère", "Développé couché strict", "Développé couché avec mouvement du bassin",
    "Renfo ischios", "Renfo adducteurs", "Tirage nuque", "Tirage rowing", "Abdos",
    "Exos lombaires", "Renfo cheville", "Dips", "Vélo", "Rowing machine", "Lancer de medecine ball"
]

EXOS_PREPA = ["Médecine ball", "Passage de haies", "Série de médecine ball JB", "Gainage"]
EXOS_TECH = ["Lancers de balles", "Courses d’élan", "Point technique précis", "Lancers de javelots"]

SHEET_ID = "ton_sheet_id"
SHEET_NAME = "ton_nom_de_feuille"

st.title("Carnet de séance Javelot")

athlete = st.selectbox("Athlète :", ATHLETES)
selected_date = st.date_input("Date :", datetime.today())
phase = st.selectbox("Phase :", ["Prépa", "Compétition", "Récupération"])
type_seance = st.selectbox("Type de séance :", ["Musculation", "Prépa Physique", "Technique", "Autre"])

exercices = []

with st.form("form_seance"):
    if type_seance == "Musculation":
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

    elif type_seance == "Prépa Physique":
        prepa = st.multiselect("Prépa physique :", EXOS_PREPA)
        prepa_comment = st.text_area("Commentaire prépa")
        exercices = prepa

    elif type_seance == "Technique":
        tech = st.multiselect("Technique :", EXOS_TECH)
        tech_comment = st.text_area("Commentaire technique")
        exercices = tech

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
        exos_final = "; ".join(exercices) if exercices else (autres_exos if type_seance == "Autre" else "")
        if type_seance == "Prépa Physique" and prepa_comment:
            exos_final += f"\nPrépa : {prepa_comment}"
        if type_seance == "Technique" and tech_comment:
            exos_final += f"\nTechnique : {tech_comment}"

        new_row = [
            athlete,
            selected_date.strftime("%Y-%m-%d"),
            selected_date.strftime("%A"),
            phase,
            type_seance,
            exos_final,
            sommeil,
            hydratation,
            nutrition,
            rpe,
            fatigue,
            notes
        ]
        df, sheet = load_sheet(SHEET_ID, SHEET_NAME)
        append_row_to_sheet(sheet, new_row)
        st.success("Séance enregistrée ✅")
        df, _ = load_sheet(SHEET_ID, SHEET_NAME)
        st.dataframe(df)

# Export CSV
df, _ = load_sheet(SHEET_ID, SHEET_NAME)
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📁 Télécharger CSV", csv, "carnet_javelot.csv", "text/csv")
