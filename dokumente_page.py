import streamlit as st
from datetime import datetime
from modules.dokumente import (
    get_dokumente,
    dokument_hochladen_dropbox,
    dokument_loeschen_dropbox,
    datei_herunterladen_dropbox,
    dokument_db_eintragen,
    dokument_db_loeschen
)

def show():
    st.header("📁 Vereins-Dokumente")
    st.caption("Dateien werden sicher in deiner Dropbox gespeichert, um Supabase zu entlasten.")
    
    user_id = st.session_state.get("user_id")
    user_rolle = st.session_state.get("user_rolle", "mitglied")
    is_leitung = user_rolle in ["admin", "administrator", "vorstand"]
    
    # Tabs definieren
    if is_leitung:
        tab_oeffentlich, tab_vorstand, tab_upload = st.tabs([
            "📂 Öffentliche Dokumente", 
            "🔒 Vorstandsdokumente", 
            "📤 Dokument hochladen"
        ])
    else:
        tab_oeffentlich = st.container()
        tab_vorstand = None
        tab_upload = None

    # ==========================================
    # HELFER-FUNKTION FÜR DIE ANZEIGE & AKTIONEN
    # ==========================================
    def dokumente_liste_rendern(docs_data, bereich_name):
        if docs_data:
            for doc in docs_data:
                with st.expander(f"📄 {doc.get('titel')}"):
                    st.write(f"**Beschreibung:** {doc.get('beschreibung', 'Keine Beschreibung')}")
                    
                    hochgeladen_am = str(doc.get('created_at'))[:10] if doc.get('created_at') else '-'
                    m_info = doc.get('mitglieder')
                    hochgeladen_von_name = f"{m_info.get('vorname', '')} {m_info.get('nachname', '')}" if m_info else "Unbekannt"
                    
                    st.caption(f"Hochgeladen am {hochgeladen_am} von {hochgeladen_von_name}")
                    
                    # Download aus Dropbox
                    dateipfad = doc.get("dateipfad")
                    if dateipfad:
                        file_bytes = datei_herunterladen_dropbox(dateipfad)
                        if file_bytes:
                            st.download_button(
                                label="📥 Datei herunterladen",
                                data=file_bytes,
                                file_name=dateipfad.split("_", 1)[-1] if "_" in dateipfad else dateipfad,
                                key=f"dl_{bereich_name}_{doc.get('id')}"
                            )
                        else:
                            st.warning("⚠️ Datei konnte nicht aus der Dropbox geladen werden (möglicherweise wurde sie dort gelöscht).")
                            
                    # Löschen (Nur Vorstand/Admin)
                    if is_leitung:
                        if st.button("🗑️ Dokument endgültig löschen", key=f"del_{bereich_name}_{doc.get('id')}", type="secondary"):
                            # 1. Aus Dropbox löschen
                            erfolg_dbx = dokument_loeschen_dropbox(dateipfad)
                            # 2. Aus Supabase DB löschen
                            dokument_db_loeschen(doc.get("id"))
                            
                            if erfolg_dbx:
                                st.success("Dokument erfolgreich aus Dropbox und Datenbank gelöscht!")
                            else:
                                st.warning("Eintrag aus Datenbank gelöscht, aber Datei war evtl. nicht mehr in Dropbox.")
                            st.rerun()
        else:
            st.info("Keine Dokumente in diesem Bereich vorhanden.")

    # ==========================================
    # TAB 1: ÖFFENTLICHE DOKUMENTE
    # ==========================================
    if not is_leitung:
        st.subheader("Öffentliche Dokumente")
        
    with (tab_oeffentlich if is_leitung else st.container()):
        if is_leitung:
            st.subheader("Öffentliche Dokumente (für alle Mitglieder sichtbare Dateien)")
        oeffentliche_docs = get_dokumente(bereich="oeffentlich")
        dokumente_liste_rendern(oeffentliche_docs, "oeffentlich")

    # ==========================================
    # TAB 2: VORSTANDSDOKUMENTE
    # ==========================================
    if is_leitung and tab_vorstand:
        with tab_vorstand:
            st.subheader("🔒 Interne Vorstandsdokumente")
            vorstands_docs = get_dokumente(bereich="vorstand")
            dokumente_liste_rendern(vorstands_docs, "vorstand")

    # ==========================================
    # TAB 3: UPLOAD
    # ==========================================
    if is_leitung and tab_upload:
        with tab_upload:
            st.subheader("Neues Dokument hochladen")
            
            with st.form("upload_form"):
                titel = st.text_input("Dokumententitel *")
                beschreibung = st.text_area("Beschreibung (optional)")
                bereich = st.selectbox(
                    "Sichtbarkeit / Bereich",
                    options=["oeffentlich", "vorstand"],
                    format_func=lambda x: "🌐 Öffentlicher Bereich (Alle Mitglieder)" if x == "oeffentlich" else "🔒 Nur Vorstand / Admin"
                )
                hochgeladene_datei = st.file_uploader("Datei auswählen *")
                
                submit_btn = st.form_submit_button("Hochladen", type="primary")
                
                if submit_btn:
                    if not titel or not hochgeladene_datei:
                        st.error("Bitte gib mindestens einen Titel an und wähle eine Datei aus.")
                    else:
                        dateiname_eindeutig = f"{int(datetime.now().timestamp())}_{hochgeladene_datei.name}"
                        datei_bytes = hochgeladene_datei.getvalue()
                        
                        # Upload zu Dropbox
                        erfolg_storage, msg = dokument_hochladen_dropbox(datei_bytes, dateiname_eindeutig)
                        
                        if erfolg_storage:
                            try:
                                db_daten = {
                                    "titel": titel,
                                    "beschreibung": beschreibung if beschreibung else None,
                                    "dateipfad": dateiname_eindeutig,
                                    "bereich": bereich,
                                    "hochgeladen_von": user_id
                                }
                                dokument_db_eintragen(db_daten)
                                st.success("Dokument erfolgreich in Dropbox hochgeladen und in der Datenbank gespeichert!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Speichern der Metadaten in Supabase: {e}")
                        else:
                            st.error(f"Fehler beim Dropbox-Upload: {msg}")