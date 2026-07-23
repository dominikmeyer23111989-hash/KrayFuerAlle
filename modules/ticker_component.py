import streamlit as st
from database import supabase

def zeige_ticker():
    # Prüfen, ob der Nutzer den Ticker in dieser Sitzung weggeklickt hat
    if "ticker_geschlossen" not in st.session_state:
        st.session_state.ticker_geschlossen = False

    # Wenn geschlossen, zeigen wir einen kleinen unauffälligen Button zum Wiederöffnen
    if st.session_state.ticker_geschlossen:
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        col_dummy, col_btn = st.columns([10, 2])
        with col_btn:
            if st.button("📢 Ankündigung anzeigen", key="reopen_ticker", use_container_width=True):
                st.session_state.ticker_geschlossen = False
                st.rerun()
        return

    # Aktuellen Ticker aus Supabase laden
    try:
        res = supabase.table("ticker").select("*").order("erstellt_am", desc=True).limit(1).execute()
        data = res.data if res.data else []
    except Exception:
        data = []

    if data:
        ticker_text = data[0].get("text", "")
        if ticker_text.strip():
            st.markdown("---")
            # Layout für Ticker-Banner und Schließen-Button (nutzt CSS-Variablen für perfekten Dark/Light-Mode Kontrast)
            col_text, col_close = st.columns([22, 1])
            with col_text:
                st.markdown(f"""
                    <div style="background-color: var(--secondary-background-color); color: var(--text-color); padding: 10px 15px; border-radius: 8px; border-left: 6px solid #ff4b4b; font-size: 14px; border: 1px solid rgba(128, 128, 128, 0.2);">
                        <b>📢 Wichtige Ankündigung des Vorstands:</b> {ticker_text}
                    </div>
                """, unsafe_allow_html=True)
            with col_close:
                if st.button("❌", key="close_ticker_btn", help="Ticker für diese Sitzung ausblenden"):
                    st.session_state.ticker_geschlossen = True
                    st.rerun()

def admin_ticker_bereich():
    user_rolle = st.session_state.get("user_rolle", "").lower()
    if user_rolle in ["admin", "administrator", "vorstand"]:
        with st.expander("📢 Ankündigung / Ticker verwalten (Admin)"):
            # Aktuellen Text laden
            akt_text = ""
            try:
                res = supabase.table("ticker").select("*").order("erstellt_am", desc=True).limit(1).execute()
                if res.data:
                    akt_text = res.data[0].get("text", "")
            except:
                pass

            new_text = st.text_area("Ankündigungstext für alle Mitglieder:", value=akt_text, placeholder="Trage hier eine Nachricht ein (leer lassen zum Löschen)...")
            
            if st.button("Ankündigung speichern", type="primary"):
                if new_text.strip():
                    try:
                        supabase.table("ticker").insert({"text": new_text.strip()}).execute()
                        st.success("Ankündigung erfolgreich aktualisiert!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")
                else:
                    try:
                        supabase.table("ticker").insert({"text": ""}).execute()
                        st.success("Ankündigung gelöscht.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")