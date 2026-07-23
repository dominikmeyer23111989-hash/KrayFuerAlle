from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from database import supabase

def get_mitglieder_geburtstage():
    try:
        res = supabase.table("mitglieder").select("id, vorname, nachname, geburtsdatum, rolle, email").execute()
        mitglieder = res.data if res.data else []
        
        heute = datetime.today()
        geburtsliste = []
        
        for m in mitglieder:
            g_str = m.get("geburtsdatum")
            if g_str:
                g_date = datetime.strptime(g_str, "%Y-%m-%d")
                naechster_geb = g_date.replace(year=heute.year)
                if naechster_geb.date() < heute.date():
                    naechster_geb = g_date.replace(year=heute.year + 1)
                
                alter_wird = naechster_geb.year - g_date.year
                tage_bis = (naechster_geb.date() - heute.date()).days
                
                geburtsliste.append({
                    "id": m["id"],
                    "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip(),
                    "geburtsdatum": g_date.strftime("%d.%m.%Y"),
                    "alter_wird": alter_wird,
                    "tage_bis": tage_bis,
                    "datum_obj": naechster_geb.date()
                })
        
        geburtsliste.sort(key=lambda x: x["tage_bis"])
        return geburtsliste
    except Exception as e:
        print(f"Fehler beim Laden der Geburtstage: {e}")
        return []

def get_alle_ehrungen():
    try:
        res = supabase.table("ehrungen").select("*, mitglieder(vorname, nachname, rolle)").order("ehrungs_datum").execute()
        return res.data if res.data else []
    except Exception:
        return []

def ehrung_erstellen(daten):
    return supabase.table("ehrungen").insert(daten).execute()

def ehrung_loeschen(ehrung_id):
    return supabase.table("ehrungen").delete().eq("id", ehrung_id).execute()

def urkunde_hochladen(file_bytes, file_name):
    """Lädt eine Urkunde in den Supabase Storage Bucket 'urkunden' hoch und gibt die öffentliche URL zurück."""
    try:
        path = f"urkunde_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
        supabase.storage.from_("urkunden").upload(path, file_bytes)
        public_url_res = supabase.storage.from_("urkunden").get_public_url(path)
        return public_url_res
    except Exception as e:
        print(f"Fehler beim Upload: {e}")
        return None

def generiere_ehrungen_pdf(ehrungen_liste):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'EhrungenTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1E3A8A'), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'EhrungenSubtitle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#4B5563'), spaceAfter=10
    )
    normal_style = styles['Normal']
    
    story.append(Paragraph("<b>Übersicht: Ehrungen & Jubiläen</b>", title_style))
    story.append(Paragraph(f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr | DRK Station", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#1E3A8A'), spaceAfter=12))
    
    if ehrungen_liste:
        rows = [[Paragraph("<b>Mitglied</b>", normal_style), Paragraph("<b>Anlass</b>", normal_style), Paragraph("<b>Jahre</b>", normal_style), Paragraph("<b>Datum</b>", normal_style), Paragraph("<b>Status</b>", normal_style)]]
        for e in ehrungen_liste:
            m = e.get('mitglieder', {}) or {}
            m_name = f"{m.get('vorname', '')} {m.get('nachname', '')}".strip() or "-"
            d_str = e.get('ehrungs_datum', '')
            d_formatted = f"{d_str[8:10]}.{d_str[5:7]}.{d_str[0:4]}" if len(d_str) >= 10 else d_str
            
            rows.append([
                Paragraph(m_name, normal_style),
                Paragraph(str(e.get('anlass', '-')), normal_style),
                Paragraph(f"{e.get('jahre', 0)} Jahre", normal_style),
                Paragraph(d_formatted, normal_style),
                Paragraph(str(e.get('status', '-')), normal_style)
            ])
        
        t = Table(rows, colWidths=[120, 140, 70, 70, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E5E7EB')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("Keine Ehrungen eingetragen.", normal_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()