import streamlit as st
from datetime import datetime
from modules.chronik import get_chronik_eintraege, chronik_erstellen, chronik_loeschen

def show():
    st.markdown("""
        <style>
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            h1 { font-size: 1.4rem !important; }
            h2 { font-size: 1.2rem !important; }
            h3 { font-size: 1.1rem !important; }
        }
        </style>
    """, unsafe_allow_html=True)

    st.header("📜 Vereinschronik & Geschichte")
    st.caption("Blick auf die Meilensteine, Höhepunkte und die Historie unseres Vereins.")

    user_rolle = st.session_state.get("user_rolle", "").lower()
    ist_admin = user_rolle in ["admin", "administrator", "vorstand"]

    if ist_admin:
        tab_ansicht, tab_neu = st.tabs(["📖 Chronik ansehen", "➕ Eintrag hinzufügen"])
    else:
        tab_ansicht, tab_neu = st.tabs(["📖 Chronik ansehen", None])

    with tab_ansicht:
        st.subheader("Meilensteine unserer Vereinsgeschichte")
        eintraege = get_chronik_eintraege()

        if eintraege:
            for eintrag in eintraege:
                roh_datum = eintrag.get("datum")
                if roh_datum:
                    try:
                        formatiertes_datum = datetime.strptime(roh_datum, "%Y-%m-%d").strftime("%d.%m.%Y")
                    except:
                        formatiertes_datum = roh_datum
                else:
                    formatiertes_datum = "Unbekanntes Datum"

                kategorie = eintrag.get("kategorie", "Allgemein")
                titel = eintrag.get("titel", "Kein Titel")
                beschreibung = eintrag.get("beschreibung", "")

                with st.expander(f"📌 {formatiertes_datum} — {titel} [{kategorie}]"):
                    st.write(beschreibung)
                    
                    if ist_admin:
                        if st.button("🗑️ Eintrag löschen", key=f"del_chronik_{eintrag['id']}"):
                            try:
                                chronik_loeschen(eintrag['id'])
                                st.success("Eintrag gelöscht!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler beim Löschen: {e}")
        else:
            st.info("Bisher wurden noch keine Einträge in der Chronik hinterlegt.")

    if ist_admin and tab_neu:
        with tab_neu:
            st.subheader("Neuen Meilenstein eintragen")
            
            with st.form("chronik_form"):
                titel = st.text_input("Titel des Ereignisses * (z.B. 25-jähriges Jubiläum)")
                datum = st.date_input("Datum", value=datetime.today(), format="DD.MM.YYYY")
                kategorie = st.selectbox("Kategorie", [
                    "Gründung", "Meilenstein", "Sportlicher Erfolg", "Veranstaltung", "Umbau / Gelände", "Sonstiges"
                ])
                beschreibung = st.text_area("Beschreibung / Geschichte *", placeholder="Erzähle die Geschichte zu diesem Ereignis...")
                erstellt_von = st.session_state.get("vorname", "Vorstand")

                submitted = st.form_submit_button("In Chronik speichern", type="primary", use_container_width=True)

                if submitted:
                    if not titel or not beschreibung:
                        st.error("Bitte fülle mindestens Titel und Beschreibung aus!")
                    else:
                        neuer_eintrag = {
                            "titel": titel.strip(),
                            "datum": datum.strftime("%Y-%m-%d"),
                            "kategorie": kategorie,
                            "beschreibung": beschreibung.strip(),
                            "erstellt_von": erstellt_von
                        }
                        try:
                            chronik_erstellen(neuer_eintrag)
                            st.success("Erfolgreich zur Chronik hinzugefügt! 🎉")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Speichern: {e}")