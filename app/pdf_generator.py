"""
Generation de rapports PDF.
============================
Genere un rapport de diagnostic complet au format PDF.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
from datetime import datetime


# === COULEURS ===
COLOR_PRIMARY = colors.HexColor("#00d4aa")
COLOR_DARK = colors.HexColor("#1a1a2e")
COLOR_RED = colors.HexColor("#ef4444")
COLOR_ORANGE = colors.HexColor("#f97316")
COLOR_YELLOW = colors.HexColor("#eab308")
COLOR_GREEN = colors.HexColor("#22c55e")
COLOR_GRAY = colors.HexColor("#6b7280")
COLOR_LIGHT_BG = colors.HexColor("#f8fafc")


def generer_rapport_pdf(
    score_global: float,
    fuite_totale_eur: float,
    fuite_pct_ca: float,
    nb_indicateurs: int,
    nb_critiques: int,
    nb_quick_wins: int,
    domaines: list[dict],
    indicateurs: list[dict],
    recommandations: list[str],
    secteur: str = "",
    nom_entreprise: str = "",
    ca_annuel_ht: float = 0,
) -> bytes:
    """
    Genere un rapport PDF complet.
    Retourne les bytes du PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # === STYLES CUSTOM ===
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=28,
        textColor=COLOR_PRIMARY,
        spaceAfter=6*mm,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=COLOR_GRAY,
        alignment=TA_CENTER,
        spaceAfter=10*mm,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=COLOR_DARK,
        spaceBefore=8*mm,
        spaceAfter=4*mm,
        borderWidth=0,
        borderPadding=0,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=3*mm,
    )
    highlight_style = ParagraphStyle(
        "Highlight",
        parent=styles["Normal"],
        fontSize=20,
        textColor=COLOR_PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=2*mm,
        fontName="Helvetica-Bold",
    )

    # === PAGE 1 : COUVERTURE ===
    elements.append(Spacer(1, 40*mm))
    elements.append(Paragraph("Money Leak Calculator", title_style))
    elements.append(Paragraph("Rapport de Diagnostic Supply Chain", subtitle_style))
    elements.append(Spacer(1, 10*mm))

    # Info client
    info_data = [
        ["Entreprise", nom_entreprise or "Non precise"],
        ["Secteur", secteur or "Non precise"],
        ["CA Annuel HT", f"{ca_annuel_ht:,.0f} EUR" if ca_annuel_ht else "Non precise"],
        ["Date", datetime.now().strftime("%d/%m/%Y")],
    ]
    info_table = Table(info_data, colWidths=[45*mm, 100*mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COLOR_LIGHT_BG),
        ("TEXTCOLOR", (0, 0), (0, -1), COLOR_GRAY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    elements.append(info_table)
    elements.append(PageBreak())

    # === PAGE 2 : SCORE GLOBAL ===
    elements.append(Paragraph("Score Global", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY))
    elements.append(Spacer(1, 5*mm))

    # Score en gros
    score_color = COLOR_GREEN if score_global >= 7 else COLOR_YELLOW if score_global >= 4 else COLOR_RED
    score_style = ParagraphStyle(
        "ScoreBig",
        parent=styles["Normal"],
        fontSize=48,
        textColor=score_color,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    elements.append(Paragraph(f"{score_global}/10", score_style))
    elements.append(Paragraph("Score global de maturite Supply Chain", subtitle_style))
    elements.append(Spacer(1, 5*mm))

    # KPIs cles
    kpi_data = [
        ["Fuite totale estimee", f"{fuite_totale_eur:,.0f} EUR"],
        ["Fuite / CA", f"{fuite_pct_ca:.2f}%"],
        ["Indicateurs analyses", str(nb_indicateurs)],
        ["Indicateurs critiques", str(nb_critiques)],
        ["Quick wins identifies", str(nb_quick_wins)],
    ]
    kpi_table = Table(kpi_data, colWidths=[80*mm, 80*mm])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COLOR_LIGHT_BG),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    elements.append(kpi_table)
    elements.append(PageBreak())

    # === PAGE 3 : SCORES PAR DOMAINE ===
    elements.append(Paragraph("Scores par Domaine", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY))
    elements.append(Spacer(1, 5*mm))

    if domaines:
        domaine_data = [["Domaine", "Score", "Indicateurs", "Critiques"]]
        for d in domaines:
            score = d.get("score", 0)
            sc = COLOR_GREEN if score >= 7 else COLOR_YELLOW if score >= 4 else COLOR_RED
            domaine_data.append([
                d.get("domaine", ""),
                f"{score}/10",
                str(d.get("nb_indicateurs", 0)),
                str(d.get("nb_critiques", 0)),
            ])
        domaine_table = Table(domaine_data, colWidths=[55*mm, 30*mm, 35*mm, 30*mm])
        domaine_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ]))
        elements.append(domaine_table)

    elements.append(PageBreak())

    # === PAGE 4 : INDICATEURS DETAILLES ===
    elements.append(Paragraph("Detail des Indicateurs", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY))
    elements.append(Spacer(1, 5*mm))

    if indicateurs:
        # Trier par note (critiques en premier)
        indicateurs_tries = sorted(indicateurs, key=lambda x: x.get("note", 10))

        ind_data = [["Code", "Indicateur", "Valeur", "Benchmark", "Note"]]
        for ind in indicateurs_tries[:30]:  # Top 30 (les plus mauvais)
            note = ind.get("note", 0)
            ind_data.append([
                ind.get("code", ""),
                Paragraph(ind.get("nom", ""), ParagraphStyle("Small", fontSize=8, leading=10)),
                f"{ind.get('valeur', 0)}",
                f"{ind.get('benchmark', 0)}",
                f"{note}/10",
            ])

        ind_table = Table(ind_data, colWidths=[18*mm, 55*mm, 28*mm, 28*mm, 20*mm])
        ind_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ]))
        elements.append(ind_table)

    elements.append(PageBreak())

    # === PAGE 5 : RECOMMANDATIONS ===
    elements.append(Paragraph("Recommandations", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_PRIMARY))
    elements.append(Spacer(1, 5*mm))

    for i, reco in enumerate(recommandations[:15], 1):
        elements.append(Paragraph(f"<b>{i}.</b> {reco}", body_style))
        elements.append(Spacer(1, 2*mm))

    # === FOOTER ===
    elements.append(Spacer(1, 15*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_GRAY))
    elements.append(Spacer(1, 3*mm))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=COLOR_GRAY,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        f"Money Leak Calculator v4.0 — Rapport genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}",
        footer_style
    ))
    elements.append(Paragraph("SC&T Consulting — Supply Chain Intelligence", footer_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
