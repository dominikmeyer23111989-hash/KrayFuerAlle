import streamlit as st
from datetime import datetime
from modules.todos import (
    get_todos_fuer_nutzer,
    get_alle_mitglieder,
    todo_erstellen,
    todo_aktualisieren,
    todo_loeschen
)

def formatiere_datum(d_str):
    """Formatiert ein Datenbank-Datum (YYYY-MM-DD oder Zeitstempel) ins deutsche Format (DD.MM.YYYY)."""
    if not d_str:
        return ""
    try:
        s = str(d_str)[:10]
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return d_str

def show():
    st.header("📋 Aufgaben & To-Dos")
    
    user_id = st.session_state.get("user_id")
    user_rolle = st.session_state.get("user_rolle", "mitglied")
    is_leitung = user_rolle in ["admin", "administrator", "vorstand"]
    
    tab_uebersicht, tab_erstellen = st.tabs([
        "📋 Aufgaben-Übersicht",
        "➕ Neue Aufgabe erstellen"
    ])
    
    mitglieder_liste = get_alle_mitglieder()
    mitglieder_map = {m["id"]: f"{m.get('vorname', '')} {m.get('nachname', '')}" for m in mitglieder_liste}

    # ==========================================
    # TAB 1: ÜBERSICHT & BEARBEITUNG
    # ==========================================
    with tab_uebersicht:
        st.subheader("Aktuelle To-Dos")
        todos = get_todos_fuer_nutzer(user_rolle, user_id)
        
        if todos:
            status_filter = st.radio("Status-Filter", ["Alle", "Offen", "In Bearbeitung", "Erledigt"], horizontal=True, key="todo_filter")
            
            gefilterte_todos = []
            for t in todos:
                aktueller_status = t.get("status", "Offen")
                if status_filter != "Alle" and aktueller_status != status_filter:
                    continue
                gefilterte_todos.append(t)
                
            if gefilterte_todos:
                for t in gefilterte_todos:
                    t_id = t.get("id")
                    titel = t.get("titel", "Kein Titel")
                    status = t.get("status", "Offen")
                    
                    # Farb-Icons nach Status
                    status_icon = "🟢" if status == "Erledigt" else ("🟡" if status == "In Bearbeitung" else "🔴")
                    
                    # Zugewiesene Person ermitteln
                    zugewiesen_id = t.get("zugewiesen_an")
                    zugewiesen_name = "Niemand"
                    if zugewiesen_id in mitglieder_map:
                        zugewiesen_name = mitglieder_map[zugewiesen_id]
                    elif isinstance(t.get("zugewiesener"), dict):
                        m_info = t.get("zugewiesener")
                        zugewiesen_name = f"{m_info.get('vorname', '')} {m_info.get('nachname', '')}"

                    deadline_formatiert = formatiere_datum(t.get('deadline'))
                    erstellt_am_formatiert = formatiere_datum(t.get('created_at'))

                    with st.expander(f"{status_icon} [{status}] {titel} (Für: {zugewiesen_name})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Deadline:** {deadline_formatiert if t.get('deadline') else 'Keine'}")
                            st.write(f"**Zugewiesen an:** {zugewiesen_name}")
                        with col2:
                            ersteller_id = t.get("erstellt_von")
                            ersteller_name = mitglieder_map.get(ersteller_id, "Unbekannt")
                            st.write(f"**Erstellt von:** {ersteller_name}")
                            st.write(f"**Erstellt am:** {erstellt_am_formatiert if t.get('created_at') else '-'}")
                            
                        if t.get("beschreibung"):
                            st.info(f"**Beschreibung:** {t.get('beschreibung')}")
                            
                        st.divider()
                        
                        # Schnell-Statusänderung für jeden berechtigten Nutzer / Bearbeiter
                        c_s1, c_s2, c_s3 = st.columns(3)
                        if c_s1.button("📌 Offen", key=f"t_offen_{t_id}", use_container_width=True):
                            todo_aktualisieren(t_id, {"status": "Offen", "finished_at": None})
                            st.success("Status auf Offen gesetzt!")
                            st.rerun()
                        if c_s2.button("⏳ In Bearbeitung", key=f"t_bearb_{t_id}", use_container_width=True):
                            todo_aktualisieren(t_id, {"status": "In Bearbeitung", "finished_at": None})
                            st.success("Status geändert!")
                            st.rerun()
                        if c_s3.button("✅ Erledigt", key=f"t_erledigt_{t_id}", use_container_width=True):
                            todo_aktualisieren(t_id, {"status": "Erledigt", "finished_at": datetime.now().isoformat()})
                            st.success("Aufgabe als erledigt markiert!")
                            st.rerun()
                            
                        # Löschen oder Bearbeiten für Ersteller oder Admins/Vorstand
                        if is_leitung or t.get("erstellt_von") == user_id or t.get("zugewiesen_an") == user_id:
                            st.divider()
                            with st.expander("⚙️ Aufgabe bearbeiten / löschen"):
                                with st.form(f"edit_todo_form_{t_id}"):
                                    e_titel = st.text_input("Titel", value=t.get("titel", ""))
                                    e_beschreibung = st.text_area("Beschreibung", value=t.get("beschreibung", "") or "")
                                    
                                    # Mitglied-Auswahl für Zuweisung
                                    mitglieder_ids = [None] + [m["id"] for m in mitglieder_liste]
                                    aktueller_zugewiesener = t.get("zugewiesen_an")
                                    idx = mitglieder_ids.index(aktueller_zugewiesener) if aktueller_zugewiesener in mitglieder_ids else 0
                                    
                                    e_zugewiesen = st.selectbox(
                                        "Zugewiesen an", 
                                        options=mitglieder_ids, 
                                        index=idx,
                                        format_func=lambda x: "Niemand" if x is None else mitglieder_map.get(x, str(x))
                                    )
                                    
                                    # Datum parsen
                                    try:
                                        d_val = datetime.strptime(t.get("deadline"), "%Y-%m-%d").date() if t.get("deadline") else datetime.today().date()
                                    except:
                                        d_val = datetime.today().date()
                                        
                                    e_deadline = st.date_input("Deadline", value=d_val, format="DD.MM.YYYY")
                                    
                                    col_up, col_del = st.columns(2)
                                    with col_up:
                                        sub_up = st.form_submit_button("Änderungen speichern", type="primary")
                                    with col_del:
                                        sub_del = st.form_submit_button("Aufgabe löschen", type="secondary")
                                        
                                    if sub_up:
                                        up_data = {
                                            "titel": e_titel,
                                            "beschreibung": e_beschreibung if e_beschreibung else None,
                                            "zugewiesen_an": e_zugewiesen,
                                            "deadline": e_deadline.strftime("%Y-%m-%d") if e_deadline else None
                                        }
                                        try:
                                            todo_aktualisieren(t_id, up_data)
                                            st.success("Aufgabe aktualisiert!")
                                            st.rerun()
                                        except Exception as err:
                                            st.error(f"Fehler: {err}")
                                            
                                    if sub_del:
                                        try:
                                            todo_loeschen(t_id)
                                            st.success("Aufgabe gelöscht!")
                                            st.rerun()
                                        except Exception as err:
                                            st.error(f"Fehler beim Löschen: {err}")
            else:
                st.info("Keine Aufgaben für diesen Filter gefunden.")
        else:
            st.info("Keine Aufgaben vorhanden.")

    # ==========================================
    # TAB 2: NEUES TODO ERSTELLEN
    # ==========================================
    with tab_erstellen:
        st.subheader("Neue Aufgabe anlegen")
        
        with st.form("neues_todo_form"):
            t_titel = st.text_input("Aufgaben-Titel *")
            t_beschreibung = st.text_area("Beschreibung / Details")
            
            mitglieder_ids = [None] + [m["id"] for m in mitglieder_liste]
            t_zugewiesen = st.selectbox(
                "Zuweisen an", 
                options=mitglieder_ids,
                format_func=lambda x: "Niemand (Offen für alle)" if x is None else mitglieder_map.get(x, str(x))
            )
            
            t_deadline = st.date_input("Deadline (optional)", value=datetime.today(), format="DD.MM.YYYY")
            
            sub_erstellen = st.form_submit_button("Aufgabe erstellen", type="primary")
            if sub_erstellen:
                if not t_titel:
                    st.error("Bitte gib einen Titel ein.")
                else:
                    neues_todo = {
                        "titel": t_titel,
                        "beschreibung": t_beschreibung if t_beschreibung else None,
                        "erstellt_von": user_id,
                        "zugewiesen_an": t_zugewiesen,
                        "deadline": t_deadline.strftime("%Y-%m-%d") if t_deadline else None,
                        "status": "Offen"
                    }
                    try:
                        todo_erstellen(neues_todo)
                        st.success("Aufgabe erfolgreich erstellt!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Erstellen: {e}")