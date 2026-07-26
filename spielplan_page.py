import streamlit as st

def show():
    st.title("🎮 Spielplan & Kommende Spiele")
    st.write("Hier sammeln wir alle kommenden Spiele. Dieser Bereich wird nach und nach erweitert.")
    
    st.info("Bereich im Aufbau. Du kannst hier bald alle Spiele eintragen und verwalten.")
    
    # Beispiel-Struktur für deine Spiele
    with st.expander("➕ Spiel hinzufügen (Entwurf)"):
        titel = st.text_input("Spiel-Titel / Begegnung")
        datum = st.date_input("Datum des Spiels")
        notiz = st.text_area("Notizen / Details")
        if st.button("Speichern"):
            if titel:
                st.success(f"Spiel '{titel}' vorgemerkt!")
            else:
                st.warning("Bitte gib einen Titel ein.")