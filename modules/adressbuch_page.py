import streamlit as st
from modules.adressbuch import (
    get_alle_kontakte,
    kontakt_hinzufuegen,
    kontakt_aktualisieren,
    kontakt_loeschen
)

def show():
    st.header("📇 Vereins-Adressbuch")
    
    # Zentrale Nachrichten
    if "adressbuch_msg" in st.session_state:
        msg = st.session_state["adressbuch_msg"]
        if msg["type"] == "success":
            st.success(msg["text"])
        elif msg["type"] == "error":
            st.error(msg["text"])
        del st.session_state["adressbuch_msg"]
    
    is_admin_or_vorstand = st.session_state.get("user_rolle", "").lower() in ["admin", "administrator", "vorstand"]
    has_adressbuch_rights = st.session_state.get("hat_adressbuch_rechte", False)
    
    # Tabs definieren
    if is_admin_or_vorstand or has_adressbuch_rights:
        tab_liste, tab_neu, tab_bearbeiten = st.tabs([
            "📋 Kontakte-Liste", 
            "➕ Neuen Kontakt anlegen", 
            "⚙️ Kontakt bearbeiten / löschen"
        ])
    else:
        tab_liste = st.container()
        tab_neu, tab_bearbeiten = None, None

    # ==========================================
    # 1. KONTAKTE-LISTE (Ohne ID und created_at)
    # ==========================================
    with tab_liste:
        kontakte = get_alle_kontakte()
        if kontakte:
            suchbegriff = st.text_input("🔍 Suche (Name, Kat, Ort...)", key="ab_suche")
            
            gefilterte_kontakte = []
            for k in kontakte:
                # Suche über alle Werte des Eintrags
                such_text = " ".join([str(v) for v in k.values() if v is not None]).lower()
                if not suchbegriff or suchbegriff.lower() in such_text:
                    # Hier bauen wir das Dictionary für die Anzeige zusammen (OHNE id und created_at)
                    gefilterte_kontakte.append({
                        "Nachname": k.get("nachname") or "-",
                        "Vorname": k.get("vorname") or "-",
                        "Kategorie": k.get("kategorie") or "-",
                        "Telefon": k.get("telefon") or "-",
                        "E-Mail": k.get("email") or "-",
                        "Adresse": k.get("adresse") or "-",
                        "Zimmer": k.get("zimmer") or "-",
                        "Erreichbarkeit": k.get("erreichbarkeit") or "-",
                        "Fax": k.get("fax") or "-"
                    })
            
            st.metric("Gefundene Kontakte", len(gefilterte_kontakte))
            st.dataframe(gefilterte_kontakte, use_container_width=True, hide_index=True)
        else:
            st.info("Keine Kontakte im Adressbuch gefunden.")

    # ==========================================
    # 2. NEUEN KONTAKT ANLEGEN
    # ==========================================
    if tab_neu:
        with tab_neu:
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
                    neuer_eintrag = {
                        "vorname": vorname if vorname else None,
                        "nachname": nachname if nachname else None,
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
                        anzeige_name = f"{vorname or ''} {nachname or ''}".strip() or "Unbekannt"
                        st.session_state["adressbuch_msg"] = {"type": "success", "text": f"Kontakt '{anzeige_name}' erfolgreich hinzugefügt!"}
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Speichern: {e}")

    # ==========================================
    # 3. KONTAKT BEARBEITEN / LÖSCHEN
    # ==========================================
    if tab_bearbeiten:
        with tab_bearbeiten:
            kontakte = get_alle_kontakte()
            if kontakte:
                # Dropdown-Auswahl OHNE ID im Anzeigetext (die ID wird intern im Dictionary gemerkt)
                kontakt_dict = {f"{k.get('nachname', 'k.A.')}, {k.get('vorname', '')} (Kat: {k.get('kategorie', 'k.A.')})": k for k in kontakte}
                auswahl = st.selectbox("Kontakt für Bearbeitung auswählen", options=list(kontakt_dict.keys()))
                sel = kontakt_dict[auswahl]
                
                with st.form("edit_kontakt_form"):
                    e_vorname = st.text_input("Vorname", value=sel.get("vorname", "") or "")
                    e_nachname = st.text_input("Nachname", value=sel.get("nachname", "") or "")
                    e_kategorie = st.text_input("Kategorie", value=sel.get("kategorie", "") or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        e_telefon = st.text_input("Telefon", value=sel.get("telefon", "") or "")
                        e_fax = st.text_input("Fax", value=sel.get("fax", "") or "")
                        e_email = st.text_input("E-Mail", value=sel.get("email", "") or "")
                    with col2:
                        e_adresse = st.text_input("Adresse", value=sel.get("adresse", "") or "")
                        e_zimmer = st.text_input("Zimmer", value=sel.get("zimmer", "") or "")
                        e_erreichbarkeit = st.text_input("Erreichbarkeit", value=sel.get("erreichbarkeit", "") or "")
                    
                    st.markdown("---")
                    loesch_check = st.checkbox("⚠️ Ich möchte diesen Kontakt wirklich unwiderruflich löschen.")
                    
                    col_save, col_del = st.columns(2)
                    with col_save:
                        update_btn = st.form_submit_button("Änderungen speichern", type="primary")
                    with col_del:
                        delete_btn = st.form_submit_button("Kontakt löschen", type="secondary")
                        
                    if update_btn:
                        update_daten = {
                            "vorname": e_vorname if e_vorname else None,
                            "nachname": e_nachname if e_nachname else None,
                            "kategorie": e_kategorie if e_kategorie else None,
                            "telefon": e_telefon if e_telefon else None,
                            "fax": e_fax if e_fax else None,
                            "email": e_email if e_email else None,
                            "adresse": e_adresse if e_adresse else None,
                            "zimmer": e_zimmer if e_zimmer else None,
                            "erreichbarkeit": e_erreichbarkeit if e_erreichbarkeit else None
                        }
                        try:
                            kontakt_aktualisieren(sel.get("id"), update_daten)
                            st.session_state["adressbuch_msg"] = {"type": "success", "text": "Kontakt erfolgreich aktualisiert!"}
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Aktualisieren: {e}")
                            
                    if delete_btn:
                        if loesch_check:
                            try:
                                kontakt_loeschen(sel.get("id"))
                                st.session_state["adressbuch_msg"] = {"type": "success", "text": "Kontakt erfolgreich gelöscht."}
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Löschen: {e}")
                        else:
                            st.warning("Bitte erst das Häkchen für die Bestätigung setzen.")
            else:
                st.info("Keine Kontakte zum Bearbeiten vorhanden.")
