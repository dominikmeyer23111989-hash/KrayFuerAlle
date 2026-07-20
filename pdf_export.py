import os
from tkinter import filedialog, messagebox
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def export_kassenbuch_pdf(daten, jahr, monat_name, kassenbestand):
    """
    Exportiert die übergebenen Kassenbuchdaten in ein schickes PDF.
    """
    filepath = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF-Dokument", "*.pdf")],
        title="Kassenbuch exportieren",
        initialfile=f"Kassenbuch_{jahr}_{monat_name}.pdf"
    )
    if not filepath:
        return

    try:
        # Dokument anlegen
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []
        styles = getSampleStyleSheet()

        # Eigene Styles definieren
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=10,
            textColor=colors.HexColor("#1e272c")
        )
        meta_style = ParagraphStyle(
            'MetaStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#555555")
        )

        # Titel & Meta-Infos
        story.append(Paragraph("KrayFürAlle e.V. - Kassenbericht", title_style))
        story.append(Paragraph(f"Abrechnungszeitraum: {monat_name} {jahr}", meta_style))
        story.append(Paragraph(f"Erstellt am: {jahr}-07-13", meta_style)) # Dynamisches Datum
        story.append(Spacer(1, 20))

        # Tabellendaten vorbereiten
        # Header
        table_data = [["Datum", "Typ", "Betrag", "Kategorie", "Zahler/Empfänger", "Zweck"]]
        
        einnahmen = 0.0
        ausgaben = 0.0

        for row in daten:
            betrag = float(row['betrag'])
            if row['typ'] == 'Einnahme':
                einnahmen += betrag
                betrag_str = f"+{betrag:.2f} €"
            else:
                ausgaben += betrag
                betrag_str = f"-{betrag:.2f} €"

            table_data.append([
                row['datum'],
                row['typ'],
                betrag_str,
                row['kategorie'],
                row['person'],
                row['zweck'] or "-"
            ])

        # Tabelle stylen
        t = Table(table_data, colWidths=[70, 60, 70, 100, 110, 130])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e272c")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8f9fa")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # Zusammenfassung
        summary_data = [
            ["Einnahmen in diesem Monat:", f"{einnahmen:.2f} €"],
            ["Ausgaben in diesem Monat:", f"-{ausgaben:.2f} €"],
            ["Endgültiger Kassenbestand (Iststand):", f"{kassenbestand:.2f} €"]
        ]
        sum_table = Table(summary_data, colWidths=[250, 100])
        sum_table.setStyle(TableStyle([
            ('FONTNAME', (0,2), (1,2), 'Helvetica-Bold'),
            ('LINEABOVE', (0,0), (-1,0), 1, colors.HexColor("#1e272c")),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        story.append(sum_table)

        # PDF bauen
        doc.build(story)
        messagebox.showinfo("Erfolg", "PDF erfolgreich exportiert!")
    except Exception as e:
        messagebox.showerror("Fehler", f"PDF-Export fehlgeschlagen:\n{e}")