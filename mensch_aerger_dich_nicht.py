import random
import time
import streamlit as st

# ==========================================
# SPIEL-KONSTANTEN & KOORDINATEN FÜRS SPIELBRETT
# ==========================================
PLAYERS_CONFIG = {
    "R": {"name": "Rot", "start": 0, "color_code": "🔴"},
    "B": {"name": "Blau", "start": 10, "color_code": "🔵"},
    "G": {"name": "Grün", "start": 20, "color_code": "🟢"},
    "Y": {"name": "Gelb", "start": 30, "color_code": "🟡"},
}
PLAYER_ORDER = ["R", "B", "G", "Y"]
DICE_FACES = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

# 40 Hauptfelder auf dem Kreuz-Rundkurs (Mapping auf 11x11 Grid Koordinaten)
TRACK_COORDS = {
    0: (10, 4), 1: (9, 4), 2: (8, 4), 3: (7, 4), 4: (6, 4), 5: (6, 3), 6: (6, 2), 7: (6, 1), 8: (6, 0), 9: (5, 0),
    10: (4, 0), 11: (4, 1), 12: (4, 2), 13: (4, 3), 14: (4, 4), 15: (3, 4), 16: (2, 4), 17: (1, 4), 18: (0, 4), 19: (0, 5),
    20: (0, 6), 21: (1, 6), 22: (2, 6), 23: (3, 6), 24: (4, 6), 25: (4, 7), 26: (4, 8), 27: (4, 9), 28: (4, 10), 29: (5, 10),
    30: (6, 10), 31: (6, 9), 32: (6, 8), 33: (6, 7), 34: (6, 6), 35: (7, 6), 36: (8, 6), 37: (9, 6), 38: (10, 6), 39: (10, 5),
}

# Zielgeraden (Felder 40 bis 43) pro Spieler
HOME_COORDS = {
    "R": {40: (9, 5), 41: (8, 5), 42: (7, 5), 43: (6, 5)},
    "B": {40: (5, 1), 41: (5, 2), 42: (5, 3), 43: (5, 4)},
    "G": {40: (1, 5), 41: (2, 5), 42: (3, 5), 43: (4, 5)},
    "Y": {40: (5, 9), 41: (5, 8), 42: (5, 7), 43: (5, 6)},
}

def init_spiel(player_types):
    st.session_state.madn_player_types = player_types
    st.session_state.madn_spielstand = {
        "R": [-1, -1, -1, -1],
        "B": [-1, -1, -1, -1],
        "G": [-1, -1, -1, -1],
        "Y": [-1, -1, -1, -1],
    }
    st.session_state.madn_am_zug = "R"
    st.session_state.madn_wuerfel = None
    st.session_state.madn_gewinner = None
    st.session_state.madn_meldung = "Spiel gestartet! Rot beginnt und braucht eine 6, um zu starten."

def get_absolute_pos(player, rel_pos):
    if rel_pos < 0 or rel_pos >= 40: return rel_pos
    return (rel_pos + PLAYERS_CONFIG[player]["start"]) % 40

def berechne_neue_position(player, aktuelle_pos, wurf):
    if aktuelle_pos == -1:
        if wurf == 6: return 0, False
        return -1, False
    if aktuelle_pos >= 40:
        neue_ziel_pos = aktuelle_pos + wurf
        if neue_ziel_pos <= 43: return neue_ziel_pos, True
        return aktuelle_pos, False
    neue_pos = aktuelle_pos + wurf
    if neue_pos >= 40:
        ziel_pos = 40 + (neue_pos - 40)
        if ziel_pos <= 43: return ziel_pos, True
        return aktuelle_pos, False
    return neue_pos, False

def hat_gueltige_zuege(player, wurf):
    figuren = st.session_state.madn_spielstand[player]
    im_nest = [f for f in figuren if f == -1]
    auf_brett = [f for f in figuren if f > -1]

    if wurf == 6 and im_nest:
        start_feld_abs = PLAYERS_CONFIG[player]["start"]
        eigene_auf_start = any(get_absolute_pos(player, f) == start_feld_abs for f in auf_brett if f < 40)
        if not eigene_auf_start: return True

    for f in auf_brett:
        neue_pos, _ = berechne_neue_position(player, f, wurf)
        if neue_pos != f and neue_pos not in figuren: return True
    return False

def zug_ausfuehren(player, figur_idx):
    wurf = st.session_state.madn_wuerfel
    figuren = st.session_state.madn_spielstand[player]
    aktuelle_pos = figuren[figur_idx]

    # Aus dem Nest starten
    if aktuelle_pos == -1 and wurf == 6:
        start_feld_abs = PLAYERS_CONFIG[player]["start"]
        if any(get_absolute_pos(player, f) == start_feld_abs for f in figuren if -1 < f < 40):
            return False

        # Gegner schlagen
        for gegner_p, g_figuren in st.session_state.madn_spielstand.items():
            if gegner_p == player: continue
            for g_idx, g_pos in enumerate(g_figuren):
                if -1 < g_pos < 40 and get_absolute_pos(gegner_p, g_pos) == start_feld_abs:
                    st.session_state.madn_spielstand[gegner_p][g_idx] = -1
                    st.session_state.madn_meldung = f"💥 {PLAYERS_CONFIG[player]['name']} schlägt eine Figur!"

        figuren[figur_idx] = 0
        beende_zug(wurf == 6)
        return True

    # Normale Bewegung
    elif aktuelle_pos > -1:
        neue_pos, im_ziel = berechne_neue_position(player, aktuelle_pos, wurf)
        if neue_pos == aktuelle_pos or neue_pos in figuren: return False

        if not im_ziel:
            neue_abs = get_absolute_pos(player, neue_pos)
            for gegner_p, g_figuren in st.session_state.madn_spielstand.items():
                if gegner_p == player: continue
                for g_idx, g_pos in enumerate(g_figuren):
                    if -1 < g_pos < 40 and get_absolute_pos(gegner_p, g_pos) == neue_abs:
                        st.session_state.madn_spielstand[gegner_p][g_idx] = -1
                        st.session_state.madn_meldung = f"💥 {PLAYERS_CONFIG[player]['name']} schlägt eine Figur!"

        figuren[figur_idx] = neue_pos
        if all(f >= 40 for f in figuren):
            st.session_state.madn_gewinner = player

        beende_zug(wurf == 6)
        return True
    return False

def beende_zug(hat_sechs):
    st.session_state.madn_wuerfel = None
    if hat_sechs and st.session_state.madn_gewinner is None:
        st.session_state.madn_meldung += " ✨ Extra-Wurf durch eine 6!"
        return

    aktiver_idx = PLAYER_ORDER.index(st.session_state.madn_am_zug)
    for i in range(1, 5):
        naechster = PLAYER_ORDER[(aktiver_idx + i) % 4]
        if naechster in st.session_state.madn_player_types:
            st.session_state.madn_am_zug = naechster
            break

def ki_zug_ausfuehren():
    p = st.session_state.madn_am_zug
    if st.session_state.madn_gewinner is not None: return

    wurf = random.randint(1, 6)
    st.session_state.madn_wuerfel = wurf
    c_name = PLAYERS_CONFIG[p]["name"]

    if not hat_gueltige_zuege(p, wurf):
        st.session_state.madn_meldung = f"🤖 {c_name} würfelt eine {wurf} – kein gültiger Zug."
        beende_zug(False)
        return

    st.session_state.madn_meldung = f"🤖 {c_name} würfelt eine {wurf} und zieht..."
    figuren = st.session_state.madn_spielstand[p]
    moegliche_zuege = []

    for idx, pos in enumerate(figuren):
        if pos == -1 and wurf == 6:
            moegliche_zuege.append((idx, 100))
        elif pos > -1:
            neue_pos, _ = berechne_neue_position(p, pos, wurf)
            if neue_pos != pos and neue_pos not in figuren:
                moegliche_zuege.append((idx, neue_pos))

    if moegliche_zuege:
        moegliche_zuege.sort(key=lambda x: x[1], reverse=True)
        zug_ausfuehren(p, moegliche_zuege[0][0])


# ==========================================
# HAUPTANSICHT STREAMLIT
# ==========================================
def show():
    st.set_page_config(page_title="Mensch ärger dich nicht", layout="centered")
    st.header("🎲 Mensch ärger dich nicht")
    
    if "madn_modus" not in st.session_state:
        st.session_state.madn_modus = "setup"

    # ----------------------------------------
    # SETUP MENÜ
    # ----------------------------------------
    if st.session_state.madn_modus == "setup":
        st.subheader("⚙️ Spielkonfiguration")
        col1, col2 = st.columns(2)
        with col1:
            r_type = st.selectbox("🔴 Team Rot", ["Mensch", "KI"], index=0)
            g_type = st.selectbox("🟢 Team Grün", ["Mensch", "KI"], index=1)
        with col2:
            b_type = st.selectbox("🔵 Team Blau", ["Mensch", "KI"], index=1)
            y_type = st.selectbox("🟡 Team Gelb", ["Mensch", "KI"], index=1)

        if st.button("🚀 Spiel starten", type="primary", use_container_width=True):
            init_spiel({"R": r_type, "B": b_type, "G": g_type, "Y": y_type})
            st.session_state.madn_modus = "game"
            st.rerun()

    # ----------------------------------------
    # SPIELGESCHEHEN
    # ----------------------------------------
    elif st.session_state.madn_modus == "game":
        if st.button("⚙️ Zurück zur Konfiguration"):
            st.session_state.madn_modus = "setup"
            st.rerun()

        if st.session_state.get("madn_gewinner"):
            g_name = PLAYERS_CONFIG[st.session_state.madn_gewinner]["name"]
            st.balloons()
            st.success(f"🏆 **Team {g_name} hat gewonnen!**")
            return

        am_zug = st.session_state.madn_am_zug
        typ = st.session_state.madn_player_types[am_zug]
        c_info = PLAYERS_CONFIG[am_zug]

        st.info(f"Am Zug: **{c_info['color_code']} {c_info['name']}** ({typ})  \n{st.session_state.madn_meldung}")

        if typ == "KI" and st.session_state.madn_gewinner is None:
            with st.spinner(f"🤖 KI {c_info['name']} denkt nach..."):
                time.sleep(1.2)
                ki_zug_ausfuehren()
                st.rerun()

        # ==========================================
        # MODERNES SPIELBRETT-RENDERING (CSS/HTML)
        # ==========================================
        track_pawns = {}
        nest_pawns = {"R": [], "B": [], "G": [], "Y": []}
        
        for p_key, figs in st.session_state.madn_spielstand.items():
            for idx, pos in enumerate(figs):
                if pos == -1:
                    nest_pawns[p_key].append(idx + 1)
                elif 0 <= pos < 40:
                    abs_pos = (pos + PLAYERS_CONFIG[p_key]["start"]) % 40
                    rc = TRACK_COORDS.get(abs_pos)
                    if rc: track_pawns[rc] = (p_key, idx + 1)
                elif pos >= 40:
                    rc = HOME_COORDS[p_key].get(pos)
                    if rc: track_pawns[rc] = (p_key, idx + 1)

        def get_nest_pawn(r, c):
            if 9 <= r <= 10 and 0 <= c <= 1:
                idx = (r - 9) * 2 + c
                return ("R", nest_pawns["R"][idx]) if idx < len(nest_pawns["R"]) else None
            elif 0 <= r <= 1 and 0 <= c <= 1:
                idx = r * 2 + c
                return ("B", nest_pawns["B"][idx]) if idx < len(nest_pawns["B"]) else None
            elif 0 <= r <= 1 and 9 <= c <= 10:
                idx = r * 2 + (c - 9)
                return ("G", nest_pawns["G"][idx]) if idx < len(nest_pawns["G"]) else None
            elif 9 <= r <= 10 and 9 <= c <= 10:
                idx = (r - 9) * 2 + (c - 9)
                return ("Y", nest_pawns["Y"][idx]) if idx < len(nest_pawns["Y"]) else None
            return None

        # CSS Styling für Brett & 3D Figuren
        css_styles = """
        <style>
        .board-wrapper { display: flex; justify-content: center; margin: 20px 0; }
        .board-container {
            background-color: #fdf5e6;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
            border: 2px solid #e2d1b3;
        }
        .madn-table { border-collapse: separate; border-spacing: 5px; margin: 0; }
        .madn-td { padding: 0; border: none; background: transparent; width: 44px; height: 44px; }
        .field { width: 44px; height: 44px; border-radius: 50%; position: relative; margin: auto; }
        
        .field-track { background: #ffffff; border: 2px solid #b2bec3; box-shadow: inset 1px 1px 4px rgba(0,0,0,0.1); }
        .field-start-R { background: #ffcccc; border: 2px solid #d63031; }
        .field-start-B { background: #cce0ff; border: 2px solid #0984e3; }
        .field-start-G { background: #ccffcc; border: 2px solid #00b894; }
        .field-start-Y { background: #fff0cc; border: 2px solid #f39c12; }
        
        .field-nest-R { background: #ff7675; border: 3px solid #d63031; }
        .field-nest-B { background: #74b9ff; border: 3px solid #0984e3; }
        .field-nest-G { background: #55efc4; border: 3px solid #00b894; }
        .field-nest-Y { background: #ffeaa7; border: 3px solid #f39c12; }

        .pawn {
            width: 32px; height: 32px; border-radius: 50%;
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            display: flex; align-items: center; justify-content: center;
            font-family: Arial, sans-serif; font-weight: bold; font-size: 15px; color: white;
            box-shadow: 0 6px 8px rgba(0,0,0,0.4), inset 0 2px 5px rgba(255,255,255,0.7), inset 0 -4px 6px rgba(0,0,0,0.3);
            border: 1px solid rgba(0,0,0,0.5); z-index: 10; text-shadow: 1px 1px 2px rgba(0,0,0,0.6);
        }
        .p-R { background: radial-gradient(circle at 35% 35%, #ff7675, #d63031); }
        .p-B { background: radial-gradient(circle at 35% 35%, #74b9ff, #0984e3); }
        .p-G { background: radial-gradient(circle at 35% 35%, #55efc4, #00b894); }
        .p-Y { background: radial-gradient(circle at 35% 35%, #fff200, #f39c12); color: #444; text-shadow: 1px 1px 0px rgba(255,255,255,0.5); }
        </style>
        """

        table_html = css_styles + '<div class="board-wrapper"><div class="board-container"><table class="madn-table">'

        for r in range(11):
            table_html += "<tr>"
            for c in range(11):
                cell_html = ""
                is_field = False
                field_class = ""
                pawn_info = None

                # Nester prüfen
                if 9 <= r <= 10 and 0 <= c <= 1:
                    is_field = True; field_class = "field-nest-R"; pawn_info = get_nest_pawn(r, c)
                elif 0 <= r <= 1 and 0 <= c <= 1:
                    is_field = True; field_class = "field-nest-B"; pawn_info = get_nest_pawn(r, c)
                elif 0 <= r <= 1 and 9 <= c <= 10:
                    is_field = True; field_class = "field-nest-G"; pawn_info = get_nest_pawn(r, c)
                elif 9 <= r <= 10 and 9 <= c <= 10:
                    is_field = True; field_class = "field-nest-Y"; pawn_info = get_nest_pawn(r, c)

                # Laufweg prüfen
                elif (4 <= c <= 6) or (4 <= r <= 6):
                    rc = (r, c)
                    is_field = True
                    field_class = "field-track"

                    # Start- & Zielfelder einfärben
                    for pk, pc in PLAYERS_CONFIG.items():
                        if TRACK_COORDS.get(pc["start"]) == rc: field_class = f"field-start-{pk}"
                    for pk, h_dict in HOME_COORDS.items():
                        if rc in h_dict.values(): field_class = f"field-start-{pk}"

                    pawn_info = track_pawns.get(rc)

                if is_field:
                    pawn_div = f'<div class="pawn p-{pawn_info[0]}">{pawn_info[1]}</div>' if pawn_info else ""
                    cell_html = f'<div class="field {field_class}">{pawn_div}</div>'

                table_html += f'<td class="madn-td">{cell_html}</td>'
            table_html += "</tr>"

        table_html += "</table></div></div>"
        st.markdown(table_html, unsafe_allow_html=True)

        # ==========================================
        # STEUERUNG (MENSCH)
        # ==========================================
        if typ == "Mensch":
            col_w, col_z = st.columns([1.5, 3])

            with col_w:
                if st.session_state.madn_wuerfel is None:
                    if st.button("🎲 Würfeln", type="primary", use_container_width=True):
                        wurf = random.randint(1, 6)
                        st.session_state.madn_wuerfel = wurf
                        if not hat_gueltige_zuege(am_zug, wurf):
                            st.session_state.madn_meldung = f"Gewürfelt: {wurf}. Leider kein gültiger Zug möglich!"
                            beende_zug(False)
                        else:
                            st.session_state.madn_meldung = f"Eine **{wurf}** gewürfelt! Wähle eine Figur aus."
                        st.rerun()
                else:
                    st.markdown(
                        f"<div style='text-align: center; font-size: 80px; line-height: 1; color: #2c3e50;'>{DICE_FACES[st.session_state.madn_wuerfel]}</div>"
                        f"<div style='text-align: center; font-weight: bold;'>Gewürfelt: {st.session_state.madn_wuerfel}</div>", 
                        unsafe_allow_html=True
                    )

            with col_z:
                if st.session_state.madn_wuerfel is not None:
                    st.write(f"Wähle die Figur, die ziehen soll:")
                    fig_cols = st.columns(4)
                    for idx in range(4):
                        pos = st.session_state.madn_spielstand[am_zug][idx]
                        status = "Nest 🏠" if pos == -1 else f"Ziel 🎯 ({pos-39})" if pos >= 40 else f"Feld {pos}"

                        with fig_cols[idx]:
                            if st.button(f"Figur {idx+1}\n({status})", key=f"btn_p_{idx}", use_container_width=True):
                                erfolg = zug_ausfuehren(am_zug, idx)
                                if not erfolg:
                                    st.warning("Dieser Zug ist nicht möglich!")
                                st.rerun()

if __name__ == "__main__":
    show()