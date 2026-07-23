import streamlit as st
from database import supabase
from datetime import datetime
from zoneinfo import ZoneInfo

def show():
    # --- MOBILE OPTIMIERUNG & CSS ---
    st.markdown("""
        <style>
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
        }
        /* Dezenter Stil für Chat-Meta-Infos */
        .chat-meta {
            font-size: 11px;
            color: gray;
        }
        </style>
    """, unsafe_allow_html=True)

    st.header("💬 Vereins-Chat & Räume")
    st.caption("Tausche dich in verschiedenen Themen-Räumen aus. Passe Farbe, Schrift und Größe individuell an!")

    user_id = str(st.session_state.get("user_id", "unbekannt"))
    user_rolle = st.session_state.get("user_rolle", "mitglied").lower()
    ist_admin_oder_vorstand = user_rolle in ["admin", "administrator", "vorstand"]

    # --- 1. RÄUME LADEN & UNGELESEN-STATUS ERMITTELN ---
    try:
        res_raeume = supabase.table("chat_raeume").select("*").order("name").execute()
        raeume_liste = res_raeume.data if res_raeume.data else [{"name": "Allgemein", "ist_vorstand": False}]
    except Exception:
        raeume_liste = [{"name": "Allgemein", "ist_vorstand": False}]

    # Lesezeichen des Users laden, um ungelesene Räume zu erkennen
    lesezeichen_dict = {}
    try:
        res_lz = supabase.table("chat_lesezeichen").select("*").eq("user_id", user_id).execute()
        if res_lz.data:
            for lz in res_lz.data:
                lesezeichen_dict[lz["raum"]] = lz["letzter_besuch"]
    except:
        pass

    # Filter: Normale Mitglieder sehen keine Vorstands-Räume
    verfuegbare_raeume = []
    raum_labels = {}
    
    for r in raeume_liste:
        r_name = r["name"]
        is_vorstand_raum = r.get("ist_vorstand", False)
        
        if is_vorstand_raum and not ist_admin_oder_vorstand:
            continue
            
        verfuegbare_raeume.append(r_name)
        
        # Prüfen ob es neue Nachrichten seit dem letzten Besuch gibt
        letzter_besuch_iso = lesezeichen_dict.get(r_name)
        hat_neue_nachrichten = False
        
        if letzter_besuch_iso:
            try:
                # Schneller Check über Supabase count oder Filter (hier vereinfacht via Abfrage)
                res_check = supabase.table("chat").select("id", count="exact").eq("raum", r_name).gt("erstellt_am", letzter_besuch_iso).execute()
                if res_check.count and res_check.count > 0:
                    hat_neue_nachrichten = True
            except:
                pass
        else:
            # Wenn noch nie besucht, aber Nachrichten existieren
            try:
                res_check = supabase.table("chat").select("id", count="exact").eq("raum", r_name).execute()
                if res_check.count and res_check.count > 0:
                    hat_neue_nachrichten = True
            except:
                pass

        label = f"🔒 {r_name} (Vorstand)" if is_vorstand_raum else r_name
        if hat_neue_nachrichten and r_name != st.session_state.get("aktiver_chat_raum"):
            label += " 🔴 Neu!"
            
        raum_labels[r_name] = label

    if not verfuegbare_raeume:
        verfuegbare_raeume = ["Allgemein"]
        raum_labels = {"Allgemein": "Allgemein"}

    # Session State für aktiven Raum initialisieren
    if "aktiver_chat_raum" not in st.session_state or st.session_state.aktiver_chat_raum not in verfuegbare_raeume:
        st.session_state.aktiver_chat_raum = verfuegbare_raeume[0]

    # --- 2. LAYOUT: RAUM-AUSWAHL & NEUER RAUM ---
    col_select, col_new = st.columns([3, 2])
    
    with col_select:
        # Selectbox mit sprechenden Labels (inkl. Neu-Badge)
        aktiver_raum = st.selectbox(
            "Aktiver Chat-Raum", 
            verfuegbare_raeume, 
            format_func=lambda x: raum_labels.get(x, x),
            key="aktiver_chat_raum"
        )

    with col_new:
        with st.expander("➕ Neuen Raum erstellen"):
            neuer_raum_name = st.text_input("Name des Raumes", placeholder="z.B. Angler-Treff")
            nur_vorstand_raum = st.checkbox("Nur für Vorstand & Admin", value=False)
            
            if st.button("Raum anlegen", use_container_width=True):
                if neuer_raum_name.strip():
                    clean_name = neuer_raum_name.strip()
                    if clean_name in [r["name"] for r in raeume_liste]:
                        st.warning("Diesen Raum gibt es bereits!")
                    else:
                        try:
                            supabase.table("chat_raeume").insert({
                                "name": clean_name,
                                "ist_vorstand": nur_vorstand_raum if ist_admin_oder_vorstand else False,
                                "erstellt_von": st.session_state.get('vorname', 'Mitglied')
                            }).execute()
                            st.success(f"Raum '{clean_name}' erstellt!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler: {e}")
                else:
                    st.warning("Bitte einen Namen eingeben.")

    # Sobald der Raum betreten wird: Letzten Besuch aktualisieren (Nachrichten gelten als gelesen)
    try:
        supabase.table("chat_lesezeichen").upsert({
            "user_id": user_id,
            "raum": aktiver_raum,
            "letzter_besuch": datetime.now(ZoneInfo("Europe/Berlin")).isoformat()
        }, on_conflict="user_id,raum").execute()
    except Exception:
        pass

    st.divider()

    # --- 3. STIL-EINSTELLUNGEN ---
    with st.expander("🎨 Deine Chat-Stilvorlagen (Farbe, Größe, Schriftart)"):
        c1, c2, c3 = st.columns(3)
        with c1:
            text_farbe = st.color_picker("Schriftfarbe", "#000000", key="chat_color")
        with c2:
            schriftgroesse_wahl = st.selectbox(
                "Schriftgröße", 
                ["Klein (14px)", "Normal (16px)", "Groß (20px)", "Sehr groß (24px)"],
                index=1,
                key="chat_size"
            )
        with c3:
            schriftart_wahl = st.selectbox(
                "Schriftart", 
                ["Standard (Arial)", "Serif (Georgia)", "Monospace (Courier New)", "Fantasy (Impact)"],
                index=0,
                key="chat_font"
            )

    groessen_map = {"Klein (14px)": "14px", "Normal (16px)": "16px", "Groß (20px)": "20px", "Sehr groß (24px)": "24px"}
    schriften_map = {
        "Standard (Arial)": "Arial, sans-serif",
        "Serif (Georgia)": "Georgia, serif",
        "Monospace (Courier New)": "'Courier New', monospace",
        "Fantasy (Impact)": "Impact, sans-serif"
    }
    css_groesse = groessen_map.get(schriftgroesse_wahl, "16px")
    css_schriftart = schriften_map.get(schriftart_wahl, "Arial, sans-serif")

    st.markdown(f"### 📍 Raum: {aktiver_raum}")

    # --- 4. NACHRICHTEN LADEN & ANZEIGEN ---
    try:
        res = supabase.table("chat").select("*").eq("raum", aktiver_raum).order("erstellt_am", desc=False).execute()
        nachrichten = res.data if res.data else []
    except Exception as e:
        st.error(f"Fehler beim Laden des Chats: {e}")
        nachrichten = []

    if not nachrichten:
        st.info(f"Noch keine Nachrichten im Raum '{aktiver_raum}'. Schreib die erste Nachricht! 🚀")
    
    for m in nachrichten:
        msg_id = m.get("id")
        msg_user_id = m.get("user_id")
        sender = m.get("sender_name", "Mitglied")
        text = m.get("nachricht", "")
        farbe = m.get("farbe", "#000000")
        groesse = m.get("schriftgroesse", "16px")
        schrift = m.get("schriftart", "Arial, sans-serif")
        
        datum_roh = m.get("erstellt_am", "")
        uhrzeit = ""
        try:
            dt = datetime.fromisoformat(datum_roh.replace("Z", "+00:00"))
            dt_lokal = dt.astimezone(ZoneInfo("Europe/Berlin"))
            uhrzeit = dt_lokal.strftime("%d.%m. um %H:%M Uhr")
        except:
            pass

        with st.chat_message("user"):
            col_info, col_del = st.columns([8, 1])
            with col_info:
                st.markdown(f"**{sender}** <span class='chat-meta'>({uhrzeit})</span>", unsafe_allow_html=True)
            
            # Lösch-Button für eigene Nachrichten oder Admins/Vorstand
            is_own_msg = (str(msg_user_id) == str(user_id))
            if is_own_msg or ist_admin_oder_vorstand:
                with col_del:
                    if st.button("🗑️", key=f"del_msg_{msg_id}", help="Nachricht löschen"):
                        try:
                            supabase.table("chat").delete().eq("id", msg_id).execute()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler: {e}")

            st.markdown(f"<div style='color: {farbe}; font-size: {groesse}; font-family: {schrift}; word-break: break-word; margin-top: 4px;'>{text}</div>", unsafe_allow_html=True)

    # --- 5. NACHRICHT SENDEN ---
    user_text = st.chat_input(f"Schreibe in #{aktiver_raum}... Emojis 😊🔥🎉 sind erlaubt")

    if user_text:
        if user_text.strip():
            absender_name = f"{st.session_state.get('vorname', 'Mitglied')} ({user_rolle.capitalize()})"
            
            neue_nachricht = {
                "user_id": user_id,
                "raum": aktiver_raum,
                "sender_name": absender_name,
                "nachricht": user_text.strip(),
                "farbe": text_farbe,
                "schriftgroesse": css_groesse,
                "schriftart": css_schriftart
            }
            
            try:
                supabase.table("chat").insert(neue_nachricht).execute()
                st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Senden: {e}")