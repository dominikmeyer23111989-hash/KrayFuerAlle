import streamlit as st
from datetime import datetime, time
import pandas as pd
import requests
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from modules.events import (
    get_alle_events,
    event_erstellen,
    event_aktualisieren,
    event_loeschen,
    get_schichten_fuer_event,
    schicht_erstellen,
    schicht_loeschen,
    get_rsvps_fuer_event,
    setze_rsvp,
    get_material_fuer_event,
    event_material_hinzufuegen,
    event_material_loeschen,
    get_freigaben_fuer_event,
    freigabe_hinzufuegen,
    freigabe_loeschen
)
from modules.inventar import get_alle_inventar, formatiere_datum_fuer_anzeige
from database import supabase

def safe_val(d, key, fallback=""):
    """Sicherer Dictionary-Lookup, der auch None-Werte zuverlässig abfängt."""
    if not d or key not in d or d[key] is None:
        return fallback
    return d[key]

def get_alle_mitglieder():
    try:
        res = supabase.table("mitglieder").select("id, vorname, nachname, rolle, email").execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_kontakte_fuer_auswahl():
    kontakte = []
    try:
        res_m = supabase.table("mitglieder").select("vorname, nachname").execute()
        if res_m.data:
            for m in res_m.data:
                v = safe_val(m, 'vorname')
                n = safe_val(m, 'nachname')
                name = f"{v} {n}".strip()
                if name:
                    kontakte.append(f"{name} (Mitglied)")
    except Exception:
        pass
    try:
        res_a = supabase.table("adressbuch").select("name, vorname, nachname").execute()
        if res_a.data:
            for a in res_a.data:
                n = safe_val(a, 'name') or f"{safe_val(a, 'vorname')} {safe_val(a, 'nachname')}".strip()
                if n:
                    kontakte.append(f"{n} (Adressbuch)")
    except Exception:
        pass
    return sorted(list(set(kontakte)))

def parse_time(t_str):
    if not t_str:
        return time(0, 0)
    try:
        parts = str(t_str).split(":")
        if len(parts) >= 2:
            return time(hour=int(parts[0]), minute=int(parts[1]))
    except Exception:
        pass
    return time(0, 0)

def get_wetter_fuer_ort_und_datum(ort, datum_str):
    if not ort:
        ort = "Bochum"
        
    try:
        if datum_str:
            event_date = datetime.strptime(datum_str, "%Y-%m-%d").date()
            heute = datetime.today().date()
            tage_diff = (event_date - heute).days
            
            if tage_diff > 14:
                return {
                    "t_max": "-",
                    "t_min": "-",
                    "rain": "-",
                    "beschreibung": "Erst ca. 14 Tage vor Event verfügbar",
                    "icon": "⏳"
                }
    except Exception:
        pass

    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(str(ort))}&count=1&language=de&format=json"
        geo_res = requests.get(geo_url, timeout=3).json()
        if not geo_res.get("results"):
            lat, lon = 51.4818, 7.2162  # Fallback Bochum
        else:
            lat = geo_res["results"][0]["lat"]
            lon = geo_res["results"][0]["lon"]
            
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Europe/Berlin"
        w_res = requests.get(weather_url, timeout=3).json()
        
        daily = w_res.get("daily", {})
        times = daily.get("time", [])
        
        idx = 0
        if datum_str and datum_str in times:
            idx = times.index(datum_str)
        
        t_max = daily.get("temperature_2m_max", [20])[idx] if daily.get("temperature_2m_max") else 20
        t_min = daily.get("temperature_2m_min", [10])[idx] if daily.get("temperature_2m_min") else 10
        rain = daily.get("precipitation_sum", [0])[idx] if daily.get("precipitation_sum") else 0
        wcode = daily.get("weathercode", [0])[idx] if daily.get("weathercode") else 0
        
        w_desc, w_icon = "Klar / Sonnig", "☀️"
        if wcode in [1, 2, 3]: w_desc, w_icon = "Teilweise bewölkt", "⛅"
        elif wcode in [45, 48]: w_desc, w_icon = "Nebel", "🌫️"
        elif wcode in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67]: w_desc, w_icon = "Regen", "🌧️"
        elif wcode in [71, 73, 75, 77]: w_desc, w_icon = "Schneefall", "🌨️"
        elif wcode in [80, 81, 82]: w_desc, w_icon = "Regenschauer", "🌦️"
        elif wcode in [95, 96, 99]: w_desc, w_icon = "Gewitter", "⚡"
        
        return {
            "t_max": t_max,
            "t_min": t_min,
            "rain": rain,
            "beschreibung": w_desc,
            "icon": w_icon
        }
    except Exception:
        return {
            "t_max": 22,
            "t_min": 12,
            "rain": 0.0,
            "beschreibung": "Wetterdaten (geschätzt)",
            "icon": "⛅"
        }

def generiere_event_pdf(ev, rsvps, schichten, inventar_liste, wetter_info):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'EventTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1E3A8A'), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'EventSubtitle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#4B5563'), spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'EventH2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1E3A8A'), spaceBefore=10, spaceAfter=4
    )
    normal_style = styles['Normal']
    
    ev_name = safe_val(ev, 'name', 'Event')
    story.append(Paragraph(f"<b>Event-Steckbrief: {ev_name}</b>", title_style))
    story.append(Paragraph(f"Erstellt am {datetime.now().strftime('%d.%m.%Y %H:%M')} Uhr | KrayFürAlle e.V.", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#1E3A8A'), spaceAfter=8))
    
    w_text = f"{wetter_info['icon']} {wetter_info['beschreibung']} ({wetter_info['t_min']}°C - {wetter_info['t_max']}°C)" if wetter_info else "Keine Daten"
    
    start_d = formatiere_datum_fuer_anzeige(safe_val(ev, 'start_datum'))
    end_d = formatiere_datum_fuer_anzeige(safe_val(ev, 'end_datum'))
    u_start = str(safe_val(ev, 'uhrzeit_start', ''))[:5]
    u_ende = str(safe_val(ev, 'uhrzeit_ende', ''))[:5]
    treff = safe_val(ev, 'treffpunkt', '-')
    u_treffen = str(safe_val(ev, 'uhrzeit_treffen', ''))[:5]
    ort = safe_val(ev, 'ort', '-')
    ansprech = safe_val(ev, 'ansprechperson', '-')

    details_data = [
        [Paragraph("<b>Startdatum:</b>", normal_style), Paragraph(start_d, normal_style),
         Paragraph("<b>Enddatum:</b>", normal_style), Paragraph(end_d, normal_style)],
        [Paragraph("<b>Uhrzeit Beginn:</b>", normal_style), Paragraph(u_start, normal_style),
         Paragraph("<b>Uhrzeit Ende:</b>", normal_style), Paragraph(u_ende, normal_style)],
        [Paragraph("<b>Treffpunkt:</b>", normal_style), Paragraph(f"{treff} ({u_treffen} Uhr)", normal_style),
         Paragraph("<b>Veranstaltungsort:</b>", normal_style), Paragraph(ort, normal_style)],
        [Paragraph("<b>Ansprechperson:</b>", normal_style), Paragraph(ansprech, normal_style),
         Paragraph("<b>Wettervorhersage:</b>", normal_style), Paragraph(w_text, normal_style)]
    ]
    t_details = Table(details_data, colWidths=[100, 170, 100, 170])
    t_details.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    story.append(t_details)
    
    bemerkungen = safe_val(ev, 'bemerkungen')
    if bemerkungen:
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Bemerkungen:</b> {bemerkungen}", normal_style))
        
    story.append(Paragraph("Teilnahme-Rückmeldungen (RSVP)", h2_style))
    kann, kann_nicht, unsicher = [], [], []
    for r in rsvps:
        m = safe_val(r, 'mitglieder', {})
        m_name = f"{safe_val(m, 'vorname')} {safe_val(m, 'nachname')}".strip()
        status = safe_val(r, 'status')
        if status == 'kann': kann.append(m_name)
        elif status == 'kann nicht': kann_nicht.append(m_name)
        elif status == 'uns
