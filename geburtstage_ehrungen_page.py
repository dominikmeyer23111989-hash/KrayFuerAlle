import streamlit as st
import dropbox
from dropbox.exceptions import ApiError
from datetime import datetime
from modules.ehrungen_geburtstage import (
    get_mitglieder_geburtstage, 
    get_alle_ehrungen, 
    ehrung_erstellen, 
    ehrung_loeschen,
    generiere_ehrungen_pdf
)
from modules.events import get_alle_mitglieder, safe_val
from modules.inventar import formatiere_datum_fuer_anzeige

def upload_to_dropbox(file_obj, file_name):
    """Lädt eine Datei direkt in deine Dropbox hoch und gibt den Freigabe-Link zurück."""
    # Token aus den Streamlit-Secrets (oder Fallback direkt hier)
    token = st.secrets.get("DROPBOX_ACCESS_TOKEN", "sl.u.AGquFDbqPVy16K9Gk91VSsboQ5u86C5zpMGNYk6Y34Z4jNgkWV7g6QKW-tNwaaSuMyxO6n-y4jn4Z-JKU2a-aqdUKWiBFhMbSnqspDf3QwGv4E2ymTJkmXNddpA1q9NchBXSiTwdrg-0jED3b_hGZTdYNBUkQmVm_TtwEsdmOR2HXnGNimyMeg8EMW9EsEKN3cAnB3JsEi3iHhoxS1oQT7taxccu5QPWUT_D50e21g-vFDTkjTwa2T8Y7RwMcw2woaFBgTVIVMH-9yk2aij8JBqhofHKwOYGvZfjHHCoVasqZd6o2O3aZKgaHI85cBdeOvkUgJTV4lWYS4vf5b4w6CtMAyFK2ASoq9o0T9fz7JCoKZW7jiLennD12sslVmWvxNpCPAuVgXSlvnpZ6rRud_JKZ3XLzPOKjpfzKGRZVGEMRtBCcUZpkn21hpVKkbFY34Su7wfAq7PZjQgQUQmdSgwenhsiBm1xcpQbT5uj7x23JtAMEEVj5kZPvkKlKUAGBxduvH6RPAO_d6K5NfJ2sTtSCZG0d1mUACrwaZKA7BVZlFSYiNSpaanuLNruOpyh_Vda1X_efWk4-ivgmZErYkBEynl9uPSn7XU1DyLfZuTjDS0wjLQRtK3Esw1v38WX2ijKvs75K0wkTR2Khpt6p2VRLV8y1xL3sB7V3sD85R4GMX-Th4TngOkjhO0olkJQb6YSNPPktrqGoEPpcR-F_4-08HRa46FJLatwpNRH-bCYUeElVi0DUV_erUSNOSZ_Oa8bDrrX-K3pFgFY97bO5b78eRc7qtYP-372ZzYZhJa_qk2W4WDVh8JM6e9fG1OoclIfHlr6lGmMaF-zpLYn0q60lo-83z56M-jVh7y9IFtCb42LAjsOTYUj0H6LseoOvHi2hIqRNm2qwSQulCis7vcmD-ui7xhT8mv1v2yyNTITPcP33x9ZhQqqxgNIIjBSFADC0ycs_VbcJqlMmlbSD8kOaYjqXdslfr3ELKEjYUJ312vEnlp-CQe5T1-uFxHY405tkRq7rlcs4Irv5mUvZiA6RHMEL8gRpI8DPVj_0jsynfKQaGRHL83YUQYQtT1IkqUUSo3_LGpovy-wDI8dtW_RT2BT5cKanjCX5-9G14HakcPpZQqgHTaYm6BM7-wr-DgI3GUeytrohLgsrqMDn-6qOBkDTVoPCvy33MFAU5KV1r963II78RVcwKpVzxVuB97gokky4o7T_knY-jg3_ruOq0NdJqXHkgBp16QztIMZ8OlRtiaOQ57DvPeVDDnO_GbcSJkOliRtvYgUoCf2KgjXDh4LUdrieF-CrjT4HNk6YFX8-xhtbG2Gjs87_o4k1U9vJW4LaRj6LSc8AD1MsLRw51DSuOw_dHWAGk8I5rrD16j-euREP-vU8l5cRgoQuRSARghqAnefJkBDAWdOfauwWdDSXzozxCte21IhZok01f4h5cpOFbqeJv6df4QAGbo")
    dbx = dropbox.Dropbox(token)
    
    path = f"/KrayFuerAlle_Urkunden/{file_name}"
    
    try:
        dbx.files_upload(file_obj, path, mode=dropbox.files.WriteMode.overwrite)
        try:
            shared_link = dbx.sharing_create_shared_link_with_settings(path)
            url = shared_link.url
        except ApiError:
            links = dbx.sharing_get_shared_link_metadata(path)
            url = links.url
            
        # Auf Direkt-Ansicht umschreiben (?dl=0 -> ?raw=1)
        url = url.replace("?dl=0", "?raw=1")
        return url
    except Exception as e:
        st.error(f"Fehler beim Dropbox-Upload: {e}")
        return None

def show():
    st.header("🎂 Geburtstage & 🏆 Ehrungen")
    
    is_admin_or_vorstand = st.session_state.get("user_rolle", "").lower() in ["admin", "administrator", "vorstand"]
    
    tab_geburtstage, tab_ehrungen = st.tabs(["🎁 Geburtstagsliste", "🏆 Ehrungen & Jubiläen"])
    
    # ==========================================
    # 1. GEBURTSTAGE
    # ==========================================
    with tab_geburtstage:
        st.subheader("Anstehende Geburtstage")
        geburtstage = get_mitglieder_geburtstage()
        
        if geburtstage:
            geb_anzeige = []
            for g in geburtstage:
                geb_anzeige.append({
                    "Mitglied": g["name"],
                    "Geburtstag": g["geburtsdatum"],
                    "Wird alt": f"{g['alter_wird']} Jahre",
                    "Tage bis dahin": f"in {g['tage_bis']} Tagen" if g['tage_bis'] > 0 else "HEUTE! 🎈"
                })
            st.dataframe(geb_anzeige, use_container_width=True, hide_index=True)
        else:
            st.info("Keine Geburtsdaten in den Stammdaten hinterlegt. (Bitte in der Mitgliederverwaltung ergänzen).")

    # ==========================================
    # 2. EHRUNGEN
    # ==========================================
    with tab_ehrungen:
        st.subheader("Verwaltung von Ehrungen & Jubiläen")
        
        ehrungen = get_alle_ehrungen()
        if ehrungen:
            st.markdown("**Aktuelle Ehrungsliste:**")
            e_anzeige = []
            for e in ehrungen:
                m = safe_val(e, 'mitglieder', {})
                m_name = f"{safe_val(m, 'vorname')} {safe_val(m, 'nachname')}".strip() or "-"
                e_anzeige.append({
                    "ID": safe_val(e, "id"),
                    "Mitglied": m_name,
                    "Anlass": safe_val(e, "anlass"),
                    "Jahre": f"{safe_val(e, 'jahre')} Jahre",
                    "Datum": formatiere_datum_fuer_anzeige(safe_val(e, "ehrungs_datum")),
                    "Status": safe_val(e, "status"),
                    "Urkunde": "Vorhanden" if safe_val(e, "dokument_url") else "-"
                })
            st.dataframe(e_anzeige, use_container_width=True, hide_index=True)
            
            # PDF Export für Ehrungsliste
            try:
                pdf_bytes = generiere_ehrungen_pdf(ehrungen)
                st.download_button(
                    label="📥 Ehrungsliste als PDF herunterladen",
                    data=pdf_bytes,
                    file_name=f"Ehrungen_Uebersicht_{datetime.now().strftime('%Y-%m-%d')}.pdf",
                    mime="application/pdf",
                    key="pdf_ehrungen_btn"
                )
            except Exception as pdf_err:
                st.error(f"Fehler beim Erstellen des PDF-Buttons: {pdf_err}")
                
            st.divider()
            
            # Urkunden Download / Einsicht für bestehende Ehrungen
            st.markdown("#### 📂 Urkunde ansehen / herunterladen")
            ehrungen_mit_dok = [e for e in ehrungen if safe_val(e, "dokument_url")]
            if ehrungen_mit_dok:
                dok_dict = {f"{safe_val(e, 'anlass')} ({e.get('jahre')} Jahre) - {safe_val(e, 'mitglieder', {}).get('nachname', '')}": safe_val(e, "dokument_url") for e in ehrungen_mit_dok}
                w_dok = st.selectbox("Ehrung / Urkunde auswählen", options=list(dok_dict.keys()))
                if w_dok:
                    url = dok_dict[w_dok]
                    st.markdown(f"🔗 [Direkter Link zur Urkunde in Dropbox öffnen]({url})", unsafe_allow_html=True)
            else:
                st.info("Bisher sind keine Urkunden hinterlegt worden.")
            
            if is_admin_or_vorstand:
                st.divider()
                e_ids = [safe_val(e, "id") for e in ehrungen]
                del_e_id = st.selectbox("Ehrung zum Löschen auswählen (ID)", options=[None] + e_ids)
                if del_e_id and st.button("Ausgewählte Ehrung löschen"):
                    try:
                        ehrung_loeschen(del_e_id)
                        st.success("Ehrung entfernt!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Fehler: {err}")
        else:
            st.info("Bisher keine Ehrungen eingetragen.")
            
        if is_admin_or_vorstand:
            st.divider()
            st.markdown("#### Neue Ehrung / Jubiläum eintragen & Urkunde hochladen")
            mitglieder = get_alle_mitglieder()
            
            if mitglieder:
                mitglied_dict = {f"{safe_val(m, 'vorname')} {safe_val(m, 'nachname')} ({safe_val(m, 'rolle', 'Mitglied')})": safe_val(m, 'id') for m in mitglieder}
                
                with st.form("neue_ehrung_form"):
                    w_mitglied = st.selectbox("Mitglied auswählen", options=list(mitglied_dict.keys()))
                    anlass = st.text_input("Anlass / Art der Ehrung (z.B. Treue Mitgliedschaft, Aktiver Dienst) *", value="Mitgliedschaft")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        jahre = st.number_input("Jahre (flexibel wählbar)", min_value=1, max_value=100, value=10)
                    with col2:
                        ehrungs_datum = st.date_input("Datum der Ehrung", value=datetime.today())
                        
                    status = st.selectbox("Status", ["Geplant", "Durchgeführt", "Ausstehend"])
                    bemerkung = st.text_area("Bemerkung / Laudatio Stichpunkte (optional)")
                    
                    uploaded_file = st.file_uploader("Urkunde / Dokument hochladen (PDF, JPG, PNG)", type=["pdf", "png", "jpg", "jpeg"])
                    
                    sub = st.form_submit_button("Ehrung speichern", type="primary")
                    if sub:
                        if not anlass:
                            st.error("Bitte einen Anlass angeben.")
                        else:
                            dok_url = None
                            if uploaded_file is not None:
                                with st.spinner("Lade Datei in Dropbox hoch..."):
                                    file_name = f"{int(datetime.timestamp(datetime.now()))}_{uploaded_file.name}"
                                    dok_url = upload_to_dropbox(uploaded_file.getvalue(), file_name)
                                    
                            daten = {
                                "mitglied_id": mitglied_dict[w_mitglied],
                                "anlass": anlass,
                                "jahre": int(jahre),
                                "ehrungs_datum": ehrungs_datum.strftime("%Y-%m-%d"),
                                "status": status,
                                "bemerkung": bemerkung if bemerkung else None,
                                "dokument_url": dok_url
                            }
                            try:
                                ehrung_erstellen(daten)
                                st.success("Ehrung und Urkunde erfolgreich in Dropbox & Datenbank gespeichert!")
                                st.rerun()
                            except Exception as err:
                                st.error(f"Fehler beim Speichern: {err}")
            else:
                st.warning("Keine Mitglieder im System gefunden.")