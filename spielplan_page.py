import streamlit as st
import darts_page  
import poker 
import mensch_aerger_dich_nicht

def show():
    st.title("🎮 Vereins-Arcade & Spiele")
    st.write("Wähle einfach das gewünschte Spiel aus, um direkt loszulegen.")
    
    # Tabs für die verschiedenen Spiele (wächst einfach mit, wenn neue hinzukommen)
    tab_dart, tab_poker, tab_mensch_aerger_dich_nicht, tab_spiel2 = st.tabs(["🎯 Vereins-Dart", "🃏 Vereins-Poker", "👨‍👩‍👧‍👦 Mensch ärgere dich nicht", "🎲 [Zukünftiges Spiel]"])
    
    with tab_dart:
        # Hier wird der komplette Dart-Automat eingebunden
        darts_page.show()
        
    with tab_poker:
        # Hier wird der komplette Poker-Tisch eingebunden
        poker.show()
        
    with tab_mensch_aerger_dich_nicht:
        # Hier wird das komplette Mensch ärgere dich nicht-Spiel eingebunden
        mensch_aerger_dich_nicht.show()

    with tab_spiel2:
        st.subheader("Demnächst verfügbar")
        st.info("Hier kannst du später ein weiteres Minispiel (z. B. Billard, Kicker-Counter oder Kniffel) integrieren.")