import streamlit as st
from datetime import datetime
import pandas as pd
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
import supabase

def get_alle_mitglieder():
    try:
        res = supabase.table("mitglieder").select("id, vorname, nachname, rolle, email").execute()
        return res.data if res.data else []
    except Exception:
        return []

def show():
    st.header("📅 Event- & Veranstaltungsverwaltung")
    
    is_admin_or_vorstand = st.session_state.get("user_rolle", "").lower() in ["admin", "administrator", "vorstand", "kassenwart"]
    aktuelles_mitglied_id = st.session_state.get("mitglied_id")
    
    # Tabs definieren
    tab_uebersicht, tab_erstellung, tab_schichten, tab_material, tab_freigaben = st.tabs([
        "📋 Event-Übersicht & RSVP",
        "➕ Event anlegen & bearbeiten",
        "👥 Schichtplaner",
        "📦 Material & Ausstattung",
        "🔒 Event-Freigaben"
    ])

    events = get_alle_events()
    
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
                if ansicht_filter == "Nur kommende" and ev.get("end_datum", "") < heute_str:
                    continue
                gefilterte_events.append(ev)
                
            if gefilterte_events:
                for ev in gefilterte_events:
                    with st.expander(f"📌 {ev.get('name')} ({formatiere_datum_fuer_anzeige(ev.get('start_datum'))} - {formatiere_datum_fuer_anzeige(ev.get('end_datum'))})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Ort:** {ev.get('ort', '-')}")
                            st.write(f"**Treffpunkt:** {ev.get('treffpunkt', '-')} um {ev.get('uhrzeit_treffen', '')[:5]} Uhr")
                            st.write(f"**Beginn - Ende:** {ev.get('uhrzeit_start', '')[:5]} - {ev.get('uhrzeit_ende', '-') and ev.get('uhrzeit_ende', '')[:5]} Uhr")
                        with col2:
                            st.write(f"**Ansprechperson:** {ev.get('ansprechperson', '-')}")
                            if ev.get('bemerkungen'):
                                st.info(f"**Bemerkungen:** {ev.get('bemerkungen')}")
                        
                        st.divider()
                        
                        # RSVP Sektion für eingeloggtes Mitglied
                        st.markdown("#### Deine Rückmeldung (RSVP)")
                        rsvps = get_rsvps_fuer_event(ev.get("id"))
                        
                        aktueller_status = "unsicher"
                        if aktuelles_mitglied_id:
                            for r in rsvps:
                                if r.get("mitglied_id") == aktuelles_mitglied_id:
                                    aktueller_status = r.get("status", "unsicher")
                                    break
                        
                        status_optionen = ["kann", "kann nicht", "unsicher"]
                        try:
                            current_index = status_optionen.index(aktueller_status)
                        except ValueError:
                            current_index = 2
                            
                        if aktuelles_mitglied_id:
                            neuer_status = st.selectbox(
                                "Kannst du teilnehmen?",
                                options=status_optionen,
                                index=current_index,
                                format_func=lambda x: {"kann": "✅ Kann teilnehmen", "kann nicht": "❌ Kann nicht", "unsicher": "❓ Unsicher"}[x],
                                key=f"rsvp_{ev.get('id')}"
                            )
                            if st.button("Rückmeldung speichern", key=f"btn_rsvp_{ev.get('id')}"):
                                try:
                                    setze_rsvp(ev.get("id"), aktuelles_mitglied_id, neuer_status)
                                    st.success("Rückmeldung gespeichert!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fehler: {e}")
                        else:
                            st.warning("Keine Mitglieds-ID im Session State gefunden, um RSVP direkt zu setzen.")
                            
                        # Übersicht aller Zusagen
                        st.markdown("**Teilnahme-Übersicht:**")
                        if rsvps:
                            kann_liste = [f"{r.get('mitglieder', {}).get('vorname', '')} {r.get('mitglieder', {}).get('nachname', '')}" for r in rsvps if r.get('status') == 'kann']
                            kann_nicht_liste = [f"{r.get('mitglieder', {}).get('vorname', '')} {r.get('mitglieder', {}).get('nachname', '')}" for r in rsvps if r.get('status') == 'kann nicht']
                            unsicher_liste = [f"{r.get('mitglieder', {}).get('vorname', '')} {r.get('mitglieder', {}).get('nachname', '')}" for r in rsvps if r.get('status') == 'unsicher']
                            
                            c1, c2, c3 = st.columns(3)
                            c1.success(f"**Kann ({len(kann_liste)})**\n" + "\n".join([f"- {n}" for n in kann_liste]) if kann_liste else "**Kann (0)**")
                            c2.error(f"**Kann nicht ({len(kann_nicht_liste)})**\n" + "\n".join([f"- {n}" for n in kann_nicht_liste]) if kann_nicht_liste else "**Kann nicht (0)**")
                            c3.info(f"**Unsicher ({len(unsicher_liste)})**\n" + "\n".join([f"- {n}" for n in unsicher_liste]) if unsicher_liste else "**Unsicher (0)**")
                        else:
                            st.text("Bisher keine Rückmeldungen eingetragen.")
            else:
                st.info("Keine Events für diesen Filter gefunden.")
        else:
            st.info("Keine Events vorhanden.")

    # ==========================================
    # 2. EVENT ERSTELLEN & BEARBEITEN (Admin / Vorstand)
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
                        e_start = st.date_input("Startdatum", value=datetime.today())
                        e_end = st.date_input("Enddatum", value=datetime.today())
                        e_treffpunkt = st.text_input("Treffpunkt *")
                        e_ort = st.text_input("Ort / Veranstaltungsort *")
                    with col2:
                        e_uhr_start = st.time_input("Uhrzeit Beginn")
                        e_uhr_treffen = st.time_input("Uhrzeit Treffen")
                        e_uhr_ende = st.time_input("Uhrzeit Ende (optional)", value=None)
                        e_ansprech = st.text_input("Ansprechperson")
                        
                    e_bemerkung = st.text_area("Bemerkungen / Infos")
                    
                    submitted = st.form_submit_button("Event speichern", type="primary")
                    if submitted:
                        if not e_name or not e_treffpunkt or not e_ort:
                            st.error("Name, Treffpunkt und Ort sind Pflichtfelder.")
                        else:
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
                                "ansprechperson": e_ansprech if e_ansprech else None
                            }
                            try:
                                event_erstellen(daten)
                                st.success(f"Event '{e_name}' erfolgreich erstellt!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Erstellen: {e}")
            else:
                if events:
                    event_dict = {f"{ev.get('id')} - {ev.get('name')} ({ev.get('start_datum')})": ev for ev in events}
                    w_event = st.selectbox("Event auswählen", options=list(event_dict.keys()))
                    sel_ev = event_dict[w_event]
                    
                    with st.form("edit_event_form"):
                        ee_name = st.text_input("Event-Name", value=sel_ev.get("name", ""))
                        
                        s_str = sel_ev.get("start_datum")
                        s_val = datetime.strptime(s_str, "%Y-%m-%d") if s_str else datetime.today()
                        ee_start = st.date_input("Startdatum", value=s_val)
                        
                        en_str = sel_ev.get("end_datum")
                        en_val = datetime.strptime(en_str, "%Y-%m-%d") if en_str else datetime.today()
                        ee_end = st.date_input("Enddatum", value=en_val)
                        
                        ee_treffpunkt = st.text_input("Treffpunkt", value=sel_ev.get("treffpunkt", ""))
                        ee_ort = st.text_input("Ort", value=sel_ev.get("ort", ""))
                        
                        def parse_time(t_str):
                            if not t_str:
                                return datetime.now().time()
                            parts = t_str.split(":")
                            return datetime.now().time(hour=int(parts[0]), minute=int(parts[1]))
                            
                        ee_uhr_start = st.time_input("Uhrzeit Beginn", value=parse_time(sel_ev.get("uhrzeit_start")))
                        ee_uhr_treffen = st.time_input("Uhrzeit Treffen", value=parse_time(sel_ev.get("uhrzeit_treffen")))
                        
                        ende_str = sel_ev.get("uhrzeit_ende")
                        ee_uhr_ende = st.time_input("Uhrzeit Ende", value=parse_time(ende_str) if ende_str else None)
                        
                        ee_ansprech = st.text_input("Ansprechperson", value=sel_ev.get("ansprechperson", "") or "")
                        ee_bemerkungen = st.text_area("Bemerkungen", value=sel_ev.get("bemerkungen", "") or "")
                        
                        col_s, col_d = st.columns(2)
                        with col_s:
                            up_btn = st.form_submit_button("Änderungen speichern", type="primary")
                        with col_d:
                            del_btn = st.form_submit_button("Event löschen", type="secondary")
                            
                        if up_btn:
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
                                "ansprechperson": ee_ansprech if ee_ansprech else None
                            }
                            try:
                                event_aktualisieren(sel_ev.get("id"), daten)
                                st.success("Event erfolgreich aktualisiert!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler: {e}")
                                
                        if del_btn:
                            try:
                                event_loeschen(sel_ev.get("id"))
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
            event_dict = {f"{ev.get('id')} - {ev.get('name')} ({ev.get('start_datum')})": ev for ev in events}
            w_ev_s = st.selectbox("Event für Schichten wählen", options=list(event_dict.keys()), key="schicht_ev_sel")
            sel_ev_s = event_dict[w_ev_s]
            
            schichten = get_schichten_fuer_event(sel_ev_s.get("id"))
            
            if schichten:
                st.markdown("**Aktuelle Schichten:**")
                schicht_liste_anzeige = []
                for s in schichten:
                    m_name = "-"
                    if s.get("mitglieder"):
                        m_name = f"{s['mitglieder'].get('vorname', '')} {s['mitglieder'].get('nachname', '')}"
                    schicht_liste_anzeige.append({
                        "ID": s.get("id"),
                        "Stand / Bereich": s.get("stand_name"),
                        "Mitglied": m_name,
                        "Von": s.get("von_zeit", "")[:5],
                        "Bis": s.get("bis_zeit", "")[:5]
                    })
                st.dataframe(schicht_liste_anzeige, use_container_width=True, hide_index=True)
                
                schicht_ids = [s.get("id") for s in schichten]
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
                    
                    mitglied_dict = {f"{m.get('vorname')} {m.get('nachname')} ({m.get('rolle', 'Mitglied')})": m.get('id') for m in mitglieder}
                    w_mitglied = st.selectbox("Mitglied zuweisen", options=["Keine direkte Zuweisung"] + list(mitglied_dict.keys()))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        von_zeit = st.time_input("Von Uhrzeit", value=datetime.now().time())
                    with col2:
                        bis_zeit = st.time_input("Bis Uhrzeit", value=datetime.now().time())
                        
                    s_sub = st.form_submit_button("Schicht anlegen", type="primary")
                    if s_sub:
                        if not stand_name:
                            st.error("Bitte einen Stand- / Aufgaben Namen angeben.")
                        else:
                            m_id = mitglied_dict.get(w_mitglied) if w_mitglied != "Keine direkte Zuweisung" else None
                            schicht_daten = {
                                "event_id": sel_ev_s.get("id"),
                                "mitglied_id": m_id,
                                "stand_name": stand_name,
                                "von_zeit": von_zeit.strftime("%H:%M:%S"),
                                "bis_zeit": bis_zeit.strftime("%H:%M:%S")
                            }
                            try:
                                schicht_erstellen(schicht_daten)
                                st.success("Schicht erfolgreich erstellt!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler: {e}")
        else:
            st.info("Keine Events verfügbar.")

    # ==========================================
    # 4. MATERIAL & AUSSTATTUNG
    # ==========================================
    with tab_material:
        st.subheader("📦 Event-Material & Inventarzuordnung")
        if events:
            event_dict = {f"{ev.get('id')} - {ev.get('name')} ({ev.get('start_datum')})": ev for ev in events}
            w_ev_m = st.selectbox("Event für Material wählen", options=list(event_dict.keys()), key="mat_ev_sel")
            sel_ev_m = event_dict[w_ev_m]
            
            event_mat = get_material_fuer_event(sel_ev_m.get("id"))
            if event_mat:
                st.markdown("**Zugewiesenes Material:**")
                mat_anzeige = []
                for em in event_mat:
                    inv = em.get("inventar") or {}
                    mat_anzeige.append({
                        "Verknüpfungs-ID": em.get("id"),
                        "Gegenstand": inv.get("name", "Unbekannt"),
                        "Lagerort": inv.get("lagerort", "-"),
                        "Benötigte Menge": em.get("menge"),
                        "Verfügbar im Lager": inv.get("menge_verfuegbar", "-")
                    })
                st.dataframe(mat_anzeige, use_container_width=True, hide_index=True)
                
                mat_ids = [em.get("id") for em in event_mat]
                del_m_id = st.selectbox("Material-Verknüpfung entfernen (ID)", options=[None] + mat_ids)
                if del_m_id and st.button("Verknüpfung löschen"):
                    try:
                        event_material_loeschen(del_m_id)
                        st.success("Material entfernt!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
            else:
                st.info("Diesem Event ist noch kein Inventar-Material zugeordnet.")
                
            if is_admin_or_vorstand:
                st.divider()
                st.markdown("#### Material aus Lager hinzufügen")
                inventar_liste = get_alle_inventar()
                if inventar_liste:
                    inv_dict = {f"{i.get('name')} (Lager: {i.get('lagerort', 'k.A.')} | Verf: {i.get('menge_verfuegbar')})": i for i in inventar_liste}
                    
                    with st.form("event_mat_form"):
                        w_inv = st.selectbox("Inventar-Gegenstand", options=list(inv_dict.keys()))
                        sel_inv = inv_dict[w_inv]
                        max_v = sel_inv.get("menge_verfuegbar", 1)
                        menge_benoetigt = st.number_input("Benötigte Menge", min_value=1, max_value=max(1, max_v), value=1)
                        
                        m_sub = st.form_submit_button("Material zu Event hinzufügen", type="primary")
                        if m_sub:
                            daten = {
                                "event_id": sel_ev_m.get("id"),
                                "inventar_id": sel_inv.get("id"),
                                "menge": menge_benoetigt
                            }
                            try:
                                event_material_hinzufuegen(daten)
                                st.success("Material erfolgreich verknüpft!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler: {e}")
                else:
                    st.warning("Kein Inventar im Lager vorhanden.")
        else:
            st.info("Keine Events verfügbar.")

    # ==========================================
    # 5. EVENT-FREIGABEN
    # ==========================================
    with tab_freigaben:
        st.subheader("🔒 Spezifische Event-Freigaben (Sichtbarkeit)")
        st.markdown("Falls Events nur für bestimmte Mitglieder sichtbar/freigegeben sein sollen, kannst du sie hier zuordnen.")
        
        if events:
            event_dict = {f"{ev.get('id')} - {ev.get('name')} ({ev.get('start_datum')})": ev for ev in events}
            w_ev_f = st.selectbox("Event für Freigaben wählen", options=list(event_dict.keys()), key="freigabe_ev_sel")
            sel_ev_f = event_dict[w_ev_f]
            
            freigaben = get_freigaben_fuer_event(sel_ev_f.get("id"))
            if freigaben:
                st.markdown("**Bereits freigegebene Mitglieder:**")
                f_anzeige = []
                for f in freigaben:
                    m = f.get("mitglieder") or {}
                    f_anzeige.append({
                        "Freigabe-ID": f.get("id"),
                        "Name": f"{m.get('vorname', '')} {m.get('nachname', '')}",
                        "E-Mail": m.get("email", "-")
                    })
                st.dataframe(f_anzeige, use_container_width=True, hide_index=True)
                
                f_ids = [f.get("id") for f in freigaben]
                del_f_id = st.selectbox("Freigabe aufheben (ID)", options=[None] + f_ids)
                if del_f_id and st.button("Freigabe entziehen"):
                    try:
                        freigabe_loeschen(del_f_id)
                        st.success("Freigabe entfernt!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
            else:
                st.info("Für dieses Event sind keine exklusiven Freigaben hinterlegt (oder öffentlich für alle).")
                
            if is_admin_or_vorstand:
                st.divider()
                st.markdown("#### Mitglied Freigabe erteilen")
                mitglieder = get_alle_mitglieder()
                if mitglieder:
                    m_dict = {f"{m.get('vorname')} {m.get('nachname')} ({m.get('email', '-')})": m.get('id') for m in mitglieder}
                    
                    with st.form("freigabe_form"):
                        w_mitglied_f = st.selectbox("Mitglied auswählen", options=list(m_dict.keys()))
                        f_sub = st.form_submit_button("Freigabe erteilen", type="primary")
                        
                        if f_sub:
                            m_id = m_dict[w_mitglied_f]
                            daten = {
                                "event_id": sel_ev_f.get("id"),
                                "mitglied_id": m_id
                            }
                            try:
                                freigabe_hinzufuegen(daten)
                                st.success("Freigabe erfolgreich erteilt!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler (vielleicht schon freigegeben?): {e}")
                else:
                    st.warning("Keine Mitglieder gefunden.")
        else:
            st.info("Keine Events verfügbar.")