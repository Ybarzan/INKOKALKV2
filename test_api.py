"""
Test rapide de l'API — Verifie que tout fonctionne.
====================================================
Lance le serveur puis teste les endpoints principaux.
Usage : python test_api.py
"""

import requests
import json

BASE = "http://127.0.0.1:8000"

def test_health():
    r = requests.get(f"{BASE}/api/health")
    assert r.status_code == 200
    print(f"[OK] Health: {r.json()}")

def test_register_and_login():
    # Register
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": "test@example.com",
        "password": "test1234",
        "nom": "Test",
        "prenom": "User",
    })
    assert r.status_code == 200
    token = r.json()["access_token"]
    print(f"[OK] Register: token recu")
    return token

def test_diagnostic(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(f"{BASE}/api/diagnostic", json={
        "secteur": "E-commerce",
        "ca_annuel_ht": 28000000,
        "nom_entreprise": "Test Corp",
        "valeurs": {
            "T01": 14.0, "T02": 1.6, "T03": 60, "S01": 50,
            "S02": 6, "S03": 12, "E03": 2.0, "E05": 1.5,
        },
    }, headers=headers)
    assert r.status_code == 200
    data = r.json()
    print(f"[OK] Diagnostic: score={data['score_global']}/10, fuite={data['fuite_totale_eur']} EUR")
    print(f"     Critiques: {data['nb_critiques']}, Quick wins: {data['nb_quick_wins']}")
    for reco in data["recommandations"][:3]:
        print(f"     → {reco}")

def test_secteurs(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE}/api/diagnostic/secteurs", headers=headers)
    assert r.status_code == 200
    print(f"[OK] Secteurs: {r.json()['secteurs'][:5]}...")

def test_indicateurs(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE}/api/diagnostic/indicateurs", headers=headers)
    assert r.status_code == 200
    print(f"[OK] Indicateurs: {len(r.json()['indicateurs'])} indicateurs")

def test_packs():
    r = requests.get(f"{BASE}/api/packs")
    assert r.status_code == 200
    print(f"[OK] Packs: {len(r.json()['packs'])} packs")

def test_landing():
    r = requests.get(f"{BASE}/")
    assert r.status_code == 200
    assert "Money Leak" in r.text
    print(f"[OK] Landing page: {len(r.text)} bytes")

if __name__ == "__main__":
    print("=" * 50)
    print("  Test API — Money Leak Calculator SaaS")
    print("=" * 50)
    try:
        test_health()
        token = test_register_and_login()
        test_diagnostic(token)
        test_secteurs(token)
        test_indicateurs(token)
        test_packs()
        test_landing()
        print("\n" + "=" * 50)
        print("  TOUS LES TESTS PASSENT ✓")
        print("=" * 50)
    except requests.ConnectionError:
        print("\n[ERREUR] Serveur non demarre. Lancez : python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n[ERREUR] {e}")
