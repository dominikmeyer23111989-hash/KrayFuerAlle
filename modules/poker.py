import random
import time
import json
import streamlit as st
from supabase import create_client

# ==========================================
# SUPABASE INITIALISIERUNG
# ==========================================
@st.cache_resource
def init_supabase():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception as e:
        return None

supabase = init_supabase()

# ==========================================
# SPIEL-KONSTANTEN & HILFSFUNKTIONEN
# ==========================================
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALS = {r: i for i, r in enumerate(RANKS, 2)}

AI_NAME_POOL = [
    "Alpha", "DeepBluff", "Calculator", "Maverick", 
    "CyberDealer", "Skynet", "Matrix", "BitRoller", "NeoBot", "AceBot"
]
PERSONALITIES = ["Aggressiv", "Konservativ", "Bluff-King", "Unberechenbar"]

def create_deck():
    deck = [{"rank": r, "suit": s, "val": RANK_VALS[r]} for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck

def card_html(card):
    if not card:
        return '<div class="card card-back">?</div>'
    color = "red" if card["suit"] in ["♥", "♦"] else "black"
    return f"""
    <div class="card" style="color: {color};">
        <div style="font-size: 18px; font-weight: bold;">{card['rank']}</div>
        <div style="font-size: 24px; text-align: center;">{card['suit']}</div>
        <div style="font-size: 18px; font-weight: bold; text-align: right;">{card['rank']}</div>
    </div>
    """

def evaluate_hand(hole_cards, community_cards):
    all_cards = hole_cards + community_cards
    if not all_cards: return 0, "Keine Karten"
    
    vals = sorted([c["val"] for c in all_cards], reverse=True)
    suits = [c["suit"] for c in all_cards]
    
    is_flush = any(suits.count(s) >= 5 for s in SUITS)
    
    unique_vals = sorted(list(set(vals)), reverse=True)
    is_straight = False
    straight_high = 0
    for i in range(len(unique_vals) - 4):
        chunk = unique_vals[i:i+5]
        if chunk[0] - chunk[4] == 4 and len(chunk) == 5:
            is_straight = True
            straight_high = chunk[0]
            break
    if not is_straight and set([14, 2, 3, 4, 5]).issubset(set(vals)):
        is_straight = True
        straight_high = 5

    val_counts = {v: vals.count(v) for v in set(vals)}
    counts = sorted(val_counts.values(), reverse=True)
    
    if is_flush and is_straight:
        return 900 + straight_high, "Straight Flush!"
    if counts[0] == 4:
        return 800 + max([v for v, c in val_counts.items() if c == 4]), "Vierling (Four of a Kind)"
    if counts[0] == 3 and counts[1] >= 2:
        return 700 + max([v for v, c in val_counts.items() if c == 3]), "Full House"
    if is_flush:
        return 600 + vals[0], "Flush"
    if is_straight:
        return 500 + straight_high, "Straße (Straight)"
    if counts[0] == 3:
        return 400 + max([v for v, c in val_counts.items() if c == 3]), "Drilling (Three of a Kind)"
    if counts[0] == 2 and counts[1] == 2:
        pairs = sorted([v for v, c in val_counts.items() if c == 2], reverse=True)
        return 300 + pairs[0]*15 + pairs[1], "Zwei Paar"
    if counts[0] == 2:
        pair_val = max([v for v, c in val_counts.items() if c == 2])
        return 200 + pair_val, "Ein Paar"
    
    return 100 + vals[0], f"High Card ({RANKS[vals[0]-2]})"

# ==========================================
# SPIEL- & TURNIERINITIALISIERUNG
# ==========================================
def init_poker_game(mode="mixed", god_mode=False, player_configs=None, room_id=None, starting_chips=1000):
    st.session_state.poker_mode = mode
    st.session_state.room_id = room_id
    st.session_state.poker_stage = "preflop"
    st.session_state.deck = create_deck()
    st.session_state.community_cards = []
    st.session_state.current_bet = 20 if mode != "tournament" else st.session_state.get("t_small_blind", 10) * 2
    st.session_state.message = "Neue Runde gestartet! Blinds wurden gesetzt."
    
    players_list = []
    
    if player_configs:
        for idx, cfg in enumerate(player_configs):
            # Wenn im Turnier, behalte bereits existierende Chip-Stände bei, falls Neustart einer Hand
            chips = cfg.get("chips", starting_chips)
            if mode == "tournament" and "tournament_initialized" in st.session_state:
                # Bereits laufendes Turnier, Chips nicht überschreiben wenn Spieler schon da war
                pass
            players_list.append({
                "name": cfg["name"],
                "chips": chips,
                "cards": [],
                "bet": 0,
                "folded": chips <= 0,
                "is_ai": cfg["is_ai"],
                "style": cfg.get("style", "Aggressiv"),
                "eliminated": chips <= 0
            })
    else:
        players_list = [
            {"name": "Du (Spieler)", "chips": starting_chips, "cards": [], "bet": 0, "folded": False, "is_ai": False, "eliminated": False},
            {"name": "🤖 Alpha (KI - Bluff-King)", "chips": starting_chips, "cards": [], "bet": 0, "folded": False, "is_ai": True, "style": "Bluff-King", "eliminated": False},
            {"name": "🤖 BitRoller (KI - Konservativ)", "chips": starting_chips, "cards": [], "bet": 0, "folded": False, "is_ai": True, "style": "Konservativ", "eliminated": False},
            {"name": "🤖 NeoBot (KI - Unberechenbar)", "chips": starting_chips, "cards": [], "bet": 0, "folded": False, "is_ai": True, "style": "Unberechenbar", "eliminated": False}
        ]
        
    st.session_state.players = players_list
    
    # Blinds setzen für aktive Spieler
    active_non_folded = [p for p in players_list if not p["eliminated"]]
    sb = st.session_state.get("t_small_blind", 10) if mode == "tournament" else 10
    bb = sb * 2
    st.session_state.current_bet = bb
    
    pot = 0
    if len(active_non_folded) >= 2:
        active_non_folded[0]["chips"] -= sb
        active_non_folded[0]["bet"] = sb
        active_non_folded[1]["chips"] -= bb
        active_non_folded[1]["bet"] = bb
        pot = sb + bb
    st.session_state.pot = pot

    # Aktiven Spieler finden (erster nicht-eliminierter Spieler nach BB)
    non_elim_indices = [i for i, p in enumerate(players_list) if not p["eliminated"]]
    st.session_state.active_player_idx = non_elim_indices[2 % len(non_elim_indices)] if len(non_elim_indices) > 2 else non_elim_indices[0]

    for i, p in enumerate(st.session_state.players):
        if p["eliminated"]:
            p["cards"] = []
            continue
        if i == 0 and god_mode:
            p["cards"] = [{"rank": "A", "suit": "♠", "val": 14}, {"rank": "A", "suit": "♥", "val": 14}]
        else:
            p["cards"] = [st.session_state.deck.pop(), st.session_state.deck.pop()]

    if mode == "tournament":
        st.session_state.tournament_initialized = True
        if "t_hand_count" not in st.session_state:
            st.session_state.t_hand_count = 0

    if room_id and supabase:
        sync_room_state_to_supabase()

def sync_room_state_to_supabase():
    if not supabase or not st.session_state.get("room_id"):
        return
    state_data = {
        "poker_stage": st.session_state.poker_stage,
        "deck": st.session_state.deck,
        "community_cards": st.session_state.community_cards,
        "pot": st.session_state.pot,
        "current_bet": st.session_state.current_bet,
        "message": st.session_state.message,
        "active_player_idx": st.session_state.active_player_idx,
        "players": st.session_state.players
    }
    try:
        supabase.table("poker_rooms").upsert({
            "room_id": st.session_state.room_id,
            "state_json": json.dumps(state_data),
            "updated_at": "now()"
        }).execute()
    except Exception:
        pass

def load_room_state_from_supabase():
    if not supabase or not st.session_state.get("room_id"):
        return False
    try:
        res = supabase.table("poker_rooms").select("*").eq("room_id", st.session_state.room_id).execute()
        if res.data:
            data = json.loads(res.data[0]["state_json"])
            st.session_state.poker_stage = data["poker_stage"]
            st.session_state.deck = data["deck"]
            st.session_state.community_cards = data["community_cards"]
            st.session_state.pot = data["pot"]
            st.session_state.current_bet = data["current_bet"]
            st.session_state.message = data["message"]
            st.session_state.active_player_idx = data["active_player_idx"]
            st.session_state.players = data["players"]
            return True
    except Exception:
        pass
    return False

def next_stage():
    stage = st.session_state.poker_stage
    deck = st.session_state.deck
    comm = st.session_state.community_cards
    
    for p in st.session_state.players:
        p["bet"] = 0
    st.session_state.current_bet = 0

    if stage == "preflop":
        deck.pop()
        comm.extend([deck.pop(), deck.pop(), deck.pop()])
        st.session_state.poker_stage = "flop"
        st.session_state.message = "Der Flop wurde aufgedeckt."
    elif stage == "flop":
        deck.pop()
        comm.append(deck.pop())
        st.session_state.poker_stage = "turn"
        st.session_state.message = "Der Turn wurde aufgedeckt."
    elif stage == "turn":
        deck.pop()
        comm.append(deck.pop())
        st.session_state.poker_stage = "river"
        st.session_state.message = "Der River wurde aufgedeckt."
    elif stage == "river":
        st.session_state.poker_stage = "showdown"
        evaluate_showdown()

def evaluate_showdown():
    active_players = [p for p in st.session_state.players if not p["folded"] and not p["eliminated"]]
    if not active_players:
        active_players = [p for p in st.session_state.players if not p["eliminated"]]

    best_score = -1
    winners = []
    
    results_text = "<div style='background: rgba(0,0,0,0.6); padding: 15px; border-radius: 10px; border: 1px solid #f1c40f;'>"
    results_text += "<h3 style='color: #f1c40f; margin-top: 0;'>🏆 Showdown Ergebnisse:</h3>"
    for p in active_players:
        score, desc = evaluate_hand(p["cards"], st.session_state.community_cards)
        results_text += f"<p style='margin: 5px 0;'><b>{p['name']}</b>: {desc}</p>"
        if score > best_score:
            best_score = score
            winners = [p]
        elif score == best_score:
            winners.append(p)
            
    win_amount = st.session_state.pot // len(winners)
    winner_names = " & ".join([w["name"] for w in winners])
    results_text += f"<h4 style='color: #27ae60; margin-bottom: 0;'>🎉 {winner_names} gewinnt den Pot von {st.session_state.pot} Chips!</h4></div>"
    
    for w in winners:
        w["chips"] += win_amount
        
    # Prüfen, ob Spieler durch 0 Chips eliminiert sind
    for p in st.session_state.players:
        if p["chips"] <= 0 and not p["eliminated"]:
            p["eliminated"] = True
            results_text += f"<p style='color: #e74c3c; font-weight: bold;'>❌ {p['name']} ist aus dem Turnier ausgeschieden!</p>"

    st.session_state.message = results_text

    # Im Turniermodus Hand-Zähler erhöhen & Blinds anpassen
    if st.session_state.poker_mode == "tournament":
        st.session_state.t_hand_count = st.session_state.get("t_hand_count", 0) + 1
        hands_per_level = st.session_state.get("t_blind_interval", 4)
        if st.session_state.t_hand_count % hands_per_level == 0:
            st.session_state.t_small_blind *= 2
            st.session_state.message += f"<p style='color: #3498db; font-weight: bold;'>⚠️ BLIND-ANSTIEG! Neue Blinds: {st.session_state.t_small_blind} / {st.session_state.t_small_blind * 2}</p>"

        # Prüfen ob Turniersieger feststeht (nur 1 Spieler übrig)
        remaining = [p for p in st.session_state.players if not p["eliminated"]]
        if len(remaining) == 1:
            st.session_state.tournament_winner = remaining[0]["name"]
            st.session_state.message += f"<h2 style='color: #f1c40f; text-align: center;'>👑 TURNIER-SIEGESKRÖNUNG: {remaining[0]['name']} gewinnt das gesamte Turnier! 🏆</h2>"

    if supabase and st.session_state.players[0]["chips"] > 0 and st.session_state.poker_mode != "tournament":
        try:
            supabase.table("poker_highscores").insert({
                "player_name": st.session_state.players[0]["name"],
                "chips": st.session_state.players[0]["chips"]
            }).execute()
        except Exception:
            pass

def ai_turn():
    idx = st.session_state.active_player_idx
    p = st.session_state.players[idx]
    
    if p["folded"] or p["eliminated"] or p["chips"] <= 0:
        advance_player()
        return

    style = p.get("style", "Aggressiv")
    if style == "Aggressiv":
        action = random.choices(["call", "fold", "raise"], weights=[55, 10, 35])[0]
    elif style == "Konservativ":
        action = random.choices(["call", "fold", "raise"], weights=[50, 40, 10])[0]
    elif style == "Bluff-King":
        action = random.choices(["call", "fold", "raise"], weights=[40, 20, 40])[0]
    else:
        action = random.choices(["call", "fold", "raise"], weights=[60, 20, 20])[0]

    if action == "fold" and st.session_state.current_bet > 0:
        p["folded"] = True
        st.session_state.message = f"🤖 {p['name']} passt (fold)."
    else:
        call_amt = st.session_state.current_bet - p["bet"]
        if call_amt > p["chips"]: call_amt = p["chips"]
        p["chips"] -= call_amt
        p["bet"] += call_amt
        st.session_state.pot += call_amt
        st.session_state.message = f"🤖 {p['name']} geht mit (call)."
        
    advance_player()

def advance_player():
    active = [i for i, p in enumerate(st.session_state.players) if not p["folded"] and not p["eliminated"] and p["chips"] > 0]
    current_idx = st.session_state.active_player_idx
    
    try:
        next_idx_pos = active.index(current_idx) + 1
        if next_idx_pos >= len(active):
            st.session_state.active_player_idx = 0
            if st.session_state.poker_stage != "showdown":
                next_stage()
        else:
            st.session_state.active_player_idx = active[next_idx_pos]
    except ValueError:
        st.session_state.active_player_idx = active[0] if active else 0

    if st.session_state.get("room_id"):
        sync_room_state_to_supabase()

# ==========================================
# HAUPTANSICHT STREAMLIT
# ==========================================
def show():
    st.set_page_config(page_title="Texas Hold'em Poker 3D", layout="wide")
    
    st.sidebar.title("⚙️ Spiel-Optionen")
    god_mode = st.sidebar.checkbox("🚀 Gott-Modus (Immer Startkarten: Ass-Ass)", value=False)
    xray_mode = st.sidebar.checkbox("👀 Röntgenblick (Gegner-Karten aufdecken)", value=False)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("👤 Spieler-Profile")
    my_name = st.sidebar.text_input("Dein Name / Mitgliedsname", value="Du (Spieler)")

    st.markdown("""
    <style>
    .poker-table {
        background: radial-gradient(circle, #1b4d3e 0%, #0b261d 100%);
        border: 12px solid #5c3a21;
        border-radius: 150px;
        padding: 40px;
        box-shadow: inset 0 0 50px rgba(0,0,0,0.8), 0 10px 20px rgba(0,0,0,0.5);
        margin: 20px auto;
        min-height: 350px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .card {
        width: 65px; height: 95px; background: white; border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3); display: inline-flex;
        flex-direction: column; justify-content: space-between; padding: 6px;
        margin: 3px; font-family: sans-serif; font-weight: bold;
        transform: perspective(500px) rotateX(5deg);
        transition: transform 0.2s;
    }
    .card:hover { transform: perspective(500px) rotateX(0deg) scale(1.05); }
    .card-back { background: linear-gradient(135deg, #2c3e50, #000000); color: white; align-items: center; justify-content: center; }
    h4 { white-space: nowrap; }
    </style>
    """, unsafe_allow_html=True)

    st.title("♠️♥️ Texas Hold'em Poker 3D (Cash & Turniere) ♣️♦️")

    if "poker_mode" not in st.session_state:
        st.session_state.poker_mode = "menu"

    if st.session_state.poker_mode == "menu":
        tab_cash, tab_turnier, tab_online, tab_highscores = st.tabs([
            "🎮 Einzelspiel / Mixed", "🏆 Turnier-Modus (Neu)", "🌐 Online Multiplayer", "☁️ Highscores"
        ])

        with tab_cash:
            st.subheader("Lokaler Tisch gegen KI & Mitglieder")
            with st.expander("🛠️ Tisch & Teilnehmer festlegen", expanded=True):
                num_humans = st.number_input("Anzahl Menschlicher Spieler (Mitglieder)", min_value=1, max_value=4, value=1, key="cash_humans")
                num_bots = st.number_input("Anzahl KI-Bots", min_value=0, max_value=4, value=3, key="cash_bots")
                
                bot_configs = []
                chosen_names = random.sample(AI_NAME_POOL, min(num_bots, len(AI_NAME_POOL)))
                for b_i in range(num_bots):
                    b_style = st.selectbox(f"Bot {b_i+1} Stil", PERSONALITIES, key=f"cash_style_{b_i}")
                    bot_configs.append({"name": f"🤖 {chosen_names[b_i]} (KI - {b_style})", "is_ai": True, "style": b_style})

                human_configs = [{"name": my_name if h_i == 0 else f"Mitglied {h_i+1}", "is_ai": False} for h_i in range(num_humans)]
                total_cash_configs = human_configs + bot_configs

            if st.button("🚀 Cash-Game Starten", use_container_width=True, type="primary"):
                init_poker_game(mode="mixed", god_mode=god_mode, player_configs=total_cash_configs, starting_chips=1000)
                st.rerun()

        with tab_turnier:
            st.subheader("🏆 Sepates Vereinsturnier anlegen")
            st.markdown("Im Turniermodus steigen die Blinds in regelmäßigen Abständen an und Spieler schieden bei 0 Chips endgültig aus!")
            
            with st.expander("⚙️ Turnier-Einstellungen", expanded=True):
                t_name = st.text_input("Name des Turniers", value="Vereinsmeisterschaft 2026")
                t_starting_chips = st.number_input("Start-Chips pro Spieler", min_value=500, max_value=10000, value=2000, step=500)
                t_start_sb = st.number_input("Start Small Blind", min_value=5, max_value=100, value=10)
                t_blind_interval = st.number_input("Blind-Erhöhung alle X Hände", min_value=1, max_value=20, value=4)
                
                t_num_humans = st.number_input("Turnier-Teilnehmer (Menschen)", min_value=1, max_value=4, value=1, key="t_humans")
                t_num_bots = st.number_input("Turnier-Teilnehmer (KI-Bots)", min_value=1, max_value=6, value=3, key="t_bots")
                
                t_bot_configs = []
                t_chosen_names = random.sample(AI_NAME_POOL, min(t_num_bots, len(AI_NAME_POOL)))
                for b_i in range(t_num_bots):
                    b_style = st.selectbox(f"Turnier-Bot {b_i+1} Stil", PERSONALITIES, key=f"t_style_{b_i}")
                    t_bot_configs.append({"name": f"🤖 {t_chosen_names[b_i]} (KI - {b_style})", "is_ai": True, "style": b_style})

                t_human_configs = [{"name": my_name if h_i == 0 else f"Mitglied {h_i+1}", "is_ai": False} for h_i in range(t_num_humans)]
                total_tournament_configs = t_human_configs + t_bot_configs

            st.session_state.t_small_blind = t_start_sb
            st.session_state.t_blind_interval = t_blind_interval
            st.session_state.tournament_name = t_name

            if st.button("🏁 Turnier Offiziell Starten", use_container_width=True, type="primary"):
                st.session_state.tournament_winner = None
                st.session_state.t_hand_count = 0
                init_poker_game(mode="tournament", god_mode=god_mode, player_configs=total_tournament_configs, starting_chips=t_starting_chips)
                st.rerun()

        with tab_online:
            st.subheader("🌐 Online-Mitglieder-Tisch (Supabase)")
            room_input = st.text_input("Tisch-Name / Raum-ID eingeben", value="Vereinstisch-1")
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                if st.button("Tisch erstellen / beitreten", use_container_width=True):
                    init_poker_game(mode="multiplayer", god_mode=god_mode, player_configs=None, room_id=room_input)
                    st.rerun()
            with col_r2:
                if st.button("Tisch-Daten laden", use_container_width=True):
                    st.session_state.room_id = room_input
                    if load_room_state_from_supabase():
                        st.success("Tisch erfolgreich geladen!")
                        st.rerun()
                    else:
                        st.warning("Kein aktiver Tisch mit dieser ID gefunden.")

        with tab_highscores:
            st.subheader("☁️ Supabase Highscores")
            if supabase:
                try:
                    res = supabase.table("poker_highscores").select("*").order("chips", desc=True).limit(5).execute()
                    if res.data:
                        for idx, row in enumerate(res.data, 1):
                            st.write(f"**{idx}. {row['player_name']}** – {row['chips']} Chips")
                    else:
                        st.info("Noch keine Highscores vorhanden.")
                except Exception:
                    st.warning("Highscore-Tabelle konnte nicht geladen werden.")
            else:
                st.warning("Keine Supabase Verbindung konfiguriert.")
        return

    if st.button("⬅️ Zurück zum Hauptmenü"):
        st.session_state.poker_mode = "menu"
        st.session_state.room_id = None
        st.rerun()

    if st.session_state.get("room_id"):
        if st.button("🔄 Online-Status aktualisieren (Tisch prüfen)"):
            load_room_state_from_supabase()
            st.rerun()

    # Turnierinfos anzeigen, falls im Turniermodus
    if st.session_state.poker_mode == "tournament":
        t_name = st.session_state.get("tournament_name", "Vereinsturnier")
        t_sb = st.session_state.get("t_small_blind", 10)
        t_hand = st.session_state.get("t_hand_count", 0)
        st.sidebar.markdown("---")
        st.sidebar.subheader(f"🏆 {t_name}")
        st.sidebar.write(f"Hand: **#{t_hand + 1}**")
        st.sidebar.write(f"Aktuelle Blinds: **{t_sb} / {t_sb*2}**")
        
        # Turnier-Rangliste in Sidebar
        st.sidebar.markdown("### 📊 Teilnehmer & Status")
        for p in st.session_state.players:
            status_icon = "❌ (Ausgeschieden)" if p["eliminated"] else f"💰 {p['chips']} Chips"
            st.sidebar.write(f"- **{p['name']}**: {status_icon}")

    col_info1, col_info2, col_info3 = st.columns(3)
    col_info1.metric("Status", st.session_state.poker_stage.upper())
    col_info2.markdown(f"### Pot: 💰 {st.session_state.pot} Chips")
    col_info3.metric("Aktueller Einsatz", f"{st.session_state.current_bet} Chips")

    community_html = "".join([card_html(c) for c in st.session_state.community_cards])
    if not community_html:
        community_html = "<span style='color: #a3e4d7; font-style: italic;'>Wartet auf Flop...</span>"

    st.markdown(f"""
    <div class="poker-table">
        <div style="color: white; margin-bottom: 15px; font-weight: bold; letter-spacing: 2px;">COMMUNITY CARDS</div>
        <div style="display: flex; gap: 8px;">{community_html}</div>
    </div>
    """, unsafe_allow_html=True)

    players = st.session_state.players
    num_players = len(players)
    cols = st.columns(num_players)
    active_idx = st.session_state.active_player_idx

    for i, p in enumerate(players):
        with cols[i]:
            if p["eliminated"]:
                st.markdown(f"""
                <div style="border: 1px solid rgba(255,0,0,0.3); background: rgba(50,0,0,0.4); padding: 10px; border-radius: 10px; text-align: center; color: #e74c3c;">
                    <h4>{p['name']}</h4>
                    <p><b>AUSGESCHIEDEN</b></p>
                    <div style="font-size: 24px; margin: 10px 0;">💀</div>
                </div>
                """, unsafe_allow_html=True)
                continue

            border_color = "2px solid #f1c40f" if i == active_idx else "1px solid rgba(255,255,255,0.2)"
            bg_color = "rgba(0,0,0,0.4)" if not p["folded"] else "rgba(100,100,100,0.2)"
            
            show_cards = (not p["is_ai"] and p["name"] == my_name) or (st.session_state.poker_stage == "showdown") or xray_mode
            cards_str = "".join([card_html(c if show_cards else None) for c in p["cards"]])
            
            st.markdown(f"""
            <div style="border: {border_color}; background: {bg_color}; padding: 10px; border-radius: 10px; text-align: center; color: white;">
                <h4>{p['name']}</h4>
                <p>💰 {p['chips']} Chips</p>
                <div style="display: flex; justify-content: center; margin: 5px 0;">{cards_str}</div>
                <p style="font-size: 12px; color: {'#e74c3c' if p['folded'] else '#2ecc71'};">{'Gefoldet' if p['folded'] else f'Einsatz: {p["bet"]}'}</p>
            </div>
            """, unsafe_allow_html=True)

    if st.session_state.poker_stage == "showdown":
        st.markdown(st.session_state.message, unsafe_allow_html=True)
    else:
        st.info(st.session_state.message)

    # Wenn Turniersieger feststeht, Spiel pausieren
    if st.session_state.get("tournament_winner"):
        st.success(f"Das Turnier wurde von **{st.session_state.tournament_winner}** gewonnen!")
        if st.button("🔄 Zurück zum Hauptmenü", type="primary", use_container_width=True):
            st.session_state.poker_mode = "menu"
            st.rerun()
        return

    current_player = players[active_idx]

    if st.session_state.poker_stage != "showdown" and current_player["is_ai"] and not current_player["folded"] and not current_player["eliminated"]:
        with st.spinner(f"{current_player['name']} überlegt..."):
            time.sleep(1.0)
            ai_turn()
            st.rerun()

    if st.session_state.poker_stage != "showdown" and not current_player["is_ai"] and not current_player["eliminated"]:
        if current_player["name"] == my_name or st.session_state.poker_mode in ["mixed", "tournament"]:
            st.markdown(f"### 👉 Du bist am Zug ({current_player['name']})!")
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            call_amt = st.session_state.current_bet - current_player["bet"]
            
            with col_btn1:
                if st.button("💵 Check / Call", use_container_width=True, key=f"call_{active_idx}"):
                    if call_amt > current_player["chips"]: call_amt = current_player["chips"]
                    current_player["chips"] -= call_amt
                    current_player["bet"] += call_amt
                    st.session_state.pot += call_amt
                    st.session_state.message = f"{current_player['name']} ist mitgegangen."
                    advance_player()
                    st.rerun()
                    
            with col_btn2:
                if st.button("📈 Raise (+50)", use_container_width=True, key=f"raise_{active_idx}"):
                    raise_total = call_amt + 50
                    if raise_total > current_player["chips"]: raise_total = current_player["chips"]
                    current_player["chips"] -= raise_total
                    current_player["bet"] += raise_total
                    st.session_state.current_bet = current_player["bet"]
                    st.session_state.pot += raise_total
                    st.session_state.message = f"{current_player['name']} hat erhöht!"
                    advance_player()
                    st.rerun()
                    
            with col_btn3:
                if st.button("🚪 Fold (Aufgeben)", use_container_width=True, key=f"fold_{active_idx}"):
                    current_player["folded"] = True
                    st.session_state.message = f"{current_player['name']} hat die Runde aufgegeben."
                    advance_player()
                    st.rerun()
        else:
            st.info(f"Warte auf Zug von **{current_player['name']}**...")

    if st.session_state.poker_stage == "showdown":
        if st.button("🔄 Nächste Hand starten", type="primary", use_container_width=True):
            init_poker_game(st.session_state.poker_mode, god_mode, player_configs=st.session_state.players, room_id=st.session_state.get("room_id"))
            st.rerun()

if __name__ == "__main__":
    show()