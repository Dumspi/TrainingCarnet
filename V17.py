import json
import unicodedata
from datetime import date

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


# ============================================================
# CONFIGURATION GOOGLE SHEETS
# ============================================================

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = "1JrfYOXXajQFjl_wMqHpM4qJfBkgZiUO2VtTiPuwhmEk"

PROGRAMME_SHEET_NAME = "programme"
SEANCES_SHEET_NAME = "séances enregistrées"
MAXS_SHEET_NAME = "Maxs"


# ============================================================
# PARAMÈTRES
# ============================================================

ATHLETES = [
    "Joffrey", "Marie", "Dorine", "Fabien",
    "Yann", "Lucile", "Arthur", "Baptiste"
]

JOURS = [
    "lundi", "mardi", "mercredi", "jeudi",
    "vendredi", "samedi", "dimanche"
]

EXOS_MUSCU = [
    "Épaulé",
    "Épaulé avec bandes",
    "Arraché",
    "Arraché avec bandes",
    "Arraché force",
    "Squat",
    "Squat avec ceinture",
    "Demi-squat",
    "Pull over avec mouvement du bassin",
    "Pull over avec haltère",
    "Développé couché strict",
    "Développé couché avec mouvement du bassin",
]

PERF_PHYSIQUE = [
    ("Watt max vélo", "Watt"),
    ("Saut en longueur sans élan", "m"),
]

LANCERS = [
    ("Lancer de medecine ball de 4kg en touche", "m"),
    ("Lancer de poids avant 4kg", "m"),
    ("Lancer de poids arrière 4kg", "m"),
    ("Lancer de javelot sans élan", "m"),
    ("Lancer de javelot sur un hop", "m"),
]

SEANCE_HEADERS = [
    "Athlète",
    "Date",
    "Semaine",
    "Jour",
    "Catégorie",
    "Exercice prévu",
    "Exercice réalisé",
    "Statut",
    "Séries prévues",
    "Répétitions prévues",
    "Charge prévue",
    "Pourcentage prévu",
    "Séries réalisées",
    "Répétitions réalisées",
    "Charge réalisée",
    "Pourcentage réalisé",
    "Motif",
    "Commentaire",
]

MAX_HEADERS = [
    "Athlète",
    "Date",
    "Jour",
    "Type",
    "Catégorie",
    "Exercice",
    "Valeur",
    "Unité",
    "Commentaire",
]


# ============================================================
# CONNEXION GOOGLE SHEETS
# ============================================================

@st.cache_resource
def get_gsheet_client():
    try:
        with open("credentials.json", "r", encoding="utf-8") as file:
            creds_data = json.load(file)

        credentials = Credentials.from_service_account_info(
            creds_data,
            scopes=SCOPES,
        )
        return gspread.authorize(credentials)

    except Exception as exc:
        st.error(
            "⛔ Impossible de charger credentials.json.\n\n"
            f"Détail : {exc}"
        )
        st.stop()


@st.cache_resource
def get_workbook():
    client = get_gsheet_client()
    return client.open_by_key(SHEET_ID)


def get_or_create_worksheet(name, headers):
    workbook = get_workbook()

    try:
        worksheet = workbook.worksheet(name)
    except gspread.WorksheetNotFound:
        worksheet = workbook.add_worksheet(
            title=name,
            rows=2000,
            cols=max(len(headers), 10),
        )

    if not worksheet.get_all_values():
        worksheet.append_row(headers, value_input_option="USER_ENTERED")

    return worksheet


def load_programme():
    workbook = get_workbook()

    try:
        worksheet = workbook.worksheet(PROGRAMME_SHEET_NAME)
    except gspread.WorksheetNotFound:
        st.error(
            f"⛔ L’onglet « {PROGRAMME_SHEET_NAME} » est introuvable."
        )
        st.stop()

    records = worksheet.get_all_records()
    dataframe = pd.DataFrame(records)

    if dataframe.empty:
        return dataframe

    # Uniformise les noms de colonnes venant du tableur.
    dataframe.columns = [
        normaliser_texte(column)
        for column in dataframe.columns
    ]

    return dataframe


def append_rows(worksheet, rows):
    if not rows:
        return

    worksheet.append_rows(
        rows,
        value_input_option="USER_ENTERED",
    )


# ============================================================
# OUTILS
# ============================================================

def normaliser_texte(value):
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )


def as_float(value, default=0.0):
    if value in (None, ""):
        return default

    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def as_int(value, default=0):
    return int(round(as_float(value, default)))


def afficher_nombre(value):
    number = as_float(value)

    if number == 0:
        return ""

    if number.is_integer():
        return str(int(number))

    return str(number).replace(".", ",")


def construire_resume(row):
    pieces = []

    series = as_int(row.get("series", 0))
    repetitions = as_int(row.get("repetitions", 0))
    charge = as_float(row.get("charges", 0))
    pourcentage = as_float(row.get("pourcentage", 0))

    if series and repetitions:
        pieces.append(f"{series} × {repetitions}")
    elif series:
        pieces.append(f"{series} série(s)")
    elif repetitions:
        pieces.append(f"{repetitions} répétition(s)")

    if charge:
        pieces.append(f"{afficher_nombre(charge)} kg")

    if pourcentage:
        pieces.append(f"{afficher_nombre(pourcentage)} %")

    return " — ".join(pieces) if pieces else "Consigne libre"


def filtrer_seance(programme, selected_date):
    if programme.empty:
        return programme

    week_number = selected_date.isocalendar().week
    day_name = JOURS[selected_date.weekday()]

    required_columns = {
        "semaine",
        "jour",
        "categorie",
        "exercice",
        "series",
        "repetitions",
        "charges",
        "pourcentage",
    }

    missing = required_columns.difference(programme.columns)

    if missing:
        st.error(
            "⛔ Il manque des colonnes dans l’onglet programme : "
            + ", ".join(sorted(missing))
        )
        st.stop()

    programme = programme.copy()
    programme["semaine_num"] = pd.to_numeric(
        programme["semaine"],
        errors="coerce",
    )
    programme["jour_normalise"] = programme["jour"].map(normaliser_texte)

    return programme[
        (programme["semaine_num"] == week_number)
        & (programme["jour_normalise"] == day_name)
    ]


def liste_exercices_connus(programme):
    base = EXOS_MUSCU + [name for name, _ in PERF_PHYSIQUE] + [
        name for name, _ in LANCERS
    ]

    if not programme.empty and "exercice" in programme.columns:
        base.extend(
            str(value).strip()
            for value in programme["exercice"].dropna().tolist()
            if str(value).strip()
        )

    return sorted(set(base), key=str.casefold)


# ============================================================
# INTERFACE
# ============================================================

st.set_page_config(
    page_title="Carnet Team Lancers",
    layout="centered",
)

st.sidebar.title("👤 Sélection du profil")
athlete = st.sidebar.selectbox(
    "Sélectionne l’athlète :",
    ATHLETES,
    key="select_athlete",
)

st.title("📘 Carnet de suivi — Team Lancers")

selected_date = st.date_input(
    "📅 Choisis la date :",
    date.today(),
)

week_number = selected_date.isocalendar().week
day_name = JOURS[selected_date.weekday()]

st.caption(
    f"Semaine {week_number} — {day_name.capitalize()} "
    f"{selected_date.strftime('%d/%m/%Y')}"
)

programme = load_programme()
seance_du_jour = filtrer_seance(programme, selected_date)
exercices_connus = liste_exercices_connus(programme)

tab_seance, tab_maxs = st.tabs([
    "✅ Séance du jour",
    "🔺 Maxs",
])


# ============================================================
# ONGLET SÉANCE DU JOUR
# ============================================================

with tab_seance:
    st.subheader("Séance prévue")

    if seance_du_jour.empty:
        st.info(
            "Aucune séance n’est programmée pour cette semaine et ce jour."
        )
    else:
        st.write(
            "Coche les exercices faits comme prévu. "
            "Ouvre « Modifier ou remplacer » uniquement si nécessaire."
        )

        with st.form("form_seance_du_jour"):
            rows_to_save = []

            for position, (_, row) in enumerate(
                seance_du_jour.iterrows(),
                start=1,
            ):
                category = str(row.get("categorie", "")).strip()
                planned_exercise = str(row.get("exercice", "")).strip()

                planned_series = as_int(row.get("series", 0))
                planned_reps = as_int(row.get("repetitions", 0))
                planned_load = as_float(row.get("charges", 0))
                planned_percent = as_float(row.get("pourcentage", 0))

                st.markdown(
                    f"### {position}. {planned_exercise}"
                )

                if category:
                    st.caption(
                        f"{category.capitalize()} — {construire_resume(row)}"
                    )
                else:
                    st.caption(construire_resume(row))

                done_as_planned = st.checkbox(
                    "Fait comme prévu",
                    key=f"done_{position}",
                )

                status = "Fait comme prévu" if done_as_planned else "Non fait"
                realized_exercise = planned_exercise
                realized_series = planned_series
                realized_reps = planned_reps
                realized_load = planned_load
                realized_percent = planned_percent
                reason = ""
                comment = ""

                if not done_as_planned:
                    status = st.radio(
                        "Que s’est-il passé ?",
                        ["Non fait", "Modifié / remplacé"],
                        horizontal=True,
                        key=f"status_{position}",
                    )

                    if status == "Modifié / remplacé":
                        with st.expander(
                            "Modifier ou remplacer l’exercice",
                            expanded=True,
                        ):
                            use_known_exercise = st.checkbox(
                                "Choisir un exercice dans la liste",
                                value=True,
                                key=f"use_known_{position}",
                            )

                            if use_known_exercise:
                                default_index = (
                                    exercices_connus.index(planned_exercise)
                                    if planned_exercise in exercices_connus
                                    else 0
                                )

                                realized_exercise = st.selectbox(
                                    "Exercice réellement effectué",
                                    exercices_connus,
                                    index=default_index,
                                    key=f"realized_exercise_{position}",
                                )
                            else:
                                realized_exercise = st.text_input(
                                    "Nom de l’exercice réellement effectué",
                                    value=planned_exercise,
                                    key=f"custom_exercise_{position}",
                                )

                            col1, col2 = st.columns(2)

                            with col1:
                                realized_series = st.number_input(
                                    "Séries réalisées",
                                    min_value=0,
                                    value=planned_series,
                                    step=1,
                                    key=f"realized_series_{position}",
                                )
                                realized_load = st.number_input(
                                    "Charge réalisée (kg)",
                                    min_value=0.0,
                                    value=planned_load,
                                    step=0.5,
                                    key=f"realized_load_{position}",
                                )

                            with col2:
                                realized_reps = st.number_input(
                                    "Répétitions réalisées",
                                    min_value=0,
                                    value=planned_reps,
                                    step=1,
                                    key=f"realized_reps_{position}",
                                )
                                realized_percent = st.number_input(
                                    "Pourcentage réalisé",
                                    min_value=0.0,
                                    max_value=200.0,
                                    value=planned_percent,
                                    step=1.0,
                                    key=f"realized_percent_{position}",
                                )

                            reason = st.selectbox(
                                "Motif de la modification",
                                [
                                    "",
                                    "Douleur",
                                    "Fatigue",
                                    "Matériel indisponible",
                                    "Consigne de l’entraîneur",
                                    "Manque de temps",
                                    "Autre",
                                ],
                                key=f"reason_{position}",
                            )

                            comment = st.text_input(
                                "Commentaire",
                                key=f"comment_{position}",
                            )

                    else:
                        reason = st.selectbox(
                            "Motif",
                            [
                                "",
                                "Douleur",
                                "Fatigue",
                                "Manque de temps",
                                "Séance annulée",
                                "Autre",
                            ],
                            key=f"not_done_reason_{position}",
                        )
                        comment = st.text_input(
                            "Commentaire",
                            key=f"not_done_comment_{position}",
                        )

                rows_to_save.append({
                    "category": category,
                    "planned_exercise": planned_exercise,
                    "realized_exercise": (
                        realized_exercise
                        if status != "Non fait"
                        else ""
                    ),
                    "status": status,
                    "planned_series": planned_series,
                    "planned_reps": planned_reps,
                    "planned_load": planned_load,
                    "planned_percent": planned_percent,
                    "realized_series": (
                        realized_series
                        if status != "Non fait"
                        else 0
                    ),
                    "realized_reps": (
                        realized_reps
                        if status != "Non fait"
                        else 0
                    ),
                    "realized_load": (
                        realized_load
                        if status != "Non fait"
                        else 0
                    ),
                    "realized_percent": (
                        realized_percent
                        if status != "Non fait"
                        else 0
                    ),
                    "reason": reason,
                    "comment": comment,
                })

                st.divider()

            st.subheader("➕ Exercices non prévus")

            added_count = st.number_input(
                "Nombre d’exercices ajoutés",
                min_value=0,
                max_value=10,
                value=0,
                step=1,
            )

            added_rows = []

            for extra_index in range(int(added_count)):
                st.markdown(f"#### Exercice ajouté {extra_index + 1}")

                category = st.selectbox(
                    "Catégorie",
                    [
                        "échauffement",
                        "muscu",
                        "lancers",
                        "technique",
                        "renforcement",
                        "saut",
                        "course",
                        "footing",
                        "autre",
                    ],
                    key=f"extra_category_{extra_index}",
                )

                choose_from_list = st.checkbox(
                    "Choisir dans la liste",
                    value=True,
                    key=f"extra_known_{extra_index}",
                )

                if choose_from_list:
                    exercise = st.selectbox(
                        "Exercice",
                        exercices_connus,
                        key=f"extra_exercise_{extra_index}",
                    )
                else:
                    exercise = st.text_input(
                        "Nom de l’exercice",
                        key=f"extra_custom_{extra_index}",
                    )

                col1, col2 = st.columns(2)

                with col1:
                    series = st.number_input(
                        "Séries",
                        min_value=0,
                        step=1,
                        key=f"extra_series_{extra_index}",
                    )
                    load = st.number_input(
                        "Charge (kg)",
                        min_value=0.0,
                        step=0.5,
                        key=f"extra_load_{extra_index}",
                    )

                with col2:
                    reps = st.number_input(
                        "Répétitions",
                        min_value=0,
                        step=1,
                        key=f"extra_reps_{extra_index}",
                    )
                    percent = st.number_input(
                        "Pourcentage",
                        min_value=0.0,
                        max_value=200.0,
                        step=1.0,
                        key=f"extra_percent_{extra_index}",
                    )

                reason = st.text_input(
                    "Pourquoi cet exercice a-t-il été ajouté ?",
                    key=f"extra_reason_{extra_index}",
                )

                comment = st.text_input(
                    "Commentaire",
                    key=f"extra_comment_{extra_index}",
                )

                added_rows.append({
                    "category": category,
                    "exercise": exercise,
                    "series": series,
                    "reps": reps,
                    "load": load,
                    "percent": percent,
                    "reason": reason,
                    "comment": comment,
                })

                st.divider()

            general_comment = st.text_area(
                "Commentaire général sur la séance",
            )

            submit_session = st.form_submit_button(
                "✅ Enregistrer toute la séance",
                use_container_width=True,
            )

        if submit_session:
            session_sheet = get_or_create_worksheet(
                SEANCES_SHEET_NAME,
                SEANCE_HEADERS,
            )

            date_text = selected_date.strftime("%Y-%m-%d")
            rows = []

            for item in rows_to_save:
                comment = item["comment"]

                if general_comment:
                    comment = (
                        f"{comment} | {general_comment}"
                        if comment
                        else general_comment
                    )

                rows.append([
                    athlete,
                    date_text,
                    week_number,
                    day_name,
                    item["category"],
                    item["planned_exercise"],
                    item["realized_exercise"],
                    item["status"],
                    item["planned_series"],
                    item["planned_reps"],
                    item["planned_load"],
                    item["planned_percent"],
                    item["realized_series"],
                    item["realized_reps"],
                    item["realized_load"],
                    item["realized_percent"],
                    item["reason"],
                    comment,
                ])

            for item in added_rows:
                comment = item["comment"]

                if general_comment:
                    comment = (
                        f"{comment} | {general_comment}"
                        if comment
                        else general_comment
                    )

                rows.append([
                    athlete,
                    date_text,
                    week_number,
                    day_name,
                    item["category"],
                    "",
                    item["exercise"],
                    "Ajouté",
                    0,
                    0,
                    0,
                    0,
                    item["series"],
                    item["reps"],
                    item["load"],
                    item["percent"],
                    item["reason"],
                    comment,
                ])

            append_rows(session_sheet, rows)

            st.success(
                f"✅ Séance enregistrée : {len(rows)} ligne(s) ajoutée(s)."
            )


# ============================================================
# ONGLET MAXS
# ============================================================

with tab_maxs:
    with st.form("form_maxs"):
        st.subheader("🏋️ Maxs musculation")

        maxs_muscu = {}

        for exercise in EXOS_MUSCU:
            value = st.number_input(
                f"{exercise} (kg)",
                min_value=0.0,
                step=0.5,
                key=f"max_{exercise}",
            )

            if value > 0:
                maxs_muscu[exercise] = value

        st.subheader("🚴 Performances physiques")
        perf_physique = {}

        for name, unit in PERF_PHYSIQUE:
            value = st.number_input(
                f"{name} ({unit})",
                min_value=0.0,
                step=0.1,
                key=f"perf_{name}",
            )

            if value > 0:
                perf_physique[name] = (value, unit)

        st.subheader("🏹 Maxs lancers")
        maxs_lancers = {}

        for name, unit in LANCERS:
            value = st.number_input(
                f"{name} ({unit})",
                min_value=0.0,
                step=0.1,
                key=f"lancer_{name}",
            )

            if value > 0:
                maxs_lancers[name] = (value, unit)

        max_comment = st.text_area(
            "🗒️ Commentaire général",
            key="max_comment",
        )

        submit_maxs = st.form_submit_button(
            "✅ Enregistrer les maxs"
        )

    if submit_maxs:
        max_sheet = get_or_create_worksheet(
            MAXS_SHEET_NAME,
            MAX_HEADERS,
        )

        date_text = selected_date.strftime("%Y-%m-%d")
        max_rows = []

        for exercise, value in maxs_muscu.items():
            max_rows.append([
                athlete,
                date_text,
                day_name,
                "Max",
                "Muscu",
                exercise,
                value,
                "kg",
                max_comment,
            ])

        for name, (value, unit) in perf_physique.items():
            max_rows.append([
                athlete,
                date_text,
                day_name,
                "Max",
                "Perf physique",
                name,
                value,
                unit,
                max_comment,
            ])

        for name, (value, unit) in maxs_lancers.items():
            max_rows.append([
                athlete,
                date_text,
                day_name,
                "Max",
                "Lancer",
                name,
                value,
                unit,
                max_comment,
            ])

        if max_rows:
            append_rows(max_sheet, max_rows)
            st.success("✅ Maxs enregistrés.")
        else:
            st.warning("Aucune valeur supérieure à zéro n’a été saisie.")
