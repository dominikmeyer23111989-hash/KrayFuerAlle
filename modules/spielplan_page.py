import streamlit as st
import darts_page  
import poker 
import mensch_aerger_dich_nicht
import kniffel
import bundesliga_tippspiel

def show():
    st.title("🎮 Vereins-Arcade & Spiele")
    st.write("Wähle einfach das gewünschte Spiel aus, um direkt loszulegen.")
    
    # Der Tab-Variable einen anderen Namen geben, um den Konflikt zu lösen
    tab_dart, tab_poker, tab_mensch_aerger_dich_nicht, tab_kniffel, tab_tipp = st.tabs([
        "🎯 Vereins-Dart", 
        "🃏 Vereins-Poker", 
        "👨‍👩‍👧‍👦 Mensch ärgere dich nicht", 
        "🎲 Kniffel", 
        "⚽ Bundesliga-Tippspiel"
    ])
    
    with tab_dart:
        darts_page.show()
        
    with tab_poker:
        poker.show()
        
    with tab_mensch_aerger_dich_nicht:
        mensch_aerger_dich_nicht.show()

    with tab_kniffel:
        kniffel.show()
        
    with tab_tipp:
        # Hier wird nun das Modul korrekt angesprochen
        bundesliga_tippspiel.show()