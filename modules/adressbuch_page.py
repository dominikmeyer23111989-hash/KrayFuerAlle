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

    # 1. KONTAKTE-LISTE
    with tab_liste:
        kontakte = get_alle_kontakte()
        if kontakte:
            suchbegriff = st.text_input("🔍 Suche (Name, Kat, Ort...)", key="ab_suche")
            
            # Robustere Suche: Wir joinen alle Werte, die nicht None sind
            gefilterte_kontakte = []
            for k in kontakte:
                such_text = " ".join([str(v) for v in k.values() if v is not None]).lower()
                if not suchbegriff or suchbegriff.lower() in such_text:
                    gefilterte_kontakte.append(k)
            
            st.metric("Gefundene Kontakte", len(gefilterte_kontakte))
            # Optional: Die DataFrame-Ansicht zeigen
            st.dataframe(gefilterte_kontakte, use_container_width=True, hide_index=True)
        else:
            st.info("Keine Kontakte gefunden.")

    # 2. NEUEN KONTAKT ANLEGEN
    if tab_neu:
        with tab_neu:
            with st.form("neuer_kontakt_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                vorname = col1.text_input("Vorname")
                nachname = col2.text_input("Nachname")
                kategorie = col1.text_input("Kategorie")
                telefon = col2.text_input("Telefonnummer")
                email = col1.text_input("E-Mail-Adresse")
                adresse = col2.text_input("Adresse")
                
                submitted = st.form_submit_button("Kontakt speichern", type="primary")
                if submitted:
                    neuer_eintrag = {
                        "vorname": vorname if vorname else None,
                        "nachname": nachname if nachname else None,
                        "kategorie": kategorie if kategorie else None,
                        "telefon": telefon if telefon else None,
                        "email": email if email else None,
                        "adresse": adresse if adresse else None
                    }
                    try:
                        kontakt_hinzufuegen(neuer_eintrag)
                        st.session_state["adressbuch_msg"] = {"type": "success", "text": "Erfolgreich hinzugefügt!"}
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")

    # 3. KONTAKT BEARBEITEN / LÖSCHEN
    if tab_bearbeiten:
        with tab_bearbeiten:
            kontakte = get_alle_kontakte()
            if kontakte:
                kontakt_dict = {f"{k.get('nachname')}, {k.get('vorname')} (ID: {k.get('id')})": k for k in kontakte}
                auswahl = st.selectbox("Kontakt auswählen", options=list(kontakt_dict.keys()))
                sel = kontakt_dict[auswahl]
                
                with st.form("edit_form"):
                    e_vorname = st.text_input("Vorname", value=sel.get("vorname") or "")
                    e_nachname = st.text_input("Nachname", value=sel.get("nachname") or "")
                    # ... (weitere Felder wie gehabt)
                    
                    # Sicherheits-Checkbox zum Löschen
                    loesch_check = st.checkbox("⚠️ Ich möchte diesen Kontakt wirklich unwiderruflich löschen.")
                    
                    col_s, col_d = st.columns(2)
                    update_btn = col_s.form_submit_button("Änderungen speichern")
                    delete_btn = col_d.form_submit_button("Kontakt löschen", type="primary")
                    
                    if update_btn:
                        kontakt_aktualisieren(sel.get("id"), {"vorname": e_vorname, "nachname": e_nachname})
                        st.session_state["adressbuch_msg"] = {"type": "success", "text": "Aktualisiert!"}
                        st.rerun()
                    
                    if delete_btn:
                        if loesch_check:
                            kontakt_loeschen(sel.get("id"))
                            st.session_state["adressbuch_msg"] = {"type": "success", "text": "Gelöscht."}
                            st.rerun()
                        else:
                            st.warning("Bitte erst das Häkchen für die Bestätigung setzen.")
