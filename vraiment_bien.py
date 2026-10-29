import streamlit as st
import pandas as pd

st.set_page_config(page_title="Qui me connaît le mieux ?", page_icon="🧠")

# --- Chargement des données ---
@st.cache_data
def charger_questions(path="questions.csv"):
    df = pd.read_csv(path)
    # Détection automatique des options (option_A, option_B, ...)
    options_cols = [c for c in df.columns if c.startswith("option_")]
    # Détection automatique des amis (ami_1_nom, ami_2_nom, ...)
    amis = []
    i = 1
    while f"ami_{i}_nom" in df.columns:
        amis.append({
            "index": i,
            "nom_col": f"ami_{i}_nom",
            "pred_col": f"ami_{i}_prediction",
        })
        i += 1
    return df, options_cols, amis

df, options_cols, amis = charger_questions()

st.title("🧠 Qui me connaît le mieux ?")
st.write("Réponds à chaque question, puis devine la réponse de chaque ami.")

# --- Formulaire de jeu ---
with st.form("questionnaire"):
    reponses_utilisateur = {}
    predictions = {a["index"]: {} for a in amis}

    for _, row in df.iterrows():
        st.subheader(f"Q{row['id']} — {row['question']}")
        options = [row[c] for c in options_cols if pd.notna(row[c])]
        lettres = [c.replace("option_", "") for c in options_cols if pd.notna(row[c])]
        choix = [f"{l} — {o}" for l, o in zip(lettres, options)]

        # Ta réponse
        rep = st.radio(
            "Ta réponse :",
            choix,
            key=f"user_{row['id']}",
            index=None,
        )
        reponses_utilisateur[row["id"]] = rep.split(" — ")[0] if rep else None

        # Prédictions pour chaque ami
        for a in amis:
            nom_ami = row[a["nom_col"]]
            if pd.isna(nom_ami):
                continue
            pred = st.radio(
                f"Pour {nom_ami}, je pense qu'il/elle choisira :",
                choix,
                key=f"pred_{row['id']}_{a['index']}",
                index=None,
            )
            predictions[a["index"]][row["id"]] = pred.split(" — ")[0] if pred else None

        st.divider()

    submitted = st.form_submit_button("Valider mes réponses")

# --- Calcul des scores ---
if submitted:
    st.header("📊 Résultats")

    # Score de l'utilisateur (a-t-il bien deviné ses amis ?)
    st.subheader("Tes prédictions")
    for a in amis:
        nom_ami = df[a["nom_col"]].dropna().iloc[0] if not df[a["nom_col"]].dropna().empty else f"Ami {a['index']}"
        total = 0
        correct = 0
        for _, row in df.iterrows():
            vraie = row[a["pred_col"]]  # ce que l'ami est supposé avoir répondu (référence)
            pred = predictions[a["index"]].get(row["id"])
            if pred is not None:
                total += 1
                if pred == vraie:
                    correct += 1
        pct = (correct / total * 100) if total else 0
        st.metric(f"Tu connais {nom_ami}", f"{pct:.0f}%", f"{correct}/{total} bonnes prédictions")

    # Score de l'utilisateur sur ses propres réponses (contrôle)
    st.subheader("Tes réponses")
    total_q = 0
    correct_q = 0
    for _, row in df.iterrows():
        rep = reponses_utilisateur.get(row["id"])
        if rep is not None:
            total_q += 1
            if rep == row["reponse_createur"]:
                correct_q += 1
    if total_q:
        st.metric("Cohérence avec les réponses validées par Dieu", f"{correct_q/total_q*100:.0f}%", f"{correct_q}/{total_q}")

    st.info(
        "💡 Pour comparer 'qui connaît le mieux l'autre', il faut que chaque ami "
        "remplisse le même formulaire de son côté (avec ses propres prédictions sur toi), "
        "puis comparer les pourcentages."
    )
