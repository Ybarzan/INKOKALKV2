"""
Route /api/widget — Widget Excel VBA.
======================================
Genere et telecharge le module VBA pour Excel.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from ..auth import get_current_user
from ..models import User
import io

router = APIRouter(prefix="/api/widget", tags=["widget"])

VBA_CODE = """'==========================================================
' Money Leak Calculator — Widget Excel
'==========================================================

Private Const API_URL As String = "https://moneyleak-api.onrender.com"
Private m_token As String

Sub MoneyLeak_Login()
    Dim http As Object
    Dim email As String, password As String
    
    email = InputBox("Email :", "Money Leak Login")
    password = InputBox("Mot de passe :", "Money Leak Login")
    If email = "" Or password = "" Then Exit Sub
    
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "POST", API_URL & "/api/auth/login", False
    http.setRequestHeader "Content-Type", "application/json"
    http.send "{""email"":""" & email & """,""password"":""" & password & """}"
    
    If http.Status = 200 Then
        Dim resp As String: resp = http.responseText
        m_token = Mid(resp, InStr(resp, """access_token"":""") + 16)
        m_token = Left(m_token, InStr(m_token, """") - 1)
        MsgBox "Connecte !", vbInformation, "Money Leak"
    Else
        MsgBox "Erreur " & http.Status, vbCritical, "Money Leak"
    End If
    Set http = Nothing
End Sub

Sub MoneyLeak_Diagnostic()
    If m_token = "" Then MsgBox "Connectez-vous d'abord": Exit Sub
    
    Dim http As Object, ws As Worksheet, json As String
    Set ws = ActiveSheet
    
    Dim secteur As String: secteur = ws.Range("A1").Value
    If secteur = "" Then secteur = "Industrie"
    Dim ca As String: ca = ws.Range("A2").Value
    If ca = "" Then ca = "10000000"
    Dim nom As String: nom = ws.Range("A3").Value
    If nom = "" Then nom = "Client Excel"
    
    json = "{""secteur"":""" & secteur & """,""ca_annuel_ht"":" & ca & ",""nom_entreprise"":""" & nom & """,""valeurs"":{"
    Dim codes As Variant: codes = Array("T01","T03","T05","S01","S03","S05","E03","E05","P03","A03")
    Dim i As Integer, first As Boolean: first = True
    For i = 0 To 9
        Dim v As String: v = ws.Range("B" & (i + 1)).Value
        If v <> "" Then
            If Not first Then json = json & ","
            json = json & """" & codes(i) & """:" & v: first = False
        End If
    Next i
    json = json & "}}"
    
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "POST", API_URL & "/api/diagnostic", False
    http.setRequestHeader "Content-Type", "application/json"
    http.setRequestHeader "Authorization", "Bearer " & m_token
    http.send json
    
    If http.Status = 200 Then
        Dim r As String: r = http.responseText
        ws.Range("C1").Value = "Score": ws.Range("D1").Value = Extraire(r, "score_global")
        ws.Range("C2").Value = "Fuite EUR": ws.Range("D2").Value = Extraire(r, "fuite_totale_eur")
        ws.Range("C3").Value = "Fuite/CA": ws.Range("D3").Value = Extraire(r, "fuite_pct_ca") & "%"
        ws.Range("C4").Value = "Critiques": ws.Range("D4").Value = Extraire(r, "nb_critiques")
        ws.Range("C5").Value = "Quick wins": ws.Range("D5").Value = Extraire(r, "nb_quick_wins")
        MsgBox "Score : " & Extraire(r, "score_global") & "/10", vbInformation, "Money Leak"
    Else
        MsgBox "Erreur " & http.Status, vbCritical, "Money Leak"
    End If
    Set http = Nothing
End Sub

Private Function Extraire(json As String, cle As String) As String
    Dim p1 As Integer, p2 As Integer
    p1 = InStr(json, """" & cle & """:")
    If p1 = 0 Then Extraire = "N/A": Exit Function
    p1 = p1 + Len(cle) + 3
    While Mid(json, p1, 1) = " ": p1 = p1 + 1: Wend
    p2 = InStr(p1, json, ",")
    If p2 = 0 Then p2 = InStr(p1, json, "}")
    If p2 > p1 Then Extraire = Trim(Mid(json, p1, p2 - p1)) Else Extraire = "N/A"
    If Left(Extraire, 1) = """" Then Extraire = Mid(Extraire, 2, Len(Extraire) - 2)
End Function
"""


@router.get("/excel")
def telecharger_widget_excel(
    user: User = Depends(get_current_user),
):
    """Telecharge le module VBA pour Excel."""
    return StreamingResponse(
        io.BytesIO(VBA_CODE.encode("utf-8")),
        media_type="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=moneyleak_widget.bas"
        },
    )


@router.get("/instructions")
def instructions_widget():
    """Instructions pour installer le widget Excel."""
    return {
        "instructions": [
            "1. Ouvrir Microsoft Excel",
            "2. Creer un nouveau classeur",
            "3. Dans la feuille, remplir :",
            "   A1 = secteur (ex: E-commerce)",
            "   A2 = CA annuel HT (ex: 28000000)",
            "   A3 = nom entreprise",
            "   B1-B10 = valeurs indicateurs (T01, T03, T05, S01, S03, S05, E03, E05, P03, A03)",
            "4. Alt+F11 pour ouvrir l'editeur VBA",
            "5. Inserer → Module",
            "6. Coller le code telecharge",
            "7. Executer MoneyLeak_Login puis MoneyLeak_Diagnostic",
        ],
        "download_url": "/api/widget/excel",
    }
