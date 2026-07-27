import streamlit as st
import json
from database import supabase

# ==========================================
# DATENBANK FÜR BEWEISE & AKTEN
# ==========================================
BEWEISE_DB = {
    "Blutiger Handschuh": "Ein teurer schwarzer Lederhandschuh (Marke Roeckl, Größe 10). Auf der Innenseite sind die Initialen 'M.B.' eingenäht. Der Handschuh riecht leicht nach Maschinenöl.",
    "Notizbuch des Opfers": "Das kleine schwarze Buch des toten Ingenieurs. Viele Seiten sind herausgerissen. Auf der letzten verbliebenen Seite steht hastig gekritzelt:\n\n*Projekt Phönix stoppen! Sie waschen die Millionen über die Spedition in Dortmund. Beweise sind auf meinem Handy gesichert. Mein Lebensretter-Passwort: Der Tag des Mauerfalls (TTMM).*",
    "Gesperrtes Smartphone": "Ein modernes Smartphone mit einem Riss im Display. Es ist mit einer 4-stelligen PIN (TTMM) gesperrt. Mehrfache falsche Eingabe löscht die Daten.",
    "Akte Whistleblower (Entschlüsselt)": "Mails vom Handy des Opfers. Eine Mail von einer Adresse 'Hachtmann_Privat@ruhrmail.de' sticht heraus: *'Wenn der Ingenieur zur Presse geht, sind wir erledigt. M.B. kümmert sich um die Logistik. Beseitigt das Problem.'*",
    "Chemikalien-Probe": "Eine Bodenprobe aus Gelsenkirchen. Das Labor bestätigt: Hochgiftige Industrieabfälle, illegal im Grundwasser versickert.",
    "Fracht-Logbuch": "Ein gebundenes Buch aus der Spedition. Es beweist, dass Tonnen von Giftmüll nicht verbrannt, sondern nachts im Revier verbuddelt wurden. Abgezeichnet von 'Markus Brandt'.",
    "Finanz-Akte": "Kontoauszüge aus einer Rüttenscheider Kanzlei. Es flossen wöchentlich 50.000 Euro Schmiergeld auf das Privatkonto von Dezernatsleiter Dr. Hachtmann."
}

STORY_PROLOG = """
### 📖 Prolog: Der Schatten über dem Revier

Es ist eine kalte, neblige Nieselregen-Nacht im Essener Stadtteil Kray. An der belebten Markthalle wird eine leblose Person gefunden. Der Tote ist Thomas K., ein Umwelt-Ingenieur. 
Dein Bauchgefühl sagt dir: Das war kein normaler Raubmord. Die Art, wie die Leiche drapiert wurde, wirkt professionell. 

Du bist auf dich allein gestellt. Vertraue niemandem im Präsidium – die Korruption im Ruhrgebiet reicht tief. Lies dir deine Beweise genau durch, merke dir Namen und Daten. Wenn du am Ende vor dem Haftrichter stehst und nur rätst, wird man dich wegen Inkompetenz suspendieren.
"""

def show():
    st.header("🕵️ Krayer Tatort: Schatten über dem Revier (Director's Cut)")
    st.markdown("Ein tiefgründiges Point & Click Adventure. Lies Dokumente, knacke Codes, durchschaue Lügen und sammle stichhaltige Beweise für das große Finale.")
    st.divider()

    # Hauptmenü initialisieren
    if "spiel_modus" not in st.session_state:
        st.session_state.spiel_modus = "hauptmenue"

    # ==========================================
    # HAUPTMENÜ
    # ==========================================
    if st.session_state.spiel_modus == "hauptmenue":
        with st.expander("📖 Story-Hintergrund & Prolog lesen"):
            st.markdown(STORY_PROLOG)
            
        col1, col2 = st.columns(2)
        with col1:
            st.info("👤 **Einzelspieler-Kampagne (Story Modus)**\n\n10 Kapitel Rätsel, Verhöre und Entscheidungen.")
            if st.button("Kampagne starten", use_container_width=True, type="primary"):
                st.session_state.spiel_modus = "single_menu"
                st.rerun()
                
        with col2:
            st.warning("👥 **Multiplayer-Duell**\n\nSchnelles Katz-und-Maus-Spiel gegen Freunde.")
            if st.button("Multiplayer starten", use_container_width=True):
                st.session_state.spiel_modus = "multi_menu"
                st.rerun()

    # ==========================================
    # 1. EINZELSPIELER MENÜ & LADEN
    # ==========================================
    elif st.session_state.spiel_modus == "single_menu":
        if st.button("⬅️ Zurück zum Hauptmenü"):
            st.session_state.spiel_modus = "hauptmenue"
            st.rerun()

        st.subheader("👤 Kampagnen-Verwaltung")
        tab_neu, tab_laden = st.tabs(["Neues Spiel", "Spielstand laden"])
        
        with tab_neu:
            if st.button("Fall eröffnen (Ermittler)", type="primary", use_container_width=True):
                st.session_state.spiel_modus = "single_spiel"
                st.session_state.single_rolle = "ermittler"
                st.session_state.aktuelle_stadt = "Essen-Kray"
                st.session_state.erm_kapitel = 1
                st.session_state.erm_spuren = [] # Liste der gefundenen Beweise
                st.session_state.erm_zeugen = [] # Wen man befragt hat
                st.session_state.kapitel_progress = 0 # Für Zwischenschritte im Kapitel
                st.rerun()
                
        with tab_laden:
            st.info("Speichern & Laden in dieser stark erweiterten Version vorübergehend deaktiviert, um State-Fehler zu vermeiden. Bitte spiele die Story am Stück (ca. 30-45 Min).")

    # ==========================================
    # 2. EINZELSPIELER SPIEL-LOGIK (10 KAPITEL)
    # ==========================================
    elif st.session_state.spiel_modus == "single_spiel":
        
        # ----------------------------------------------------
        # SIDEBAR: DIE INTERAKTIVE BEWEIS-AKTE
        # ----------------------------------------------------
        st.sidebar.markdown("### 🗂️ Deine Ermittlungsakte")
        st.sidebar.write(f"**Kapitel:** {st.session_state.erm_kapitel} / 10")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("#### 🔍 Sichergestellte Beweise")
        if not st.session_state.erm_spuren:
            st.sidebar.write("*Noch keine Beweise gesichert.*")
        else:
            st.sidebar.write("*(Klicke zum Lesen auf einen Beweis)*")
            for beweis in st.session_state.erm_spuren:
                with st.sidebar.expander(f"📄 {beweis}"):
                    st.write(BEWEISE_DB.get(beweis, "Keine weiteren Details erkennbar."))

        st.divider()

        kapitel = st.session_state.erm_kapitel
        progress = st.session_state.kapitel_progress

        # ----------------------------------------------------
        # KAPITEL 1: Der Fundort (Essen-Kray)
        # ----------------------------------------------------
        if kapitel == 1:
            st.markdown("### 🌧️ Kapitel 1: Der Krayer Markt")
            st.write("Der Regen wäscht fast alle Spuren weg. Die Leiche des Ingenieurs liegt im Dreck. Der Streifenpolizist zuckt mit den Schultern: 'Sieht nach einem Raub aus, Boss. Brieftasche fehlt.'")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Leiche durchsuchen"):
                    if "Notizbuch des Opfers" not in st.session_state.erm_spuren:
                        st.session_state.erm_spuren.append("Notizbuch des Opfers")
                        st.success("Du findest in der inneren Jackentasche ein verstecktes Notizbuch!")
                    else:
                        st.info("Du hast die Leiche bereits gründlich durchsucht.")
            with col2:
                if st.button("Umgebung (Mülltonnen) absuchen"):
                    if "Gesperrtes Smartphone" not in st.session_state.erm_spuren:
                        st.session_state.erm_spuren.append("Gesperrtes Smartphone")
                        st.success("Im Müll findest du ein Smartphone! Jemand wollte es verschwinden lassen.")
                    else:
                        st.info("Hier ist nur noch stinkender Müll.")
            with col3:
                if st.button("Gullygitter überprüfen"):
                    if "Blutiger Handschuh" not in st.session_state.erm_spuren:
                        st.session_state.erm_spuren.append("Blutiger Handschuh")
                        st.success("Ein teurer Lederhandschuh klemmt im Gitter. Eingetütet!")
                    else:
                        st.info("Du hast den Handschuh bereits.")

            st.markdown("---")
            if len(st.session_state.erm_spuren) >= 3:
                st.success("Du hast alle entscheidenden Spuren am Tatort gesichert. Zeit, sich umzuhören.")
                if st.button("Nächster Schritt: Zeugen befragen ➡️", type="primary"):
                    st.session_state.erm_kapitel = 2
                    st.session_state.kapitel_progress = 0
                    st.rerun()
            else:
                st.warning("Durchsuche den Tatort gründlicher. Da muss mehr sein! (3 Spuren versteckt)")

        # ----------------------------------------------------
        # KAPITEL 2: Zeugen im Veedel
        # ----------------------------------------------------
        elif kapitel == 2:
            st.markdown("### 🗣️ Kapitel 2: Lügen und Wahrheiten")
            st.write("Die Sonne geht langsam auf. Drei Personen treiben sich noch rund um den Krayer Markt herum. Wer hat etwas gesehen?")
            
            tab1, tab2, tab3 = st.tabs(["Kiosk-Besitzerin", "Der Obdachlose", "Der Frühaufsteher"])
            
            with tab1:
                st.write("**Frau Özkan:** 'Herr Kommissar, ich habe nur gehört, wie ein Auto mit quietschenden Reifen wegfuhr. Ein dicker Wagen, schwarz oder dunkelblau.'")
                if "Frau Özkan" not in st.session_state.erm_zeugen:
                    if st.button("Glauben und Notieren (Özkan)"):
                        st.session_state.erm_zeugen.append("Frau Özkan")
                        st.success("Notiert: Dunkles, schweres Fahrzeug.")
                        st.rerun()
                else:
                    st.write("✅ Aussage aufgenommen.")

            with tab2:
                st.write("**Kalle (Obdachloser):** 'Gib mir nen Fünfer, dann sag ich dir, dass es ein Typ in ner roten Jacke war. Ganz sicher, roter Hoodie!'")
                if "Kalle" not in st.session_state.erm_zeugen:
                    if st.button("Glauben und Notieren (Kalle)"):
                        st.session_state.erm_zeugen.append("Kalle")
                        st.error("Du notierst dir den Hinweis. (Dein Bauchgefühl sagt: Kalle wollte nur Geld für Bier. Eine falsche Fährte!)")
                        st.rerun()
                else:
                    st.write("✅ Aussage (oder Lüge) aufgenommen.")

            with tab3:
                st.write("**Rentner Herr Müller:** 'Ich stand am Fenster. Da war ein riesiger Kerl. Hatte einen teuren schwarzen Mantel an. Wirkte wie so ein Türsteher-Typ. Er stieg in einen Mercedes SUV.'")
                if "Herr Müller" not in st.session_state.erm_zeugen:
                    if st.button("Glauben und Notieren (Müller)"):
                        st.session_state.erm_zeugen.append("Herr Müller")
                        st.success("Notiert: Großer Mann, Mantel, SUV. Passt zu einem teuren Handschuh!")
                        st.rerun()
                else:
                    st.write("✅ Aussage aufgenommen.")

            st.markdown("---")
            if len(st.session_state.erm_zeugen) >= 3:
                st.write("Du hast genug gehört. Die Hinweise verdichten sich in Richtung organisiertes Verbrechen. Ein Kontakt aus Gelsenkirchen könnte mehr wissen.")
                if st.button("Nach Gelsenkirchen fahren ➡️", type="primary"):
                    st.session_state.erm_kapitel = 3
                    st.session_state.kapitel_progress = 0
                    st.rerun()

        # ----------------------------------------------------
        # KAPITEL 3: Der Türsteher in Gelsenkirchen
        # ----------------------------------------------------
        elif kapitel == 3:
            st.markdown("### 🏭 Kapitel 3: Das Milieu von Gelsenkirchen")
            st.write("Du stehst vor einer zwielichtigen Bar in Gelsenkirchen-Ückendorf. Ein Informant wartet angeblich drinnen. Doch der massive Türsteher blockiert den Weg.")
            st.write("**Türsteher:** 'Geschlossene Gesellschaft, Bulle. Wen suchst du? Wer schickt dich?'")
            
            if progress == 0:
                antwort = st.selectbox("Was antwortest du dem Türsteher?", ["Bitte wählen...", "Ich bin von der Polizei, lassen Sie mich durch!", "Ich suche den Kerl in der roten Jacke.", "Die Initialen M.B. schicken mich."])
                
                if antwort == "Ich bin von der Polizei, lassen Sie mich durch!":
                    st.error("Der Türsteher lacht dich aus und schubst dich auf die Straße. So kommst du nicht rein.")
                elif antwort == "Ich suche den Kerl in der roten Jacke.":
                    st.error("Der Türsteher schüttelt den Kopf. 'Keine Ahnung wovon du redest. Verpiss dich.' (Kalles Tipp war falsch!)")
                elif antwort == "Die Initialen M.B. schicken mich.":
                    st.success("Der Türsteher zuckt zusammen. 'Brandt? Scheiße, okay. Geh rein. Hinten links sitzt dein Mann.'")
                    if st.button("Die Bar betreten"):
                        st.session_state.kapitel_progress = 1
                        st.rerun()
            elif progress == 1:
                st.write("Du triffst deinen Informanten. Er ist nervös.")
                st.write("**Informant:** 'Du schnüffelst in Sachen herum, die zu groß für dich sind. M.B. steht für Markus Brandt, ein knallharter Logistiker. Die pumpen heimlich Industriechemikalien ins Grundwasser bei Herne. Hier ist eine Bodenprobe.'")
                if st.button("Bodenprobe sichern & nach Herne fahren ➡️", type="primary"):
                    st.session_state.erm_spuren.append("Chemikalien-Probe")
                    st.session_state.erm_kapitel = 4
                    st.session_state.kapitel_progress = 0
                    st.rerun()

        # ----------------------------------------------------
        # KAPITEL 4: Das Passwort-Rätsel in Bochum
        # ----------------------------------------------------
        elif kapitel == 4:
            st.markdown("### 🎓 Kapitel 4: Die RUB und das Handy")
            st.write("Bevor du nach Herne fährst, hältst du an der Ruhr-Uni Bochum. Die IT-Forensik hat das Smartphone ans Kabel geschlossen, scheitert aber an der PIN.")
            st.write("**IT-Experte:** 'Kommissar, wir haben nur noch einen Versuch, bevor sich das Handy löscht. Sie sagten, im Notizbuch steht ein Hinweis?'")
            
            st.info("💡 Tipp: Öffne dein 'Notizbuch' in der Sidebar. Lies den Text genau. Weißt du, wann die Berliner Mauer fiel?")
            
            pin_eingabe = st.text_input("Gib die 4-stellige PIN ein (Format: TTMM):")
            
            if st.button("PIN bestätigen"):
                if pin_eingabe == "0911":
                    st.balloons()
                    st.success("BINGO! Das Telefon entsperrt sich. Du lädst die brisanten Mails herunter.")
                    st.session_state.erm_spuren.append("Akte Whistleblower (Entschlüsselt)")
                    st.session_state.erm_spuren.remove("Gesperrtes Smartphone")
                    if st.button("Mails lesen & Weiter nach Dortmund ➡️", type="primary"):
                        st.session_state.erm_kapitel = 5
                        st.rerun()
                elif pin_eingabe != "":
                    st.error("Falsche PIN! Der Bildschirm blinkt rot. Denk nach! Tag (2 Ziffern), Monat (2 Ziffern).")

        # ----------------------------------------------------
        # KAPITEL 5: Der Hafen von Dortmund
        # ----------------------------------------------------
        elif kapitel == 5:
            st.markdown("### ⚓ Kapitel 5: Razzia im Hafen")
            st.write("Die entschlüsselten Mails erwähnen die Logistik. Du stürmst mit ein paar Kollegen das Büro der Spedition Brandt am Dortmunder Hafen.")
            st.write("Markus Brandt ist nicht hier, aber sein Schreibtisch ist ein Chaos aus Papier. Du hast nur 2 Minuten, bevor sein Anwalt auftaucht.")
            
            if progress == 0:
                auswahl = st.radio("Welchen Stapel durchsuchst du?", ["Personalakten", "Gebäudepläne", "Fracht-Logbücher für Nachtfahrten"])
                if st.button("Durchsuchen"):
                    if auswahl == "Fracht-Logbücher für Nachtfahrten":
                        st.success("Treffer! Du findest die Belege für die Müllverschiebung.")
                        st.session_state.erm_spuren.append("Fracht-Logbuch")
                        st.session_state.kapitel_progress = 1
                        st.rerun()
                    else:
                        st.error("Nichts Relevantes. Die Zeit tickt!")
            elif progress == 1:
                st.write("Der Anwalt stürmt herein: 'Sie haben hier nichts verloren!' - Du lächelst nur und hältst das Logbuch hoch.")
                if st.button("Der Spur des Geldes nach Rüttenscheid folgen ➡️", type="primary"):
                    st.session_state.erm_kapitel = 6
                    st.session_state.kapitel_progress = 0
                    st.rerun()

        # ----------------------------------------------------
        # KAPITEL 6: Die Kanzlei in Rüttenscheid
        # ----------------------------------------------------
        elif kapitel == 6:
            st.markdown("### 💳 Kapitel 6: Die Höhle der Löwen")
            st.write("Essen-Rüttenscheid. Eine noble Steuerkanzlei. Die Empfangsdame blockt ab: 'Wir geben keine Auskunft über Mandanten.'")
            st.write("Du musst sie austricksen, um einen Blick in den PC zu werfen.")
            
            trick = st.radio("Wie gehst du vor?", [
                "Brüllen und mit Verhaftung drohen.",
                "Sagen, dass Dr. Hachtmann wegen eines Notfalls angerufen hat und du sofort die Akte 'Projekt Phönix' brauchst.",
                "Den Feueralarm auslösen."
            ])
            
            if st.button("Aktion ausführen"):
                if trick == "Sagen, dass Dr. Hachtmann wegen eines Notfalls angerufen hat und du sofort die Akte 'Projekt Phönix' brauchst.":
                    st.success("Die Sekretärin wird blass. 'Dr. Hachtmann? Oh mein Gott, natürlich.' Sie dreht den Bildschirm zu dir. Du kopierst die Daten!")
                    st.session_state.erm_spuren.append("Finanz-Akte")
                    st.session_state.kapitel_progress = 1
                    st.rerun()
                elif trick == "Brüllen und mit Verhaftung drohen.":
                    st.error("Sie ruft unbeeindruckt den Kanzlei-Anwalt. Du fliegst raus und musst dich über die Hintertür einschleichen. (Kostet Zeit, versuch was anderes).")
                else:
                    st.error("Feueralarm? Das Gebäude wird evakuiert, PC wird automatisch gesperrt. Falsche Idee.")
                    
            if progress == 1:
                if st.button("Mit den Beweisen zum Präsidium rasen ➡️", type="primary"):
                    st.session_state.erm_kapitel = 7
                    st.rerun()

        # ----------------------------------------------------
        # KAPITEL 7, 8, 9 (Kompakte Überleitung zum Finale)
        # ----------------------------------------------------
        elif kapitel in [7, 8, 9]:
            st.markdown(f"### 🚓 Kapitel {kapitel}: Schlinge zieht sich zu")
            st.write("Das Netz zieht sich zusammen. Du hast Handlanger verhaftet, Konten eingefroren und Zeugen in Sicherheit gebracht. Das SEK steht bereit. M.B. (Markus Brandt) sitzt im Verhörraum, schweigt aber.")
            st.write("Alles hängt nun davon ab, dass du den wahren Kopf der Bande – deinen eigenen Boss – im Präsidium stellst.")
            
            st.info("Nutze diesen Moment, um **ALLE Beweise in der Sidebar** noch einmal gründlich durchzulesen. Du darfst im Finale keinen Fehler machen!")
            
            if st.button("Ich bin bereit. Ab in Kapitel " + str(kapitel+1) + " ➡️", type="primary"):
                st.session_state.erm_kapitel += 1
                st.rerun()

        # ----------------------------------------------------
        # KAPITEL 10: DAS FINALE (Hard-Fail Verhör)
        # ----------------------------------------------------
        elif kapitel == 10:
            st.markdown("### ⚖️ KAPITEL 10: Der Showdown im Präsidium")
            st.write("Du reißt die Tür zum Büro des Polizeipräsidenten auf. Dort sitzt Dezernatsleiter Dr. Hachtmann auf dem Ledersofa und trinkt Kaffee.")
            st.write("**Hachtmann:** 'Was soll dieser Aufstand, Kommissar? Geben Sie mir Ihre Dienstmarke, Sie sind suspendiert!'")
            st.write("**Polizeipräsident:** 'Erklären Sie sich, sofort! Wen beschuldigen Sie hier und warum?'")
            
            st.error("⚠️ **ACHTUNG:** Beantworte die 3 Fragen korrekt. Ein Fehler, und das Spiel ist verloren!")

            f1 = st.selectbox("1. Wer ist der Kopf hinter dem Umweltskandal?", ["Bitte wählen...", "Markus Brandt", "Frau Özkan vom Kiosk", "Dr. Hachtmann", "Der ermordete Ingenieur"])
            f2 = st.selectbox("2. Wer war der Mann für das Grobe (der Mörder vor Ort)?", ["Bitte wählen...", "Dr. Hachtmann", "Ein unbekannter Dritter", "Markus Brandt (Initialen M.B.)"])
            f3 = st.selectbox("3. Welches Beweismittel beweist eindeutig den Tötungsbefehl von Hachtmann?", ["Bitte wählen...", "Die Finanz-Akte", "Der blutige Handschuh", "Das Fracht-Logbuch", "Die entschlüsselte Akte Whistleblower (Mails)"])

            if st.button("Beweisführung abschließen & Verhaftung fordern! 🚨", type="primary", use_container_width=True):
                if f1 == "Bitte wählen..." or f2 == "Bitte wählen..." or f3 == "Bitte wählen...":
                    st.warning("Bitte fülle alle Antworten aus!")
                else:
                    if f1 == "Dr. Hachtmann" and f2 == "Markus Brandt (Initialen M.B.)" and f3 == "Die entschlüsselte Akte Whistleblower (Mails)":
                        st.balloons()
                        st.success("### 🎉 GEWONNEN! EIN MEISTERHAFTER DETEKTIV!")
                        st.write("Dr. Hachtmann wird kreidebleich. Der Polizeipräsident liest die Mails und nickt dem SEK zu. Die Handschellen klicken.")
                        st.write("Du hast den Sumpf trockengelegt und das Ruhrgebiet vor einer Umweltkatastrophe bewahrt. Das war echte Polizeiarbeit!")
                        if st.button("Spiel neu starten"):
                            st.session_state.spiel_modus = "hauptmenue"
                            st.rerun()
                    else:
                        st.error("### ❌ GAME OVER: SUSPENDIERT!")
                        st.write("Der Polizeipräsident schüttelt den Kopf. 'Ihre Beweiskette ist lückenhaft oder unlogisch. Geben Sie Marke und Waffe ab!'")
                        st.write("Dr. Hachtmann grinst hämisch. Du hast versagt.")
                        if st.button("Komplett von vorn beginnen"):
                            st.session_state.spiel_modus = "hauptmenue"
                            st.rerun()

    # ==========================================
    # 3. MULTIPLAYER (Bleibt simpel & intakt)
    # ==========================================
    elif st.session_state.spiel_modus == "multi_menu":
        if st.button("⬅️ Zurück zum Hauptmenü"):
            st.session_state.spiel_modus = "hauptmenue"
            st.rerun()
            
        st.subheader("👥 Multiplayer Duell (Schnelles Spiel)")
        st.write("Hier kannst du ein asynchrones Katz-und-Maus-Spiel gegen einen Freund spielen.")
        col1, col2 = st.columns(2)
        
        with col1:
            p_name = st.text_input("Dein Name", value="Kommissar")
            code = st.text_input("Raumcode", value="KRAY-DUO")
            wahl = st.selectbox("Rolle", ["ermittler", "moerder"])
            if st.button("Raum erstellen", type="primary"):
                try:
                    data = {"room_code": code, "ermittler_name": p_name if wahl == "ermittler" else "Wartet...", "moerder_name": p_name if wahl == "moerder" else "Wartet...", "fahndungsdruck": 15, "am_zug": "ermittler", "status": "warten"}
                    supabase.table("mord_multiplayer").insert(data).execute()
                    st.session_state.multi_code = code
                    st.session_state.multi_rolle = wahl
                    st.session_state.spiel_modus = "multi_spiel"
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler: {e}")

        with col2:
            p_name2 = st.text_input("Dein Name (Mitspieler)", value="Flüchtiger")
            code2 = st.text_input("Raumcode beitreten", value="KRAY-DUO")
            if st.button("Beitreten"):
                try:
                    res = supabase.table("mord_multiplayer").select("*").eq("room_code", code2).execute()
                    if res.data:
                        raum = res.data[0]
                        wahl = "moerder" if raum["ermittler_name"] != "Wartet..." else "ermittler"
                        update_field = {"ermittler_name": p_name2} if wahl == "ermittler" else {"moerder_name": p_name2, "status": "laeuft"}
                        supabase.table("mord_multiplayer").update(update_field).eq("room_code", code2).execute()
                        st.session_state.multi_code = code2
                        st.session_state.multi_rolle = wahl
                        st.session_state.spiel_modus = "multi_spiel"
                        st.rerun()
                    else:
                        st.error("Raum nicht gefunden.")
                except Exception as e:
                    st.error(f"Fehler: {e}")

    elif st.session_state.spiel_modus == "multi_spiel":
        if st.button("⬅️ Spiel verlassen"):
            st.session_state.spiel_modus = "hauptmenue"
            st.rerun()
            
        code = st.session_state.multi_code
        rolle = st.session_state.multi_rolle
        
        res = supabase.table("mord_multiplayer").select("*").eq("room_code", code).execute()
        if not res.data:
            st.error("Raum wurde geschlossen.")
            st.session_state.spiel_modus = "hauptmenue"
            st.rerun()
            return
            
        spiel = res.data[0]
        st.markdown(f"### 🕹️ Multiplayer [Raum: {code}]")
        st.markdown(f"👤 **Ermittler:** {spiel['ermittler_name']} vs. 🦹 **Mörder:** {spiel['moerder_name']}")
        st.metric("🚨 Fahndungsdruck", f"{spiel['fahndungsdruck']}%")
        
        if st.button("🔄 Aktualisieren"):
            st.rerun()
            
        st.divider()
        if spiel["am_zug"] == rolle:
            st.success("🟢 Du bist am Zug!")
            if rolle == "ermittler":
                if st.button("Ermitteln & Druck erhöhen (+20%)"):
                    supabase.table("mord_multiplayer").update({"fahndungsdruck": spiel['fahndungsdruck'] + 20, "am_zug": "moerder"}).eq("room_code", code).execute()
                    st.rerun()
            else:
                if st.button("Abtauchen (Druck sinkt, Zug abgeben)"):
                    supabase.table("mord_multiplayer").update({"fahndungsdruck": max(0, spiel['fahndungsdruck'] - 10), "am_zug": "ermittler"}).eq("room_code", code).execute()
                    st.rerun()
        else:
            st.warning("⏳ Warten auf Mitspieler...")

if __name__ == "__main__":
    show()