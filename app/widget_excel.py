"""
Widget Excel VBA — Module de connexion a l'API Money Leak.
==========================================================
Ce fichier genere le code VBA a coller dans Excel.
Usage : python generate_vba.py → output: moneyleak_widget.bas
"""

VBA_CODE = """
'==========================================================
' Money Leak Calculator — Widget Excel
' Genere automatiquement par moneyleak-saas
' Coller ce code dans un module VBA (Alt+F11 → Inserer → Module)
'==========================================================

Private Const API_URL As String = "https://moneyleak-api.onrender.com"

' --- Token JWT (a remplir apres login) ---
Private m_token As String

'==========================================================
' LOGIN — Connecte a l'API et recupere le token
'==========================================================
Sub MoneyLeak_Login()
    Dim http As Object
    Dim email As String
    Dim password As String
    Dim response As String
    
    email = InputBox("Email :", "Money Leak Login")
    password = InputBox("Mot de passe :", "Money Leak Login")
    
    If email = "" Or password = "" Then Exit Sub
    
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "POST", API_URL & "/api/auth/login", False
    http.setRequestHeader "Content-Type", "application/json"
    http.send "{""email"":""" & email & """,""password"":""" & password & """}"
    
    If http.Status = 200 Then
        ' Extraire le token (parse JSON basique)
        response = http.responseText
        m_token = Mid(response, InStr(response, """access_token"":""") + 16)
        m_token = Left(m_token, InStr(m_token, """") - 1)
        MsgBox "Connecte !", vbInformation, "Money Leak"
    Else
        MsgBox "Erreur : " & http.Status & vbCrLf & http.responseText, vbCritical, "Money Leak"
    End If
    
    Set http = Nothing
End Sub

'==========================================================
' DIAGNOSTIC — Lance un diagnostic avec les valeurs d'Excel
'==========================================================
Sub MoneyLeak_Diagnostic()
    If m_token = "" Then
        MsgBox "Connectez-vous d'abord (MoneyLeak_Login)", vbExclamation
        Exit Sub
    End If
    
    Dim http As Object
    Dim ws As Worksheet
    Dim json As String
    Dim response As String
    
    Set ws = ActiveSheet
    
    ' Lire les valeurs depuis les cellules
    ' A1: secteur, A2: CA, A3: nom entreprise
    ' B1-B10: valeurs des indicateurs (T01, T03, T05, S01, S03, S05, E03, E05, P03, A03)
    Dim secteur As String
    Dim ca As String
    Dim nom As String
    
    secteur = ws.Range("A1").Value
    If secteur = "" Then secteur = "Industrie"
    ca = ws.Range("A2").Value
    If ca = "" Then ca = "10000000"
    nom = ws.Range("A3").Value
    If nom = "" Then nom = "Client Excel"
    
    ' Construire le JSON des valeurs
    json = "{""secteur"":""" & secteur & """,""ca_annuel_ht"":" & ca & ",""nom_entreprise"":""" & nom & """,""valeurs"":{"
    
    ' Lire les indicateurs depuis la colonne B (lignes 1-10)
    Dim codes As Variant
    codes = Array("T01", "T03", "T05", "S01", "S03", "S05", "E03", "E05", "P03", "A03")
    
    Dim first As Boolean
    first = True
    Dim i As Integer
    For i = 0 To 9
        Dim val As String
        val = ws.Range("B" & (i + 1)).Value
        If val <> "" Then
            If Not first Then json = json & ","
            json = json & """" & codes(i) & """:" & val
            first = False
        End If
    Next i
    
    json = json & "}}"
    
    ' Envoyer a l'API
    Set http = CreateObject("MSXML2.XMLHTTP")
    http.Open "POST", API_URL & "/api/diagnostic", False
    http.setRequestHeader "Content-Type", "application/json"
    http.setRequestHeader "Authorization", "Bearer " & m_token
    http.send json
    
    If http.Status = 200 Then
        response = http.responseText
        
        ' Ecrire les resultats dans le sheet
        ws.Range("C1").Value = "Score"
        ws.Range("D1").Value = ExtraireValeur(response, "score_global")
        
        ws.Range("C2").Value = "Fuite (EUR)"
        ws.Range("D2").Value = ExtraireValeur(response, "fuite_totale_eur")
        
        ws.Range("C3").Value = "Fuite / CA"
        ws.Range("D3").Value = ExtraireValeur(response, "fuite_pct_ca") & "%"
        
        ws.Range("C4").Value = "Critiques"
        ws.Range("D4").Value = ExtraireValeur(response, "nb_critiques")
        
        ws.Range("C5").Value = "Quick wins"
        ws.Range("D5").Value = ExtraireValeur(response, "nb_quick_wins")
        
        MsgBox "Diagnostic termine !" & vbCrLf & _
               "Score : " & ExtraireValeur(response, "score_global") & "/10" & vbCrLf & _
               "Fuite : " & ExtraireValeur(response, "fuite_totale_eur") & " EUR", _
               vbInformation, "Money Leak"
    Else
        MsgBox "Erreur : " & http.Status & vbCrLf & http.responseText, vbCritical, "Money Leak"
    End If
    
    Set http = Nothing
End Sub

'==========================================================
' PDF — Genere et telecharge le rapport PDF
'==========================================================
Sub MoneyLeak_PDF()
    If m_token = "" Then
        MsgBox "Connectez-vous d'abord", vbExclamation
        Exit Sub
    End If
    
    MsgBox "Le telechargement PDF sera disponible prochainement.", vbInformation, "Money Leak"
End Sub

'==========================================================
' UTILITAIRE — Extrait une valeur d'une reponse JSON simple
'==========================================================
Private Function ExtraireValeur(json As String, cle As String) As String
    Dim pos1 As Integer
    Dim pos2 As Integer
    Dim recherche As String
    
    recherche = """" & cle & """:"
    pos1 = InStr(json, recherche)
    
    If pos1 = 0 Then
        ExtraireValeur = "N/A"
        Exit Function
    End If
    
    pos1 = pos1 + Len(recherche)
    
    ' Sauter les espaces
    While Mid(json, pos1, 1) = " "
        pos1 = pos1 + 1
    Wend
    
    ' Trouver la fin (virgule ou accolade)
    pos2 = InStr(pos1, json, ",")
    If pos2 = 0 Then pos2 = InStr(pos1, json, "}")
    
    If pos2 > pos1 Then
        ExtraireValeur = Trim(Mid(json, pos1, pos2 - pos1))
        ' Retirer les guillemets si presents
        If Left(ExtraireValeur, 1) = """" Then
            ExtraireValeur = Mid(ExtraireValeur, 2, Len(ExtraireValeur) - 2)
        End If
    Else
        ExtraireValeur = "N/A"
    End If
End Function
"""


def generer_vba(filepath: str = "moneyleak_widget.bas"):
    """Genere le fichier VBA pour Excel."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(VBA_CODE)
    print(f"Widget VBA genere : {filepath}")
    print("Pour l'utiliser :")
    print("  1. Ouvrir Excel → Alt+F11")
    print("  2. Inserer → Module")
    print("  3. Coller le contenu du fichier")
    print("  4. Execuer MoneyLeak_Login")


if __name__ == "__main__":
    generer_vba()
