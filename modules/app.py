import streamlit as st
from database import supabase
from modules.auth import (
    login_user, 
    finde_email_zu_benutzer, 
    passwort_zuruecksetzen_mit_sicherheitsfrage,
    erstes_passwort_setzen
)
from modules import finanzen_page, inventar_page, adressbuch_page, events_page, termine_page, todos_page, dokumente_page


# Muss der allererste Streamlit-Befehl sein
st.set_page_config(page_title="KrayFürAlle e.V. - Verwaltung", page_icon="🏢", layout="wide")

# Einziger verbleibender Seiten-Import
import mitglieder_page  

# --- SESSION STATE INITIALISIERUNG ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_rolle = "mitglied"
    st.session_state.vorname = "Mitglied"
    st.session_state.hat_inventar_rechte = False
    st.session_state.hat_adressbuch_rechte = False

# --- OBERFLÄCHE FÜR NICHT EINGELOGGTE NUTZER ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🏢 KrayFürAlle e.V.")
        st.subheader("Vereinsverwaltung Portal")
        
        tab_login, tab_aktivieren, tab_passwort = st.tabs([
            "🔑 Anmelden", 
            "✨ Konto aktivieren", 
            "🔒 Passwort vergessen"
        ])
        
        # --- TAB 1: LOGIN ---
        with tab_login:
            st.markdown("### Vereins-Login")
            user_val = st.text_input("Benutzername / Telefonnummer / E-Mail", key="login_user")
            pw_val = st.text_input("Passwort", type="password", key="login_pw")
            
            if st.button("Anmelden", type="primary", use_container_width=True):
                if user_val and pw_val:
                    result = login_user(user_val, pw_val)
                    
                    if result["success"]:
                        email = finde_email_zu_benutzer(user_val)
                        try:
                            data = supabase.table("mitglieder").select("id, vorname, rolle, hat_inventar_rechte, hat_adressbuch_rechte").eq("email", email).single().execute()
                            user_data = data.data
                            
                            st.session_state.user_id = user_data.get("id")
                            st.session_state.vorname = user_data.get("vorname", "Mitglied")
                            
                            rohes_feld = user_data.get("rolle", "mitglied")
                            st.session_state.user_rolle = str(rohes_feld).strip().lower()
                            
                            st.session_state.hat_inventar_rechte = user_data.get("hat_inventar_rechte", False)
                            st.session_state.hat_adressbuch_rechte = user_data.get("hat_adressbuch_rechte", False)
                            st.session_state.logged_in = True
                            
                            st.success(f"Willkommen zurück, {st.session_state.vorname}!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Fehler beim Laden der Benutzerdaten: {e}")
                    else:
                        st.error(result["message"])
                else:
                    st.warning("Bitte Benutzernamen und Passwort eingeben.")

        # --- TAB 2: KONTO AKTIVIEREN ---
        with tab_aktivieren:
            st.markdown("### Account aktivieren")
            ident = st.text_input("Mitglieds-Nr, E-Mail oder Tel", key="reg_ident")
            pw = st.text_input("Neues Passwort", type="password", key="reg_pw")
            frage = st.text_input("Sicherheitsfrage (z.B. Name des ersten Haustiers?)", key="reg_frage")
            antwort = st.text_input("Antwort zur Sicherheitsfrage", key="reg_antwort")
            
            if st.button("Konto freischalten", use_container_width=True):
                if all([ident, pw, frage, antwort]):
                    erfolg, msg = erstes_passwort_setzen(ident, pw)
                    
                    if erfolg:
                        try:
                            query = f"email.eq.{ident},telefonnummer.eq.{ident},mitgliedsnummer.eq.{ident}"
                            supabase.table("mitglieder").update({
                                "sicherheitsfrage": frage,
                                "sicherheitsantwort": antwort
                            }).or_(query).execute()
                            
                            st.success(msg)
                        except Exception as e:
                            st.warning(f"Konto aktiviert, aber Sicherheitsfrage konnte nicht gespeichert werden: {e}")
                    else:
                        st.error(msg)
                else:
                    st.error("Bitte fülle alle Felder aus!")

        # --- TAB 3: PASSWORT VERGESSEN ---
        with tab_passwort:
            st.markdown("### Passwort zurücksetzen")
            
            if "reset_step" not in st.session_state:
                st.session_state.reset_step = 1
                st.session_state.reset_ident = ""
                st.session_state.reset_frage = ""

            if st.session_state.reset_step == 1:
                ident_input = st.text_input("E-Mail, Tel oder Mitgliedsnummer", key="forgot_ident")
                if st.button("Sicherheitsfrage abrufen", use_container_width=True):
                    if ident_input:
                        try:
                            res = supabase.table("mitglieder").select("sicherheitsfrage").or_(f"email.eq.{ident_input},telefonnummer.eq.{ident_input},mitgliedsnummer.eq.{ident_input}").execute()
                            
                            if res.data and len(res.data) > 0:
                                frage_db = res.data[0].get("sicherheitsfrage")
                                if not frage_db:
                                    st.error("Für diesen Benutzer ist keine Sicherheitsfrage hinterlegt.")
                                else:
                                    st.session_state.reset_ident = ident_input.strip()
                                    st.session_state.reset_frage = frage_db
                                    st.session_state.reset_step = 2
                                    st.rerun()
                            else:
                                st.error("Benutzer nicht gefunden. Bitte Eingabe prüfen.")
                        except Exception as e:
                            st.error(f"Technischer Fehler: {e}")
                    else:
                        st.warning("Bitte gib deine Kennung ein.")
            
            elif st.session_state.reset_step == 2:
                st.info(f"**Sicherheitsfrage:** {st.session_state.reset_frage}")
                antwort_input = st.text_input("Deine Antwort", key="forgot_antwort")
                neues_pw_input = st.text_input("Neues Passwort", type="password", key="forgot_pw")
                
                col_back, col_submit = st.columns(2)
                with col_back:
                    if st.button("Zurück"):
                        st.session_state.reset_step = 1
                        st.rerun()
                with col_submit:
                    if st.button("Passwort aktualisieren"):
                        if antwort_input and neues_pw_input:
                            erfolg, msg = passwort_zuruecksetzen_mit_sicherheitsfrage(
                                st.session_state.reset_ident, 
                                antwort_input.strip(), 
                                neues_pw_input.strip()
                            )
                            if erfolg:
                                st.success(msg)
                                st.session_state.reset_step = 1 
                            else:
                                st.error(msg)
                        else:
                            st.error("Bitte alle Felder ausfüllen.")

# --- OBERFLÄCHE FÜR EINGELOGGTE NUTZER ---
else:
    st.sidebar.title("🏢 KrayFürAlle e.V.")
    st.sidebar.markdown(f"Hallo, **{st.session_state.vorname}**!")
    st.sidebar.caption(f"Rolle: {st.session_state.user_rolle.capitalize()}")
    
    if st.session_state.hat_inventar_rechte:
        st.sidebar.info("🔑 Inventar-Rechte aktiv")
    if st.session_state.hat_adressbuch_rechte:
        st.sidebar.info("📇 Adressbuch-Rechte aktiv")

    st.sidebar.divider()
    
    # Navigation dynamisch nach Rolle / Rechten aufbauen
    nav_optionen = [
        "Mitglieder & Rollen", 
        "Inventar & Ausleihe", 
        "Events & Schichten", 
        "Kalender & Termine",
        "Aufgaben & To-Dos",
        "Dokumente"
    ]
    
    erlaubte_rollen_finanzen = ["admin", "administrator", "vorstand", "kassenwart"]
    if st.session_state.user_rolle in erlaubte_rollen_finanzen:
        nav_optionen.append("Finanzen & Kassenbuch")
        
    erlaubte_rollen_leitung = ["admin", "administrator", "vorstand"]
    if st.session_state.user_rolle in erlaubte_rollen_leitung or st.session_state.get("hat_adressbuch_rechte", False):
        nav_optionen.append("Adressbuch")
        
    menue = st.sidebar.radio("Navigation", nav_optionen)
    
    st.sidebar.divider()
    
    if st.sidebar.button("🚗 Abmelden", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_rolle = "mitglied"
        st.session_state.vorname = "Mitglied"
        st.session_state.hat_inventar_rechte = False
        st.session_state.hat_adressbuch_rechte = False
        st.success("Erfolgreich abgemeldet.")
        st.rerun()

    # Seiten aufrufen
    if menue == "Mitglieder & Rollen":
        mitglieder_page.show()
    elif menue == "Inventar & Ausleihe":
        inventar_page.show()
    elif menue == "Events & Schichten":
        events_page.show()
    elif menue == "Kalender & Termine":
        termine_page.show()
    elif menue == "Aufgaben & To-Dos":
        todos_page.show()
    elif menue == "Dokumente":
        dokumente_page.show()
    elif menue == "Finanzen & Kassenbuch":
        finanzen_page.show()
    elif menue == "Adressbuch":
        adressbuch_page.show()