import streamlit as st
from database import supabase
from datetime import datetime

def show():
    st.title("🚀 Changelog & Neuigkeiten")
    st.caption("Hier siehst du alle Updates, Neuerungen und Verbesserungen, die am Portal vorgenommen wurden.")

    # Admin-Bereich zum Hinzufügen neuer Einträge
    user_rolle = st.session_state.get("user_rolle", "").lower()
    if user_rolle in ["admin", "administrator", "vorstand"]:
        with st.expander("➕ Neuen Changelog-Eintrag erstellen (Admin)"):
            with st.form("changelog_form"):
                kategorie = st.selectbox(
                    "Kategorie", 
                    ["Feature", "Bugfix", "Wartung", "Ankündigung", "Allgemein"]
                )
                t_input = st.text_input("Titel der Änderung", placeholder="z.B. Ankündigungs-Ticker hinzugefügt")
                b_input = st.text_area("Beschreibung", placeholder="Beschreibe, was neu ist, verbessert oder behoben wurde...")
                
                submit_btn = st.form_submit_button("Eintrag veröffentlichen", type="primary")
                if submit_btn:
                    if t_input and b_input:
                        try:
                            supabase.table("changelog").insert({
                                "kategorie": kategorie,
                                "titel": t_input.strip(),
                                "beschreibung": b_input.strip()
                            }).execute()
                            st.success("Changelog-Eintrag erfolgreich veröffentlicht!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Speichern: {e}")
                    else:
                        st.warning("Bitte Titel und Beschreibung ausfüllen.")
        st.divider()

    # Einträge aus Supabase laden
    try:
        res = supabase.table("changelog").select("*").order("erstellt_am", desc=True).execute()
        entries = res.data if res.data else []
    except Exception as e:
        st.error(f"Fehler beim Laden des Changelogs: {e}")
        entries = []

    if not entries:
        st.info("Bisher sind noch keine Changelog-Einträge vorhanden.")
        return

    # Einträge formatiert ausgeben
    for item in entries:
        datum_roh = item.get("erstellt_am", "")
        datum_formatiert = ""
        if datum_roh:
            try:
                dt = datetime.fromisoformat(datum_roh.replace("Z", "+00:00"))
                datum_formatiert = dt.strftime("%d.%m.%Y um %H:%M Uhr")
            except:
                datum_formatiert = datum_roh[:10]

        kategorie = item.get("kategorie", "Allgemein")
        titel = item.get("titel", "Update")
        beschreibung = item.get("beschreibung", "")

        # Farbliche Unterscheidung der Kategorien für das Badge
        bg_color = "#6c757d"  # Standard Grau
        if kategorie == "Feature":
            bg_color = "#28a745"  # Grün
        elif kategorie == "Bugfix":
            bg_color = "#dc3545"  # Rot
        elif kategorie == "Wartung":
            bg_color = "#fd7e14"  # Orange
        elif kategorie == "Ankündigung":
            bg_color = "#17a2b8"  # Blau

        with st.container():
            col_badge, col_title = st.columns([1, 6])
            with col_badge:
                st.markdown(f"<div style='background-color: {bg_color}; color: white; padding: 4px 8px; border-radius: 4px; text-align: center; font-weight: bold; font-size: 12px;'>{kategorie}</div>", unsafe_allow_html=True)
            with col_title:
                st.markdown(f"### {titel}")
            
            st.caption(f"Veröffentlicht am: {datum_formatiert}")
            st.write(beschreibung)
            st.markdown("---")