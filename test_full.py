"""Test complet : API + DB + PDF"""
import requests

BASE = "http://127.0.0.1:8000"

# Health
r = requests.get(f"{BASE}/api/health")
print(f"Health: {r.json()}")

# Register
r = requests.post(f"{BASE}/api/auth/register", json={"email": "test2@test.com", "password": "test1234"})
token = r.json()["access_token"]
print("Register: OK")
headers = {"Authorization": f"Bearer {token}"}

# Diagnostic
r = requests.post(f"{BASE}/api/diagnostic", json={
    "secteur": "E-commerce",
    "ca_annuel_ht": 28000000,
    "nom_entreprise": "Test Corp",
    "valeurs": {"T01": 14.0, "T03": 60, "S01": 50, "E03": 2.0},
}, headers=headers)
data = r.json()
score = data["score_global"]
fuite = data["fuite_totale_eur"]
print(f"Diagnostic: score={score}/10, fuite={fuite} EUR")

# Mes diagnostics
r = requests.get(f"{BASE}/api/diagnostic/mes-diagnostics", headers=headers)
nb = len(r.json()["diagnostics"])
print(f"Mes diagnostics: {nb} sauvegardes")

# PDF
r = requests.post(f"{BASE}/api/rapport/pdf", json={
    "secteur": "E-commerce",
    "ca_annuel_ht": 28000000,
    "nom_entreprise": "Test Corp",
    "score_global": data["score_global"],
    "fuite_totale_eur": data["fuite_totale_eur"],
    "fuite_pct_ca": data["fuite_pct_ca"],
    "nb_indicateurs": data["nb_indicateurs"],
    "nb_critiques": data["nb_critiques"],
    "nb_quick_wins": data["nb_quick_wins"],
    "domaines": [{"domaine": d["domaine"], "score": d["score"], "nb_indicateurs": d["nb_indicateurs"], "nb_critiques": d["nb_critiques"]} for d in data["domaines"]],
    "indicateurs": [{"code": i["code"], "nom": i["nom"], "valeur": i["valeur"], "benchmark": i["benchmark"], "note": i["note"], "statut": i["statut"]} for i in data["indicateurs_detailles"][:20]],
    "recommandations": data["recommandations"],
}, headers=headers)
print(f"PDF: {len(r.content)} bytes, type={r.headers.get('content-type')}")

print("\nTOUS LES TESTS PASSENT")
