import streamlit as st
from datetime import datetime, time
from modules.termine import (
    get_termine_fuer_nutzer,
    termin_erstellen,
    termin_aktualisieren,
    termin_loeschen,
    get_teilnahmen_fuer_termin,
    setze_teilnahme
)

def formatiere_datum(d_str):
    """Formatiert ein Datenbank-Datum (YYYY-MM-DD) ins deutsche Format (DD.MM.YYYY)."""
    if not d_str:
        return ""
    try:
        dt = datetime.strptime(str(d_str), "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return d_str

def parse_time(t_str):
    if not t_str:
        return time(0, 0)
    try:
        parts = str(t_str).split(":")
        return time(hour=int(parts[0]), minute=int(parts[1]))
    except Exception:
        return time(0, 0)

def show():
    st.header("📅 Kalender & Termine")
    
    user_id = st.session_state.get("user_id")
    user_rolle = st.session_state.get("user_rolle", "mitglied")
    is_leitung = user_rolle in ["admin", "administrator", "vorstand"]
    
    tab_uebersicht, tab_erstellen = st.tabs([
        "📋 Termin-Übersicht & Rückmeldungen",
        "➕ Neuen Termin anlegen"
    ])
    
    # ==========================================
    # TAB 1: ÜBERSICHT & RSVP
    # ==========================================
    with tab_uebersicht:
        st.subheader("Anstehende Termine")
        termine = get_termine_fuer_nutzer(user_rolle, user_id)
        
        if termine:
            filter_ansicht = st.radio("Ansicht", ["Alle Termine", "Nur kommende"], horizontal=True, key="termin_filter")
            heute_str = datetime.today().strftime("%Y-%m-%d")
            
            gefilterte = []
            for t in termine:
                if filter_ansicht == "Nur kommende" and t.get("datum", "") < heute_str:
                    continue
                gefilterte.append(t)
                
            if gefilterte:
                for t in gefilterte:
                    sichtb = t.get("sichtbarkeit", "alle")
                    badge = f" 🔒 [{sichtb.upper()}]" if sichtb != "alle" else ""
                    
                    datum_formatiert = formatiere_datum(t.get('datum'))
                    
                    with st.expander(f"📌 {t.get('titel')} am {datum_formatiert}{badge}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Datum:** {datum_formatiert}")
                            u_von = t.get('uhrzeit_von', '')
                            u_bis = t.get('uhrzeit_bis', '')
                            if u_von or u_bis:
                                st.write(f"**Uhrzeit:** {u_von[:5] if u_von else ''} - {u_bis[:5] if u_bis else ''} Uhr")
                            if t.get('ort'):
                                st.write(f"**Ort:** {t.get('ort')}")
                        with col2:
                            st.write(f"**Sichtbarkeit:** {sichtb.capitalize()}")
                            if t.get('beschreibung'):
                                st.info(f"**Beschreibung:** {t.get('beschreibung')}")
                                
                        st.divider()
                        
                        # Teilnahme / RSVP Sektion
                        st.markdown("#### Deine Teilnahme")
                        teilnahmen = get_teilnahmen_fuer_termin(t.get("id"))
                        
                        aktueller_status = "unsicher"
                        if user_id:
                            for tn in teilnahmen:
                                if tn.get("user_id") == user_id:
                                    aktueller_status = tn.get("status", "unsicher")
                                    break
                                    
                        st.markdown(f"Dein Status: **{aktueller_status.capitalize()}**")
                        
                        if user_id:
                            t_id = t.get("id")
                            b1, b2, b3 = st.columns(3)
                            if b1.button("✅ Kann", key=f"t_kann_{t_id}", use_container_width=True):
                                setze_teilnahme(t_id, user_id, "kann")
                                st.success("Zusage gespeichert!")
                                st.rerun()
                            if b2.button("❌ Kann nicht", key=f"t_nicht_{t_id}", use_container_width=True):
                                setze_teilnahme(t_id, user_id, "kann nicht")
                                st.success("Absage gespeichert!")
                                st.rerun()
                            if b3.button("❓ Unsicher", key=f"t_uns_{t_id}", use_container_width=True):
                                setze_teilnahme(t_id, user_id, "unsicher")
                                st.success("Status auf unsicher gesetzt!")
                                st.rerun()
                                
                        st.divider()
                        st.markdown("**Teilnehmer-Übersicht:**")
                        if teilnahmen:
                            kann = [f"{n.get('mitglieder', {}).get('vorname', '')} {n.get('mitglieder', {}).get('nachname', '')}" for n in teilnahmen if n.get('status') == 'kann']
                            kann_nicht = [f"{n.get('mitglieder', {}).get('vorname', '')} {n.get('mitglieder', {}).get('nachname', '')}" for n in teilnahmen if n.get('status') == 'kann nicht']
                            unsicher = [f"{n.get('mitglieder', {}).get('vorname', '')} {n.get('mitglieder', {}).get('nachname', '')}" for n in teilnahmen if n.get('status') == 'unsicher']
                            
                            tc1, tc2, tc3 = st.columns(3)
                            tc1.success(f"**Kann ({len(kann)})**\n" + "\n".join([f"- {x}" for x in kann]) if kann else "**Kann (0)**")
                            tc2.error(f"**Kann nicht ({len(kann_nicht)})**\n" + "\n".join([f"- {x}" for x in kann_nicht]) if kann_nicht else "**Kann nicht (0)**")
                            tc3.info(f"**Unsicher ({len(unsicher)})**\n" + "\n".join([f"- {x}" for x in unsicher]) if unsicher else "**Unsicher (0)**")
                        else:
                            st.text("Bisher keine Rückmeldungen.")
                            
                        # Bearbeiten / Löschen Option für Ersteller oder Admin/Vorstand
                        if is_leitung or t.get("creator_id") == user_id:
                            st.divider()
                            with st.expander("⚙️ Termin verwalten (Bearbeiten / Löschen)"):
                                with st.form(f"edit_termin_form_{t.get('id')}"):
                                    et_titel = st.text_input("Titel", value=t.get("titel", ""))
                                    et_datum = st.date_input("Datum", value=datetime.strptime(t.get("datum"), "%Y-%m-%d") if t.get("datum") else datetime.today(), format="DD.MM.YYYY")
                                    et_ort = st.text_input("Ort", value=t.get("ort", "") or "")
                                    
                                    col_u1, col_u2 = st.columns(2)
                                    with col_u1:
                                        et_von = st.time_input("Uhrzeit von", value=parse_time(t.get("uhrzeit_von")))
                                    with col_u2:
                                        et_bis = st.time_input("Uhrzeit bis", value=parse_time(t.get("uhrzeit_bis")))
                                        
                                    current_sichtb = t.get("sichtbarkeit", "alle")
                                    sichtb_options = ["alle", "vorstand", "admin"]
                                    idx = sichtb_options.index(current_sichtb) if current_sichtb in sichtb_options else 0
                                    et_sichtbarkeit = st.selectbox("Sichtbarkeit", options=sichtb_options, index=idx)
                                    
                                    et_beschreibung = st.text_area("Beschreibung", value=t.get("beschreibung", "") or "")
                                    
                                    col_up, col_del = st.columns(2)
                                    with col_up:
                                        up_sub = st.form_submit_button("Änderungen speichern", type="primary")
                                    with col_del:
                                        del_sub = st.form_submit_button("Termin löschen", type="secondary")
                                        
                                    if up_sub:
                                        update_daten = {
                                            "titel": et_titel,
                                            "datum": et_datum.strftime("%Y-%m-%d"),
                                            "ort": et_ort if et_ort else None,
                                            "uhrzeit_von": et_von.strftime("%H:%M:%S") if et_von else None,
                                            "uhrzeit_bis": et_bis.strftime("%H:%M:%S") if et_bis else None,
                                            "sichtbarkeit": et_sichtbarkeit,
                                            "beschreibung": et_beschreibung if et_beschreibung else None
                                        }
                                        try:
                                            termin_aktualisieren(t.get("id"), update_daten)
                                            st.success("Termin aktualisiert!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Fehler: {e}")
                                            
                                    if del_sub:
                                        try:
                                            termin_loeschen(t.get("id"))
                                            st.success("Termin gelöscht!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Fehler beim Löschen: {e}")
            else:
                st.info("Keine Termine für diesen Filter vorhanden.")
        else:
            st.info("Keine Termine eingetragen.")

    # ==========================================
    # TAB 2: TERMIN ERSTELLEN (Jedes Mitglied)
    # ==========================================
    with tab_erstellen:
        st.subheader("Neuen Termin anlegen")
        st.markdown("Jedes Mitglied kann Termine eintragen. Du kannst die Sichtbarkeit einschränken (z. B. nur für den Vorstand).")
        
        with st.form("neuer_termin_form"):
            c1, c2 = st.columns(2)
            with c1:
                t_titel = st.text_input("Titel *")
                t_datum = st.date_input("Datum *", value=datetime.today(), format="DD.MM.YYYY")
                t_ort = st.text_input("Ort / Raum")
            with c2:
                t_von = st.time_input("Uhrzeit von")
                t_bis = st.time_input("Uhrzeit bis")
                t_sichtbarkeit = st.selectbox(
                    "Sichtbarkeit", 
                    options=["alle", "vorstand", "admin"],
                    format_func=lambda x: "Alle Mitglieder" if x == "alle" else ("Nur Vorstand" if x == "vorstand" else "Nur Admins")
                )
                
            t_beschreibung = st.text_area("Beschreibung / Details")
            
            sub_neu = st.form_submit_button("Termin erstellen", type="primary")
            if sub_neu:
                if not t_titel:
                    st.error("Bitte gib mindestens einen Titel an.")
                else:
                    neuer_termin = {
                        "titel": t_titel,
                        "datum": t_datum.strftime("%Y-%m-%d"),
                        "uhrzeit_von": t_von.strftime("%H:%M:%S") if t_von else None,
                        "uhrzeit_bis": t_bis.strftime("%H:%M:%S") if t_bis else None,
                        "sichtbarkeit": t_sichtbarkeit,
                        "ort": t_ort if t_ort else None,
                        "beschreibung": t_beschreibung if t_beschreibung else None,
                        "creator_id": user_id if isinstance(user_id, str) else None
                    }
                    try:
                        termin_erstellen(neuer_termin)
                        st.success("Termin erfolgreich erstellt!")
                        st.rerun()
                    except Exception as e:
                        try:
                            neuer_termin.pop("creator_id", None)
                            termin_erstellen(neuer_termin)
                            st.success("Termin erfolgreich erstellt!")
                            st.rerun()
                        except Exception as e2:
                            st.error(f"Fehler beim Erstellen des Termins: {e2}")