import random
import streamlit as st

try:
  from database import supabase
except ImportError:
  supabase = None


# ==========================================
# HILFSFUNKTIONEN & SPIELOGIK
# ==========================================
def check_winner(board):
  # Gewinnlinien (Zeilen, Spalten, Diagonalen)
  linien = [
      (0, 1, 2),
      (3, 4, 5),
      (6, 7, 8),  # Zeilen
      (0, 3, 6),
      (1, 4, 7),
      (2, 5, 8),  # Spalten
      (0, 4, 8),
      (2, 4, 6),  # Diagonalen
  ]
  for a, b, c in linien:
    if board[a] and board[a] == board[b] == board[c]:
      return board[a]
  if "" not in board:
    return "Unentschieden"
  return None


def ki_zug(board):
  # 1. Prüfen, ob KI in einem Zug gewinnen kann
  for i in range(9):
    if board[i] == "":
      board[i] = "O"
      if check_winner(board) == "O":
        return i
      board[i] = ""

  # 2. Prüfen, ob Spieler im nächsten Zug gewinnen kann und blockieren
  for i in range(9):
    if board[i] == "":
      board[i] = "X"
      if check_winner(board) == "X":
        board[i] = ""
        return i
      board[i] = ""

  # 3. Zentrum nehmen, falls frei
  if board[4] == "":
    return 4

  # 4. Ecken nehmen
  ecken = [0, 2, 6, 8]
  freie_ecken = [e for e in ecken if board[e] == ""]
  if freie_ecken:
    return random.choice(freie_ecken)

  # 5. Restliche Felder (Ränder)
  freie_felder = [i for i, x in enumerate(board) if x == ""]
  return random.choice(freie_felder) if freie_felder else None


def reset_spiel():
  st.session_state.ttt_board = [""] * 9
  st.session_state.ttt_am_zug = "X"
  st.session_state.ttt_gewinner = None


# ==========================================
# HAUPTFUNKTION DER APP
# ==========================================
def show():
  st.header("❌ Tic-Tac-Toe Arena ⭕")
  st.markdown(
      "Spiele eine Runde Tic-Tac-Toe – entweder entspannt gegen den Computer"
      " oder im Duell gegen ein anderes Mitglied!"
  )
  st.divider()

  # Session State initialisieren
  if "ttt_board" not in st.session_state:
    reset_spiel()
  if "ttt_modus" not in st.session_state:
    st.session_state.ttt_modus = "menu"
  if "ttt_score_x" not in st.session_state:
    st.session_state.ttt_score_x = 0
  if "ttt_score_o" not in st.session_state:
    st.session_state.ttt_score_o = 0
  if "ttt_score_draw" not in st.session_state:
    st.session_state.ttt_score_draw = 0

  # ----------------------------------------
  # MENÜ: MODUSWÄHler
  # ----------------------------------------
  if st.session_state.ttt_modus == "menu":
    col1, col2 = st.columns(2)

    with col1:
      st.info("🤖 **Einzelspieler**\n\nTritt gegen die Computer-KI an.")
      if st.button(
          "Gegen KI spielen", use_container_width=True, type="primary"
      ):
        st.session_state.ttt_modus = "single"
        reset_spiel()
        st.rerun()

    with col2:
      st.warning(
          "👥 **Multiplayer**\n\nLokal an einem Gerät oder online über"
          " Datenbank."
      )
      if st.button("Multiplayer starten", use_container_width=True):
        st.session_state.ttt_modus = "multi_menu"
        st.rerun()

  # ----------------------------------------
  # EINZELSPIELER (VS KI)
  # ----------------------------------------
  elif st.session_state.ttt_modus == "single":
    if st.button("⬅️ Zurück zur Moduswahl"):
      st.session_state.ttt_modus = "menu"
      st.rerun()

    st.subheader("🤖 Einzelspieler vs. KI")

    # Punktestand Anzeige
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Spieler (X)", st.session_state.ttt_score_x)
    sc2.metric("Unentschieden", st.session_state.ttt_score_draw)
    sc3.metric("Computer (O)", st.session_state.ttt_score_o)

    st.write(
        f"Aktuell am Zug: **{'Du (X)' if st.session_state.ttt_am_zug == 'X' else 'Computer (O)'}**"
    )

    # Spielfeld rendern (3x3 Grid)
    board = st.session_state.ttt_board
    gewinner = check_winner(board)

    for r in range(3):
      cols = st.columns(3)
      for c in range(3):
        idx = r * 3 + c
        with cols[c]:
          label = board[idx] if board[idx] != "" else " "
          disabled = (
              board[idx] != ""
              or gewinner is not None
              or st.session_state.ttt_am_zug == "O"
          )

          if st.button(label, key=f"cell_{idx}", disabled=disabled, use_container_width=True):
            if board[idx] == "" and gewinner is None:
              board[idx] = "X"
              st.session_state.ttt_am_zug = "O"
              
              # Prüfen nach Spielerauswahl
              gewinner = check_winner(board)
              if gewinner:
                st.session_state.ttt_gewinner = gewinner
                if gewinner == "X":
                  st.session_state.ttt_score_x += 1
                elif gewinner == "O":
                  st.session_state.ttt_score_o += 1
                else:
                  st.session_state.ttt_score_draw += 1
              else:
                # KI-Zug direkt ausführen
                ki_idx = ki_zug(board)
                if ki_idx is not None:
                  board[ki_idx] = "O"
                  st.session_state.ttt_am_zug = "X"
                  gewinner = check_winner(board)
                  if gewinner:
                    st.session_state.ttt_gewinner = gewinner
                    if gewinner == "X":
                      st.session_state.ttt_score_x += 1
                    elif gewinner == "O":
                      st.session_state.ttt_score_o += 1
                    else:
                      st.session_state.ttt_score_draw += 1
              st.rerun()

    if gewinner:
      if gewinner == "Unentschieden":
        st.warning("🤝 Das Spiel endet unentschieden!")
      else:
        st.success(
            f"🏆 Gewinner: {'Du (Spieler X)' if gewinner == 'X' else 'Computer (O)'}!"
        )

      if st.button("🔄 Nächste Runde", type="primary"):
        reset_spiel()
        st.rerun()

  # ----------------------------------------
  # MULTIPLAYER MENÜ (Lokal oder Online)
  # ----------------------------------------
  elif st.session_state.ttt_modus == "multi_menu":
    if st.button("⬅️ Zurück zum Menü"):
      st.session_state.ttt_modus = "menu"
      st.rerun()

    st.subheader("👥 Multiplayer Auswahl")
    tab_lokal, tab_online = st.tabs(["Lokal (Gleiches Gerät)", "Online (Supabase Raum)"])

    with tab_lokal:
      st.write("Spielt abwechselnd zu zweit an einem Bildschirm.")
      if st.button("Lokales Match starten", type="primary", use_container_width=True):
        st.session_state.ttt_modus = "multi_local"
        reset_spiel()
        st.rerun()

    with tab_online:
      if supabase is None:
        st.error("Supabase ist in diesem Environment nicht konfiguriert.")
      else:
        st.write("Erstelle einen Raum oder trete einem bestehenden Raum bei, um gegen ein anderes Mitglied zu spielen.")
        raum_code = st.text_input("Raum-Code (z.B. TTT-VEREIN)", value="TTT-123")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
          if st.button("Raum erstellen / beitreten", type="primary", use_container_width=True):
            st.session_state.ttt_room = raum_code
            st.session_state.ttt_modus = "multi_online"
            st.rerun()

  # ----------------------------------------
  # MULTIPLAYER LOKAL (Pass-and-Play)
  # ----------------------------------------
  elif st.session_state.ttt_modus == "multi_local":
    if st.button("⬅️ Zurück zur Auswahl"):
      st.session_state.ttt_modus = "multi_menu"
      st.rerun()

    st.subheader("👥 Lokales Multiplayer-Duell")
    st.write(f"Am Zug: **Spieler {st.session_state.ttt_am_zug}**")

    board = st.session_state.ttt_board
    gewinner = check_winner(board)

    for r in range(3):
      cols = st.columns(3)
      for c in range(3):
        idx = r * 3 + c
        with cols[c]:
          label = board[idx] if board[idx] != "" else " "
          disabled = board[idx] != "" or gewinner is not None

          if st.button(label, key=f"local_cell_{idx}", disabled=disabled, use_container_width=True):
            if board[idx] == "" and gewinner is None:
              board[idx] = st.session_state.ttt_am_zug
              gewinner = check_winner(board)
              if gewinner:
                st.session_state.ttt_gewinner = gewinner
              else:
                st.session_state.ttt_am_zug = "O" if st.session_state.ttt_am_zug == "X" else "X"
              st.rerun()

    if gewinner:
      if gewinner == "Unentschieden":
        st.warning("🤝 Unentschieden!")
      else:
        st.success(f"🏆 Spieler {gewinner} hat gewonnen!")
      if st.button("🔄 Nächste Runde", type="primary"):
        reset_spiel()
        st.rerun()

  # ----------------------------------------
  # MULTIPLAYER ONLINE (Supabase Sync)
  # ----------------------------------------
  elif st.session_state.ttt_modus == "multi_online":
    if st.button("⬅️ Raum verlassen"):
      st.session_state.ttt_modus = "multi_menu"
      st.rerun()

    room = st.session_state.get("ttt_room", "TEST")
    st.subheader(f"🌐 Online-Duell [Raum: {room}]")

    # Daten aus Supabase laden
    try:
      res = supabase.table("tictactoe_rooms").select("*").eq("room_code", room).execute()
      if not res.data:
        # Raum initialisieren falls nicht vorhanden
        initial_data = {
            "room_code": room,
            "board": [""] * 9,
            "am_zug": "X",
            "gewinner": None
        }
        supabase.table("tictactoe_rooms").insert(initial_data).execute()
        room_data = initial_data
      else:
        room_data = res.data[0]
    except Exception as e:
      st.error(f"Datenbankfehler: {e}")
      return

    board = room_data["board"]
    am_zug = room_data["am_zug"]
    gewinner = room_data["gewinner"]

    if st.button("🔄 Spielfeld aktualisieren"):
      st.rerun()

    st.write(f"Am Zug: **Spieler {am_zug}**")

    for r in range(3):
      cols = st.columns(3)
      for c in range(3):
        idx = r * 3 + c
        with cols[c]:
          label = board[idx] if board[idx] != "" else " "
          disabled = board[idx] != "" or gewinner is not None

          if st.button(label, key=f"online_cell_{idx}", disabled=disabled, use_container_width=True):
            if board[idx] == "" and gewinner is None:
              board[idx] = am_zug
              n_zug = "O" if am_zug == "X" else "X"
              n_gewinner = check_winner(board)
              
              # In Supabase speichern
              supabase.table("tictactoe_rooms").update({
                  "board": board,
                  "am_zug": n_zug,
                  "gewinner": n_gewinner
              }).eq("room_code", room).execute()
              st.rerun()

    if gewinner:
      if gewinner == "Unentschieden":
        st.warning("🤝 Unentschieden!")
      else:
        st.success(f"🏆 Spieler {gewinner} hat gewonnen!")
      if st.button("🔄 Raum zurücksetzen", type="primary"):
        supabase.table("tictactoe_rooms").update({
            "board": [""] * 9,
            "am_zug": "X",
            "gewinner": None
        }).eq("room_code", room).execute()
        reset_spiel()
        st.rerun()


if __name__ == "__main__":
  show()