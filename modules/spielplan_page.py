import streamlit as st
import darts_page  
import poker 
import mensch_aerger_dich_nicht
import kniffel
import bundesliga_tippspiel

def show():
    st.title("🎮 Vereins-Arcade & Spiele")
    st.write("Wähle einfach das gewünschte Spiel aus, um direkt loszulegen.")
    
    # Tabs für die verschiedenen Spiele (wächst einfach mit, wenn neue hinzukommen)
    tab_dart, tab_poker, tab_mensch_aerger_dich_nicht, tab_kniffel, tab_bundesliga_tippspiel = st.tabs(["🎯 Vereins-Dart", "🃏 Vereins-Poker", "👨‍👩‍👧‍👦 Mensch ärgere dich nicht", "🎲 Kniffel", "⚽ Bundesliga-Tippspiel"])
    
    with tab_dart:
        # Hier wird der komplette Dart-Automat eingebunden
        darts_page.show()
        
    with tab_poker:
        # Hier wird der komplette Poker-Tisch eingebunden
        poker.show()
        
    with tab_mensch_aerger_dich_nicht:
        # Hier wird das komplette Mensch ärgere dich nicht-Spiel eingebunden
        mensch_aerger_dich_nicht.show()

    with tab_kniffel:
        # Hier wird das komplette Kniffel-Spiel eingebunden
        kniffel.show()
        
    with tab_bundesliga_tippspiel:
        # Hier wird das komplette Bundesliga-Tippspiel eingebunden
        bundesliga_tippspiel.show()