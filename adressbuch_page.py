import streamlit as st
from modules.adressbuch import (
    get_alle_kontakte,
    kontakt_hinzufuegen,
    kontakt_aktualisieren,
    kontakt_loeschen
)

def show():
    st.header("📇 Vereins-Adressbuch")
    
    # ==========================================
    # ZENTRALES NACHRICHTEN-SYSTEM (Nach dem Rerun)
    # ==========================================
    if "adressbuch_msg" in st.session_state:
        msg = st.session_state["adressbuch_msg"]
        if msg["type"] == "success":
            st.success(msg["text"])
        elif msg["type"] == "error":
            st.error(msg["text"])
        del st.session_state["adressbuch_msg"]
    
    is_admin_or_vorstand = st.session_state.get("user_rolle", "").lower() in ["admin", "administrator", "vorstand"]
    has_adressbuch_rights = st.session_state.get("hat_adressbuch_rechte", False)
    
    # Tabs definieren (Bearbeiten/Neu anlegen nur für Vorstand/Admin oder Berechtigte)
    if is_admin_or_vorstand or has_adressbuch_rights:
        tab_liste, tab_neu, tab_bearbeiten = st.tabs([
            "📋 Kontakte-Liste", 
            "➕ Neuen Kontakt anlegen", 
            "⚙️ Kontakt bearbeiten / löschen"
        ])
    else:
        tab_liste = st.container()
        tab_neu = None
        tab_bearbeiten = None

    # ==========================================
    # 1. KONTAKTE-LISTE & SUCHE
    # ==========================================
    if tab_liste:
        with (tab_liste if hasattr(tab_liste, "__enter__") else st.container()):
            if not (is_admin_or_vorstand or has_adressbuch_rights):
                st.subheader("📋 Kontakte-Liste")
                
            kontakte = get_alle_kontakte()
            
            if kontakte:
                suchbegriff = st.text_input("🔍 Kontakte durchsuchen (Name, Kategorie, Ort, E-Mail...)", key="ab_suche")
                
                gefilterte_kontakte = []
                for k in kontakte:
                    such_text = f"{k.get('vorname', '')} {k.get('nachname', '')} {k.get('kategorie', '')} {k.get('email', '')} {k.get('adresse', '')} {k.get('telefon', '')}".lower()
                    if not suchbegriff or suchbegriff.lower() in such_text:
                        gefilterte_kontakte.append({
                            "Nachname": k.get("nachname", ""),
                            "Vorname": k.get("vorname", ""),
                            "Kategorie": k.get("kategorie", ""),
                            "Telefon": k.get("telefon", ""),
                            "E-Mail": k.get("email", ""),
                            "Adresse": k.get("adresse", ""),
                            "Zimmer": k.get("zimmer", ""),
                            "Erreichbarkeit": k.get("erreichbarkeit", ""),
                            "Fax": k.get("fax", "")
                        })
                
                st.metric("Gefundene Kontakte", len(gefilterte_kontakte))
                st.dataframe(gefilterte_kontakte, use_container_width=True, hide_index=True)
            else:
                st.info("Keine Kontakte im Adressbuch gefunden.")

    # ==========================================
    # 2. NEUEN KONTAKT ANLEGEN
    # ==========================================
    if tab_neu is not None:
        with tab_neu:
            st.subheader("Neuen Kontakt hinzufügen")
            
            with st.form("neuer_kontakt_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    vorname = st.text_input("Vorname")
                    nachname = st.text_input("Nachname")
                    kategorie = st.text_input("Kategorie (z.B. Behörde, Lieferant, Vorstand, Partner)")
                    telefon = st.text_input("Telefonnummer")
                    fax = st.text_input("Fax")
                with col2:
                    email = st.text_input("E-Mail-Adresse")
                    adresse = st.text_input("Adresse / Straße & Ort")
                    zimmer = st.text_input("Zimmer / Büro")
                    erreichbarkeit = st.text_input("Erreichbarkeit (z.B. Mo-Fr 9-14 Uhr)")
                    
                submitted = st.form_submit_button("Kontakt speichern", type="primary")
                
                if submitted:
                    # Keine if/else Prüfung mehr auf None. 
                    # Wenn ein Feld leer ist, wird einfach ein leerer Text ("") gespeichert.
                    # Das verhindert Fehler in der Datenbank, falls diese keine NULL-Werte mag.
                    neuer_eintrag = {
                        "vorname": vorname,
                        "nachname": nachname,
                        "kategorie": kategorie,
                        "telefon": telefon,
                        "fax": fax,
                        "email": email,
                        "adresse": adresse,
                        "zimmer": zimmer,
                        "erreichbarkeit": erreichbarkeit
                    }
                    try:
                        kontakt_hinzufuegen(neuer_eintrag)
                        
                        # Name für die Erfolgsmeldung generieren (falls alles leer ist)
                        anzeige_name = f"{vorname} {nachname}".strip()
                        if not anzeige_name:
                            anzeige_name = "Unbenannter Kontakt"
                            
                        st.session_state["adressbuch_msg"] = {"type": "success", "text": f"Kontakt '{anzeige_name}' erfolgreich hinzugefügt!"}
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Speichern in der Datenbank: {e}")

    # ==========================================
    # 3. KONTAKT BEARBEITEN / LÖSCHEN
    # ==========================================
    if tab_bearbeiten is not None:
        with tab_bearbeiten:
            st.subheader("Bestehenden Kontakt bearbeiten oder löschen")
            kontakte = get_alle_kontakte()
            
            if kontakte:
                # Fallback, falls Kontakte gar keinen Namen haben
                kontakt_dict = {f"{k.get('nachname', '')}, {k.get('vorname', '')} (Kat: {k.get('kategorie', '')}) - ID: {k.get('id')}": k for k in kontakte}
                auswahl = st.selectbox("Kontakt auswählen", options=list(kontakt_dict.keys()))
                selected_kontakt = kontakt_dict[auswahl]
                
                with st.form("edit_kontakt_form"):
                    e_vorname = st.text_input("Vorname", value=selected_kontakt.get("vorname", "") or "")
                    e_nachname = st.text_input("Nachname", value=selected_kontakt.get("nachname", "") or "")
                    e_kategorie = st.text_input("Kategorie", value=selected_kontakt.get("kategorie", "") or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        e_telefon = st.text_input("Telefon", value=selected_kontakt.get("telefon", "") or "")
                        e_fax = st.text_input("Fax", value=selected_kontakt.get("fax", "") or "")
                        e_email = st.text_input("E-Mail", value=selected_kontakt.get("email", "") or "")
                    with col2:
                        e_adresse = st.text_input("Adresse", value=selected_kontakt.get("adresse", "") or "")
                        e_zimmer = st.text_input("Zimmer", value=selected_kontakt.get("zimmer", "") or "")
                        e_erreichbarkeit = st.text_input("Erreichbarkeit", value=selected_kontakt.get("erreichbarkeit", "") or "")
                        
                    col_save, col_del = st.columns(2)
                    with col_save:
                        update_btn = st.form_submit_button("Änderungen speichern", type="primary")
                    with col_del:
                        delete_btn = st.form_submit_button("Kontakt löschen", type="secondary")
                        
                    if update_btn:
                        # Auch hier: Direkte Übergabe der Strings, kein "None" mehr.
                        update_daten = {
                            "vorname": e_vorname,
                            "nachname": e_nachname,
                            "kategorie": e_kategorie,
                            "telefon": e_telefon,
                            "fax": e_fax,
                            "email": e_email,
                            "adresse": e_adresse,
                            "zimmer": e_zimmer,
                            "erreichbarkeit": e_erreichbarkeit
                        }
                        try:
                            kontakt_aktualisieren(selected_kontakt.get("id"), update_daten)
                            st.session_state["adressbuch_msg"] = {"type": "success", "text": "Kontakt erfolgreich aktualisiert!"}
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Aktualisieren: {e}")
                            
                    if delete_btn:
                        try:
                            kontakt_loeschen(selected_kontakt.get("id"))
                            st.session_state["adressbuch_msg"] = {"type": "success", "text": "Kontakt erfolgreich gelöscht."}
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Löschen: {e}")
            else:
                st.info("Keine Kontakte zum Bearbeiten vorhanden.")
