import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

def get_supabase_members():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return ["Jan", "Sarah", "Tim", "Lisa"]
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("mitglieder").select("vorname, nachname").execute()
        if response.data:
            return [f"{row.get('vorname', '')} {row.get('nachname') or ''}".strip() for row in response.data]
    except Exception as e:
        st.error(f"Fehler beim Laden der Mitglieder aus Supabase: {e}")
    
    return ["Jan", "Sarah", "Tim", "Lisa"]

def show():
    st.markdown("""
        <style>
            .block-container { padding-top: 0rem; padding-bottom: 0rem; max-width: 1050px; }
        </style>
    """, unsafe_allow_html=True)

    members = get_supabase_members()
    
    ai_bots = [
        "🤖 Robo-Rainer (KI-Bot)",
        "🤖 Cyber-Tom (KI-Bot)",
        "🤖 Dice-Matrix (KI-Bot)",
        "🤖 Kniffel-King (KI-Bot)"
    ]
    
    all_tournament_participants = members + ai_bots
    
    tournament_options_html = "".join([f'<option value="{p}">{p}</option>' for p in all_tournament_participants])
    ai_options_html = "".join([f'<option value="{b}">{b}</option>' for b in ai_bots])

    kniffel_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            background-color: #f0f2f5;
            color: #000;
            font-family: Arial, Helvetica, sans-serif;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            margin: 0;
            padding: 20px 10px;
            min-height: 100vh;
        }}
        .cabinet {{
            background: #ffffff;
            border: 2px solid #000;
            border-radius: 4px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 750px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        
        .screen {{
            display: none;
            flex-direction: column;
            align-items: center;
            width: 100%;
        }}
        .screen.active {{
            display: flex;
        }}

        h1 {{ 
            color: #000; 
            font-size: 20px; 
            text-align: center; 
            margin: 0 0 5px 0; 
            font-weight: bold;
            text-transform: uppercase;
        }}
        .subtitle {{ color: #555; font-size: 12px; margin-bottom: 15px; text-align: center; }}
        
        .menu-group {{
            width: 100%;
            margin-bottom: 14px;
        }}
        .menu-label {{
            font-size: 11px;
            color: #333;
            margin-bottom: 4px;
            text-transform: uppercase;
            font-weight: bold;
        }}
        .select-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            width: 100%;
        }}
        .select-btn {{
            background: #f8f9fa;
            color: #333;
            border: 1px solid #ccc;
            padding: 8px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 12px;
            cursor: pointer;
            text-align: center;
        }}
        .select-btn:hover {{ background: #e2e6ea; }}
        .select-btn.active {{
            background: #000;
            color: #fff;
            border-color: #000;
        }}
        .input-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            width: 100%;
        }}
        .player-select {{
            background: #fff;
            border: 1px solid #ccc;
            color: #000;
            padding: 8px;
            border-radius: 3px;
            font-size: 12px;
            width: 100%;
            cursor: pointer;
        }}

        .start-game-btn {{
            background: #28a745;
            color: white;
            border: 1px solid #28a745;
            width: 100%;
            padding: 10px;
            border-radius: 3px;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
            text-transform: uppercase;
        }}
        .start-game-btn:hover {{ background: #218838; }}

        .bracket-box {{
            background: #f8f9fa;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 10px;
            width: 100%;
            margin-bottom: 10px;
        }}
        .bracket-title {{
            color: #000;
            font-size: 11px;
            text-transform: uppercase;
            margin-bottom: 8px;
            text-align: center;
            font-weight: bold;
        }}
        .match-card {{
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 3px;
            padding: 8px 12px;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .match-info {{ font-size: 12px; color: #000; }}
        .match-btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 11px;
            cursor: pointer;
        }}
        .match-btn:hover:not(:disabled) {{ background: #0056b3; }}
        .match-btn:disabled {{ background: #e9ecef; color: #aaa; cursor: not-allowed; }}

        .game-layout {{
            display: flex;
            flex-direction: column;
            width: 100%;
            gap: 12px;
        }}
        .info-bar {{
            background-color: #f8f9fa;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 8px 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .turn-indicator {{ color: #000; font-size: 14px; font-weight: bold; }}
        .round-indicator {{ color: #555; font-size: 12px; }}

        .felt-table {{
            background: #fff;
            border: 2px solid #000;
            border-radius: 4px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        .dice-container {{
            display: flex;
            gap: 10px;
            margin: 10px 0;
        }}

        .die {{
            width: 45px;
            height: 45px;
            background: #fff;
            border-radius: 4px;
            display: grid;
            grid-template: repeat(3, 1fr) / repeat(3, 1fr);
            padding: 5px;
            cursor: pointer;
            border: 2px solid #000;
            transition: transform 0.1s;
        }}
        .die.held {{
            border-color: #d9534f;
            background: #fdf7f7;
            transform: translateY(-3px);
        }}
        .die.shake {{
            animation: shakeDie 0.3s ease-in-out infinite;
        }}
        @keyframes shakeDie {{
            0% {{ transform: translate(0, 0) rotate(0deg); }}
            25% {{ transform: translate(-2px, 2px) rotate(-8deg); }}
            50% {{ transform: translate(2px, -2px) rotate(8deg); }}
            75% {{ transform: translate(-1px, -2px) rotate(-4deg); }}
            100% {{ transform: translate(0, 0) rotate(0deg); }}
        }}

        .dot {{
            background: #000;
            border-radius: 50%;
            width: 7px;
            height: 7px;
            align-self: center;
            justify-self: center;
        }}
        .d-1-1 {{ grid-area: 1 / 1; }} .d-1-3 {{ grid-area: 1 / 3; }}
        .d-2-2 {{ grid-area: 2 / 2; }}
        .d-3-1 {{ grid-area: 3 / 1; }} .d-3-3 {{ grid-area: 3 / 3; }}
        .d-1-2 {{ grid-area: 1 / 2; }} .d-3-2 {{ grid-area: 3 / 2; }}
        .d-2-1 {{ grid-area: 2 / 1; }} .d-2-3 {{ grid-area: 2 / 3; }}

        .cup-area {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .cup-btn {{
            background: #000;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 12px;
            cursor: pointer;
            text-transform: uppercase;
        }}
        .cup-btn:hover:not(:disabled) {{ background: #333; }}
        .cup-btn:disabled {{ background: #ccc; cursor: not-allowed; }}

        /* Exakter Block-Tabellenstil */
        .scorecard-wrapper {{
            background: #ffffff;
            border: 2px solid #000;
            border-radius: 4px;
            overflow-x: auto;
            width: 100%;
        }}
        .score-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            text-align: left;
        }}
        .score-table th, .score-table td {{
            padding: 5px 8px;
            border: 1px solid #000;
        }}
        .score-table th {{
            background: #f1f1f1;
            color: #000;
            text-transform: uppercase;
            font-weight: bold;
            text-align: center;
            border-bottom: 2px solid #000;
        }}
        .score-cell {{
            text-align: center;
            cursor: pointer;
            background: #ffffff;
            font-weight: bold;
            color: #000;
        }}
        .score-cell:hover:not(.filled) {{
            background: #e9ecef;
        }}
        .score-cell.filled {{
            color: #333;
            cursor: default;
            background: #fff;
        }}
        .score-cell.potential {{
            color: #0056b3;
            background: #e7f1ff;
        }}

        .section-header-row td {{
            background-color: #f1f1f1;
            font-weight: bold;
            color: #000;
        }}
        .thick-bottom-border {{
            border-bottom: 3px solid #000 !important;
        }}

        .controls-row {{
            display: flex;
            justify-content: space-between;
            width: 100%;
            gap: 8px;
        }}
        .action-btn {{
            background: #f8f9fa;
            color: #000;
            border: 1px solid #ccc;
            padding: 8px 12px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 11px;
            cursor: pointer;
            flex: 1;
            text-align: center;
        }}
        .action-btn:hover {{ background: #e2e6ea; }}
    </style>
    </head>
    <body>
        <div class="cabinet">
            <div id="menu-screen" class="screen active">
                <h1>🎲 KNIFFEL-SPIELBLOCK</h1>
                <div class="subtitle">Originalgetreue Block-Edition & Supabase Live</div>

                <div class="menu-group">
                    <div class="menu-label">Spiel-Typ</div>
                    <div class="select-grid" style="grid-template-columns: repeat(4, 1fr);">
                        <div class="select-btn active" onclick="setGameType('solo', this)">1P</div>
                        <div class="select-btn" onclick="setGameType('pvp', this)">PvP</div>
                        <div class="select-btn" onclick="setGameType('pve', this)">vs KI</div>
                        <div class="select-btn" onclick="setGameType('tournament', this)">🏆 Cup</div>
                    </div>
                </div>

                <div class="menu-group" id="pve-setup" style="display:none;">
                    <div class="menu-label">KI-Gegner wählen</div>
                    <select id="pve_opponent" class="player-select">
                        {ai_options_html}
                    </select>
                </div>

                <div class="menu-group" id="tournament-setup" style="display:none;">
                    <div class="menu-label">Turnier-Größe</div>
                    <div class="select-grid" style="margin-bottom: 8px;">
                        <div class="select-btn active" onclick="setTournamentSize(4, this)">4 Spieler</div>
                        <div class="select-btn" onclick="setTournamentSize(8, this)">8 Spieler</div>
                    </div>
                    <div class="menu-label">Teilnehmer-Auswahl (Mitglieder & KI)</div>
                    <div id="tournament-inputs" class="input-grid"></div>
                </div>

                <button class="start-game-btn" onclick="startApp()">Spiel starten 🚀</button>
            </div>

            <div id="tournament-screen" class="screen">
                <h1>🏆 KNIFFEL-CUP</h1>
                <div class="subtitle" id="cup-status">K.-o.-Runde läuft</div>

                <div class="bracket-box">
                    <div class="bracket-title">Vorrunde</div>
                    <div id="vr-matches"></div>
                </div>

                <div id="sf-container" class="bracket-box" style="display:none;">
                    <div class="bracket-title">Halbfinale</div>
                    <div id="sf-matches"></div>
                </div>

                <div class="bracket-box">
                    <div class="bracket-title">Finale</div>
                    <div class="match-card">
                        <div class="match-info" id="final-label">Gewinner vs Gewinner</div>
                        <button class="match-btn" id="btn-final" onclick="startTournamentMatch('final', 0)" disabled>Finale 🏆</button>
                    </div>
                </div>

                <button class="action-btn" onclick="returnToMenu()" style="width: 100%; margin-top: 8px; padding: 10px;">🏠 Abbrechen / Menü</button>
            </div>

            <div id="game-screen" class="screen">
                <div class="game-layout">
                    <div class="info-bar">
                        <div>
                            <div class="turn-indicator" id="activePlayerLabel">Spieler 1</div>
                            <div class="round-indicator" id="roundLabel">Runde 1 / 13</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 10px; color: #555;">WÜRFE ÜBRIG</div>
                            <div id="rollsLeftDisplay" style="font-size: 15px; color: #000; font-weight: bold;">3 / 3</div>
                        </div>
                    </div>

                    <div class="felt-table">
                        <div style="font-size: 10px; color: #555; font-weight: bold; margin-bottom: 5px;">WÜRFELTISCH (Zum Halten anklicken)</div>
                        <div class="dice-container" id="diceContainer">
                        </div>
                        <div class="cup-area">
                            <button class="cup-btn" id="rollBtn" onclick="rollDice()">🎲 Würfeln</button>
                        </div>
                    </div>

                    <div class="scorecard-wrapper">
                        <table class="score-table">
                            <thead>
                                <tr>
                                    <th style="width: 48%; text-align: left; padding-left: 8px;">SPIELERNAME:</th>
                                    <th id="thP1" style="text-align:center;">Spieler 1</th>
                                    <th id="thP2" style="text-align:center; display:none;">Spieler 2</th>
                                </tr>
                            </thead>
                            <tbody id="scoreTableBody">
                            </tbody>
                        </table>
                    </div>

                    <div class="controls-row">
                        <button class="action-btn" onclick="quitMatch()">🏠 Zurück</button>
                        <button class="action-btn" onclick="resetMatch()">🔄 Neustart</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let config = {{
                gameType: 'solo',
                tournamentSize: 4
            }};

            let tournamentOptionsHtml = `{tournament_options_html}`;

            let tournament = {{
                size: 4,
                players: [],
                vr: [],
                sf: [],
                final: {{ p1Idx: null, p2Idx: null, winner: null }},
                activeRound: null,
                activeMatchIdx: null
            }};

            const blockRows = [
                {{ id: 'ones', name: '1er', desc: 'Nur Einser zählen', type: 'category', section: 'upper' }},
                {{ id: 'twos', name: '2er', desc: 'Nur Zweier zählen', type: 'category', section: 'upper' }},
                {{ id: 'threes', name: '3er', desc: 'Nur Dreier zählen', type: 'category', section: 'upper' }},
                {{ id: 'fours', name: '4er', desc: 'Nur Vierer zählen', type: 'category', section: 'upper' }},
                {{ id: 'fives', name: '5er', desc: 'Nur Fünfer zählen', type: 'category', section: 'upper' }},
                {{ id: 'sixes', name: '6er', desc: 'Nur Sechser zählen', type: 'category', section: 'upper' }},
                {{ id: 'gesamt_oben', name: 'Gesamt', desc: '', type: 'sum_upper' }},
                {{ id: 'bonus', name: 'Bonus bei 63 oder mehr', desc: 'Plus 35', type: 'bonus' }},
                {{ id: 'gesamt_oberer_teil', name: 'Gesamt oberer Teil', desc: '', type: 'total_upper', thick: true }},
                
                {{ id: 'threeOfAKind', name: 'Dreierpasch', desc: 'Alle Augen zählen', type: 'category', section: 'lower' }},
                {{ id: 'fourOfAKind', name: 'Viererpasch', desc: 'Alle Augen zählen', type: 'category', section: 'lower' }},
                {{ id: 'fullHouse', name: 'Full House', desc: '25 Punkte', type: 'category', section: 'lower' }},
                {{ id: 'smallStraight', name: 'Kleine Straße', desc: '30 Punkte', type: 'category', section: 'lower' }},
                {{ id: 'largeStraight', name: 'Große Straße', desc: '40 Punkte', type: 'category', section: 'lower' }},
                {{ id: 'kniffel', name: 'Knobel / Kniffel', desc: '50 Punkte', type: 'category', section: 'lower' }},
                {{ id: 'chance', name: 'Chance', desc: 'Alle Augen zählen', type: 'category', section: 'lower' }},
                {{ id: 'gesamt_unterer_teil', name: 'Gesamt unterer Teil', desc: '', type: 'sum_lower' }},
                {{ id: 'gesamt_oberer_teil_wiederholung', name: 'Gesamt oberer Teil', desc: '', type: 'repeat_upper' }},
                {{ id: 'endsumme', name: 'Endsumme', desc: '', type: 'endsumme', thick: true }}
            ];

            const categories = blockRows.filter(r => r.type === 'category');

            let gameState = {{
                playerNames: ["Spieler 1", "Spieler 2"],
                scores: [{{}}, {{}}],
                activePlayer: 0,
                round: 1,
                dice: [1, 2, 3, 4, 5],
                held: [false, false, false, false, false],
                rollsLeft: 3,
                hasRolled: false,
                isGameOver: false
            }};

            function switchScreen(screenId) {{
                document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
                document.getElementById(screenId).classList.add('active');
            }}

            function setGameType(type, el) {{
                config.gameType = type;
                document.querySelectorAll('#menu-screen .select-btn').forEach(b => b.classList.remove('active'));
                el.classList.add('active');
                document.getElementById('tournament-setup').style.display = (type === 'tournament') ? 'block' : 'none';
                document.getElementById('pve-setup').style.display = (type === 'pve') ? 'block' : 'none';
                if (type === 'tournament') renderTournamentInputs();
            }}

            function setTournamentSize(size, el) {{
                config.tournamentSize = size;
                document.querySelectorAll('#tournament-setup .select-btn').forEach(b => b.classList.remove('active'));
                el.classList.add('active');
                renderTournamentInputs();
            }}

            function renderTournamentInputs() {{
                let container = document.getElementById('tournament-inputs');
                container.innerHTML = '';
                for (let i = 0; i < config.tournamentSize; i++) {{
                    container.innerHTML += `<select id="t_p${{i}}" class="player-select">${{tournamentOptionsHtml}}</select>`;
                }}
            }}

            function startApp() {{
                if (config.gameType === 'tournament') {{
                    tournament.size = config.tournamentSize;
                    tournament.players = [];
                    for (let i = 0; i < tournament.size; i++) {{
                        tournament.players.push(document.getElementById(`t_p${{i}}`).value);
                    }}

                    tournament.vr = [];
                    tournament.sf = [];
                    tournament.final.winner = null;
                    tournament.final.p1Idx = null;
                    tournament.final.p2Idx = null;

                    let numVrMatches = tournament.size / 2;
                    for (let i = 0; i < numVrMatches; i++) {{
                        tournament.vr.push({{ p1Idx: i * 2, p2Idx: i * 2 + 1, winner: null }});
                    }}

                    if (tournament.size === 8) {{
                        tournament.sf = [
                            {{ p1Idx: null, p2Idx: null, winner: null }},
                            {{ p1Idx: null, p2Idx: null, winner: null }}
                        ];
                    }}

                    switchScreen('tournament-screen');
                    updateTournamentUI();
                }} else if (config.gameType === 'pve') {{
                    switchScreen('game-screen');
                    initGameSession("Spieler 1", document.getElementById('pve_opponent').value);
                }} else {{
                    switchScreen('game-screen');
                    initGameSession("Spieler 1", (config.gameType === 'pvp') ? "Spieler 2" : "");
                }}
            }}

            function updateTournamentUI() {{
                let p = tournament.players;
                let vrMatchesContainer = document.getElementById('vr-matches');
                let sfContainer = document.getElementById('sf-container');
                let sfMatchesContainer = document.getElementById('sf-matches');

                vrMatchesContainer.innerHTML = '';
                for (let i = 0; i < tournament.vr.length; i++) {{
                    let m = tournament.vr[i];
                    let wText = m.winner !== null ? ` (Sieger: ${{p[m.winner]}})` : '';
                    vrMatchesContainer.innerHTML += `
                        <div class="match-card">
                            <div class="match-info">VR ${{i+1}}: ${{p[m.p1Idx]}} vs ${{p[m.p2Idx]}}${{wText}}</div>
                            <button class="match-btn" id="btn-vr-${{i}}" onclick="startTournamentMatch('vr', ${{i}})" ${{m.winner !== null ? 'disabled' : ''}}>Spielen ▶</button>
                        </div>
                    `;
                }}

                if (tournament.size === 8) {{
                    sfContainer.style.display = 'block';
                    sfMatchesContainer.innerHTML = '';
                    for (let i = 0; i < 2; i++) {{
                        let m = tournament.sf[i];
                        let p1Name = m.p1Idx !== null ? p[m.p1Idx] : `Sieger VR ${{i*2+1}}`;
                        let p2Name = m.p2Idx !== null ? p[m.p2Idx] : `Sieger VR ${{i*2+2}}`;
                        let wText = m.winner !== null ? ` (Sieger: ${{p[m.winner]}})` : '';
                        let disabled = (m.p1Idx === null || m.p2Idx === null || m.winner !== null);

                        sfMatchesContainer.innerHTML += `
                            <div class="match-card">
                                <div class="match-info">HF ${{i+1}}: ${{p1Name}} vs ${{p2Name}}${{wText}}</div>
                                <button class="match-btn" id="btn-sf-${{i}}" onclick="startTournamentMatch('sf', ${{i}})" ${{disabled ? 'disabled' : ''}}>Spielen ▶</button>
                            </div>
                        `;
                    }}
                }} else {{
                    sfContainer.style.display = 'none';
                }}

                let f = tournament.final;
                let f1Name, f2Name, finalReady = false;

                if (tournament.size === 4) {{
                    f1Name = f.p1Idx !== null ? p[f.p1Idx] : "Sieger VR 1";
                    f2Name = f.p2Idx !== null ? p[f.p2Idx] : "Sieger VR 2";
                    finalReady = (tournament.vr[0].winner !== null && tournament.vr[1].winner !== null);
                }} else {{
                    f1Name = f.p1Idx !== null ? p[f.p1Idx] : "Sieger HF 1";
                    f2Name = f.p2Idx !== null ? p[f.p2Idx] : "Sieger HF 2";
                    finalReady = (tournament.sf[0].winner !== null && tournament.sf[1].winner !== null);
                }}

                let fText = f.winner !== null ? ` 🏆 CHAMPION: ${{p[f.winner]}}` : '';
                document.getElementById('final-label').innerText = `${{f1Name}} vs ${{f2Name}}${{fText}}`;

                let finalDone = (f.winner !== null);
                document.getElementById('btn-final').disabled = (!finalReady || finalDone);
            }}

            function startTournamentMatch(round, idx) {{
                tournament.activeRound = round;
                tournament.activeMatchIdx = idx;
                let m;
                if (round === 'vr') m = tournament.vr[idx];
                else if (round === 'sf') m = tournament.sf[idx];
                else m = tournament.final;

                switchScreen('game-screen');
                initGameSession(tournament.players[m.p1Idx], tournament.players[m.p2Idx]);
            }}

            function initGameSession(p1Name, p2Name) {{
                gameState.playerNames = p2Name ? [p1Name, p2Name] : [p1Name, ""];
                gameState.scores = [{{}}, {{}}];
                gameState.activePlayer = 0;
                gameState.round = 1;
                gameState.dice = [1, 2, 3, 4, 5];
                gameState.held = [false, false, false, false, false];
                gameState.rollsLeft = 3;
                gameState.hasRolled = false;
                gameState.isGameOver = false;

                let thP2 = document.getElementById('thP2');
                if (p2Name) {{
                    thP2.style.display = 'table-cell';
                    thP2.innerText = p2Name;
                }} else {{
                    thP2.style.display = 'none';
                }}
                document.getElementById('thP1').innerText = p1Name;

                renderScoreTable();
                renderDice();
                updateUI();
                checkAITurn();
            }}

            function quitMatch() {{
                if (config.gameType === 'tournament') {{
                    switchScreen('tournament-screen');
                    updateTournamentUI();
                }} else {{
                    switchScreen('menu-screen');
                }}
            }}

            function resetMatch() {{
                initGameSession(gameState.playerNames[0], gameState.playerNames[1] || "");
            }}

            function returnToMenu() {{
                switchScreen('menu-screen');
            }}

            function isAIPlayer(name) {{
                return name && (name.includes('Bot') || name.includes('KI') || name.startsWith('🤖'));
            }}

            function rollDice() {{
                if (gameState.rollsLeft <= 0 || gameState.isGameOver) return;
                
                let diceEls = document.querySelectorAll('.die');
                diceEls.forEach((el, idx) => {{
                    if (!gameState.held[idx]) {{
                        el.classList.add('shake');
                    }}
                }});

                document.getElementById('rollBtn').disabled = true;

                setTimeout(() => {{
                    for (let i = 0; i < 5; i++) {{
                        if (!gameState.held[i]) {{
                            gameState.dice[i] = Math.floor(Math.random() * 6) + 1;
                        }}
                    }}
                    gameState.rollsLeft--;
                    gameState.hasRolled = true;

                    diceEls.forEach(el => el.classList.remove('shake'));
                    document.getElementById('rollBtn').disabled = (gameState.rollsLeft === 0);

                    renderDice();
                    renderScoreTable();
                    updateUI();
                }}, 300);
            }}

            function toggleHold(idx) {{
                if (!gameState.hasRolled || gameState.isGameOver) return;
                let currentName = gameState.playerNames[gameState.activePlayer];
                if (isAIPlayer(currentName)) return;

                gameState.held[idx] = !gameState.held[idx];
                renderDice();
            }}

            function renderDice() {{
                let container = document.getElementById('diceContainer');
                container.innerHTML = '';

                const dotMap = {{
                    1: [['d-2-2']],
                    2: [['d-1-1'], ['d-3-3']],
                    3: [['d-1-1'], ['d-2-2'], ['d-3-3']],
                    4: [['d-1-1'], ['d-1-3'], ['d-3-1'], ['d-3-3']],
                    5: [['d-1-1'], ['d-1-3'], ['d-2-2'], ['d-3-1'], ['d-3-3']],
                    6: [['d-1-1'], ['d-1-3'], ['d-2-1'], ['d-2-3'], ['d-3-1'], ['d-3-3']]
                }};

                for (let i = 0; i < 5; i++) {{
                    let val = gameState.dice[i];
                    let isHeld = gameState.held[i] ? ' held' : '';
                    let dieDiv = document.createElement('div');
                    dieDiv.className = 'die' + isHeld;
                    dieDiv.setAttribute('onclick', `toggleHold(${{i}})`);

                    let dotsHTML = '';
                    let positions = dotMap[val] || [];
                    positions.forEach(pos => {{
                        dotsHTML += `<div class="dot ${{pos[0]}}"></div>`;
                    }});
                    dieDiv.innerHTML = dotsHTML;
                    container.appendChild(dieDiv);
                }}
            }}

            function calculatePossibleScore(dice, catId) {{
                let counts = [0,0,0,0,0,0,0];
                dice.forEach(d => counts[d]++);
                let sum = dice.reduce((a,b) => a+b, 0);

                switch(catId) {{
                    case 'ones': return counts[1] * 1;
                    case 'twos': return counts[2] * 2;
                    case 'threes': return counts[3] * 3;
                    case 'fours': return counts[4] * 4;
                    case 'fives': return counts[5] * 5;
                    case 'sixes': return counts[6] * 6;
                    case 'threeOfAKind':
                        return Object.values(counts).some(c => c >= 3) ? sum : 0;
                    case 'fourOfAKind':
                        return Object.values(counts).some(c => c >= 4) ? sum : 0;
                    case 'fullHouse':
                        let has3 = Object.values(counts).includes(3);
                        let has2 = Object.values(counts).includes(2);
                        let has5 = Object.values(counts).includes(5);
                        return ((has3 && has2) || has5) ? 25 : 0;
                    case 'smallStraight':
                        let uniq = [...new Set(dice)].sort().join('');
                        return (uniq.includes('1234') || uniq.includes('2345') || uniq.includes('346') || uniq.includes('3456') || uniq.includes('12345') || uniq.includes('23456')) ? 30 : 0;
                    case 'largeStraight':
                        let uniqL = [...new Set(dice)].sort().join('');
                        return (uniqL === '1235' || uniqL === '12345' || uniqL === '23456') ? 40 : 0;
                    case 'kniffel':
                        return Object.values(counts).includes(5) ? 50 : 0;
                    case 'chance':
                        return sum;
                    default: return 0;
                }}
            }}

            function calculateUpperSum(pIdx) {{
                let s = gameState.scores[pIdx];
                let upperIds = ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes'];
                let sum = 0;
                upperIds.forEach(id => {{
                    if (s[id] !== undefined) sum += s[id];
                }});
                return sum;
            }}

            function calculateBonus(pIdx) {{
                return calculateUpperSum(pIdx) >= 63 ? 35 : 0;
            }}

            function calculateUpperTotalWithBonus(pIdx) {{
                let upper = calculateUpperSum(pIdx);
                if (upper === 0) return 0;
                let bonus = calculateBonus(pIdx);
                return upper + bonus;
            }}

            function calculateLowerSum(pIdx) {{
                let s = gameState.scores[pIdx];
                let lowerIds = ['threeOfAKind', 'fourOfAKind', 'fullHouse', 'smallStraight', 'largeStraight', 'kniffel', 'chance'];
                let sum = 0;
                lowerIds.forEach(id => {{
                    if (s[id] !== undefined) sum += s[id];
                }});
                return sum;
            }}

            function calculateTotal(pIdx) {{
                return calculateUpperTotalWithBonus(pIdx) + calculateLowerSum(pIdx);
            }}

            function renderScoreTable() {{
                let tbody = document.getElementById('scoreTableBody');
                tbody.innerHTML = '';

                let p1Scores = gameState.scores[0];
                let p2Scores = gameState.scores[1];
                let hasP2 = (gameState.playerNames[1] !== "");

                blockRows.forEach(row => {{
                    let tr = document.createElement('tr');
                    if (row.thick) {{
                        tr.classList.add('thick-bottom-border');
                    }}

                    let tdName = document.createElement('td');
                    tdName.style.paddingLeft = '8px';
                    tdName.innerHTML = `<strong>${{row.name}}</strong>` + (row.desc ? ` <span style="color: #666; font-size: 10px; float: right;">${{row.desc}}</span>` : '');
                    tr.appendChild(tdName);

                    for (let pIdx = 0; pIdx < 2; pIdx++) {{
                        if (pIdx === 1 && !hasP2) continue;

                        let td = document.createElement('td');
                        td.className = 'score-cell';
                        let s = gameState.scores[pIdx];

                        if (row.type === 'category') {{
                            let val = s[row.id];
                            if (val !== undefined) {{
                                td.innerText = val;
                                td.classList.add('filled');
                            }} else if (gameState.activePlayer === pIdx && gameState.hasRolled) {{
                                let pot = calculatePossibleScore(gameState.dice, row.id);
                                td.innerText = pot;
                                td.classList.add('potential');
                                td.setAttribute('onclick', `selectScore('${{row.id}}')`);
                            }} else {{
                                td.innerText = '';
                            }}
                        }} else if (row.type === 'sum_upper') {{
                            td.innerText = calculateUpperSum(pIdx);
                            td.style.backgroundColor = '#f9f9f9';
                        }} else if (row.type === 'bonus') {{
                            td.innerText = calculateBonus(pIdx);
                            td.style.backgroundColor = '#f9f9f9';
                        }} else if (row.type === 'total_upper') {{
                            td.innerText = calculateUpperTotalWithBonus(pIdx);
                            td.style.backgroundColor = '#f1f1f1';
                            td.style.fontWeight = 'bold';
                        }} else if (row.type === 'sum_lower') {{
                            td.innerText = calculateLowerSum(pIdx);
                            td.style.backgroundColor = '#f9f9f9';
                        }} else if (row.type === 'repeat_upper') {{
                            td.innerText = calculateUpperTotalWithBonus(pIdx);
                            td.style.backgroundColor = '#f9f9f9';
                        }} else if (row.type === 'endsumme') {{
                            td.innerText = calculateTotal(pIdx);
                            td.style.backgroundColor = '#e2e6ea';
                            td.style.fontWeight = 'bold';
                        }}

                        tr.appendChild(td);
                    }}

                    tbody.appendChild(tr);
                }});
            }}

            function selectScore(catId) {{
                let pIdx = gameState.activePlayer;
                if (gameState.scores[pIdx][catId] !== undefined || !gameState.hasRolled) return;

                let pts = calculatePossibleScore(gameState.dice, catId);
                gameState.scores[pIdx][catId] = pts;

                nextTurnCheck();
            }}

            function nextTurnCheck() {{
                gameState.held = [false, false, false, false, false];
                gameState.rollsLeft = 3;
                gameState.hasRolled = false;

                let hasP2 = (gameState.playerNames[1] !== "");
                if (hasP2) {{
                    if (gameState.activePlayer === 1) {{
                        gameState.round++;
                    }}
                    gameState.activePlayer = (gameState.activePlayer === 1) ? 0 : 1;
                }} else {{
                    gameState.round++;
                }}

                if (gameState.round > 13) {{
                    endGame();
                    return;
                }}

                renderScoreTable();
                renderDice();
                updateUI();
                checkAITurn();
            }}

            function updateUI() {{
                let pName = gameState.playerNames[gameState.activePlayer];
                document.getElementById('activePlayerLabel').innerText = `Am Zug: ${{pName}}`;
                document.getElementById('roundLabel').innerText = `Runde ${{gameState.round}} / 13`;
                document.getElementById('rollsLeftDisplay').innerText = `${{gameState.rollsLeft}} / 3`;
            }}

            function checkAITurn() {{
                if (gameState.isGameOver) return;
                let currentName = gameState.playerNames[gameState.activePlayer];
                if (isAIPlayer(currentName)) {{
                    document.getElementById('rollBtn').disabled = true;
                    setTimeout(executeAI, 1000);
                }} else {{
                    document.getElementById('rollBtn').disabled = (gameState.rollsLeft <= 0);
                }}
            }}

            function executeAI() {{
                if (gameState.isGameOver) return;
                
                rollDice();
                
                setTimeout(() => {{
                    if (gameState.rollsLeft > 0 && Math.random() > 0.3) {{
                        for(let i=0; i<5; i++) {{
                            if(Math.random() > 0.5) gameState.held[i] = true;
                        }}
                        renderDice();
                        rollDice();
                        
                        setTimeout(() => {{
                            aiPickBestCategory();
                        }}, 800);
                    }} else {{
                        aiPickBestCategory();
                    }}
                }}, 800);
            }}

            function aiPickBestCategory() {{
                let pIdx = gameState.activePlayer;
                let bestCat = null;
                let maxPts = -1;

                categories.forEach(cat => {{
                    if (gameState.scores[pIdx][cat.id] === undefined) {{
                        let pts = calculatePossibleScore(gameState.dice, cat.id);
                        if (pts > maxPts) {{
                            maxPts = pts;
                            bestCat = cat.id;
                        }}
                    }}
                }});

                if (bestCat) {{
                    gameState.scores[pIdx][bestCat] = maxPts;
                }}
                nextTurnCheck();
            }}

            function endGame() {{
                gameState.isGameOver = true;
                let p1Total = calculateTotal(0);
                let p2Total = gameState.playerNames[1] ? calculateTotal(1) : -1;
                
                let winnerName = gameState.playerNames[0];
                let winnerIdx = 0;

                if (p2Total !== -1) {{
                    if (p2Total > p1Total) {{
                        winnerName = gameState.playerNames[1];
                        winnerIdx = 1;
                    }} else if (p1Total === p2Total) {{
                        winnerName = "Unentschieden";
                        winnerIdx = -1;
                    }}
                }}

                document.getElementById('activePlayerLabel').innerText = `🏆 SPIEL BEENDET! Sieger: ${{winnerName}}`;
                document.getElementById('rollBtn').disabled = true;

                if (config.gameType === 'tournament' && winnerIdx !== -1) {{
                    let round = tournament.activeRound;
                    let idx = tournament.activeMatchIdx;
                    let realWinnerIdx = (winnerIdx === 0) ? 
                        (round === 'vr' ? tournament.vr[idx].p1Idx : round === 'sf' ? tournament.sf[idx].p1Idx : tournament.final.p1Idx) :
                        (round === 'vr' ? tournament.vr[idx].p2Idx : round === 'sf' ? tournament.sf[idx].p2Idx : tournament.final.p2Idx);

                    if (round === 'vr') {{
                        tournament.vr[idx].winner = realWinnerIdx;
                        if (tournament.size === 4) {{
                            if (idx === 0) tournament.final.p1Idx = realWinnerIdx;
                            else tournament.final.p2Idx = realWinnerIdx;
                        }} else if (tournament.size === 8) {{
                            let sfTargetMatch = Math.floor(idx / 2);
                            let sfSlot = idx % 2;
                            if (sfSlot === 0) tournament.sf[sfTargetMatch].p1Idx = realWinnerIdx;
                            else tournament.sf[sfTargetMatch].p2Idx = realWinnerIdx;
                        }}
                    }} else if (round === 'sf') {{
                        tournament.sf[idx].winner = realWinnerIdx;
                        if (idx === 0) tournament.final.p1Idx = realWinnerIdx;
                        else tournament.final.p2Idx = realWinnerIdx;
                    }} else if (round === 'final') {{
                        tournament.final.winner = realWinnerIdx;
                    }}

                    setTimeout(() => {{
                        switchScreen('tournament-screen');
                        updateTournamentUI();
                    }}, 2000);
                }}
            }}
        </script>
    </body>
    </html>
    """

    components.html(kniffel_html, height=1250, scrolling=True)

if __name__ == "__main__":
    show()