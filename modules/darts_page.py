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
        "🤖 Bullseye-Bob (KI-Bot)",
        "🤖 Dart-Matrix (KI-Bot)"
    ]
    
    all_tournament_participants = members + ai_bots
    
    tournament_options_html = "".join([f'<option value="{p}">{p}</option>' for p in all_tournament_participants])
    ai_options_html = "".join([f'<option value="{b}">{b}</option>' for b in ai_bots])

    arcade_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            background-color: transparent;
            color: white;
            font-family: 'Courier New', Courier, monospace;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            margin: 0;
            padding: 70px 10px 50px 10px;
            min-height: 100vh;
        }}
        .cabinet {{
            background: linear-gradient(145deg, #121212, #0a0a0a);
            border: 4px solid #333;
            border-radius: 16px;
            padding: 25px 30px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.9), inset 0 0 20px rgba(0,0,0,0.9);
            width: 100%;
            max-width: 620px;
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
            color: #ff3333; 
            text-shadow: 0 0 10px rgba(255,0,0,0.7); 
            font-size: 24px; 
            text-align: center; 
            margin: 0 0 8px 0; 
            letter-spacing: 2px;
            flex-shrink: 0;
        }}
        .subtitle {{ color: #888; font-size: 13px; margin-bottom: 20px; text-align: center; flex-shrink: 0; }}
        
        .menu-group {{
            width: 100%;
            margin-bottom: 16px;
            flex-shrink: 0;
        }}
        .menu-label {{
            font-size: 13px;
            color: #00ff66;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: bold;
        }}
        .select-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            width: 100%;
        }}
        .select-btn {{
            background: #181818;
            color: #bbb;
            border: 2px solid #444;
            padding: 12px;
            border-radius: 6px;
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            font-size: 13px;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s ease;
        }}
        .select-btn:hover {{ border-color: #666; color: #fff; }}
        .select-btn.active {{
            background: #008800;
            color: #fff;
            border-color: #00ff00;
            box-shadow: 0 0 10px rgba(0,255,0,0.4);
        }}
        .input-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            width: 100%;
        }}
        .player-select {{
            background: #181818;
            border: 2px solid #444;
            color: white;
            padding: 11px;
            border-radius: 6px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
            width: 100%;
            box-sizing: border-box;
            text-align: center;
            cursor: pointer;
        }}
        .player-select:focus {{ border-color: #00ff00; outline: none; }}

        .start-game-btn {{
            background: linear-gradient(180deg, #ff2222, #990000);
            color: white;
            border: 2px solid #ff5555;
            width: 100%;
            padding: 15px;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            font-family: 'Courier New', Courier, monospace;
            cursor: pointer;
            margin-top: 15px;
            box-shadow: 0 4px 15px rgba(255,0,0,0.4);
            text-transform: uppercase;
            letter-spacing: 2px;
            flex-shrink: 0;
        }}
        .start-game-btn:hover {{ background: linear-gradient(180deg, #ff4444, #bb0000); }}

        /* TURNIER HUB SCREEN */
        .bracket-box {{
            background: #141414;
            border: 2px solid #333;
            border-radius: 8px;
            padding: 14px;
            width: 100%;
            box-sizing: border-box;
            margin-bottom: 14px;
            flex-shrink: 0;
        }}
        .bracket-title {{
            color: #00ff66;
            font-size: 13px;
            text-transform: uppercase;
            margin-bottom: 10px;
            text-align: center;
            letter-spacing: 1px;
            font-weight: bold;
        }}
        .match-card {{
            background: #1c1c1c;
            border: 1px solid #444;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .match-card:last-child {{ margin-bottom: 0; }}
        .match-info {{ font-size: 13px; color: #eee; }}
        .match-btn {{
            background: #009900;
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 4px;
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            font-size: 12px;
            cursor: pointer;
        }}
        .match-btn:hover:not(:disabled) {{ background: #00cc00; }}
        .match-btn:disabled {{ background: #222; color: #555; cursor: not-allowed; }}

        /* SPIEL SCREEN */
        .led-display {{
            background-color: #040404;
            border: 2px solid #333;
            border-radius: 8px;
            padding: 12px 18px;
            display: flex;
            justify-content: space-between;
            width: 100%;
            box-sizing: border-box;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.9);
            margin-bottom: 16px;
            flex-shrink: 0;
        }}
        .led-red {{ color: #ff3333; text-shadow: 0 0 8px rgba(255,0,0,0.6); font-size: 26px; font-weight: bold; margin: 0; }}
        .led-green {{ color: #00ff66; text-shadow: 0 0 8px rgba(0,255,0,0.5); font-size: 15px; font-weight: bold; margin: 0; }}
        .led-label {{ color: #999; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }}
        .display-block {{ text-align: center; }}

        #board-container {{
            position: relative;
            width: 380px;
            height: 380px;
            cursor: crosshair;
            user-select: none;
            flex-shrink: 0;
            margin: 0 auto;
        }}
        canvas {{
            width: 100%;
            height: 100%;
            border-radius: 50%;
            box-shadow: 0 6px 25px rgba(0,0,0,0.8), 0 0 12px rgba(255,255,255,0.05);
        }}
        #power-container {{
            width: 380px;
            margin-top: 14px;
            background: #111;
            border: 2px solid #444;
            border-radius: 6px;
            height: 24px;
            overflow: hidden;
            position: relative;
            flex-shrink: 0;
        }}
        #power-fill {{
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #00ff00, #ffcc00, #ff0000);
            transition: width 0.02s linear;
        }}
        #power-text {{
            position: absolute;
            width: 100%;
            text-align: center;
            top: 5px;
            font-size: 11px;
            font-weight: bold;
            color: #fff;
            text-shadow: 1px 1px 2px #000;
        }}
        .controls-row {{
            display: flex;
            justify-content: space-between;
            width: 380px;
            margin-top: 12px;
            gap: 10px;
            flex-shrink: 0;
        }}
        .action-btn {{
            background: #1c1c1c;
            color: #fff;
            border: 2px solid #444;
            padding: 10px 12px;
            border-radius: 6px;
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            font-size: 12px;
            cursor: pointer;
            flex: 1;
            text-align: center;
            transition: all 0.2s;
        }}
        .action-btn:hover {{ background: #2a2a2a; border-color: #00ff66; color: #00ff66; }}
        
        #history-box {{
            width: 380px;
            margin-top: 12px;
            background: #080808;
            border: 2px solid #222;
            border-radius: 6px;
            padding: 10px;
            font-size: 12px;
            max-height: 80px;
            overflow-y: auto;
            box-sizing: border-box;
            flex-shrink: 0;
        }}
        .history-item {{ margin: 3px 0; border-bottom: 1px solid #151515; padding-bottom: 3px; color: #ddd; }}
    </style>
    </head>
    <body>
        <div class="cabinet">
            <!-- HAUPTMENÜ -->
            <div id="menu-screen" class="screen active">
                <h1>🎯 VEREINS-DART AUTOMAT</h1>
                <div class="subtitle">Arcade Edition & Supabase Live</div>

                <div class="menu-group">
                    <div class="menu-label">Spielmodus</div>
                    <div class="select-grid">
                        <div class="select-btn active" onclick="setMode('501', this)">501 Double Out</div>
                        <div class="select-btn" onclick="setMode('301', this)">301 Quick Out</div>
                    </div>
                </div>

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
                    <div class="select-grid" style="margin-bottom: 10px;">
                        <div class="select-btn active" onclick="setTournamentSize(4, this)">4 Spieler</div>
                        <div class="select-btn" onclick="setTournamentSize(8, this)">8 Spieler</div>
                    </div>
                    <div class="menu-label">Teilnehmer-Auswahl (Mitglieder & KI)</div>
                    <div id="tournament-inputs" class="input-grid"></div>
                </div>

                <button class="start-game-btn" onclick="startApp()">SPIEL STARTEN 🚀</button>
            </div>

            <!-- TURNIER HUB SCREEN -->
            <div id="tournament-screen" class="screen">
                <h1>🏆 VEREINS-CUP</h1>
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

                <button class="action-btn" onclick="returnToMenu()" style="width: 100%; margin-top: 10px; padding: 12px; flex-shrink: 0;">🏠 Abbrechen / Menü</button>
            </div>

            <!-- SPIEL SCREEN -->
            <div id="game-screen" class="screen">
                <div class="led-display">
                    <div class="display-block">
                        <div class="led-label" id="p1Label">Spieler 1</div>
                        <div class="led-red" id="score1Display">501</div>
                    </div>
                    <div class="display-block" id="p2ScoreBlock">
                        <div class="led-label" id="p2Label">Spieler 2</div>
                        <div class="led-red" id="score2Display" style="color: #ffaa00;">501</div>
                    </div>
                    <div class="display-block">
                        <div class="led-label" id="turnStatusLabel">Am Zug</div>
                        <div class="led-green" id="dartCountDisplay">Pfeil 1/3</div>
                    </div>
                </div>

                <div id="board-container">
                    <canvas id="boardCanvas" width="400" height="400"></canvas>
                </div>

                <div id="power-container">
                    <div id="power-fill"></div>
                    <div id="power-text">MAUSTASTE GEDRÜCKT HALTEN & LOSLASSEN</div>
                </div>

                <div class="controls-row">
                    <button class="action-btn" onclick="quitMatch()">🏠 Zurück</button>
                    <button class="action-btn" onclick="nextTurn()" id="nextBtn" style="display:none;">Nächster</button>
                    <button class="action-btn" onclick="resetMatch()">🔄 Neustart</button>
                </div>

                <div id="history-box">
                    <div id="historyList"><div style="color: #666;">Bereit für den ersten Wurf...</div></div>
                </div>
            </div>
        </div>

        <script>
            let config = {{
                mode: '501',       
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

            let gameState = {{
                scores: [501, 501],
                activePlayer: 0,
                dartInTurn: 1,
                currentDarts: [],
                isGameOver: false,
                playerNames: ["Spieler 1", "Spieler 2"]
            }};

            let isCharging = false;
            let power = 0;
            let targetX = 200, targetY = 200;
            let interval = null;
            let powerDir = 1;
            let isAnimating = false;

            const numbers = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5];

            function switchScreen(screenId) {{
                document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
                document.getElementById(screenId).classList.add('active');
            }}

            function setMode(mode, el) {{
                config.mode = mode;
                document.querySelectorAll('#menu-screen .menu-group:nth-child(2) .select-btn').forEach(b => b.classList.remove('active'));
                el.classList.add('active');
            }}

            function setGameType(type, el) {{
                config.gameType = type;
                document.querySelectorAll('#menu-screen .menu-group:nth-child(3) .select-btn').forEach(b => b.classList.remove('active'));
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
                let startPts = (config.mode === '301') ? 301 : 501;
                
                gameState.scores = [startPts, startPts];
                gameState.activePlayer = 0;
                gameState.dartInTurn = 1;
                gameState.currentDarts = [];
                gameState.isGameOver = false;
                gameState.playerNames = [p1Name, p2Name];

                let p2Block = document.getElementById('p2ScoreBlock');
                if (!p2Name) {{
                    p2Block.style.display = 'none';
                    document.getElementById('p1Label').innerText = "Punkte Rest";
                }} else {{
                    p2Block.style.display = 'block';
                    document.getElementById('p1Label').innerText = p1Name;
                    document.getElementById('p2Label').innerText = p2Name;
                }}

                updateUI();
                drawBoard();
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
                initGameSession(gameState.playerNames[0], gameState.playerNames[1]);
            }}

            function returnToMenu() {{
                switchScreen('menu-screen');
            }}

            const canvas = document.getElementById('boardCanvas');
            const ctx = canvas.getContext('2d');

            function drawBoard() {{
                const cx = 200, cy = 200;
                ctx.clearRect(0, 0, 400, 400);

                ctx.fillStyle = '#0a0a0a';
                ctx.beginPath();
                ctx.arc(cx, cy, 195, 0, 2 * Math.PI);
                ctx.fill();

                for (let i = 0; i < 20; i++) {{
                    const startAngle = (i * 18 - 99) * Math.PI / 180;
                    const endAngle = ((i + 1) * 18 - 99) * Math.PI / 180;
                    const isEven = i % 2 === 0;
                    const baseColor = isEven ? '#1c1c1c' : '#f0e6d2';
                    const redColor = '#cc0000';
                    const greenColor = '#00aa00';

                    drawSector(cx, cy, 25, 110, startAngle, endAngle, baseColor);
                    drawSector(cx, cy, 110, 125, startAngle, endAngle, isEven ? redColor : greenColor);
                    drawSector(cx, cy, 125, 170, startAngle, endAngle, baseColor);
                    drawSector(cx, cy, 170, 185, startAngle, endAngle, isEven ? redColor : greenColor);
                }}

                ctx.fillStyle = '#00aa00'; ctx.beginPath(); ctx.arc(cx, cy, 25, 0, 2 * Math.PI); ctx.fill();
                ctx.fillStyle = '#cc0000'; ctx.beginPath(); ctx.arc(cx, cy, 10, 0, 2 * Math.PI); ctx.fill();

                for (let i = 0; i < 20; i++) {{
                    const angle = (i * 18 - 90) * Math.PI / 180;
                    ctx.beginPath(); ctx.moveTo(cx, cy);
                    ctx.lineTo(cx + 185 * Math.cos(angle), cy + 185 * Math.sin(angle));
                    ctx.strokeStyle = '#333'; ctx.lineWidth = 1; ctx.stroke();
                }}

                ctx.fillStyle = '#ffffff'; ctx.font = 'bold 15px monospace'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                for (let i = 0; i < 20; i++) {{
                    const angle = (i * 18 - 90) * Math.PI / 180;
                    ctx.fillText(numbers[i], cx + 190 * Math.cos(angle), cy + 190 * Math.sin(angle));
                }}

                gameState.currentDarts.forEach(d => {{
                    drawStuckDart(d.x, d.y, d.label);
                }});
            }}

            function drawSector(cx, cy, rIn, rOut, startA, endA, color) {{
                ctx.beginPath();
                ctx.arc(cx, cy, rOut, startA, endA, false);
                ctx.arc(cx, cy, rIn, endA, startA, true);
                ctx.closePath();
                ctx.fillStyle = color; ctx.fill();
                ctx.strokeStyle = '#222'; ctx.lineWidth = 0.5; ctx.stroke();
            }}

            function drawStuckDart(x, y, label) {{
                ctx.save();
                ctx.fillStyle = '#ff0000'; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2;
                ctx.beginPath(); ctx.arc(x, y, 7, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
                ctx.fillStyle = '#ffffff'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                ctx.fillText(label, x, y);
                ctx.restore();
            }}

            function calculateScore(x, y) {{
                const dx = x - 200, dy = y - 200;
                const dist = Math.sqrt(dx*dx + dy*dy);
                const angleRad = Math.atan2(dy, dx);
                const clockAngle = (angleRad * 180 / Math.PI + 90 + 360) % 360;
                const segIndex = Math.round(clockAngle / 18) % 20;
                const baseNum = numbers[segIndex];

                if (dist <= 10) return {{ pts: 50, text: "BULLSEYE", icon: "🎯" }};
                if (dist <= 25) return {{ pts: 25, text: "Outer Bull", icon: "🔴" }};
                if (dist <= 110) return {{ pts: baseNum, text: `Single ${{baseNum}}`, icon: "⚪" }};
                if (dist <= 125) return {{ pts: baseNum * 3, text: `TRIPLE ${{baseNum}}`, icon: "🔥" }};
                if (dist <= 170) return {{ pts: baseNum, text: `Single ${{baseNum}}`, icon: "⚪" }};
                if (dist <= 185) return {{ pts: baseNum * 2, text: `DOUBLE ${{baseNum}}`, icon: "💥" }};
                return {{ pts: 0, text: "MISS", icon: "❌" }};
            }}

            function isAIPlayer(name) {{
                return name && (name.includes('Bot') || name.includes('KI') || name.startsWith('🤖'));
            }}

            function checkAITurn() {{
                if (gameState.isGameOver) return;
                let currentName = gameState.playerNames[gameState.activePlayer];
                if (isAIPlayer(currentName)) {{
                    document.getElementById('power-text').innerText = `${{currentName}} wirft... 🤖`;
                    setTimeout(executeAIThrow, 1000);
                }}
            }}

            function executeAIThrow() {{
                if (gameState.isGameOver) return;
                let pIdx = gameState.activePlayer;
                let score = gameState.scores[pIdx];

                let targetX = 200, targetY = 82.5;
                if (score <= 40 && score % 2 === 0) {{
                    let doubleNum = score / 2;
                    let segIdx = numbers.indexOf(doubleNum);
                    if (segIdx !== -1) {{
                        let angle = (segIdx * 18 - 90) * Math.PI / 180;
                        targetX = 200 + 177 * Math.cos(angle);
                        targetY = 200 + 177 * Math.sin(angle);
                    }}
                }} else if (score === 50) {{
                    targetX = 200; targetY = 200;
                }} else if (score < 170 && Math.random() > 0.4) {{
                    let segIdx = numbers.indexOf(19);
                    let angle = (segIdx * 18 - 90) * Math.PI / 180;
                    targetX = 200 + 117 * Math.cos(angle);
                    targetY = 200 + 117 * Math.sin(angle);
                }}

                let aiTargetX = targetX + (Math.random() - 0.5) * 26;
                let aiTargetY = targetY + (Math.random() - 0.5) * 26;
                animateFlight(aiTargetX, aiTargetY);
            }}

            canvas.addEventListener('mousedown', function(e) {{
                let currentName = gameState.playerNames[gameState.activePlayer];
                if (isAIPlayer(currentName)) return;
                if (isAnimating || gameState.isGameOver) return;
                if (gameState.dartInTurn > 3) return;

                const rect = canvas.getBoundingClientRect();
                targetX = (e.clientX - rect.left) * (canvas.width / rect.width);
                targetY = (e.clientY - rect.top) * (canvas.height / rect.height);
                
                isCharging = true; power = 0; powerDir = 1;
                
                interval = setInterval(() => {{
                    power += powerDir * 4;
                    if (power >= 100) {{ power = 100; powerDir = -1; }}
                    if (power <= 0) {{ power = 0; powerDir = 1; }}
                    document.getElementById('power-fill').style.width = power + '%';
                    document.getElementById('power-text').innerText = `KRAFT: ${{Math.round(power)}}% (LOSLASSEN)`;
                }}, 20);
            }});

            window.addEventListener('mouseup', function(e) {{
                let currentName = gameState.playerNames[gameState.activePlayer];
                if (isAIPlayer(currentName)) return;
                if (!isCharging) return;
                isCharging = false; clearInterval(interval);
                document.getElementById('power-fill').style.width = '0%';
                document.getElementById('power-text').innerText = 'MAUSTASTE GEDRÜCKT HALTEN & LOSLASSEN';

                const maxSpread = (power / 100.0) * 45;
                const finalX = targetX + (Math.random() - 0.5) * 2 * maxSpread;
                const finalY = targetY + (Math.random() - 0.5) * 2 * maxSpread;

                animateFlight(finalX, finalY);
            }});

            function animateFlight(finalX, finalY) {{
                isAnimating = true;
                let startX = 200, startY = 360, frames = 10, currentFrame = 0;

                function step() {{
                    currentFrame++;
                    let t = currentFrame / frames;
                    let currX = startX + (finalX - startX) * t;
                    let currY = startY + (finalY - startY) * t - Math.sin(t * Math.PI) * 30;

                    drawBoard();
                    ctx.fillStyle = '#00ffff'; ctx.beginPath(); ctx.arc(currX, currY, 5, 0, 2 * Math.PI); ctx.fill();

                    if (currentFrame < frames) {{
                        requestAnimationFrame(step);
                    }} else {{
                        isAnimating = false;
                        processThrow(finalX, finalY);
                    }}
                }}
                step();
            }}

            function processThrow(finalX, finalY) {{
                let pIdx = gameState.activePlayer;
                const res = calculateScore(finalX, finalY);

                let isBust = (gameState.scores[pIdx] - res.pts < 0);
                if (!isBust) {{
                    gameState.scores[pIdx] -= res.pts;
                    if (gameState.scores[pIdx] === 0) gameState.isGameOver = true;
                }}

                gameState.currentDarts.push({{ x: finalX, y: finalY, label: gameState.dartInTurn, text: res.text, pts: res.pts }});
                
                let playerName = gameState.playerNames[pIdx];
                let msg = `${{playerName}} (${{gameState.dartInTurn}}): ${{res.icon}} ${{res.text}}`;
                if (gameState.isGameOver) {{
                    msg += ` 🎉 ${{playerName}} GEWONNEN!`;
                    if (config.gameType === 'tournament') {{
                        let round = tournament.activeRound;
                        let idx = tournament.activeMatchIdx;
                        let winnerIdx = (pIdx === 0) ? 
                            (round === 'vr' ? tournament.vr[idx].p1Idx : round === 'sf' ? tournament.sf[idx].p1Idx : tournament.final.p1Idx) :
                            (round === 'vr' ? tournament.vr[idx].p2Idx : round === 'sf' ? tournament.sf[idx].p2Idx : tournament.final.p2Idx);

                        if (round === 'vr') {{
                            tournament.vr[idx].winner = winnerIdx;
                            if (tournament.size === 4) {{
                                if (idx === 0) tournament.final.p1Idx = winnerIdx;
                                else tournament.final.p2Idx = winnerIdx;
                            }} else if (tournament.size === 8) {{
                                let sfTargetMatch = Math.floor(idx / 2);
                                let sfSlot = idx % 2;
                                if (sfSlot === 0) tournament.sf[sfTargetMatch].p1Idx = winnerIdx;
                                else tournament.sf[sfTargetMatch].p2Idx = winnerIdx;
                            }}
                        }} else if (round === 'sf') {{
                            tournament.sf[idx].winner = winnerIdx;
                            if (idx === 0) tournament.final.p1Idx = winnerIdx;
                            else tournament.final.p2Idx = winnerIdx;
                        }} else if (round === 'final') {{
                            tournament.final.winner = winnerIdx;
                        }}

                        document.getElementById('power-text').innerText = `🏆 ${{playerName}} GEWONNEN! Weiterleitung...`;
                        setTimeout(() => {{ quitMatch(); }}, 2000);
                        return;
                    }}
                }}
                
                addHistory(msg);
                updateUI();
                drawBoard();

                if (gameState.isGameOver) {{
                    document.getElementById('power-text').innerText = `🏆 GEWONNEN! (Zurück klicken)`;
                    return;
                }}

                if (gameState.dartInTurn >= 3) {{
                    if (!gameState.playerNames[1]) {{
                        document.getElementById('nextBtn').style.display = 'block';
                        document.getElementById('power-text').innerText = "AUFNAHME BEENDET. NÄCHSTER.";
                    }} else {{
                        setTimeout(switchPlayer, 800);
                    }}
                }} else {{
                    gameState.dartInTurn++;
                    updateUI();
                    checkAITurn();
                }}
            }}

            function switchPlayer() {{
                gameState.currentDarts = [];
                gameState.dartInTurn = 1;
                gameState.activePlayer = (gameState.activePlayer === 1) ? 0 : 1;
                document.getElementById('nextBtn').style.display = 'none';
                document.getElementById('power-text').innerText = "MAUSTASTE GEDRÜCKT HALTEN & LOSLASSEN";
                updateUI();
                drawBoard();
                checkAITurn();
            }}

            function nextTurn() {{
                gameState.currentDarts = [];
                gameState.dartInTurn = 1;
                document.getElementById('nextBtn').style.display = 'none';
                document.getElementById('power-text').innerText = "MAUSTASTE GEDRÜCKT HALTEN & LOSLASSEN";
                updateUI();
                drawBoard();
                checkAITurn();
            }}

            function updateUI() {{
                document.getElementById('score1Display').innerText = gameState.scores[0];
                if (gameState.playerNames[1]) {{
                    document.getElementById('score2Display').innerText = gameState.scores[1];
                }}
                let pName = gameState.playerNames[gameState.activePlayer];
                document.getElementById('dartCountDisplay').innerText = `${{pName}} (${{gameState.dartInTurn}}/3)`;
            }}

            function addHistory(text) {{
                const list = document.getElementById('historyList');
                const div = document.createElement('div');
                div.className = 'history-item';
                div.innerText = text;
                list.prepend(div);
            }}
        </script>
    </body>
    </html>
    """

    components.html(arcade_html, height=1100, scrolling=True)

if __name__ == "__main__":
    show()