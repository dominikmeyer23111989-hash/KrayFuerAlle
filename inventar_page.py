import streamlit as st
from datetime import datetime
import pandas as pd
from modules.inventar import (
    get_alle_inventar,
    inventar_hinzufuegen,
    inventar_aktualisieren,
    inventar_loeschen,
    get_alle_ausleihen,
    ausleihe_erstellen,
    ausleihe_zuruecknehmen,
    material_reparieren,
    get_inventar_einstellungen,
    inventar_einstellungen_aktualisieren,
    formatiere_datum_fuer_anzeige
)
import supabase

def show():
    st.header("📦 Inventar- & Ausleihverwaltung")
    
    has_inventar_rights = st.session_state.get("hat_inventar_rechte", False)
    is_admin_or_vorstand = st.session_state.get("user_rolle", "").lower() in ["admin", "administrator", "vorstand", "kassenwart"]
    
    # Zugriff haben Admins/Vorstände Oder Personen mit direktem Inventar-Recht
    can_manage_or_lend = has_inventar_rights or is_admin_or_vorstand
    
    # Tabs dynamisch aufbauen: Nur Admins/Vorstände oder Berechtigte bekommen Ausleihe & Verwaltung
    if can_manage_or_lend:
        tab_uebersicht, tab_ausleihe, tab_verwaltung, tab_reparatur, tab_einstellungen = st.tabs([
            "📋 Inventar-Liste",
            "🔄 Ausleihe & Rückgabe",
            "⚙️ Inventar pflegen",
            "🔧 Reparaturen & Defekte",
            "🔔 Einstellungen"
        ])
    else:
        # Normale Mitglieder ohne Rechte sehen AUSSCHLIESSLICH die Inventar-Liste
        tab_uebersicht = st.tabs(["📋 Inventar-Liste"])[0]
        tab_ausleihe = None
        tab_verwaltung = None
        tab_reparatur = None
        tab_einstellungen = None

    # ==========================================
    # 1. INVENTAR-LISTE (Für jeden sichtbar)
    # ==========================================
    with tab_uebersicht:
        st.subheader("Verfügbare Inventar-Gegenstände")
        inventar_liste = get_alle_inventar()
        
        if inventar_liste:
            suchbegriff = st.text_input("🔍 Inventar durchsuchen (Name, Lagerort, Charge...)", key="inv_suche")
            
            filtered_list = []
            for item in inventar_liste:
                name = str(item.get("name", "")).lower()
                lagerort = str(item.get("lagerort", "")).lower()
                chargen = str(item.get("chargennummer", "")).lower()
                if not suchbegriff or suchbegriff.lower() in name or suchbegriff.lower() in lagerort or suchbegriff.lower() in chargen:
                    filtered_list.append({
                        "ID": item.get("id"),
                        "Name": item.get("name"),
                        "Lagerort": item.get("lagerort", "-"),
                        "Gesamt": item.get("menge_gesamt"),
                        "Verfügbar": item.get("menge_verfuegbar"),
                        "Defekt": item.get("menge_defekt"),
                        "Status": item.get("status"),
                        "Prüfdatum": formatiere_datum_fuer_anzeige(item.get("pruefdatum")),
                        "Ablaufdatum": formatiere_datum_fuer_anzeige(item.get("ablaufdatum"))
                    })
            
            col1, col2 = st.columns([1, 3])
            col1.metric("Gesamtartikel", len(inventar_liste))
            
            st.dataframe(filtered_list, use_container_width=True, hide_index=True)
        else:
            st.info("Keine Inventar-Gegenstände gefunden.")

    # ==========================================
    # 2. AUSLEIHE & RÜCKGABE (Nur für Berechtigte / Admins)
    # ==========================================
    if can_manage_or_lend and tab_ausleihe is not None:
        with tab_ausleihe:
            sub_tab1, sub_tab2 = st.tabs(["📤 Gegenstand ausleihen", "📥 Aktive Ausleihen & Rückgabe"])
            
            # --- Ausleihen Formular ---
            with sub_tab1:
                st.subheader("Neue Ausleihe erfassen")
                inv_daten = get_alle_inventar()
                verfuegbare_items = [i for i in inv_daten if i.get("menge_verfuegbar", 0) > 0]
                
                if verfuegbare_items:
                    item_dict = {f"{i.get('name')} (Verfügbar: {i.get('menge_verfuegbar')} | Lagerort: {i.get('lagerort', 'k.A.')})": i for i in verfuegbare_items}
                    wahl = st.selectbox("Gegenstand auswählen", options=list(item_dict.keys()))
                    
                    selected_item = item_dict[wahl]
                    max_menge = selected_item.get("menge_verfuegbar", 1)
                    
                    with st.form("ausleihe_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            person_name = st.text_input("An wen wird verliehen (Name der Person) *")
                            menge = st.number_input("Ausleihmenge", min_value=1, max_value=max_menge, value=1)
                        with col2:
                            ausleih_datum = st.date_input("Ausleihdatum", value=datetime.today())
                            rueckgabe_soll = st.date_input("Geplantes Rückgabedatum", value=datetime.today())
                            
                        aktueller_nutzer = st.session_state.get("vorname", "System")
                        st.info(f"ℹ️ Material ausgegeben von: **{aktueller_nutzer}** (wird automatisch dokumentiert)")
                        
                        schadensbericht = st.text_area("Vorab-Notizen / Zustand (optional)")
                        
                        submitted = st.form_submit_button("Ausleihe bestätigen", type="primary")
                        
                        if submitted:
                            if not person_name:
                                st.error("Bitte gib an, an wen das Material verliehen wird.")
                            else:
                                daten = {
                                    "inventar_id": selected_item.get("id"),
                                    "person_name": person_name,
                                    "menge": menge,
                                    "ausleih_datum": ausleih_datum.strftime("%Y-%m-%d"),
                                    "rueckgabe_soll": rueckgabe_soll.strftime("%Y-%m-%d"),
                                    "status": "Aktiv",
                                    "ausgegeben_von": aktueller_nutzer,
                                    "schadensbericht": schadensbericht if schadensbericht else None
                                }
                                try:
                                    ausleihe_erstellen(daten)
                                    st.success(f"Ausleihe von '{selected_item.get('name')}' an {person_name} erfolgreich eingetragen!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fehler beim Erstellen der Ausleihe: {e}")
                else:
                    st.info("Aktuell sind keine Gegenstände zur Ausleihe verfügbar.")

            # --- Rückgabe / Aktive Ausleihen ---
            with sub_tab2:
                st.subheader("Aktive Ausleihen zurücknehmen")
                alle_ausleihen = get_alle_ausleihen()
                aktive_ausleihen = [a for a in alle_ausleihen if a.get("status") == "Aktiv"]
                
                if aktive_ausleihen:
                    ausleih_dict = {
                        f"ID {a.get('id')} - {a.get('inventar', {}).get('name', 'Unbekannt')} (Ausgeliehen an: {a.get('person_name')}, Menge: {a.get('menge')})": a 
                        for a in aktive_ausleihen
                    }
                    
                    auswahl_ausleihe = st.selectbox("Ausleihe für Rücknahme wählen", options=list(ausleih_dict.keys()))
                    selected_ausleihe = ausleih_dict[auswahl_ausleihe]
                    
                    with st.form("rueckgabe_form"):
                        st.write(f"**Gegenstand:** {selected_ausleihe.get('inventar', {}).get('name')}")
                        st.write(f"**Ausgeliehen an:** {selected_ausleihe.get('person_name')} (Menge: {selected_ausleihe.get('menge')})")
                        st.write(f"**Ausgegeben von:** {selected_ausleihe.get('ausgegeben_von', 'Unbekannt')}")
                        st.write(f"**Soll-Rückgabe:** {formatiere_datum_fuer_anzeige(selected_ausleihe.get('rueckgabe_soll'))}")
                        
                        st.divider()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            rueckgabe_ist = st.date_input("Tatsächliches Rückgabedatum", value=datetime.today())
                            rueckgeber_name = st.text_input("Wer bringt das Material zurück? (Name)", value=selected_ausleihe.get('person_name'))
                        with col2:
                            aktueller_nutzer = st.session_state.get("vorname", "System")
                            st.text_input("Wer nimmt das Material entgegen?", value=aktueller_nutzer, disabled=True)
                        
                        st.divider()
                        
                        schaden_vorhanden = st.checkbox("⚠️ Schäden / Mängel bei Rückgabe festgestellt?")
                        
                        menge_defekt_rueckgabe = 0
                        festgestellte_maengel = ""
                        
                        if schaden_vorhanden:
                            ausleih_menge = selected_ausleihe.get('menge', 1)
                            if ausleih_menge > 1:
                                menge_defekt_rueckgabe = st.number_input("Wie viele davon sind defekt?", min_value=1, max_value=ausleih_menge, value=1)
                            else:
                                menge_defekt_rueckgabe = 1
                                
                            festgestellte_maengel = st.text_area("Freitext: Was ist defekt / Schadensbeschreibung *")
                        
                        schadensbericht_neu = st.text_area("Allgemeine Notizen zur Rücknahme (optional)")
                        
                        ruecknahme_btn = st.form_submit_button("Gegenstand zurücknehmen", type="primary")
                        
                        if ruecknahme_btn:
                            if schaden_vorhanden and not festgestellte_maengel.strip():
                                st.error("Bitte trage im Freitext ein, was defekt ist.")
                            else:
                                rueckgabe_daten = {
                                    "rueckgabe_ist": rueckgabe_ist.strftime("%Y-%m-%d"),
                                    "status": "Zurückgebracht",
                                    "zurueckgebracht_von": rueckgeber_name,
                                    "entgegengenommen_von": aktueller_nutzer,
                                    "ruecknahme_durch": aktueller_nutzer,
                                    "rueckgeber_name": rueckgeber_name,
                                    "festgestellte_maengel": festgestellte_maengel if festgestellte_maengel else None,
                                    "schadensbericht": schadensbericht_neu if schadensbericht_neu else selected_ausleihe.get("schadensbericht")
                                }
                                try:
                                    ausleihe_zuruecknehmen(selected_ausleihe.get("id"), rueckgabe_daten, menge_defekt_rueckgabe)
                                    if menge_defekt_rueckgabe > 0:
                                        st.warning(f"Rücknahme erfolgt. {menge_defekt_rueckgabe} Stück wurden als defekt im Lager markiert!")
                                    else:
                                        st.success("Gegenstand erfolgreich zurückgenommen und Bestand gutgeschrieben!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fehler bei der Rücknahme: {e}")
                else:
                    st.info("Es gibt aktuell keine aktiven Ausleihen.")

    # ==========================================
    # 3. INVENTAR PFLEGEN (Nur für Berechtigte / Admins)
    # ==========================================
    if can_manage_or_lend and tab_verwaltung is not None:
        with tab_verwaltung:
            st.subheader("Inventar bearbeiten, löschen oder neu anlegen")
            sub_verw_1, sub_verw_2 = st.tabs(["➕ Neu anlegen", "⚙️ Bearbeiten & Löschen"])
            
            with sub_verw_1:
                with st.form("neues_inventar_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        inv_name = st.text_input("Gegenstandsname *")
                        inv_lagerort = st.text_input("Lagerort")
                        inv_gesamt = st.number_input("Gesamtmenge", min_value=1, value=1)
                        inv_defekt = st.number_input("Davon defekt", min_value=0, value=0)
                        inv_charge = st.text_input("Chargennummer")
                    with col2:
                        inv_anschaffung = st.date_input("Anschaffungsdatum", value=datetime.today())
                        inv_pruefung = st.date_input("Prüfdatum (Nächste Prüfung)", value=datetime.today())
                        inv_ablauf = st.date_input("Ablaufdatum (optional)", value=None)
                        inv_beschreibung = st.text_area("Beschreibung / Mängel")
                        
                    save_inv_btn = st.form_submit_button("Inventar-Gegenstand speichern", type="primary")
                    
                    if save_inv_btn:
                        if not inv_name:
                            st.error("Der Name des Gegenstands ist ein Pflichtfeld.")
                        else:
                            verfuegbar_start = max(0, inv_gesamt - inv_defekt)
                            status_start = "Verfügbar" if verfuegbar_start > 0 else "Nicht verfügbar"
                            
                            neuer_gegenstand = {
                                "name": inv_name,
                                "lagerort": inv_lagerort if inv_lagerort else None,
                                "menge_gesamt": inv_gesamt,
                                "menge_verfuegbar": verfuegbar_start,
                                "menge_defekt": inv_defekt,
                                "chargennummer": inv_charge if inv_charge else None,
                                "anschaffungs_datum": inv_anschaffung.strftime("%Y-%m-%d"),
                                "pruefdatum": inv_pruefung.strftime("%Y-%m-%d"),
                                "ablaufdatum": inv_ablauf.strftime("%Y-%m-%d") if inv_ablauf else None,
                                "status": status_start,
                                "beschreibung_maengel": inv_beschreibung if inv_beschreibung else None
                            }
                            try:
                                inventar_hinzufuegen(neuer_gegenstand)
                                st.success(f"Gegenstand '{inv_name}' erfolgreich hinzugefügt!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Speichern: {e}")

            with sub_verw_2:
                inventar_liste = get_alle_inventar()
                if inventar_liste:
                    inv_edit_dict = {f"{i.get('id')} - {i.get('name')} (Lagerort: {i.get('lagerort', 'k.A.')})": i for i in inventar_liste}
                    auswahl_inv_edit = st.selectbox("Gegenstand zum Bearbeiten wählen", options=list(inv_edit_dict.keys()))
                    selected_edit_item = inv_edit_dict[auswahl_inv_edit]
                    
                    with st.form("edit_inventar_form"):
                        e_name = st.text_input("Name", value=selected_edit_item.get("name", ""))
                        e_lagerort = st.text_input("Lagerort", value=selected_edit_item.get("lagerort", "") or "")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            e_gesamt = st.number_input("Gesamtmenge", min_value=1, value=selected_edit_item.get("menge_gesamt", 1))
                            e_defekt = st.number_input("Davon defekt", min_value=0, value=selected_edit_item.get("menge_defekt", 0))
                            e_charge = st.text_input("Chargennummer", value=selected_edit_item.get("chargennummer", "") or "")
                        with col2:
                            p_str = selected_edit_item.get("pruefdatum")
                            p_val = datetime.strptime(p_str.split("T")[0], "%Y-%m-%d") if p_str else datetime.today()
                            e_pruefung = st.date_input("Prüfdatum", value=p_val)
                            
                            a_str = selected_edit_item.get("ablaufdatum")
                            a_val = datetime.strptime(a_str.split("T")[0], "%Y-%m-%d") if a_str else None
                            e_ablauf = st.date_input("Ablaufdatum", value=a_val)
                            
                            e_status = st.selectbox("Status", ["Verfügbar", "Ausgeliehen", "Gesperrt", "Defekt"], index=0 if selected_edit_item.get("status") == "Verfügbar" else 1)
                            
                        e_beschreibung = st.text_area("Beschreibung / Mängel", value=selected_edit_item.get("beschreibung_maengel", "") or "")
                        
                        col_save_inv, col_del_inv = st.columns(2)
                        with col_save_inv:
                            update_inv_btn = st.form_submit_button("Änderungen speichern", type="primary")
                        with col_del_inv:
                            delete_inv_btn = st.form_submit_button("Gegenstand löschen", type="secondary")
                            
                        if update_inv_btn:
                            if not e_name:
                                st.error("Name ist ein Pflichtfeld.")
                            else:
                                akt_verf = selected_edit_item.get("menge_verfuegbar", 1)
                                diff_gesamt = e_gesamt - selected_edit_item.get("menge_gesamt", 1)
                                neue_verfuegbar = max(0, akt_verf + diff_gesamt)
                                
                                update_daten = {
                                    "name": e_name,
                                    "lagerort": e_lagerort if e_lagerort else None,
                                    "menge_gesamt": e_gesamt,
                                    "menge_verfuegbar": neue_verfuegbar,
                                    "menge_defekt": e_defekt,
                                    "chargennummer": e_charge if e_charge else None,
                                    "pruefdatum": e_pruefung.strftime("%Y-%m-%d"),
                                    "ablaufdatum": e_ablauf.strftime("%Y-%m-%d") if e_ablauf else None,
                                    "status": e_status,
                                    "beschreibung_maengel": e_beschreibung if e_beschreibung else None
                                }
                                try:
                                    inventar_aktualisieren(selected_edit_item.get("id"), update_daten)
                                    st.success("Inventar erfolgreich aktualisiert!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fehler beim Aktualisieren: {e}")
                                    
                        if delete_inv_btn:
                            try:
                                inventar_loeschen(selected_edit_item.get("id"))
                                st.success("Gegenstand erfolgreich gelöscht.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Löschen: {e}")
                else:
                    st.info("Keine Gegenstände zum Bearbeiten vorhanden.")

    # ==========================================
    # 4. REPARATUREN & DEFEKTE (Nur für Berechtigte / Admins)
    # ==========================================
    if can_manage_or_lend and tab_reparatur is not None:
        with tab_reparatur:
            st.subheader("🔧 Defektes Material & Reparaturen")
            st.markdown("Hier siehst du alle Gegenstände, bei denen Einheiten als defekt gemeldet wurden. Mit Klick auf **Als repariert melden** werden sie dem Lager wieder als verfügbar zugeschrieben.")
            
            inventar_liste = get_alle_inventar()
            defekte_items = [i for i in inventar_liste if i.get("menge_defekt", 0) > 0]
            
            if defekte_items:
                for item in defekte_items:
                    with st.container(border=True):
                        col_info, col_action = st.columns([3, 1])
                        with col_info:
                            st.markdown(f"### 🛠️ {item.get('name')}")
                            st.write(f"**Lagerort:** {item.get('lagerort', 'k.A.')}")
                            st.write(f"**Defekte Menge:** {item.get('menge_defekt')} von {item.get('menge_gesamt')} Gesamt")
                            if item.get("beschreibung_maengel"):
                                st.info(f"**Schadensbeschreibung / Notiz:** {item.get('beschreibung_maengel')}")
                        
                        with col_action:
                            st.write("")
                            anzahl_zu_reparieren = st.number_input(
                                "Anzahl repariert", 
                                min_value=1, 
                                max_value=item.get("menge_defekt", 1), 
                                value=item.get("menge_defekt", 1),
                                key=f"rep_anz_{item.get('id')}"
                            )
                            if st.button("🔧 Als repariert", key=f"btn_rep_{item.get('id')}", type="primary", use_container_width=True):
                                try:
                                    material_reparieren(item.get("id"), anzahl_zu_reparieren)
                                    st.success(f"{anzahl_zu_reparieren}x '{item.get('name')}' repariert & ins Lager zurückgebucht!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fehler bei der Reparatur: {e}")
            else:
                st.success("🎉 Aktuell gibt es keine defekten Gegenstände im Lager. Alles einsatzbereit!")

    # ==========================================
    # 5. EINSTELLUNGEN (Nur für Berechtigte / Admins)
    # ==========================================
    if can_manage_or_lend and tab_einstellungen is not None:
        with tab_einstellungen:
            st.subheader("🔔 Benachrichtigungs- & Inventareinstellungen")
            
            einstellungen = get_inventar_einstellungen()
            
            with st.form("einstellungen_form"):
                if einstellungen:
                    tage_vorher = st.number_input("Erinnerung X Tage vor Prüf-/Ablaufdatum", min_value=1, value=einstellungen.get("erinnerung_tage_vorher", 7))
                    email_empfaenger = st.text_input("E-Mail-Empfänger für Benachrichtigungen", value=einstellungen.get("email_empfaenger", "") or "")
                    whatsapp_tel = st.text_input("WhatsApp Telefonnummer", value=einstellungen.get("whatsapp_telefonnummer", "") or "")
                    whatsapp_key = st.text_input("WhatsApp API Key", value=einstellungen.get("whatsapp_key", "") or "", type="password")
                else:
                    tage_vorher = st.number_input("Erinnerung X Tage vor Prüf-/Ablaufdatum", min_value=1, value=7)
                    email_empfaenger = st.text_input("E-Mail-Empfänger für Benachrichtigungen", value="")
                    whatsapp_tel = st.text_input("WhatsApp Telefonnummer", value="")
                    whatsapp_key = st.text_input("WhatsApp API Key", value="", type="password")
                    
                save_settings_btn = st.form_submit_button("Einstellungen speichern", type="primary")
                
                if save_settings_btn:
                    settings_daten = {
                        "erinnerung_tage_vorher": tage_vorher,
                        "email_empfaenger": email_empfaenger if email_empfaenger else None,
                        "whatsapp_telefonnummer": whatsapp_tel if whatsapp_tel else None,
                        "whatsapp_key": whatsapp_key if whatsapp_key else None
                    }
                    try:
                        if einstellungen and "id" in einstellungen:
                            inventar_einstellungen_aktualisieren(einstellungen["id"], settings_daten)
                        else:
                            supabase.table("inventar_einstellungen").insert(settings_daten).execute()
                        st.success("Einstellungen erfolgreich gespeichert!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Speichern der Einstellungen: {e}")