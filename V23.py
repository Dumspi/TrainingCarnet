import hmac
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
WELLNESS_SHEET_NAME = "suivi quotidien"
ROUTINES_SHEET_NAME = "routines réalisées"


# ============================================================
# PARAMÈTRES
# ============================================================

ATHLETES = [
    "Marie",
    "Dorine",
    "Yann",
    "Evan",
    "Joffrey",
    "Yara",
    "Julie",
    "Lucile",
    "Fabien",
    "Naomie",
]

ATHLETE_GROUPS = {
    "Marie": "marteau",
    "Dorine": "disque",
    "Yann": "javelot",
    "Evan": "javelot",
    "Joffrey": "javelot",
    "Yara": "marteau",
    "Julie": "disque",
    "Lucile": "javelot",
    "Fabien": "javelot",
    "Naomie": "javelot",
}

JOURS = [
    "lundi", "mardi", "mercredi", "jeudi",
    "vendredi", "samedi", "dimanche"
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


WELLNESS_HEADERS = [
    "Athlète",
    "Date",
    "Semaine",
    "Jour",
    "Durée séance (min)",
    "RPE séance",
    "Fatigue avant",
    "Fatigue après",
    "Sommeil",
    "Motivation",
    "Douleur",
    "Zone douloureuse",
    "Courbatures",
    "Stress",
    "Commentaire bien-être",
    "Indice de vigilance",
]

ROUTINE_HEADERS = [
    "Athlète",
    "Date",
    "Semaine",
    "Jour",
    "Discipline",
    "Routine",
    "Réalisée",
    "Commentaire",
]

COMMON_ROUTINES = [
    "Gainage / tronc",
    "Mobilité générale",
    "Chevilles / proprioception",
]

DISCIPLINE_ROUTINES = {
    "javelot": [
        "Épaule / coiffe des rotateurs",
        "Mobilité thoracique",
        "Coude / avant-bras",
    ],
    "marteau": [
        "Hanches / bassin",
        "Adducteurs",
        "Chaîne postérieure",
    ],
    "disque": [
        "Hanches / bassin",
        "Mobilité thoracique",
        "Genoux / chevilles",
    ],
}


# ============================================================
# CONNEXION GOOGLE SHEETS
# ============================================================

@st.cache_resource
def get_gsheet_client():
    """Connexion Google Sheets, en local ou sur Streamlit Community Cloud."""
    try:
        # En ligne : le JSON complet de credentials.json est placé
        # dans le secret gcp_service_account_json.
        if "gcp_service_account_json" in st.secrets:
            creds_data = json.loads(
                st.secrets["gcp_service_account_json"]
            )
        else:
            # En local : on conserve le fonctionnement historique.
            with open("credentials.json", "r", encoding="utf-8") as file:
                creds_data = json.load(file)

        credentials = Credentials.from_service_account_info(
            creds_data,
            scopes=SCOPES,
        )
        return gspread.authorize(credentials)

    except Exception as exc:
        st.error(
            "⛔ Impossible de se connecter à Google Sheets.\n\n"
            "En local, vérifie credentials.json. En ligne, ajoute le secret "
            "gcp_service_account_json dans Streamlit Cloud.\n\n"
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


def load_worksheet_dataframe(sheet_name):
    """
    Charge un onglet Google Sheets sans utiliser get_all_records().

    Cette méthode tolère :
    - les anciens tableaux avec des en-têtes en double ;
    - les colonnes sans titre ;
    - les lignes historiques plus courtes ou plus longues.
    """
    workbook = get_workbook()

    try:
        worksheet = workbook.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        return pd.DataFrame()

    values = worksheet.get_all_values()

    if not values:
        return pd.DataFrame()

    raw_headers = values[0]
    data_rows = values[1:]

    # Donne un nom aux colonnes vides et rend chaque en-tête unique.
    headers = []
    counts = {}

    for position, header in enumerate(raw_headers, start=1):
        normalized = normaliser_texte(header)

        if not normalized:
            normalized = f"colonne_{position}"

        counts[normalized] = counts.get(normalized, 0) + 1

        if counts[normalized] > 1:
            normalized = f"{normalized}_{counts[normalized]}"

        headers.append(normalized)

    # Aligne toutes les lignes sur le nombre de colonnes de l'en-tête.
    width = len(headers)
    cleaned_rows = []

    for row in data_rows:
        padded = list(row[:width]) + [""] * max(0, width - len(row))
        cleaned_rows.append(padded)

    dataframe = pd.DataFrame(cleaned_rows, columns=headers)

    # Supprime uniquement les lignes entièrement vides.
    dataframe = dataframe.replace("", pd.NA).dropna(how="all").fillna("")

    return dataframe


def compute_vigilance_score(
    fatigue_after,
    sleep,
    pain,
    stress,
    rpe,
):
    """Score simple de vigilance, sans valeur diagnostique."""
    score = 0

    if fatigue_after >= 8:
        score += 2
    elif fatigue_after >= 6:
        score += 1

    if sleep <= 2:
        score += 2
    elif sleep == 3:
        score += 1

    if pain >= 6:
        score += 3
    elif pain >= 3:
        score += 1

    if stress >= 8:
        score += 1

    if rpe >= 9:
        score += 1

    return score


def vigilance_label(score):
    if score >= 5:
        return "Élevée"
    if score >= 3:
        return "Modérée"
    return "Faible"


def routines_for_athlete(athlete_name):
    discipline = ATHLETE_GROUPS.get(athlete_name, "")
    return COMMON_ROUTINES + DISCIPLINE_ROUTINES.get(
        discipline,
        [],
    )


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


def filtrer_seance(programme, selected_date, athlete):
    if programme.empty:
        return programme

    week_number = selected_date.isocalendar().week
    day_name = JOURS[selected_date.weekday()]
    athlete_group = normaliser_texte(ATHLETE_GROUPS[athlete])

    required_columns = {
        "semaine",
        "jour",
        "groupe",
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
    programme["groupe_normalise"] = programme["groupe"].map(normaliser_texte)

    return programme[
        (programme["semaine_num"] == week_number)
        & (programme["jour_normalise"] == day_name)
        & (
            (programme["groupe_normalise"] == athlete_group)
            | (programme["groupe_normalise"] == "tous")
        )
    ]


def liste_exercices_connus(programme):
    """Retourne les exercices déjà présents dans la programmation."""
    if programme.empty or "exercice" not in programme.columns:
        return ["Autre exercice"]

    exercises = [
        str(value).strip()
        for value in programme["exercice"].dropna().tolist()
        if str(value).strip()
    ]

    unique_exercises = sorted(set(exercises), key=str.casefold)
    return unique_exercises or ["Autre exercice"]



# ============================================================
# CONNEXION ATHLÈTES / ENTRAÎNEUR
# ============================================================

COACH_PROFILE = "Entraîneur"


def get_profile_codes():
    """Charge les codes personnels depuis st.secrets."""
    try:
        raw_codes = dict(st.secrets["profile_codes"])
    except Exception:
        st.error(
            "⛔ Aucun code de profil n’est configuré.\n\n"
            "Ajoute une section [profile_codes] dans les secrets Streamlit."
        )
        st.stop()

    codes = {
        normaliser_texte(name): str(pin).strip()
        for name, pin in raw_codes.items()
    }

    missing = [
        athlete_name
        for athlete_name in ATHLETES
        if normaliser_texte(athlete_name) not in codes
    ]

    if missing:
        st.error(
            "⛔ Il manque un code pour : " + ", ".join(missing)
        )
        st.stop()

    return codes


def get_coach_code():
    try:
        return str(st.secrets["coach_code"]).strip()
    except Exception:
        return ""


def verifier_code(profile_name, entered_code):
    entered = str(entered_code).strip()

    if profile_name == COACH_PROFILE:
        expected = get_coach_code()
        return bool(expected) and hmac.compare_digest(entered, expected)

    expected = get_profile_codes()[normaliser_texte(profile_name)]
    return hmac.compare_digest(entered, expected)


def afficher_connexion():
    st.title("🔐 Carnet Team Lancers")
    st.write("Sélectionne ton profil puis saisis ton code personnel.")

    with st.form("login_form", clear_on_submit=False):
        selected_profile = st.selectbox(
            "Profil",
            ATHLETES + [COACH_PROFILE],
            key="login_profile",
        )
        entered_code = st.text_input(
            "Code personnel",
            type="password",
            max_chars=30,
            key="login_code",
        )
        submitted = st.form_submit_button(
            "Se connecter",
            use_container_width=True,
        )

    if submitted:
        if verifier_code(selected_profile, entered_code):
            st.session_state["authenticated"] = True
            st.session_state["profile"] = selected_profile
            st.session_state["is_coach"] = (
                selected_profile == COACH_PROFILE
            )
            st.session_state.pop("login_code", None)
            st.rerun()
        else:
            st.error("Profil ou code incorrect.")


def deconnexion():
    st.session_state.clear()
    st.rerun()


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    afficher_connexion()
    st.stop()

profile = st.session_state["profile"]
is_coach = bool(st.session_state.get("is_coach", False))
athlete = None if is_coach else profile


# ============================================================
# INTERFACE
# ============================================================

st.set_page_config(
    page_title="Carnet Team Lancers — V23",
    layout="centered",
)

st.sidebar.title("👤 Mon profil")
st.sidebar.success(profile)

if not is_coach:
    athlete_group = ATHLETE_GROUPS[athlete]
    st.sidebar.caption(f"Groupe : {athlete_group.capitalize()}")

if st.sidebar.button(
    "Se déconnecter",
    use_container_width=True,
):
    deconnexion()

st.title("📘 Carnet de suivi — Team Lancers")

programme = load_programme()
exercices_connus = liste_exercices_connus(programme)

if is_coach:
    st.subheader("📊 Tableau de bord entraîneur")
    st.caption(
        "Suivi des séances, de la fatigue, des douleurs et des routines. "
        "Les indicateurs servent à ouvrir le dialogue, pas à poser un diagnostic."
    )

    sessions = load_worksheet_dataframe(SEANCES_SHEET_NAME)
    wellness = load_worksheet_dataframe(WELLNESS_SHEET_NAME)
    routines = load_worksheet_dataframe(ROUTINES_SHEET_NAME)

    col1, col2 = st.columns(2)

    with col1:
        selected_week = st.number_input(
            "Semaine à analyser",
            min_value=1,
            max_value=53,
            value=int(date.today().isocalendar().week),
            step=1,
        )

    with col2:
        selected_athlete = st.selectbox(
            "Athlète",
            ["Tous"] + ATHLETES,
        )

    def apply_filters(dataframe):
        filtered_df = dataframe.copy()

        if filtered_df.empty:
            return filtered_df

        if "semaine" in filtered_df.columns:
            filtered_df["semaine_num"] = pd.to_numeric(
                filtered_df["semaine"],
                errors="coerce",
            )
            filtered_df = filtered_df[
                filtered_df["semaine_num"] == int(selected_week)
            ]

        if (
            selected_athlete != "Tous"
            and "athlete" in filtered_df.columns
        ):
            filtered_df = filtered_df[
                filtered_df["athlete"].astype(str).str.strip()
                == selected_athlete
            ]

        return filtered_df

    filtered_sessions = apply_filters(sessions)
    filtered_wellness = apply_filters(wellness)
    filtered_routines = apply_filters(routines)

    total = len(filtered_sessions)
    done = modified = not_done = 0

    if "statut" in filtered_sessions.columns:
        statuses = filtered_sessions["statut"].astype(str)
        done = int((statuses == "Fait comme prévu").sum())
        modified = int((statuses == "Modifié / remplacé").sum())
        not_done = int((statuses == "Non fait").sum())

    avg_rpe = 0.0
    avg_fatigue = 0.0
    avg_sleep = 0.0
    pain_alerts = 0

    if not filtered_wellness.empty:
        for source_col, target_name in [
            ("rpe_seance", "rpe_numeric"),
            ("fatigue_apres", "fatigue_numeric"),
            ("sommeil", "sleep_numeric"),
            ("douleur", "pain_numeric"),
        ]:
            if source_col in filtered_wellness.columns:
                filtered_wellness[target_name] = pd.to_numeric(
                    filtered_wellness[source_col],
                    errors="coerce",
                )

        if "rpe_numeric" in filtered_wellness:
            avg_rpe = filtered_wellness["rpe_numeric"].mean()
        if "fatigue_numeric" in filtered_wellness:
            avg_fatigue = filtered_wellness["fatigue_numeric"].mean()
        if "sleep_numeric" in filtered_wellness:
            avg_sleep = filtered_wellness["sleep_numeric"].mean()
        if "pain_numeric" in filtered_wellness:
            pain_alerts = int(
                (filtered_wellness["pain_numeric"] >= 5).sum()
            )

    routine_rate = 0.0
    if (
        not filtered_routines.empty
        and "realisee" in filtered_routines.columns
    ):
        routine_values = (
            filtered_routines["realisee"]
            .astype(str)
            .str.lower()
        )
        routine_rate = (
            routine_values.isin(["oui", "true", "1"]).mean() * 100
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Exercices saisis", total)
    m2.metric("Faits comme prévu", done)
    m3.metric("Modifiés", modified)
    m4.metric("Non faits", not_done)

    n1, n2, n3, n4 = st.columns(4)
    n1.metric("RPE moyen", f"{avg_rpe:.1f}" if pd.notna(avg_rpe) else "—")
    n2.metric(
        "Fatigue moyenne",
        f"{avg_fatigue:.1f}" if pd.notna(avg_fatigue) else "—",
    )
    n3.metric(
        "Sommeil moyen",
        f"{avg_sleep:.1f}/5" if pd.notna(avg_sleep) else "—",
    )
    n4.metric("Routines réalisées", f"{routine_rate:.0f}%")

    if pain_alerts:
        st.warning(
            f"⚠️ {pain_alerts} saisie(s) avec une douleur ≥ 5/10 "
            "sur la période sélectionnée."
        )

    if (
        not filtered_wellness.empty
        and "indice_de_vigilance" in filtered_wellness.columns
    ):
        high_alerts = filtered_wellness[
            filtered_wellness["indice_de_vigilance"]
            .astype(str)
            .isin(["Élevée", "Elevee"])
        ]

        if not high_alerts.empty:
            st.error(
                "🚨 Vigilance élevée détectée. Vérifie la fatigue, "
                "le sommeil et les douleurs avec l’athlète."
            )

    coach_tab1, coach_tab2, coach_tab3 = st.tabs([
        "Séances",
        "Fatigue et récupération",
        "Routines",
    ])

    with coach_tab1:
        if (
            not filtered_sessions.empty
            and "statut" in filtered_sessions.columns
        ):
            status_counts = (
                filtered_sessions["statut"]
                .value_counts()
                .rename_axis("Statut")
                .to_frame("Nombre")
            )
            st.bar_chart(status_counts)

        display_columns = [
            column for column in [
                "athlete",
                "date",
                "jour",
                "categorie",
                "exercice_prevu",
                "exercice_realise",
                "statut",
                "motif",
                "commentaire",
            ]
            if column in filtered_sessions.columns
        ]

        if filtered_sessions.empty:
            st.info("Aucune séance ne correspond à ces filtres.")
        else:
            st.dataframe(
                (
                    filtered_sessions[display_columns]
                    if display_columns
                    else filtered_sessions
                ),
                use_container_width=True,
                hide_index=True,
            )

    with coach_tab2:
        wellness_columns = [
            column for column in [
                "athlete",
                "date",
                "duree_seance_min",
                "rpe_seance",
                "fatigue_avant",
                "fatigue_apres",
                "sommeil",
                "motivation",
                "douleur",
                "zone_douloureuse",
                "courbatures",
                "stress",
                "indice_de_vigilance",
                "commentaire_bien_etre",
            ]
            if column in filtered_wellness.columns
        ]

        if filtered_wellness.empty:
            st.info("Aucune donnée de récupération pour cette période.")
        else:
            st.dataframe(
                filtered_wellness[wellness_columns],
                use_container_width=True,
                hide_index=True,
            )

    with coach_tab3:
        routine_columns = [
            column for column in [
                "athlete",
                "date",
                "discipline",
                "routine",
                "realisee",
                "commentaire",
            ]
            if column in filtered_routines.columns
        ]

        if filtered_routines.empty:
            st.info("Aucune routine enregistrée pour cette période.")
        else:
            st.dataframe(
                filtered_routines[routine_columns],
                use_container_width=True,
                hide_index=True,
            )

    st.stop()

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

seance_du_jour = filtrer_seance(programme, selected_date, athlete)

tab_seance, tab_recuperation, tab_historique = st.tabs([
    "✅ Séance du jour",
    "🧠 État du jour",
    "🕘 Mon historique",
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
            "Choisis un seul statut pour chaque exercice. "
            "Complète les détails uniquement en cas de modification."
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

                status = st.radio(
                    "Statut de l’exercice",
                    [
                        "Fait comme prévu",
                        "Modifié / remplacé",
                        "Non fait",
                    ],
                    horizontal=True,
                    key=f"status_{position}",
                )

                realized_exercise = planned_exercise
                realized_series = planned_series
                realized_reps = planned_reps
                realized_load = planned_load
                realized_percent = planned_percent
                reason = ""
                comment = ""

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

                elif status == "Non fait":
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

            st.markdown("### Ressenti de la séance")
            st.caption(
                "Ces informations aident à adapter la charge future. "
                "Elles ne remplacent pas un avis médical."
            )

            col_a, col_b = st.columns(2)

            with col_a:
                session_duration = st.number_input(
                    "Durée de la séance (minutes)",
                    min_value=0,
                    max_value=300,
                    value=60,
                    step=5,
                )
                session_rpe = st.slider(
                    "Difficulté ressentie — RPE",
                    min_value=1,
                    max_value=10,
                    value=5,
                )
                fatigue_before = st.slider(
                    "Fatigue avant la séance",
                    min_value=1,
                    max_value=10,
                    value=4,
                )
                fatigue_after = st.slider(
                    "Fatigue après la séance",
                    min_value=1,
                    max_value=10,
                    value=5,
                )

            with col_b:
                sleep_quality = st.slider(
                    "Qualité du sommeil",
                    min_value=1,
                    max_value=5,
                    value=3,
                )
                motivation = st.slider(
                    "Motivation",
                    min_value=1,
                    max_value=5,
                    value=3,
                )
                pain_level = st.slider(
                    "Douleur actuelle",
                    min_value=0,
                    max_value=10,
                    value=0,
                )
                pain_zone = st.selectbox(
                    "Zone douloureuse",
                    [
                        "Aucune",
                        "Épaule",
                        "Coude",
                        "Dos",
                        "Hanche",
                        "Genou",
                        "Cheville",
                        "Autre",
                    ],
                )

            col_c, col_d = st.columns(2)

            with col_c:
                soreness = st.slider(
                    "Courbatures",
                    min_value=0,
                    max_value=10,
                    value=2,
                )

            with col_d:
                stress = st.slider(
                    "Stress général",
                    min_value=0,
                    max_value=10,
                    value=3,
                )

            wellness_comment = st.text_area(
                "Commentaire récupération / douleur",
            )

            st.markdown("### Routines de prévention")
            routine_results = []

            for routine_name in routines_for_athlete(athlete):
                completed = st.checkbox(
                    routine_name,
                    key=f"routine_{normaliser_texte(routine_name)}",
                )
                routine_results.append((routine_name, completed))

            routine_comment = st.text_input(
                "Commentaire sur les routines",
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

            vigilance_score = compute_vigilance_score(
                fatigue_after=fatigue_after,
                sleep=sleep_quality,
                pain=pain_level,
                stress=stress,
                rpe=session_rpe,
            )
            vigilance = vigilance_label(vigilance_score)

            wellness_sheet = get_or_create_worksheet(
                WELLNESS_SHEET_NAME,
                WELLNESS_HEADERS,
            )

            append_rows(
                wellness_sheet,
                [[
                    athlete,
                    date_text,
                    week_number,
                    day_name,
                    session_duration,
                    session_rpe,
                    fatigue_before,
                    fatigue_after,
                    sleep_quality,
                    motivation,
                    pain_level,
                    pain_zone,
                    soreness,
                    stress,
                    wellness_comment,
                    vigilance,
                ]],
            )

            routine_sheet = get_or_create_worksheet(
                ROUTINES_SHEET_NAME,
                ROUTINE_HEADERS,
            )

            discipline = ATHLETE_GROUPS.get(athlete, "")
            routine_rows = [
                [
                    athlete,
                    date_text,
                    week_number,
                    day_name,
                    discipline,
                    routine_name,
                    "Oui" if completed else "Non",
                    routine_comment,
                ]
                for routine_name, completed in routine_results
            ]
            append_rows(routine_sheet, routine_rows)

            st.success(
                f"✅ Séance enregistrée : {len(rows)} exercice(s), "
                f"{len(routine_rows)} routine(s) suivie(s)."
            )

            if vigilance == "Élevée":
                st.error(
                    "🚨 Indice de vigilance élevé : parle avec ton entraîneur "
                    "et adapte la prochaine charge si nécessaire."
                )
            elif vigilance == "Modérée":
                st.warning(
                    "⚠️ Vigilance modérée : surveille la récupération, "
                    "le sommeil et les douleurs."
                )
            else:
                st.info(
                    "🟢 Indice de vigilance faible pour cette saisie."
                )


# ============================================================
# ONGLET ÉTAT DU JOUR
# ============================================================

with tab_recuperation:
    st.subheader("🧠 État du jour et récupération")
    st.write(
        "Cette vue résume tes dernières saisies afin de mieux anticiper "
        "la charge et préserver une pratique durable."
    )

    wellness_history = load_worksheet_dataframe(WELLNESS_SHEET_NAME)
    routine_history = load_worksheet_dataframe(ROUTINES_SHEET_NAME)

    if (
        wellness_history.empty
        or "athlete" not in wellness_history.columns
    ):
        st.info(
            "Aucune donnée de récupération enregistrée pour le moment. "
            "Elle apparaîtra après ta prochaine séance."
        )
    else:
        wellness_history = wellness_history[
            wellness_history["athlete"].astype(str).str.strip()
            == athlete
        ].copy()

        if wellness_history.empty:
            st.info("Aucune donnée personnelle enregistrée.")
        else:
            if "date" in wellness_history.columns:
                wellness_history["date_parsed"] = pd.to_datetime(
                    wellness_history["date"],
                    errors="coerce",
                )
                wellness_history = wellness_history.sort_values(
                    "date_parsed",
                    ascending=False,
                )

            latest = wellness_history.iloc[0]

            def latest_number(column, default=0):
                return pd.to_numeric(
                    pd.Series([latest.get(column, default)]),
                    errors="coerce",
                ).fillna(default).iloc[0]

            latest_rpe = latest_number("rpe_seance")
            latest_fatigue = latest_number("fatigue_apres")
            latest_sleep = latest_number("sommeil")
            latest_pain = latest_number("douleur")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Dernier RPE", f"{latest_rpe:.0f}/10")
            c2.metric("Fatigue", f"{latest_fatigue:.0f}/10")
            c3.metric("Sommeil", f"{latest_sleep:.0f}/5")
            c4.metric("Douleur", f"{latest_pain:.0f}/10")

            vigilance = str(
                latest.get("indice_de_vigilance", "Faible")
            )

            if vigilance == "Élevée":
                st.error(
                    "🚨 Vigilance élevée sur la dernière saisie. "
                    "Échange avec l’entraîneur avant une séance intense."
                )
            elif vigilance == "Modérée":
                st.warning(
                    "⚠️ Vigilance modérée. Priorité à la récupération "
                    "et à la qualité du mouvement."
                )
            else:
                st.success(
                    "🟢 Les derniers indicateurs ne signalent pas "
                    "de vigilance particulière."
                )

            trend_columns = [
                column for column in [
                    "fatigue_apres",
                    "douleur",
                    "rpe_seance",
                ]
                if column in wellness_history.columns
            ]

            if "date_parsed" in wellness_history and trend_columns:
                trends = wellness_history[
                    ["date_parsed"] + trend_columns
                ].copy()

                for column in trend_columns:
                    trends[column] = pd.to_numeric(
                        trends[column],
                        errors="coerce",
                    )

                trends = (
                    trends
                    .dropna(subset=["date_parsed"])
                    .sort_values("date_parsed")
                    .set_index("date_parsed")
                    .tail(12)
                )

                if not trends.empty:
                    st.line_chart(trends)

    st.markdown("### Régularité des routines")

    if (
        routine_history.empty
        or "athlete" not in routine_history.columns
    ):
        st.info("Aucune routine enregistrée pour le moment.")
    else:
        routine_history = routine_history[
            routine_history["athlete"].astype(str).str.strip()
            == athlete
        ].copy()

        if not routine_history.empty and "realisee" in routine_history:
            completed = (
                routine_history["realisee"]
                .astype(str)
                .str.lower()
                .isin(["oui", "true", "1"])
            )
            adherence = completed.mean() * 100
            st.metric(
                "Routines réalisées",
                f"{adherence:.0f}%",
            )

            if "routine" in routine_history.columns:
                routine_summary = (
                    routine_history
                    .assign(realisee_num=completed.astype(int))
                    .groupby("routine", as_index=False)["realisee_num"]
                    .mean()
                )
                routine_summary["Réalisation (%)"] = (
                    routine_summary["realisee_num"] * 100
                ).round(0)

                st.dataframe(
                    routine_summary[
                        ["routine", "Réalisation (%)"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )


# ============================================================
# ONGLET HISTORIQUE ATHLÈTE
# ============================================================

with tab_historique:
    st.subheader("🕘 Mes séances enregistrées")

    history_df = load_worksheet_dataframe(SEANCES_SHEET_NAME)

    if history_df.empty or "athlete" not in history_df.columns:
        st.info("Aucune séance enregistrée pour le moment.")
    else:
        history_df = history_df[
            history_df["athlete"].astype(str).str.strip() == athlete
        ].copy()

        if history_df.empty:
            st.info("Tu n’as encore enregistré aucune séance.")
        else:
            if "date" in history_df.columns:
                history_df["date_parsed"] = pd.to_datetime(
                    history_df["date"],
                    errors="coerce",
                )
                history_df = history_df.sort_values(
                    "date_parsed",
                    ascending=False,
                )

            selected_statuses = st.multiselect(
                "Afficher les statuts",
                [
                    "Fait comme prévu",
                    "Modifié / remplacé",
                    "Non fait",
                    "Ajouté",
                ],
                default=[
                    "Fait comme prévu",
                    "Modifié / remplacé",
                    "Non fait",
                    "Ajouté",
                ],
            )

            if selected_statuses and "statut" in history_df.columns:
                history_df = history_df[
                    history_df["statut"].isin(selected_statuses)
                ]

            display_columns = [
                column for column in [
                    "date",
                    "jour",
                    "categorie",
                    "exercice_prevu",
                    "exercice_realise",
                    "statut",
                    "motif",
                    "commentaire",
                ]
                if column in history_df.columns
            ]

            st.dataframe(
                (
                    history_df[display_columns]
                    if display_columns
                    else history_df
                ),
                use_container_width=True,
                hide_index=True,
            )
