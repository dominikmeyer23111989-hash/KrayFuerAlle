import streamlit as st
from datetime import datetime
import requests
import pandas as pd
from supabase import create_client, Client

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        return None

def get_supabase_members():
    supabase = get_supabase_client()
    if not supabase:
        return ["Jan", "Sarah", "Tim", "Lisa", "Markus", "Celine"]
    
    try:
        response = supabase.table("mitglieder").select("vorname, nachname").execute()
        if response.data:
            names = [f"{row.get('vorname', '')} {row.get('nachname') or ''}".strip() for row in response.data]
            if names:
                return names
    except Exception as e:
        st.error(f"Fehler beim Laden der Mitglieder aus Supabase: {e}")
    
    return ["Jan", "Sarah", "Tim", "Lisa", "Markus", "Celine"]

def load_tips_from_supabase():
    supabase = get_supabase_client()
    if not supabase:
        return {}
    try:
        response = supabase.table("tipps").select("*").execute()
        tips = {}
        if response.data:
            for row in response.data:
                key = (row["tipper"], row["league_shortcut"], row["match_id"])
                tips[key] = (row["home_tip"], row["away_tip"])
        return tips
    except Exception:
        return {}

def save_tip_to_supabase(tipper, league_shortcut, match_id, home_tip, away_tip):
    supabase = get_supabase_client()
    if not supabase:
        return
    try:
        supabase.table("tipps").upsert({
            "tipper": tipper,
            "league_shortcut": league_shortcut,
            "match_id": match_id,
            "home_tip": home_tip,
            "away_tip": away_tip
        }, on_conflict="tipper,league_shortcut,match_id").execute()
    except Exception as e:
        st.error(f"Fehler beim Speichern in Supabase: {e}")

def get_current_season():
    now = datetime.now()
    year = now.year
    month = now.month
    if month >= 7:
        return f"{year}/{year + 1}"
    else:
        return f"{year - 1}/{year}"

@st.cache_data(ttl=3600)
def fetch_matches_from_api(league_shortcut):
    now = datetime.now()
    year = now.year if now.month >= 7 else now.year - 1
    url = f"https://api.openligadb.de/getmatchdata/{league_shortcut}/{year}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def calculate_tip_points(tip_home, tip_away, res_home, res_away):
    if tip_home is None or tip_away is None or res_home is None or res_away is None:
        return 0, 0, 0, 0
    
    if tip_home == res_home and tip_away == res_away:
        return 3, 1, 0, 0
    
    tip_tendency = 1 if tip_home > tip_away else (-1 if tip_home < tip_away else 0)
    res_tendency = 1 if res_home > res_away else (-1 if res_home < res_away else 0)
    
    if tip_tendency != res_tendency:
        return 0, 0, 0, 0
    
    tip_diff = tip_home - tip_away
    res_diff = res_home - res_away
    
    if tip_diff == res_diff:
        return 2, 0, 1, 0
    
    return 1, 0, 0, 1

def calculate_league_table(matches):
    table_dict = {}
    for match in matches:
        t1 = match.get("team1", {}).get("teamName")
        t2 = match.get("team2", {}).get("teamName")
        if not t1 or not t2:
            continue
        
        for team in [t1, t2]:
            if team not in table_dict:
                table_dict[team] = {"Sp": 0, "S": 0, "U": 0, "N": 0, "Tore": 0, "Gegentore": 0, "Pkt": 0}
        
        results = match.get("matchResults", [])
        if results:
            final_res = next((r for r in results if r.get("resultID") == 2), results[-1])
            res_h = final_res.get('pointsTeam1')
            res_a = final_res.get('pointsTeam2')
            
            if res_h is not None and res_a is not None:
                table_dict[t1]["Sp"] += 1
                table_dict[t2]["Sp"] += 1
                table_dict[t1]["Tore"] += res_h
                table_dict[t1]["Gegentore"] += res_a
                table_dict[t2]["Tore"] += res_a
                table_dict[t2]["Gegentore"] += res_h
                
                if res_h > res_a:
                    table_dict[t1]["S"] += 1
                    table_dict[t1]["Pkt"] += 3
                    table_dict[t2]["N"] += 1
                elif res_h < res_a:
                    table_dict[t2]["S"] += 1
                    table_dict[t2]["Pkt"] += 3
                    table_dict[t1]["N"] += 1
                else:
                    table_dict[t1]["U"] += 1
                    table_dict[t1]["Pkt"] += 1
                    table_dict[t2]["U"] += 1
                    table_dict[t2]["Pkt"] += 1
                    
    rows = []
    for team, stats in table_dict.items():
        diff = stats["Tore"] - stats["Gegentore"]
        rows.append({
            "Verein": team,
            "Sp": stats["Sp"],
            "S": stats["S"],
            "U": stats["U"],
            "N": stats["N"],
            "Tore": f"{stats['Tore']}:{stats['Gegentore']}",
            "Diff": diff,
            "Pkt": stats["Pkt"],
            "_raw_tore": stats["Tore"],
            "_raw_gt": stats["Gegentore"]
        })
        
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["Pkt", "Diff", "_raw_tore", "Verein"], ascending=[False, False, False, True]).reset_index(drop=True)
        df.insert(0, "Platz", range(1, len(df) + 1))
        df = df.drop(columns=["_raw_tore", "_raw_gt"])
    return df

def show():
    st.markdown("""
        <style>
            .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1100px; }
            .stTabs [data-baseweb="tab-list"] { gap: 10px; }
            .stTabs [data-baseweb="tab"] { background-color: #f8f9fa; border-radius: 4px; padding: 10px 20px; font-weight: bold; }
            .stTabs [aria-selected="true"] { background-color: #212529 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

    season = get_current_season()
    members = get_supabase_members()
    
    user_tips = load_tips_from_supabase()

    if "prev_ranks" not in st.session_state:
        st.session_state.prev_ranks = {m: i + 1 for i, m in enumerate(members)}

    st.title("⚽ Bundesliga & RWE Tippspiel")
    st.markdown(f"**Aktuelle Saison:** `{season}` | **Aktive Tipper (Mitglieder):** {len(members)}")
    st.markdown("---")

    tab_tippabgabe, tab_tabelle, tab_liga_tabelle, tab_spielplan, tab_regeln = st.tabs([
        "📝 Tipps abgeben", 
        "🏆 Tippspiel-Wertung", 
        "📊 Ligatabelle", 
        "📅 Spielplan & Ergebnisse", 
        "📖 Punkteregeln"
    ])

    with tab_tippabgabe:
        st.subheader("Tippabgabe für den aktuellen Spieltag")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_tipper = st.selectbox("Mitglied (Tipper) auswählen:", members)
        with col2:
            league_choice = st.selectbox("Wettbewerb:", ["1. Bundesliga", "2. Bundesliga", "Rot-Weiss Essen (Sondertipp - 3. Liga)"])

        shortcut = "bl1"
        if "2. Bundesliga" in league_choice:
            shortcut = "bl2"
        elif "Rot-Weiss Essen" in league_choice:
            shortcut = "liga3"

        matches = fetch_matches_from_api(shortcut)
        
        if matches:
            matchdays = sorted(list(set(m.get("group", {}).get("groupOrderID", 1) for m in matches)))
            selected_matchday = st.selectbox("Spieltag wählen:", matchdays, index=0)
            
            current_matches = [m for m in matches if m.get("group", {}).get("groupOrderID") == selected_matchday]
            
            if "Rot-Weiss Essen" in league_choice:
                current_matches = [m for m in current_matches if "Essen" in m.get("team1", {}).get("teamName", "") or "Essen" in m.get("team2", {}).get("teamName", "")]
                if not current_matches:
                    st.info("Keine anstehenden RWE-Spiele für diesen Spieltag gefunden. Zeige alle RWE-Spiele der Saison:")
                    current_matches = [m for m in matches if "Essen" in m.get("team1", {}).get("teamName", "") or "Essen" in m.get("team2", {}).get("teamName", "")]

            st.markdown(f"### Spiele für {league_choice} (Spieltag {selected_matchday})")

            if current_matches:
                with st.form(f"tipp_form_{shortcut}_{selected_matchday}"):
                    form_tips = {}
                    for match in current_matches:
                        match_id = match.get("matchID")
                        home = match.get("team1", {}).get("teamName", "Heimteam")
                        away = match.get("team2", {}).get("teamName", "Gastteam")
                        
                        existing_tip = user_tips.get((selected_tipper, shortcut, match_id), (1, 1))

                        c_home, c_th, c_colon, c_ta, c_away = st.columns([3, 1, 0.3, 1, 3])
                        
                        with c_home:
                            st.markdown(f"<div style='text-align: right; padding-top: 10px; font-weight: bold;'>{home}</div>", unsafe_allow_html=True)
                        with c_th:
                            h_str = st.text_input(f"h_{match_id}", value=str(existing_tip[0]), key=f"t_h_{match_id}", label_visibility="collapsed", max_chars=2)
                        with c_colon:
                            st.markdown("<div style='text-align: center; padding-top: 10px; font-weight: bold;'>:</div>", unsafe_allow_html=True)
                        with c_ta:
                            a_str = st.text_input(f"a_{match_id}", value=str(existing_tip[1]), key=f"t_a_{match_id}", label_visibility="collapsed", max_chars=2)
                        with c_away:
                            st.markdown(f"<div style='text-align: left; padding-top: 10px; font-weight: bold;'>{away}</div>", unsafe_allow_html=True)
                        
                        try:
                            h_val = int(h_str) if h_str.strip() != "" else 0
                        except ValueError:
                            h_val = 0
                            
                        try:
                            a_val = int(a_str) if a_str.strip() != "" else 0
                        except ValueError:
                            a_val = 0

                        form_tips[match_id] = (h_val, a_val)
                        st.markdown("---")
                    
                    submitted = st.form_submit_button("Tipps speichern 💾")
                    if submitted:
                        for m_id, tip_vals in form_tips.items():
                            save_tip_to_supabase(selected_tipper, shortcut, m_id, tip_vals[0], tip_vals[1])
                        st.success(f"Tipps für **{selected_tipper}** erfolgreich in Supabase gespeichert!")
                        st.rerun()
            else:
                st.warning("Keine Spiele für diese Auswahl gefunden.")
        else:
            st.warning("Verbindung zur Fußball-Datenbank konnte nicht aufgebaut werden.")

    with tab_tabelle:
        st.subheader(f"🏆 Tippspiel-Gesamtwertung – Saison {season}")
        st.markdown("Automatische Auswertung aller Tipps der Mitglieder im Vergleich zu den echten Spielergebnissen.")

        all_shortcuts = ["bl1", "bl2", "liga3"]
        all_matches_cache = {sc: fetch_matches_from_api(sc) for sc in all_shortcuts}

        table_data = []
        for m in members:
            total_points = 0
            t3, t2, t1 = 0, 0, 0
            
            for sc in all_shortcuts:
                matches_list = all_matches_cache.get(sc, [])
                for match in matches_list:
                    match_id = match.get("matchID")
                    tip = user_tips.get((m, sc, match_id))
                    
                    if tip:
                        results = match.get("matchResults", [])
                        if results:
                            final_res = next((r for r in results if r.get("resultID") == 2), results[-1])
                            res_h = final_res.get('pointsTeam1')
                            res_a = final_res.get('pointsTeam2')
                            
                            if res_h is not None and res_a is not None:
                                pts, ex, diff, tend = calculate_tip_points(tip[0], tip[1], res_h, res_a)
                                total_points += pts
                                t3 += ex
                                t2 += diff
                                t1 += tend

            table_data.append({
                "Tipper (Mitglied)": m,
                "Punkte": total_points,
                "3er (Exakt)": t3,
                "2er (Diff)": t2,
                "1er (Tendenz)": t1
            })
        
        df_ranking = pd.DataFrame(table_data).sort_values(by=["Punkte", "3er (Exakt)"], ascending=False).reset_index(drop=True)
        
        ranking_rows = []
        new_prev_ranks = {}
        for new_idx, row in df_ranking.iterrows():
            current_rank = new_idx + 1
            member_name = row["Tipper (Mitglied)"]
            old_rank = st.session_state.prev_ranks.get(member_name, current_rank)
            
            diff_rank = old_rank - current_rank
            if diff_rank > 0:
                trend = f"▲ +{diff_rank}"
            elif diff_rank < 0:
                trend = f"▼ {diff_rank}"
            else:
                trend = "-"
            
            new_prev_ranks[member_name] = current_rank
            
            ranking_rows.append({
                "Rang": current_rank,
                "Trend": trend,
                "Tipper (Mitglied)": member_name,
                "Punkte": row["Punkte"],
                "3er (Exakt)": row["3er (Exakt)"],
                "2er (Diff)": row["2er (Diff)"],
                "1er (Tendenz)": row["1er (Tendenz)"]
            })
        
        st.session_state.prev_ranks = new_prev_ranks
        df_final_ranking = pd.DataFrame(ranking_rows)

        st.dataframe(df_final_ranking, use_container_width=True, height=450)

    with tab_liga_tabelle:
        st.subheader("📊 Aktuelle Ligatabelle")
        table_league_choice = st.selectbox("Wettbewerb für Tabelle wählen:", ["1. Bundesliga", "2. Bundesliga", "3. Liga (inkl. Rot-Weiss Essen)"], key="table_league_choice")
        
        t_shortcut = "bl1"
        if "2. Bundesliga" in table_league_choice:
            t_shortcut = "bl2"
        elif "3. Liga" in table_league_choice:
            t_shortcut = "liga3"

        t_matches = fetch_matches_from_api(t_shortcut)
        if t_matches:
            df_league_table = calculate_league_table(t_matches)
            if not df_league_table.empty:
                st.dataframe(df_league_table, use_container_width=True, height=500)
            else:
                st.info("Noch keine Tabellendaten für diese Saison verfügbar.")
        else:
            st.info("Keine Spieldaten verfügbar.")

    with tab_spielplan:
        st.subheader("📅 Live-Spielplan & Offizielle Ergebnisse")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            view_league_choice = st.selectbox("Wettbewerb wählen:", ["1. Bundesliga", "2. Bundesliga", "Rot-Weiss Essen (Sondertipp)"], key="view_league")
        
        v_shortcut = "bl1"
        if "2. Bundesliga" in view_league_choice:
            v_shortcut = "bl2"
        elif "Rot-Weiss Essen" in view_league_choice:
            v_shortcut = "liga3"

        v_matches = fetch_matches_from_api(v_shortcut)
        if v_matches:
            if "Rot-Weiss Essen" in view_league_choice:
                v_matches = [m for m in v_matches if "Essen" in m.get("team1", {}).get("teamName", "") or "Essen" in m.get("team2", {}).get("teamName", "")]

            if v_matches:
                v_matchdays = sorted(list(set(m.get("group", {}).get("groupOrderID", 1) for m in v_matches)))
                with col_v2:
                    selected_v_matchday = st.selectbox("Spieltag wählen:", v_matchdays, key="view_matchday_select")
                
                current_v_matches = [m for m in v_matches if m.get("group", {}).get("groupOrderID") == selected_v_matchday]
                
                match_data_rows = []
                for m in current_v_matches:
                    h_name = m.get("team1", {}).get("teamName", "")
                    a_name = m.get("team2", {}).get("teamName", "")
                    
                    results = m.get("matchResults", [])
                    res_str = "Noch nicht gespielt"
                    if results:
                        final_res = next((r for r in results if r.get("resultID") == 2), results[-1])
                        res_str = f"{final_res.get('pointsTeam1')} : {final_res.get('pointsTeam2')}"
                    
                    match_data_rows.append({"Heim": h_name, "Ergebnis": res_str, "Gast": a_name})
                
                if match_data_rows:
                    st.markdown(f"### Spiele für {view_league_choice} (Spieltag {selected_v_matchday})")
                    st.dataframe(pd.DataFrame(match_data_rows), use_container_width=True)
                else:
                    st.info("Keine Spiele für diesen Spieltag gefunden.")
            else:
                st.info("Keine Spiele gefunden.")
        else:
            st.info("Keine Spieldaten verfügbar.")

    with tab_regeln:
        st.subheader("Offizielle Punkteregeln")
        st.markdown("""
        Für jeden abgegebenen Tipp sammelt ihr in der 1. Bundesliga, 2. Bundesliga und beim RWE-Sondertipp Punkte nach folgendem System:

        *   **0 Punkte – Völlig falsch:** Die Tendenz ist komplett falsch getippt. (Tipp `2:3`, Ergebnis `1:0`)
        *   **1 Punkt – Richtige Tendenz:** Die Tendenz stimmt, aber Tordifferenz und Ergebnis nicht. (Tipp `0:3`, Ergebnis `1:2`)
        *   **2 Punkte – Tendenz & Tordifferenz:** Tendenz und Tordifferenz stimmen überein. (Tipp `2:0`, Ergebnis `3:1`)
        *   **3 Punkte – Exaktes Ergebnis:** Das genaue Endergebnis wurde perfekt vorausgesagt. (Tipp `2:0`, Ergebnis `2:0`)
        """)

if __name__ == "__main__":
    show()