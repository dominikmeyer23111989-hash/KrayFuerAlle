import streamlit as st
from database import supabase
from datetime import datetime
from zoneinfo import ZoneInfo
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def sende_admin_email(titel, nachricht, absender_name, kategorie):
    try:
        # Secrets auslesen
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = int(st.secrets["email"]["smtp_port"])
        sender_email = st.secrets["email"]["sender_email"]
        sender_password = st.secrets["email"]["sender_password"]
        admin_email = st.secrets["email"]["admin_email"]

        # E-Mail zusammenbauen
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = admin_email
        msg["Subject"] = f"🔔 Vereins-App: Neuer Eintrag [{kategorie}]"

        body = f"""
Hallo Admin,

es gibt einen neuen Eintrag in der Vereins-App!

Kategorie: {kategorie}
Titel: {titel}
Von: {absender_name}

Nachricht / Inhalt:
----------------------------------------
{nachricht}
----------------------------------------

Du kannst dich in der App einloggen, um den Eintrag zu bearbeiten.
"""
        msg.attach(MIMEText(body, "plain"))

        # Verbindung aufbauen und senden
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, admin_email, msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)

def show():
    st.markdown("""
        <style>
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    st.header("💡 Feedback, Wünsche & Fehler melden")
    st.caption("Hilf uns, die App und den Verein zu verbessern. Deine Nachricht geht direkt an das Admin-Team.")

    user_rolle = st.session_state.get("user_rolle", "").lower()
    ist_admin = user_rolle in ["admin", "administrator", "vorstand"]

    # Tabs dynamisch erstellen
    if ist_admin:
        tab_senden, tab_postfach = st.tabs(["✍️ Nachricht senden", "📥 Admin-Postfach"])
    else:
        tab_senden = st.container()
        tab_postfach = None

    # --- TAB 1: NACHRICHT SENDEN ---
    with tab_senden:
        st.subheader("Was hast du auf dem Herzen?")
        
        with st.form("feedback_form"):
            kategorie = st.selectbox("Kategorie", [
                "🐛 Fehler / Bug melden", 
                "✨ Funktionswunsch / Idee", 
                "🛠️ Verbesserungsvorschlag", 
                "💬 Sonstiges"
            ])
            titel = st.text_input("Kurzbeschreibung (z.B. Button auf Seite XY klemmt)")
            nachricht = st.text_area("Ausführliche Beschreibung", placeholder="Beschreibe kurz, was dir aufgefallen ist oder was du dir wünschst...")
            
            anonym = st.checkbox("Anonym absenden (Dein Name wird nicht mitgesendet)", value=False)
            
            submitted = st.form_submit_button("Absenden", type="primary", use_container_width=True)

            if submitted:
                if not titel or not nachricht:
                    st.error("Bitte fülle mindestens Kurzbeschreibung und Nachricht aus!")
                else:
                    absender = "Anonym" if anonym else f"{st.session_state.get('vorname', 'Mitglied')} ({user_rolle.capitalize()})"
                    
                    neuer_eintrag = {
                        "kategorie": kategorie,
                        "titel": titel.strip(),
                        "nachricht": nachricht.strip(),
                        "sender_name": absender
                    }
                    
                    try:
                        # 1. In Supabase speichern
                        supabase.table("feedback").insert(neuer_eintrag).execute()
                        
                        # 2. E-Mail an Admin senden
                        email_erfolgreich, email_fehler = sende_admin_email(titel.strip(), nachricht.strip(), absender, kategorie)
                        
                        if email_erfolgreich:
                            st.success("Vielen Dank! Deine Nachricht wurde gespeichert und der Admin per E-Mail informiert. 🎉")
                        else:
                            st.success("Vielen Dank! Deine Nachricht wurde in der Web-App gespeichert.")
                            st.warning(f"⚠️ Die E-Mail an den Admin konnte leider nicht gesendet werden. Technischer Fehler: `{email_fehler}`")
                            st.info("💡 **Tipp:** Überprüfe deine SMTP-Zugangsdaten und Ports (z.B. App-Passwort bei Gmail) in den Streamlit Secrets (`.streamlit/secrets.toml`).")

                    except Exception as e:
                        st.error(f"Fehler beim Speichern: {e}")

    # --- TAB 2: ADMIN POSTFACH ---
    if ist_admin and tab_postfach:
        with tab_postfach:
            st.subheader("Eingegangene Meldungen")
            
            try:
                res = supabase.table("feedback").select("*").order("erstellt_am", desc=True).execute()
                meldungen = res.data if res.data else []
            except Exception as e:
                st.error(f"Fehler beim Laden: {e}")
                meldungen = []

            if meldungen:
                offene = [m for m in meldungen if not m.get("erledigt", False)]
                st.metric("Offene Meldungen", len(offene))
                
                for m in meldungen:
                    status_icon = "✅ [Erledigt]" if m.get("erledigt") else "🔥 [Offen]"
                    datum_roh = m.get("erstellt_am", "")
                    try:
                        dt = datetime.fromisoformat(datum_roh.replace("Z", "+00:00"))
                        dt_lokal = dt.astimezone(ZoneInfo("Europe/Berlin"))
                        datum_fmt = dt_lokal.strftime("%d.%m.%Y %H:%M")
                    except:
                        datum_fmt = "Unbekannt"
                        
                    with st.expander(f"{status_icon} {m.get('kategorie')} — {m.get('titel')} ({datum_fmt})"):
                        st.write(f"**Von:** {m.get('sender_name')}")
                        st.markdown(f"**Nachricht:**\n> {m.get('nachricht')}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if not m.get("erledigt"):
                                if st.button("✔️ Als erledigt markieren", key=f"done_{m['id']}"):
                                    supabase.table("feedback").update({"erledigt": True}).eq("id", m['id']).execute()
                                    st.success("Aktualisiert!")
                                    st.rerun()
                            else:
                                if st.button("↩️ Wieder öffnen", key=f"open_{m['id']}"):
                                    supabase.table("feedback").update({"erledigt": False}).eq("id", m['id']).execute()
                                    st.rerun()
                        with col2:
                            if st.button("🗑️ Löschen", key=f"del_fb_{m['id']}"):
                                supabase.table("feedback").delete().eq("id", m['id']).execute()
                                st.success("Gelöscht!")
                                st.rerun()
            else:
                st.info("Bisher sind noch keine Feedback-Nachrichten eingegangen.")