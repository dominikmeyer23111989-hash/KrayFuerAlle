import streamlit as st
from modules.adressbuch import (
    get_alle_kontakte,
    kontakt_hinzufuegen,
    kontakt_aktualisieren,
    kontakt_loeschen
)

def show():
    st.header("📇 Vereins-Adressbuch")
    
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
                            "Nachname": k.get("nachname"),
                            "Vorname": k.get("vorname", "-"),
                            "Kategorie": k.get("kategorie", "-"),
                            "Telefon": k.get("telefon", "-"),
                            "E-Mail": k.get("email", "-"),
                            "Adresse": k.get("adresse", "-"),
                            "Zimmer": k.get("zimmer", "-"),
                            "Erreichbarkeit": k.get("erreichbarkeit", "-"),
                            "Fax": k.get("fax", "-")
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
            
            with st.form("neuer_kontakt_form"):
                col1, col2 = st.columns(2)
                with col1:
                    vorname = st.text_input("Vorname")
                    nachname = st.text_input("Nachname *")
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
                    if not nachname:
                        st.error("Der Nachname ist ein Pflichtfeld.")
                    else:
                        neuer_eintrag = {
                            "vorname": vorname if vorname else None,
                            "nachname": nachname,
                            "kategorie": kategorie if kategorie else None,
                            "telefon": telefon if telefon else None,
                            "fax": fax if fax else None,
                            "email": email if email else None,
                            "adresse": adresse if adresse else None,
                            "zimmer": zimmer if zimmer else None,
                            "erreichbarkeit": erreichbarkeit if erreichbarkeit else None
                        }
                        try:
                            kontakt_hinzufuegen(neuer_eintrag)
                            st.success(f"Kontakt '{nachname}' erfolgreich hinzugefügt!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Speichern: {e}")

    # ==========================================
    # 3. KONTAKT BEARBEITEN / LÖSCHEN
    # ==========================================
    if tab_bearbeiten is not None:
        with tab_bearbeiten:
            st.subheader("Bestehenden Kontakt bearbeiten oder löschen")
            kontakte = get_alle_kontakte()
            
            if kontakte:
                kontakt_dict = {f"{k.get('nachname')}, {k.get('vorname', '')} (Kat: {k.get('kategorie', 'k.A.')}) - ID: {k.get('id')}": k for k in kontakte}
                auswahl = st.selectbox("Kontakt auswählen", options=list(kontakt_dict.keys()))
                selected_kontakt = kontakt_dict[auswahl]
                
                with st.form("edit_kontakt_form"):
                    e_vorname = st.text_input("Vorname", value=selected_kontakt.get("vorname", "") or "")
                    e_nachname = st.text_input("Nachname *", value=selected_kontakt.get("nachname", ""))
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
                        if not e_nachname:
                            st.error("Nachname ist ein Pflichtfeld.")
                        else:
                            update_daten = {
                                "vorname": e_vorname if e_vorname else None,
                                "nachname": e_nachname,
                                "kategorie": e_kategorie if e_kategorie else None,
                                "telefon": e_telefon if e_telefon else None,
                                "fax": e_fax if e_fax else None,
                                "email": e_email if e_email else None,
                                "adresse": e_adresse if e_adresse else None,
                                "zimmer": e_zimmer if e_zimmer else None,
                                "erreichbarkeit": e_erreichbarkeit if e_erreichbarkeit else None
                            }
                            try:
                                kontakt_aktualisieren(selected_kontakt.get("id"), update_daten)
                                st.success("Kontakt erfolgreich aktualisiert!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Aktualisieren: {e}")
                                
                    if delete_btn:
                        try:
                            kontakt_loeschen(selected_kontakt.get("id"))
                            st.success("Kontakt erfolgreich gelöscht.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Löschen: {e}")
            else:
                st.info("Keine Kontakte zum Bearbeiten vorhanden.")