"""
Money Leak Calculator — Dashboard SaaS
=======================================
Streamlit app qui appelle l'API FastAPI.
Lance avec : streamlit run dashboard_saas.py
"""

import streamlit as st
import requests
import json

# === CONFIG ===
API_URL = "https://moneyleak-api.onrender.com"
# Pour le dev local : API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Money Leak Calculator",
    page_icon="🔍",
    layout="wide",
)

# === SESSION STATE ===
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None


def api_get(path, token=None):
    """GET request vers l'API."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = requests.get(f"{API_URL}{path}", headers=headers, timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        st.error(f"Erreur API: {e}")
        return None


def api_post(path, data, token=None):
    """POST request vers l'API."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    headers["Content-Type"] = "application/json"
    try:
        r = requests.post(f"{API_URL}{path}", json=data, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Erreur {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        st.error(f"Erreur API: {e}")
        return None


# === SIDEBAR ===
with st.sidebar:
    st.image("https://img.icons8.com/3d-fluency/94/magnifying-glass.png", width=60)
    st.title("Money Leak")
    st.caption("Supply Chain Intelligence")

    if st.session_state.token:
        st.success(f"Connecte: {st.session_state.user_email}")
        if st.button("Deconnexion"):
            st.session_state.token = None
            st.session_state.user_email = None
            st.rerun()
    else:
        st.info("Connecte-toi pour acceder au dashboard")


# === PAGE PRINCIPALE ===
st.title("🔍 Money Leak Calculator")
st.subheader("Supply Chain Intelligence — Detectez vos fuites de rentabilite")


# === AUTH ===
if not st.session_state.token:
    tab_register, tab_login = st.tabs(["Creer un compte", "Se connecter"])

    with tab_register:
        with st.form("register"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            nom = st.text_input("Nom")
            prenom = st.text_input("Prenom")
            submitted = st.form_submit_button("S'inscrire")
            if submitted:
                data = api_post("/api/auth/register", {
                    "email": email, "password": password,
                    "nom": nom, "prenom": prenom,
                })
                if data:
                    st.session_state.token = data["access_token"]
                    st.session_state.user_email = data["email"]
                    st.success("Compte cree !")
                    st.rerun()

    with tab_login:
        with st.form("login"):
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter")
            if submitted:
                data = api_post("/api/auth/login", {
                    "email": email, "password": password,
                })
                if data:
                    st.session_state.token = data["access_token"]
                    st.session_state.user_email = data["email"]
                    st.success("Connecte !")
                    st.rerun()

else:
    # === DIAGNOSTIC ===
    tab_diag, tab_historique, tab_pdf = st.tabs(["Nouveau Diagnostic", "Historique", "Generer PDF"])

    with tab_diag:
        st.header("Nouveau diagnostic Supply Chain")

        col1, col2 = st.columns(2)
        with col1:
            secteur = st.selectbox("Secteur", [
                "Industrie", "E-commerce", "Distribution",
                "Agroalimentaire", "Pharma", "Luxe", "Automobile",
            ])
            ca = st.number_input("CA Annuel HT (EUR)", value=10_000_000, step=1_000_000)
            nom_entreprise = st.text_input("Nom de l'entreprise")

        st.markdown("---")
        st.subheader("Valeurs des indicateurs")

        # Saisie simplifiee (top 10 indicateurs les plus importants)
        valeurs = {}

        st.markdown("**Transport**")
        c1, c2, c3 = st.columns(3)
        with c1:
            valeurs["T01"] = st.number_input("T01: Cout transport/CA (%)", value=6.0, step=0.5, key="t01")
        with c2:
            valeurs["T03"] = st.number_input("T03: Taux chargement aller (%)", value=80.0, step=1.0, key="t03")
        with c3:
            valeurs["T05"] = st.number_input("T05: OTIF transport (%)", value=95.0, step=1.0, key="t05")

        st.markdown("**Stocks**")
        c1, c2, c3 = st.columns(3)
        with c1:
            valeurs["S01"] = st.number_input("S01: DSI (jours)", value=45.0, step=1.0, key="s01")
        with c2:
            valeurs["S03"] = st.number_input("S03: Stock dormant >6m (%)", value=10.0, step=1.0, key="s03")
        with c3:
            valeurs["S05"] = st.number_input("S05: Taux rupture (%)", value=2.0, step=0.5, key="s05")

        st.markdown("**Entrepot**")
        c1, c2, c3 = st.columns(3)
        with c1:
            valeurs["E03"] = st.number_input("E03: Cout/ligne preparee (EUR)", value=1.2, step=0.1, key="e03")
        with c2:
            valeurs["E05"] = st.number_input("E05: Taux erreur picking (%)", value=0.5, step=0.1, key="e05")

        st.markdown("**Processus**")
        c1, c2 = st.columns(2)
        with c1:
            valeurs["P03"] = st.number_input("P03: Erreur facturation (%)", value=0.5, step=0.1, key="p03")
        with c2:
            valeurs["A03"] = st.number_input("A03: OTIF fournisseurs (%)", value=95.0, step=1.0, key="a03")

        if st.button("Lancer le diagnostic", type="primary", use_container_width=True):
            with st.spinner("Analyse en cours..."):
                data = api_post("/api/diagnostic", {
                    "secteur": secteur,
                    "ca_annuel_ht": ca,
                    "nom_entreprise": nom_entreprise,
                    "valeurs": valeurs,
                }, token=st.session_state.token)

            if data:
                st.session_state.last_diagnostic = data
                st.session_state.last_secteur = secteur
                st.session_state.last_ca = ca
                st.session_state.last_nom = nom_entreprise
                st.session_state.last_valeurs = valeurs

                # === AFFICHAGE DES RESULTATS ===
                st.success("Diagnostic termine !")

                # Score global
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    score = data["score_global"]
                    color = "green" if score >= 7 else "orange" if score >= 4 else "red"
                    st.metric("Score Global", f"{score}/10")
                with col2:
                    st.metric("Fuite totale", f"{data['fuite_totale_eur']:,.0f} EUR")
                with col3:
                    st.metric("Fuite / CA", f"{data['fuite_pct_ca']:.2f}%")
                with col4:
                    st.metric("Quick wins", data["nb_quick_wins"])

                # Scores par domaine
                st.subheader("Scores par domaine")
                for d in data["domaines"]:
                    score_d = d["score"]
                    bar_color = "green" if score_d >= 7 else "orange" if score_d >= 4 else "red"
                    st.progress(score_d / 10, text=f"{d['domaine']}: {score_d}/10 ({d['nb_critiques']} critiques)")

                # Indicateurs critiques
                st.subheader("Indicateurs critiques")
                critiques = [i for i in data["indicateurs_detailles"] if i["statut"] == "critique"]
                if critiques:
                    for i in critiques:
                        st.error(f"**{i['code']}** ({i['nom']}): {i['valeur']} vs benchmark {i['benchmark']} → note {i['note']}/10")
                else:
                    st.success("Aucun indicateur critique !")

                # Recommandations
                st.subheader("Recommandations")
                for reco in data["recommandations"]:
                    st.info(reco)

    with tab_historique:
        st.header("Mes diagnostics")
        data = api_get("/api/diagnostic/mes-diagnostics", token=st.session_state.token)
        if data and data.get("diagnostics"):
            for d in data["diagnostics"]:
                with st.expander(f"{d['titre']} — Score: {d.get('score_global', 'N/A')}/10 — {d.get('created_at', '')[:10]}"):
                    st.json(d)
        else:
            st.info("Pas encore de diagnostic sauvegarde")

    with tab_pdf:
        st.header("Generer un rapport PDF")
        if "last_diagnostic" in st.session_state:
            data = st.session_state.last_diagnostic
            if st.button("Telecharger le PDF", type="primary"):
                with st.spinner("Generation du PDF..."):
                    headers = {"Authorization": f"Bearer {st.session_state.token}"}
                    r = requests.post(f"{API_URL}/api/rapport/pdf", json={
                        "secteur": st.session_state.get("last_secteur", ""),
                        "ca_annuel_ht": st.session_state.get("last_ca", 0),
                        "nom_entreprise": st.session_state.get("last_nom", ""),
                        "score_global": data.get("score_global", 0),
                        "fuite_totale_eur": data.get("fuite_totale_eur", 0),
                        "fuite_pct_ca": data.get("fuite_pct_ca", 0),
                        "nb_indicateurs": data.get("nb_indicateurs", 0),
                        "nb_critiques": data.get("nb_critiques", 0),
                        "nb_quick_wins": data.get("nb_quick_wins", 0),
                        "domaines": [{"domaine": d["domaine"], "score": d["score"], "nb_indicateurs": d["nb_indicateurs"], "nb_critiques": d["nb_critiques"]} for d in data.get("domaines", [])],
                        "indicateurs": [{"code": i["code"], "nom": i["nom"], "valeur": i["valeur"], "benchmark": i["benchmark"], "note": i["note"], "statut": i["statut"]} for i in data.get("indicateurs_detailles", [])],
                        "recommandations": data.get("recommandations", []),
                    }, headers=headers, timeout=30)
                    if r.status_code == 200:
                        st.download_button(
                            label="Telecharger le PDF",
                            data=r.content,
                            file_name=f"MoneyLeak_{st.session_state.get('last_nom', 'Diagnostic')}.pdf",
                            mime="application/pdf",
                        )
                        st.success("PDF genere !")
                    else:
                        st.error(f"Erreur: {r.status_code}")
        else:
            st.info("Lance un diagnostic d'abord pour generer un PDF")

# === FOOTER ===
st.markdown("---")
st.caption("Money Leak Calculator v4.0 — SC&T Consulting")
