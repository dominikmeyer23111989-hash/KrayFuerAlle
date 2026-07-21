import streamlit as st
from datetime import date, datetime, timedelta
from modules.ausweis import (
    get_mitglied_daten,
    get_alle_mitglieder,
    foto_hochladen_dropbox,
    foto_herunterladen_dropbox,
    mitglied_ausweis_aktualisieren
)
import os

def render_ausweiskarte(m_data):
    """Hilfsfunktion zum Zeichnen der Ausweiskarte"""
    vorname = m_data.get('vorname', '')
    nachname = m_data.get('nachname', '')
    mitgliedsnummer = m_data.get('mitgliedsnummer', '---')
    gueltig_bis = m_data.get('gueltig_bis')
    ist_gesperrt = m_data.get('ist_gesperrt', False)
    foto_pfad = m_data.get('foto_pfad')
    
    # Prüfen, ob abgelaufen
    heute = date.today()
    ist_abgelaufen = True
    if gueltig_bis:
        if isinstance(gueltig_bis, str):
            g_datum = datetime.strptime(gueltig_bis, "%Y-%m-%d").date()
        else:
            g_datum = gueltig_bis
        if g_datum >= heute:
            ist_abgelaufen = False

    # Styling Box für den Ausweis
    border_color = '#ff4b4b' if ist_gesperrt or ist_abgelaufen else '#2ecc71'
    
    with st.container():
        # Äußerer Container für den Ausweis-Look
        with st.container():
            st.markdown(
                f"""
                <div style="border: 2px solid {border_color}; 
                            border-radius: 10px; padding: 15px; background-color: #0e1117; color: white; box-shadow: 2px 2px 10px rgba(0,0,0,0.5);">
                """,
                unsafe_allow_html=True
            )
            
            # Header mit größerem Vereinslogo und Titel
            col_logo, col_titel = st.columns([1, 3])
            with col_logo:
                if os.path.exists("KrayFürAlle.jpeg"):
                    st.image("KrayFürAlle.jpeg", width=90)
                else:
                    st.markdown("🏢")
            with col_titel:
                st.markdown("<h3 style='margin: 0; color: #f39c12; font-size: 20px;'>KrayFürAlle e.V.</h3>", unsafe_allow_html=True)
                st.markdown("<p style='font-size: 11px; color: gray; margin: 0;'>Offizieller Mitgliedsausweis</p>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 10px 0; border-color: #333;'>", unsafe_allow_html=True)
            
            col_foto, col_info = st.columns([1, 2])
            
            with col_foto:
                if foto_pfad:
                    img_bytes = foto_herunterladen_dropbox(foto_pfad)
                    if img_bytes:
                        st.image(img_bytes, width=110)
                    else:
                        st.info("📷 Kein Foto in Dropbox gefunden.")
                else:
                    st.info("📷 Kein Foto hochgeladen.")
                    
            with col_info:
                st.markdown(f"**Name:** {vorname} {nachname}")
                st.markdown(f"**Mitglieds-Nr:** {mitgliedsnummer}")
                
                # Statusanzeige
                if ist_gesperrt:
                    st.error("🚫 Ausweis GESPERRT")
                elif ist_abgelaufen:
                    st.warning("⚠️ Ausweis ABGELAUFEN")
                else:
                    st.success("✅ Ausweis GÜLTIG")
                    
                g_str = gueltig_bis if gueltig_bis else "Unbekannt"
                st.caption(f"Gültig bis: {g_str}")
                
            st.markdown("</div>", unsafe_allow_html=True)

def show():
    st.header("🪪 Mitgliedsausweis")
    
    user_id = st.session_state.get("user_id")
    user_rolle = st.session_state.get("user_rolle", "mitglied")
    is_leitung = user_rolle in ["admin", "administrator", "vorstand"]
    
    # Tabs für Leitung / Mitgliedertrennung oder Ansichten
    if is_leitung:
        tab_mein_ausweis, tab_alle_ausweise = st.tabs(["🪪 Mein Ausweis", "👥 Alle Ausweise & Verwaltung"])
    else:
        tab_mein_ausweis = st.container()
        tab_alle_ausweise = None

    # ==========================================
    # TAB 1: EIGENER AUSWEIS & FOTO UPLOAD
    # ==========================================
    with (tab_mein_ausweis if is_leitung else st.container()):
        st.subheader("Dein digitaler Ausweis")
        meine_daten = get_mitglied_daten(user_id)
        
        if meine_daten:
            render_ausweiskarte(meine_daten)
            
            st.divider()
            st.subheader("📤 Passbild hochladen / aktualisieren")
            with st.form("foto_upload_form"):
                neues_foto = st.file_uploader("Wähle ein Passfoto aus (JPG, PNG)", type=["jpg", "jpeg", "png"])
                submit_foto = st.form_submit_button("Foto hochladen")
                
                if submit_foto:
                    if neues_foto:
                        dateiname_eindeutig = f"mitglied_{user_id}_{int(datetime.now().timestamp())}_{neues_foto.name}"
                        erfolg, msg = foto_hochladen_dropbox(neues_foto.getvalue(), dateiname_eindeutig)
                        
                        if erfolg:
                            mitglied_ausweis_aktualisieren(user_id, {"foto_pfad": msg})
                            st.success("Passfoto erfolgreich in Dropbox gespeichert!")
                            st.rerun()
                        else:
                            st.error(f"Fehler: {msg}")
                    else:
                        st.warning("Bitte wähle zuerst eine Bilddatei aus.")

    # ==========================================
    # TAB 2: ALLE AUSWEISE VERWALTEN (Nur Vorstand/Admin)
    # ==========================================
    if is_leitung and tab_alle_ausweise:
        with tab_alle_ausweise:
            st.subheader("Verwaltung aller Mitgliedsausweise")
            mitglieder_liste = get_alle_mitglieder()
            
            if mitglieder_liste:
                suche = st.text_input("🔍 Mitglied suchen (Name oder Nummer)...")
                
                for m in mitglieder_liste:
                    name_komplett = f"{m.get('vorname', '')} {m.get('nachname', '')} {m.get('mitgliedsnummer', '')}".lower()
                    if suche and suche.lower() not in name_komplett:
                        continue
                        
                    with st.expander(f"🪪 {m.get('vorname')} {m.get('nachname')} (Nr: {m.get('mitgliedsnummer', '-')})"):
                        col_card, col_actions = st.columns([1, 1])
                        
                        with col_card:
                            render_ausweiskarte(m)
                            
                        with col_actions:
                            st.markdown("### Verwaltungs-Aktionen")
                            m_id = m.get("id")
                            
                            # 1. Gültigkeit verlängern (+ 1 Jahr)
                            if st.button("📅 Um 1 Jahr verlängern", key=f"verlaengern_{m_id}"):
                                aktuelles_gueltig = m.get("gueltig_bis")
                                basis_datum = date.today()
                                if aktuelles_gueltig:
                                    try:
                                        parsed = datetime.strptime(str(aktuelles_gueltig), "%Y-%m-%d").date()
                                        if parsed > basis_datum:
                                            basis_datum = parsed
                                    except:
                                        pass
                                neues_gueltig = basis_datum + timedelta(days=365)
                                mitglied_ausweis_aktualisieren(m_id, {"gueltig_bis": neues_gueltig.strftime("%Y-%m-%d")})
                                st.success(f"Gültigkeit bis zum {neues_gueltig.strftime('%d.%m.%Y')} verlängert!")
                                st.rerun()
                                
                            # 2. Sperren / Entsperren
                            ist_gesperrt = m.get("ist_gesperrt", False)
                            if ist_gesperrt:
                                if st.button("✅ Ausweis entsperren", key=f"entsperren_{m_id}", type="primary"):
                                    mitglied_ausweis_aktualisieren(m_id, {"ist_gesperrt": False})
                                    st.success("Ausweis entsperrt.")
                                    st.rerun()
                            else:
                                if st.button("🚫 Ausweis sperren", key=f"sperren_{m_id}", type="secondary"):
                                    mitglied_ausweis_aktualisieren(m_id, {"ist_gesperrt": True})
                                    st.warning("Ausweis wurde gesperrt.")
                                    st.rerun()
                                    
                            # 3. Foto zurücksetzen / löschen
                            if m.get("foto_pfad"):
                                if st.button("🗑️ Foto löschen", key=f"delfoto_{m_id}"):
                                    mitglied_ausweis_aktualisieren(m_id, {"foto_pfad": None})
                                    st.success("Foto entfernt.")
                                    st.rerun()
            else:
                st.info("Keine Mitglieder gefunden.")