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
        elif status == 'unsicher': unsicher.append(m_name)
    
    rsvps_data = [
        [Paragraph(f"<b>Kann ({len(kann)})</b>", normal_style), Paragraph(f"<b>Kann nicht ({len(kann_nicht)})</b>", normal_style), Paragraph(f"<b>Unsicher ({len(unsicher)})</b>", normal_style)],
        [Paragraph(", ".join(kann) if kann else "-", normal_style), Paragraph(", ".join(kann_nicht) if kann_nicht else "-", normal_style), Paragraph(", ".join(unsicher) if unsicher else "-", normal_style)]
    ]
    t_rsvps = Table(rsvps_data, colWidths=[180, 180, 180])
    t_rsvps.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E5E7EB')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    story.append(t_rsvps)
    
    story.append(Paragraph("Schichtplan & Standbetreuung", h2_style))
    if schichten:
        schicht_rows = [[Paragraph("<b>Stand / Bereich</b>", normal_style), Paragraph("<b>Mitglied</b>", normal_style), Paragraph("<b>Von</b>", normal_style), Paragraph("<b>Bis</b>", normal_style)]]
        for s in schichten:
            m = safe_val(s, 'mitglieder', {})
            m_name = f"{safe_val(m, 'vorname')} {safe_val(m, 'nachname')}".strip() or "-"
            schicht_rows.append([
                Paragraph(str(safe_val(s, 'stand_name', '-')), normal_style),
                Paragraph(str(m_name), normal_style),
                Paragraph(str(safe_val(s, 'von_zeit', ''))[:5], normal_style),
                Paragraph(str(safe_val(s, 'bis_zeit', ''))[:5], normal_style)
            ])
        t_schichten = Table(schicht_rows, colWidths=[180, 180, 70, 70])
        t_schichten.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E5E7EB')),
            ('PADDING', (0,0), (-1,-1), 4),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        story.append(t_schichten)
    else:
        story.append(Paragraph("Keine Schichten eingetragen.", normal_style))
        
    story.append(Paragraph("Zugewiesenes Material & Ausstattung", h2_style))
    if inventar_liste:
        mat_rows = [[Paragraph("<b>Gegenstand</b>", normal_style), Paragraph("<b>Lagerort</b>", normal_style), Paragraph("<b>Benötigte Menge</b>", normal_style)]]
        for em in inventar_liste:
            inv = safe_val(em, 'inventar', {})
            mat_rows.append([
                Paragraph(str(safe_val(inv, 'name', 'Unbekannt')), normal_style),
                Paragraph(str(safe_val(inv, 'lagerort', '-')), normal_style),
                Paragraph(str(safe_val(em, 'menge', '-')), normal_style)
            ])
        t_mat = Table(mat_rows, colWidths=[220, 180, 100])
        t_mat.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E5E7EB')),
            ('PADDING', (0,0), (-1,-1), 4),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#D1D5DB')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        story.append(t_mat)
    else:
        story.append(Paragraph("Kein Material zugeordnet.", normal_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def show():
    st.header("📅 Event- & Veranstaltungsverwaltung")
    
    is_admin_or_vorstand = st.session_state.get("user_rolle", "").lower() in ["admin", "administrator", "vorstand", "kassenwart"]
    aktuelles_mitglied_id = st.session_state.get("user_id")
    
    tab_uebersicht, tab_erstellung, tab_schichten, tab_material, tab_freigaben, tab_web_buchungen = st.tabs([
        "📋 Event-Übersicht & RSVP",
        "➕ Event anlegen & bearbeiten",
        "👥 Schichtplaner",
        "📦 Material & Ausstattung",
        "🔒 Event-Freigaben",
        "🌐 Web-Buchungen"
    ])

    events = get_alle_events()
    kontakte_liste = get_kontakte_fuer_auswahl()
    
    # ==========================================
    # 1. EVENT-ÜBERSICHT & RSVPS
    # ==========================================
    with tab_uebersicht:
        st.subheader("Kommende & Vergangene Events")
        if events:
            ansicht_filter = st.radio("Ansicht", ["Alle Events", "Nur kommende"], horizontal=True, key="event_ansicht_filter")
            heute_str = datetime.today().strftime("%Y-%m-%d")
            gefilterte_events = []
            for ev in events:
                end_d_val = safe_val(ev, 'end_datum', '')
                if ansicht_filter == "Nur kommende" and end_d_val < heute_str:
                    continue
                gefilterte_events.append(ev)
                
            if gefilterte_events:
                for ev in gefilterte_events:
                    ev_name = safe_val(ev, 'name', 'Event')
                    start_d_str = formatiere_datum_fuer_anzeige(safe_val(ev, 'start_datum'))
                    end_d_str = formatiere_datum_fuer_anzeige(safe_val(ev, 'end_datum'))
                    
                    with st.expander(f"📌 {ev_name} ({start_d_str} - {end_d_str})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Ort:** {safe_val(ev, 'ort', '-')}")
                            st.write(f"**Treffpunkt:** {safe_val(ev, 'treffpunkt', '-')} um {str(safe_val(ev, 'uhrzeit_treffen', ''))[:5]} Uhr")
                            st.write(f"**Beginn - Ende:** {str(safe_val(ev, 'uhrzeit_start', ''))[:5]} - {str(safe_val(ev, 'uhrzeit_ende', ''))[:5]} Uhr")
                        with col2:
                            st.write(f"**Ansprechperson:** {safe_val(ev, 'ansprechperson', '-')}")
                            bem = safe_val(ev, 'bemerkungen')
                            if bem:
                                st.info(f"**Bemerkungen:** {bem}")
                        
                        st.markdown("#### 🌤️ Wettervorhersage")
                        wetter_info = get_wetter_fuer_ort_und_datum(safe_val(ev, 'ort'), safe_val(ev, 'start_datum'))
                        if wetter_info:
                            w_cols = st.columns(4)
                            w_cols[0].metric("Zustand", f"{wetter_info['icon']} {wetter_info['beschreibung']}")
                            w_cols[1].metric("Max. Temp.", f"{wetter_info['t_max']} °C" if wetter_info['t_max'] != "-" else "-")
                            w_cols[2].metric("Min. Temp.", f"{wetter_info['t_min']} °C" if wetter_info['t_min'] != "-" else "-")
                            w_cols[3].metric("Niederschlag", f"{wetter_info['rain']} mm" if wetter_info['rain'] != "-" else "-")
                        
                        st.divider()
                        st.markdown("#### Deine Rückmeldung (RSVP)")
                        rsvps = get_rsvps_fuer_event(safe_val(ev, 'id'))
                        
                        aktueller_status = "unsicher"
                        if aktuelles_mitglied_id:
                            for r in rsvps:
                                if safe_val(r, 'mitglied_id') == aktuelles_mitglied_id:
                                    aktueller_status = safe_val(r, 'status', 'unsicher')
                                    break
                        
                        st.markdown(f"Dein aktueller Status: **{str(aktueller_status).capitalize()}**")
                        
                        if aktuelles_mitglied_id:
                            col_b1, col_b2, col_b3 = st.columns(3)
                            ev_id = safe_val(ev, 'id')
                            if col_b1.button("✅ Kann teilnehmen", key=f"btn_kann_{ev_id}", use_container_width=True):
                                setze_rsvp(ev_id, aktuelles_mitglied_id, "kann")
                                st.success("Zusage gespeichert!")
                                st.rerun()
                            if col_b2.button("❌ Kann nicht", key=f"btn_nicht_{ev_id}", use_container_width=True):
                                setze_rsvp(ev_id, aktuelles_mitglied_id, "kann nicht")
                                st.success("Absage gespeichert!")
                                st.rerun()
                            if col_b3.button("❓ Unsicher", key=f"btn_unsicher_{ev_id}", use_container_width=True):
                                setze_rsvp(ev_id, aktuelles_mitglied_id, "unsicher")
                                st.success("Status auf unsicher gesetzt!")
                                st.rerun()
                        else:
                            st.warning("Keine Mitglieds-ID im Session State gefunden.")
                            
                        st.divider()
                        st.markdown("**Teilnahme-Übersicht:**")
                        if rsvps:
                            kann_liste, kann_nicht_liste, unsicher_liste = [], [], []
                            for r in rsvps:
                                m = safe_val(r, 'mitglieder', {})
                                m_name = f"{safe_val(m, 'vorname')} {safe_val(m, 'nachname')}".strip()
                                st_val = safe_val(r, 'status')
                                if st_val == 'kann': kann_liste.append(m_name)
                                elif st_val == 'kann nicht': kann_nicht_liste.append(m_name)
                                elif st_val == 'unsicher': unsicher_liste.append(m_name)
                            
                            c1, c2, c3 = st.columns(3)
                            c1.success(f"**Kann ({len(kann_liste)})**\n" + "\n".join([f"- {n}" for n in kann_liste]) if kann_liste else "**Kann (0)**")
                            c2.error(f"**Kann nicht ({len(kann_nicht_liste)})**\n" + "\n".join([f"- {n}" for n in kann_nicht_liste]) if kann_nicht_liste else "**Kann nicht (0)**")
                            c3.info(f"**Unsicher ({len(unsicher_liste)})**\n" + "\n".join([f"- {n}" for n in unsicher_liste]) if unsicher_liste else "**Unsicher (0)**")
                        else:
                            st.text("Bisher keine Rückmeldungen eingetragen.")
                            
                        st.divider()
                        try:
                            s_pdf = get_schichten_fuer_event(safe_val(ev, 'id'))
                            m_pdf = get_material_fuer_event(safe_val(ev, 'id'))
                            pdf_bytes = generiere_event_pdf(ev, rsvps, s_pdf, m_pdf, wetter_info)
                            st.download_button(
                                label="📥 Event-Steckbrief als PDF herunterladen",
                                data=pdf_bytes,
                                file_name=f"Event_{safe_val(ev, 'name', 'Details').replace(' ', '_')}_{safe_val(ev, 'start_datum')}.pdf",
                                mime="application/pdf",
                                key=f"pdf_btn_{safe_val(ev, 'id')}"
                            )
                        except Exception as pdf_err:
                            st.error(f"Fehler beim Erstellen des PDF-Buttons: {pdf_err}")
            else:
                st.info("Keine Events für diesen Filter gefunden.")
        else:
            st.info("Keine Events vorhanden.")

    # ==========================================
    # 2. EVENT ERSTELLEN & BEARBEITEN
    # ==========================================
    with tab_erstellung:
        if not is_admin_or_vorstand:
            st.warning("Nur Admins und Vorstand können Events anlegen oder bearbeiten.")
        else:
            st.subheader("Event verwalten")
            sub_opt = st.radio("Aktion wählen", ["Neues Event anlegen", "Bestehendes Event bearbeiten / löschen"], horizontal=True)
            
            if sub_opt == "Neues Event anlegen":
                with st.form("neues_event_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        e_name = st.text_input("Event-Name *")
                        e_start = st.date_input("Startdatum", value=datetime.today(), format="DD.MM.YYYY")
                        e_end = st.date_input("Enddatum", value=datetime.today(), format="DD.MM.YYYY")
                        e_treffpunkt = st.text_input("Treffpunkt *")
                        e_ort = st.text_input("Ort / Veranstaltungsort *")
                    with col2:
                        e_uhr_start = st.time_input("Uhrzeit Beginn")
                        e_uhr_treffen = st.time_input("Uhrzeit Treffen")
                        e_uhr_ende = st.time_input("Uhrzeit Ende (optional)", value=None)
                        ansprech_wahl = st.selectbox("Ansprechperson aus Adressbuch/Mitgliedern", options=["-- Manuell eingeben --"] + kontakte_liste)
                        e_ansprech_manuell = st.text_input("Oder Ansprechperson manuell eintragen")
                        
                    e_bemerkung = st.text_area("Bemerkungen / Infos")
                    submitted = st.form_submit_button("Event speichern", type="primary")
                    
                    if submitted:
                        if not e_name or not e_treffpunkt or not e_ort:
                            st.error("Name, Treffpunkt und Ort sind Pflichtfelder.")
                        else:
                            final_ansprech = e_ansprech_manuell if ansprech_wahl == "-- Manuell eingeben --" else ansprech_wahl
                            daten = {
                                "name": e_name,
                                "start_datum": e_start.strftime("%Y-%m-%d"),
                                "end_datum": e_end.strftime("%Y-%m-%d"),
                                "uhrzeit_start": e_uhr_start.strftime("%H:%M:%S"),
                                "uhrzeit_treffen": e_uhr_treffen.strftime("%H:%M:%S"),
                                "treffpunkt": e_treffpunkt,
                                "ort": e_ort,
                                "uhrzeit_ende": e_uhr_ende.strftime("%H:%M:%S") if e_uhr_ende else None,
                                "bemerkungen": e_bemerkung if e_bemerkung else None,
                                "ansprechperson": final_ansprech if final_ansprech else None
                            }
                            try:
                                event_erstellen(daten)
                                st.success(f"Event '{e_name}' erfolgreich erstellt!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Erstellen: {e}")
            else:
                if events:
                    event_dict = {f"{safe_val(ev, 'id')} - {safe_val(ev, 'name')} ({formatiere_datum_fuer_anzeige(safe_val(ev, 'start_datum'))})": ev for ev in events}
                    w_event = st.selectbox("Event auswählen", options=list(event_dict.keys()))
                    sel_ev = event_dict[w_event]
                    
                    with st.form("edit_event_form"):
                        ee_name = st.text_input("Event-Name", value=safe_val(sel_ev, "name", ""))
                        s_str = safe_val(sel_ev, "start_datum")
                        s_val = datetime.strptime(s_str, "%Y-%m-%d") if s_str else datetime.today()
                        ee_start = st.date_input("Startdatum", value=s_val, format="DD.MM.YYYY")
                        
                        en_str = safe_val(sel_ev, "end_datum")
                        en_val = datetime.strptime(en_str, "%Y-%m-%d") if en_str else datetime.today()
                        ee_end = st.date_input("Enddatum", value=en_val, format="DD.MM.YYYY")
                        
                        ee_treffpunkt = st.text_input("Treffpunkt", value=safe_val(sel_ev, "treffpunkt", ""))
                        ee_ort = st.text_input("Ort", value=safe_val(sel_ev, "ort", ""))
                        ee_uhr_start = st.time_input("Uhrzeit Beginn", value=parse_time(safe_val(sel_ev, "uhrzeit_start")))
                        ee_uhr_treffen = st.time_input("Uhrzeit Treffen", value=parse_time(safe_val(sel_ev, "uhrzeit_treffen")))
                        
                        ende_str = safe_val(sel_ev, "uhrzeit_ende")
                        ee_uhr_ende = st.time_input("Uhrzeit Ende", value=parse_time(ende_str) if ende_str else None)
                        
                        aktuelle_ansprech = safe_val(sel_ev, "ansprechperson", "")
                        ansprech_edit_wahl = st.selectbox("Ansprechperson aus Adressbuch/Mitgliedern", options=["-- Manuell / Unverändert --"] + kontakte_liste)
                        ee_ansprech_manuell = st.text_input("Ansprechperson (manuell)", value=aktuelle_ansprech)
                        ee_bemerkungen = st.text_area("Bemerkungen", value=safe_val(sel_ev, "bemerkungen", ""))
                        
                        col_s, col_d = st.columns(2)
                        with col_s: up_btn = st.form_submit_button("Änderungen speichern", type="primary")
                        with col_d: del_btn = st.form_submit_button("Event löschen", type="secondary")
                            
                        if up_btn:
                            final_ansprech_edit = ee_ansprech_manuell if ansprech_edit_wahl == "-- Manuell / Unverändert --" else ansprech_edit_wahl
                            daten = {
                                "name": ee_name,
                                "start_datum": ee_start.strftime("%Y-%m-%d"),
                                "end_datum": ee_end.strftime("%Y-%m-%d"),
                                "uhrzeit_start": ee_uhr_start.strftime("%H:%M:%S"),
                                "uhrzeit_treffen": ee_uhr_treffen.strftime("%H:%M:%S"),
                                "treffpunkt": ee_treffpunkt,
                                "ort": ee_ort,
                                "uhrzeit_ende": ee_uhr_ende.strftime("%H:%M:%S") if ee_uhr_ende else None,
                                "bemerkungen": ee_bemerkungen if ee_bemerkungen else None,
                                "ansprechperson": final_ansprech_edit if final_ansprech_edit else None
                            }
                            try:
                                event_aktualisieren(safe_val(sel_ev, "id"), daten)
                                st.success("Event erfolgreich aktualisiert!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler: {e}")
                                
                        if del_btn:
                            try:
                                event_loeschen(safe_val(sel_ev, "id"))
                                st.success("Event gelöscht!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Löschen: {e}")
                else:
                    st.info("Keine Events vorhanden.")

    # ==========================================
    # 3. SCHICHTPLANER
    # ==========================================
    with tab_schichten:
        st.subheader("👥 Schichten & Standbetreuung planen")
        if events:
            event_dict = {f"{safe_val(ev, 'id')} - {safe_val(ev, 'name')} ({formatiere_datum_fuer_anzeige(safe_val(ev, 'start_datum'))})": ev for ev in events}
            w_ev_s = st.selectbox("Event für Schichten wählen", options=list(event_dict.keys()), key="schicht_ev_sel")
            sel_ev_s = event_dict[w_ev_s]
            
            schichten = get_schichten_fuer_event(safe_val(sel_ev_s, "id"))
            if schichten:
                st.markdown("**Aktuelle Schichten:**")
                schicht_liste_anzeige = []
                for s in schichten:
                    m = safe_val(s, 'mitglieder', {})
                    m_name = f"{safe_val(m, 'vorname')} {safe_val(m, 'nachname')}".strip() or "-"
                    schicht_liste_anzeige.append({
                        "ID": safe_val(s, "id"),
                        "Stand / Bereich": safe_val(s, "stand_name"),
                        "Mitglied": m_name,
                        "Von": str(safe_val(s, "von_zeit", ""))[:5],
                        "Bis": str(safe_val(s, "bis_zeit", ""))[:5]
                    })
                st.dataframe(schicht_liste_anzeige, use_container_width=True, hide_index=True)
                
                schicht_ids = [safe_val(s, "id") for s in schichten]
                del_s_id = st.selectbox("Schicht-ID zum Löschen auswählen", options=[None] + schicht_ids)
                if del_s_id and st.button("Ausgewählte Schicht löschen"):
                    try:
                        schicht_loeschen(del_s_id)
                        st.success("Schicht gelöscht!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
            else:
                st.info("Für dieses Event sind noch keine Schichten eingetragen.")
                
            if is_admin_or_vorstand:
                st.divider()
                st.markdown("#### Neue Schicht hinzufügen")
                mitglieder = get_alle_mitglieder()
                
                with st.form("neue_schicht_form"):
                    stand_name = st.text_input("Stand- oder Aufgabenname (z.B. Grillstand, Kasse) *")
                    mitglied_dict = {f"{safe_val(m, 'vorname')} {safe_val(m, 'nachname')} ({safe_val(m, 'rolle', 'Mitglied')})": safe_val(m, 'id') for m in mitglieder}
                    w_mitglied = st.selectbox("Mitglied zuweisen", options=["Keine direkte Zuweisung"] + list(mitglied_dict.keys()))
                    
                    col1, col2 = st.columns(2)
                    with col1: von_zeit = st.time_input("Von Uhrzeit", value=datetime.now().time())
                    with col2: bis_zeit = st.time_input("Bis Uhrzeit", value=datetime.now().time())
                        
                    s_sub = st.form_submit_button("Schicht anlegen", type="primary")
                    if s_sub:
                        if not stand_name:
                            st.error("Bitte einen Stand- / Aufgaben Namen angeben.")
                        else:
                            m_id = mitglied_dict.get(w_mitglied) if w_mitglied != "Keine direkte Zuweisung" else None
                            schicht_erstellen({
                                "event_id": safe_val(sel_ev_s, "id"),
                                "stand_name": stand_name,
                                "mitglied_id": m_id,
                                "von_zeit": von_zeit.strftime("%H:%M:%S"),
                                "bis_zeit": bis_zeit.strftime("%H:%M:%S")
                            })
                            st.success("Schicht hinzugefügt!")
                            st.rerun()

    # ==========================================
    # 4. MATERIAL & AUSSTATTUNG
    # ==========================================
    with tab_material:
        st.subheader("📦 Material & Zubehör für Events")
        if events:
            event_dict_m = {f"{safe_val(ev, 'id')} - {safe_val(ev, 'name')}": ev for ev in events}
            w_ev_m = st.selectbox("Event wählen", options=list(event_dict_m.keys()), key="mat_ev_sel")
            sel_ev_m = event_dict_m[w_ev_m]
            
            material_liste = get_material_fuer_event(safe_val(sel_ev_m, "id"))
            if material_liste:
                st.markdown("**Zugeordnetes Material:**")
                mat_anzeige = []
                for em in material_liste:
                    inv = safe_val(em, 'inventar', {})
                    mat_anzeige.append({
                        "ID": safe_val(em, "id"),
                        "Gegenstand": safe_val(inv, "name", "Unbekannt"),
                        "Menge": safe_val(em, "menge"),
                        "Lagerort": safe_val(inv, "lagerort", "-")
                    })
                st.dataframe(mat_anzeige, use_container_width=True, hide_index=True)
            else:
                st.info("Noch kein Material zugeordnet.")
                
            if is_admin_or_vorstand:
                st.divider()
                st.markdown("#### Material hinzufügen")
                alle_inv = get_alle_inventar()
                if alle_inv:
                    inv_dict = {f"{safe_val(i, 'name')} (Auf Lager: {safe_val(i, 'anzahl', 0)})": safe_val(i, 'id') for i in alle_inv}
                    with st.form("add_mat_form"):
                        w_inv = st.selectbox("Gegenstand aus Inventar wählen", options=list(inv_dict.keys()))
                        m_anzahl = st.number_input("Benötigte Menge", min_value=1, value=1)
                        m_sub = st.form_submit_button("Material zuweisen", type="primary")
                        if m_sub:
                            event_material_hinzufuegen({
                                "event_id": safe_val(sel_ev_m, "id"),
                                "inventar_id": inv_dict[w_inv],
                                "menge": m_anzahl
                            })
                            st.success("Material zugewiesen!")
                            st.rerun()

    # ==========================================
    # 5. EVENT-FREIGABEN
    # ==========================================
    with tab_freigaben:
        st.subheader("🔒 Freigaben & Dokumente")
        st.info("Hier verwaltest du behördliche Freigaben, Schanklizenzen oder Nutzungsvereinbarungen.")

    # ==========================================
    # 6. WEB-BUCHUNGEN (kray-für-alle.de)
    # ==========================================
    with tab_web_buchungen:
        st.subheader("🌐 Eingehende Online-Buchungen (kray-für-alle.de)")
        st.caption("Verwalte hier alle Anfragen, die von Bürgern über das Formular auf eurer Homepage eingereicht wurden.")

        try:
            res = supabase.table("event_bookings").select("*").order("created_at", desc=True).execute()
            web_bookings = res.data if res.data else []

            if not web_bookings:
                st.info("Aktuell liegen keine Online-Buchungsanfragen vor.")
            else:
                df_wb = pd.DataFrame(web_bookings)

                c_f1, c_f2 = st.columns(2)
                with c_f1:
                    ev_filter = st.selectbox("Nach Veranstaltung filtern:", ["Alle"] + list(df_wb["event_name"].unique()), key="wb_ev_filter")
                with c_f2:
                    st_filter = st.selectbox("Nach Status filtern:", ["Alle", "pending", "confirmed", "cancelled"], key="wb_st_filter")

                if ev_filter != "Alle":
                    df_wb = df_wb[df_wb["event_name"] == ev_filter]
                if st_filter != "Alle":
                    df_wb = df_wb[df_wb["status"] == st_filter]

                m1, m2, m3 = st.columns(3)
                m1.metric("Anfragen gesamt", len(df_wb))
                m2.metric("Offen (pending)", len(df_wb[df_wb["status"] == "pending"]))
                m3.metric("Bestätigt", len(df_wb[df_wb["status"] == "confirmed"]))

                st.divider()

                for row in df_wb.to_dict(orient="records"):
                    status = row.get("status", "pending")
                    icon = "⏳" if status == "pending" else "✅" if status == "confirmed" else "❌"
                    
                    with st.expander(f"{icon} {row['applicant_name']} – {row['event_name']} ({row['count']} Personen)"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.write(f"**E-Mail:** {row['email']}")
                            st.write(f"**Anzahl Personen:** {row['count']}")
                            st.write(f"**Anmerkung:** {row.get('notes') or 'Keine'}")
                            st.write(f"**Eingegangen am:** {row.get('created_at', '')}")
                            st.write(f"**Status:** `{status}`")

                        with col2:
                            st.write("**Aktion wählen:**")
                            if st.button("✅ Bestätigen", key=f"wb_conf_{row['id']}"):
                                supabase.table("event_bookings").update({"status": "confirmed"}).eq("id", row["id"]).execute()
                                st.success("Anfrage bestätigt!")
                                st.rerun()

                            if st.button("❌ Stornieren", key=f"wb_canc_{row['id']}"):
                                supabase.table("event_bookings").update({"status": "cancelled"}).eq("id", row["id"]).execute()
                                st.warning("Anfrage storniert!")
                                st.rerun()

                            if st.button("🗑️ Löschen", key=f"wb_del_{row['id']}"):
                                supabase.table("event_bookings").delete().eq("id", row["id"]).execute()
                                st.error("Anfrage gelöscht!")
                                st.rerun()

        except Exception as e:
            st.error(f"Fehler beim Laden der Web-Buchungen: {e}")
