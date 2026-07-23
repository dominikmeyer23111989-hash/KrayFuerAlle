import streamlit as st
from database import supabase
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

def show():
    # --- MOBILE OPTIMIERUNG (CSS INJECTION) ---
    st.markdown("""
        <style>
        /* Anpassungen für kleinere Bildschirme (Handys & Tablets) */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            /* Metriken kompakter machen auf dem Handy */
            div[data-testid="stMetricValue"] {
                font-size: 1.2rem !important;
            }
            h1 { font-size: 1.4rem !important; }
            h2 { font-size: 1.2rem !important; }
            h3 { font-size: 1.1rem !important; }
        }
        </style>
    """, unsafe_allow_html=True)

    st.header("💰 Finanzen & Kassenbuch")
    
    # 1. Rechteprüfung (Nur Admin, Vorstand, Kassenwart)
    user_rolle = st.session_state.get("user_rolle", "").lower()
    erlaubte_rollen = ["admin", "administrator", "vorstand", "kassenwart"]
    
    if user_rolle not in erlaubte_rollen:
        st.error("⛔ Zugriff verweigert. Dieser Bereich ist nur für Admin, Vorstand und Kassenwart zugänglich.")
        return

    # Tabs definieren (inkl. Logbuch)
    tab_buchungen, tab_neu, tab_beitraege, tab_statistik, tab_pdf, tab_log = st.tabs([
        "📖 Kassenbuch", 
        "➕ Neu", 
        "🏷️ Beiträge",
        "📊 Statistik", 
        "📄 PDF",
        "📜 Logbuch"
    ])

    # Daten aus Supabase laden
    try:
        res = supabase.table("kassenbuch").select("*").order("buchungs_datum", desc=True).execute()
        roh_daten = res.data if res.data else []
    except Exception as e:
        st.error(f"Fehler beim Laden der Kassenbuch-Daten: {e}")
        roh_daten = []

    df = pd.DataFrame(roh_daten)

    if not df.empty:
        df["buchungs_datum"] = pd.to_datetime(df["buchungs_datum"])
        df["jahr"] = df["buchungs_datum"].dt.year
        df["monat"] = df["buchungs_datum"].dt.month
        df["betrag"] = pd.to_numeric(df["betrag"])

    # ==========================================
    # GLOBALER KONTOSTAND & FILTER (Sidebar)
    # ==========================================
    st.sidebar.divider()
    st.sidebar.subheader("📅 Finanz-Filter & Info")
    st.sidebar.caption("📱 *Hinweis für Handy-Nutzer: Die Filter findest du immer hier in der linken Seitenleiste (Pfeil oben links).*")
    
    # Allzeit-Kontostand berechnen
    if not df.empty:
        gesamt_einnahmen = df[df["typ"] == "Einnahme"]["betrag"].sum()
        gesamt_ausgaben = df[df["typ"] == "Ausgabe"]["betrag"].sum()
        kontostand_gesamt = gesamt_einnahmen - gesamt_ausgaben
    else:
        kontostand_gesamt = 0.0

    st.sidebar.metric("💳 Ist-Stand Konto", f"{kontostand_gesamt:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))

    verfügbare_jahre = sorted(df["jahr"].unique().tolist(), reverse=True) if not df.empty else [datetime.today().year]
    if datetime.today().year not in verfügbare_jahre:
        verfügbare_jahre.insert(0, datetime.today().year)
        
    wahl_jahr = st.sidebar.selectbox("Jahr auswählen", [str(y) for y in verfügbare_jahre])
    wahl_jahr_int = int(wahl_jahr)
    
    monate_dict = {
        "Alle Monate": 0, "Januar": 1, "Februar": 2, "März": 3, "April": 4, 
        "Mai": 5, "Juni": 6, "Juli": 7, "August": 8, "September": 9, 
        "Oktober": 10, "November": 11, "Dezember": 12
    }
    wahl_monat_name = st.sidebar.selectbox("Monat auswählen", list(monate_dict.keys()))
    wahl_monat = monate_dict[wahl_monat_name]

    # Daten filtern
    df_filtered = df.copy()
    if not df_filtered.empty:
        df_filtered = df_filtered[df_filtered["jahr"] == wahl_jahr_int]
        if wahl_monat != 0:
            df_filtered = df_filtered[df_filtered["monat"] == wahl_monat]

    # ==========================================
    # TAB 1: KASSENBUCH & BEARBEITUNG
    # ==========================================
    with tab_buchungen:
        st.subheader(f"Übersicht ({wahl_monat_name} {wahl_jahr})")
        
        if not df_filtered.empty:
            f_einnahmen = df_filtered[df_filtered["typ"] == "Einnahme"]["betrag"].sum()
            f_ausgaben = df_filtered[df_filtered["typ"] == "Ausgabe"]["betrag"].sum()
            f_saldo = f_einnahmen - f_ausgaben

            col1, col2, col3 = st.columns(3)
            col1.metric("Einnahmen", f"{f_einnahmen:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            col2.metric("Ausgaben", f"{f_ausgaben:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            col3.metric("Saldo", f"{f_saldo:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.divider()

            df_anzeige = df_filtered[["id", "buchungs_datum", "typ", "betrag", "kategorie", "person", "verwendungszweck", "ist_geaendert", "letzte_aenderung_durch"]].copy()
            df_anzeige["buchungs_datum"] = df_anzeige["buchungs_datum"].dt.strftime("%d.%m.%Y")
            df_anzeige["betrag"] = df_anzeige["betrag"].map(lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            df_anzeige["status"] = df_anzeige.apply(lambda r: f"⚠️ Bearbeitet von {r['letzte_aenderung_durch']}" if r['ist_geaendert'] else "Original", axis=1)
            
            st.dataframe(
                df_anzeige[["buchungs_datum", "typ", "betrag", "kategorie", "person", "verwendungszweck", "status"]],
                use_container_width=True,
                column_config={
                    "buchungs_datum": "Datum",
                    "typ": "Typ",
                    "betrag": "Betrag",
                    "kategorie": "Kategorie",
                    "person": "Person",
                    "verwendungszweck": "Zweck",
                    "status": "Hinweis"
                },
                hide_index=True
            )

            st.divider()

            # --- BEARBEITEN & LÖSCHEN BEREICH ---
            with st.expander("✏️ Buchung bearbeiten oder 🗑️ löschen"):
                buchungs_optionen = {
                    f"[{row['id']}] {row['buchungs_datum'].strftime('%d.%m.%Y')} - {row['typ']} - {row['betrag']}€ - {row['person']} ({row['kategorie']})": row['id']
                    for _, row in df_filtered.iterrows()
                }
                
                if buchungs_optionen:
                    ausgewaehlte_label = st.selectbox("Buchung für Bearbeitung/Löschung auswählen", list(buchungs_optionen.keys()))
                    ausgewaehlte_id = buchungs_optionen[ausgewaehlte_label]
                    
                    b_row = df_filtered[df_filtered["id"] == ausgewaehlte_id].iloc[0]
                    
                    with st.form("form_bearbeite_buchung"):
                        e_datum = st.date_input("Datum", value=pd.to_datetime(b_row["buchungs_datum"]), format="DD.MM.YYYY")
                        e_typ = st.selectbox("Typ", ["Einnahme", "Ausgabe"], index=0 if b_row["typ"]=="Einnahme" else 1)
                        e_betrag = st.number_input("Betrag in €", value=float(b_row["betrag"]), min_value=0.01, step=1.00, format="%.2f")
                        e_kategorie = st.selectbox("Kategorie", [
                            "Mitgliedsbeitrag", "Spende", "Veranstaltung", "Material & Equipment", 
                            "Miete & Nebenkosten", "Gebühren & Bank", "Sonstige Einnahmen", "Sonstige Ausgaben"
                        ], index=0 if b_row["kategorie"] not in ["Mitgliedsbeitrag", "Spende", "Veranstaltung", "Material & Equipment", "Miete & Nebenkosten", "Gebühren & Bank", "Sonstige Einnahmen", "Sonstige Ausgaben"] else ["Mitgliedsbeitrag", "Spende", "Veranstaltung", "Material & Equipment", "Miete & Nebenkosten", "Gebühren & Bank", "Sonstige Einnahmen", "Sonstige Ausgaben"].index(b_row["kategorie"]))
                        e_person = st.text_input("Person / Firma", value=str(b_row["person"]))
                        e_zweck = st.text_input("Verwendungszweck", value=str(b_row["verwendungszweck"]) if pd.notna(b_row["verwendungszweck"]) else "")
                        
                        col_b1, col_b2 = st.columns(2)
                        btn_speichern = col_b1.form_submit_button("💾 Änderungen speichern", type="primary", use_container_width=True)
                        btn_loeschen = col_b2.form_submit_button("🗑️ Buchung löschen", type="secondary", use_container_width=True)
                        
                        aktueller_user = st.session_state.get("vorname", "Vorstand")
                        
                        if btn_speichern:
                            try:
                                update_daten = {
                                    "buchungs_datum": e_datum.strftime("%Y-%m-%d"),
                                    "typ": e_typ,
                                    "betrag": float(e_betrag),
                                    "kategorie": e_kategorie,
                                    "person": e_person,
                                    "verwendungszweck": e_zweck if e_zweck else None,
                                    "ist_geaendert": True,
                                    "letzte_aenderung_durch": aktueller_user,
                                    "letzte_aenderung_am": datetime.now().isoformat()
                                }
                                supabase.table("kassenbuch").update(update_daten).eq("id", ausgewaehlte_id).execute()
                                
                                log_eintrag = {
                                    "buchung_id": str(ausgewaehlte_id),
                                    "aktion": "BEARBEITET",
                                    "details": f"Buchung geändert. Vorher: {b_row['typ']} {b_row['betrag']}€ ({b_row['person']}), Neu: {e_typ} {e_betrag}€ ({e_person})",
                                    "durchgefuehrt_von": aktueller_user
                                }
                                supabase.table("kassenbuch_log").insert(log_eintrag).execute()
                                
                                st.success("Buchung aktualisiert und im Logbuch vermerkt!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler: {e}")
                                
                        if btn_loeschen:
                            try:
                                log_eintrag = {
                                    "buchung_id": str(ausgewaehlte_id),
                                    "aktion": "GELÖSCHT",
                                    "details": f"Gelöschte Buchung: {b_row['typ']} {b_row['betrag']}€ von {b_row['person']} (Zweck: {b_row['verwendungszweck']})",
                                    "durchgefuehrt_von": aktueller_user
                                }
                                supabase.table("kassenbuch_log").insert(log_eintrag).execute()
                                
                                supabase.table("kassenbuch").delete().eq("id", ausgewaehlte_id).execute()
                                
                                st.success("Buchung wurde gelöscht und im Logbuch dokumentiert.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Fehler: {e}")
                else:
                    st.info("Keine Buchungen für den Zeitraum verfügbar.")
        else:
            st.info("Keine Buchungen für den ausgewählten Zeitraum gefunden.")

    # ==========================================
    # TAB 2: BUCHUNG ERFASSEN
    # ==========================================
    with tab_neu:
        st.subheader("Neue Buchung")
        
        try:
            m_res = supabase.table("mitglieder").select("id, vorname, nachname, mitgliedsnummer").execute()
            mitglieder_liste = m_res.data if m_res.data else []
        except:
            mitglieder_liste = []

        mitglied_optionen = {f"{m['vorname']} {m['nachname']} (Nr: {m.get('mitgliedsnummer', 'N/A')})": m['id'] for m in mitglieder_liste}
        
        with st.form("kassenbuch_form"):
            buchungs_datum = st.date_input("Buchungsdatum", value=datetime.today(), format="DD.MM.YYYY")
            typ = st.selectbox("Buchungstyp", ["Einnahme", "Ausgabe"])
            betrag = st.number_input("Betrag in €", min_value=0.01, step=1.00, format="%.2f")
            kategorie = st.selectbox("Kategorie", [
                "Mitgliedsbeitrag", "Spende", "Veranstaltung", "Material & Equipment", 
                "Miete & Nebenkosten", "Gebühren & Bank", "Sonstige Einnahmen", "Sonstige Ausgaben"
            ])
            
            is_mitglied_zuordnung = st.checkbox("Mitglied zuordnen?", value=(kategorie == "Mitgliedsbeitrag"))
            
            selected_mitglied_id = None
            person_name = ""
            
            if mitglied_optionen and is_mitglied_zuordnung:
                wahl_m = st.selectbox("Mitglied auswählen", list(mitglied_optionen.keys()))
                selected_mitglied_id = mitglied_optionen[wahl_m]
                m_data = next((m for m in mitglieder_liste if m['id'] == selected_mitglied_id), None)
                if m_data:
                    person_name = f"{m_data['vorname']} {m_data['nachname']}"
            else:
                person_name = st.text_input("Name der Person / Firma *")

            verwendungszweck = st.text_input("Verwendungszweck / Bemerkung")
            entgegengenommen_von = st.text_input("Gebucht von *", value=st.session_state.get("vorname", "Vorstand"))
            beitrags_zeitraum = st.text_input("Beitragszeitraum (z.B. 2026)", value=wahl_jahr)

            submitted = st.form_submit_button("Buchung speichern", type="primary", use_container_width=True)
            
            if submitted:
                if not person_name:
                    st.error("Bitte gib eine Person oder ein Mitglied an!")
                else:
                    neue_buchung = {
                        "buchungs_datum": buchungs_datum.strftime("%Y-%m-%d"),
                        "typ": typ,
                        "betrag": float(betrag),
                        "person": person_name,
                        "kategorie": kategorie,
                        "verwendungszweck": verwendungszweck if verwendungszweck else None,
                        "entgegengenommen_von": entgegengenommen_von,
                        "erfasst_von_uuid": st.session_state.get("user_id"),
                        "mitglied_id": selected_mitglied_id,
                        "beitrags_zeitraum": beitrags_zeitraum if beitrags_zeitraum else None,
                        "ist_geaendert": False
                    }
                    try:
                        supabase.table("kassenbuch").insert(neue_buchung).execute()
                        st.success(f"Buchung über {betrag:.2f} € gespeichert!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")

    # ==========================================
    # TAB 3: BEITRÄGE & ZAHLUNGSSTATUS
    # ==========================================
    with tab_beitraege:
        st.subheader(f"Beiträge {wahl_jahr}")
        
        with st.expander("⚙️ Beitragssätze konfigurieren"):
            try:
                b_res = supabase.table("beitragssaetze").select("*").execute()
                saetze = b_res.data if b_res.data else []
            except:
                saetze = []

            if saetze:
                df_saetze = pd.DataFrame(saetze)
                st.dataframe(df_saetze[["typ", "betrag"]], hide_index=True, use_container_width=True)

            with st.form("satz_form"):
                s_typ = st.text_input("Bezeichnung (z.B. Vollmitglied)")
                s_betrag = st.number_input("Betrag in €", min_value=0.0, step=5.0)
                if st.form_submit_button("Satz speichern", use_container_width=True) and s_typ:
                    try:
                        supabase.table("beitragssaetze").upsert({"typ": s_typ.strip(), "betrag": float(s_betrag)}, on_conflict="typ").execute()
                        st.success("Gespeichert!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")

        st.divider()

        try:
            mitglieder_res = supabase.table("mitglieder").select("id, vorname, nachname, mitgliedsnummer").execute()
            alle_mitglieder = mitglieder_res.data if mitglieder_res.data else []
        except:
            alle_mitglieder = []

        try:
            kb_beitraege = supabase.table("kassenbuch").select("*").eq("kategorie", "Mitgliedsbeitrag").execute()
            zahlungen_liste = kb_beitraege.data if kb_beitraege.data else []
        except:
            zahlungen_liste = []

        if alle_mitglieder:
            status_daten = []
            for m in alle_mitglieder:
                m_id = m["id"]
                m_name = f"{m['vorname']} {m['nachname']}"
                m_nr = m.get("mitgliedsnummer", "-")
                
                bezahlt_eintrag = next((z for z in zahlungen_liste if z.get("mitglied_id") == m_id and str(wahl_jahr) in str(z.get("beitrags_zeitraum", ""))), None)
                
                if bezahlt_eintrag:
                    status = "✅ Bezahlt"
                    betrag_bezahlt = bezahlt_eintrag["betrag"]
                else:
                    status = "❌ Offen"
                    betrag_bezahlt = 0.0

                status_daten.append({
                    "id": m_id,
                    "Nr": m_nr,
                    "Name": m_name,
                    "Status": status,
                    "Betrag": f"{betrag_bezahlt:,.2f} €" if betrag_bezahlt > 0 else "-"
                })

            df_status = pd.DataFrame(status_daten)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Gesamt", len(df_status))
            c2.metric("Bezahlt", len(df_status[df_status["Status"].str.contains("Bezahlt")]))
            c3.metric("Offen", len(df_status[df_status["Status"].str.contains("Offen")]))

            st.dataframe(df_status[["Nr", "Name", "Status", "Betrag"]], use_container_width=True, hide_index=True)

            st.markdown("### ⚡ Schnell-Buchung")
            with st.form("schnell_bezahlt_form"):
                offene_mitglieder = {f"{m['Name']} (Nr: {m['Nr']})": m['id'] for m in status_daten if "Offen" in m["Status"]}
                if offene_mitglieder:
                    w_mitglied = st.selectbox("Mitglied (Offen)", list(offene_mitglieder.keys()))
                    ziel_m_id = offene_mitglieder[w_mitglied]
                else:
                    ziel_m_id = None
                    st.info("Alle haben bezahlt! 🎉")
                
                satz_optionen = {s['typ']: s['betrag'] for s in saetze} if saetze else {"Standard": 50.0}
                w_satz_typ = st.selectbox("Beitragstyp", list(satz_optionen.keys())) if satz_optionen else "Beitrag"
                b_betrag = st.number_input("Betrag in €", value=float(satz_optionen.get(w_satz_typ, 50.0)), min_value=0.0)
                b_datum = st.date_input("Datum", value=datetime.today(), format="DD.MM.YYYY")
                
                if st.form_submit_button("Als bezahlt eintragen", type="primary", use_container_width=True) and ziel_m_id:
                    m_info = next((m for m in alle_mitglieder if m["id"] == ziel_m_id), None)
                    m_voller_name = f"{m_info['vorname']} {m_info['nachname']}" if m_info else "Mitglied"
                    
                    neue_einnahme = {
                        "buchungs_datum": b_datum.strftime("%Y-%m-%d"),
                        "typ": "Einnahme",
                        "betrag": float(b_betrag),
                        "person": m_voller_name,
                        "kategorie": "Mitgliedsbeitrag",
                        "verwendungszweck": f"Jahresbeitrag {wahl_jahr} ({w_satz_typ})",
                        "entgegengenommen_von": st.session_state.get("vorname", "Kassenwart"),
                        "erfasst_von_uuid": st.session_state.get("user_id"),
                        "mitglied_id": ziel_m_id,
                        "beitrags_zeitraum": str(wahl_jahr),
                        "ist_geaendert": False
                    }
                    try:
                        supabase.table("kassenbuch").insert(neue_einnahme).execute()
                        st.success("Verbucht!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")

    # ==========================================
    # TAB 4: DIAGRAMME & ANALYSE
    # ==========================================
    with tab_statistik:
        st.subheader("📊 Statistik")
        if not df_filtered.empty:
            diag_typ = st.selectbox("Diagramm", ["Balken (Einnahmen/Ausgaben)", "Kreis (Kategorien)", "Linie (Verlauf)"])
            fig, ax = plt.subplots(figsize=(7, 4))
            
            if "Balken" in diag_typ:
                df_filtered.groupby("typ")["betrag"].sum().plot(kind="bar", ax=ax, color=["#2ca02c", "#d62728"])
                plt.xticks(rotation=0)
            elif "Kreis" in diag_typ:
                kat_typ = st.radio("Typ", ["Ausgaben", "Einnahmen"], horizontal=True)
                sub_df = df_filtered[df_filtered["typ"] == ("Ausgabe" if kat_typ == "Ausgaben" else "Einnahme")]
                if not sub_df.empty:
                    sub_df.groupby("kategorie")["betrag"].sum().plot(kind="pie", ax=ax, autopct="%1.1f%%", cmap="Set3")
                    ax.set_ylabel("")
            elif "Linie" in diag_typ:
                df_sorted = df_filtered.sort_values("buchungs_datum")
                df_sorted["vorzeichen_betrag"] = df_sorted.apply(lambda row: row["betrag"] if row["typ"] == "Einnahme" else -row["betrag"], axis=1)
                df_sorted["kumuliert"] = df_sorted["vorzeichen_betrag"].cumsum()
                ax.plot(df_sorted["buchungs_datum"], df_sorted["kumuliert"], marker="o", color="#1f77b4")
                plt.xticks(rotation=45)

            st.pyplot(fig)
        else:
            st.info("Keine Daten im Zeitraum.")

    # ==========================================
    # TAB 5: PDF-EXPORT
    # ==========================================
    with tab_pdf:
        st.subheader("📄 Kassenbericht PDF")
        if not df_filtered.empty:
            class KassenPDF(FPDF):
                def header(self):
                    self.set_font('helvetica', 'B', 14)
                    self.cell(0, 10, 'Vereins-Kassenbericht', 0, 1, 'C')
                    self.set_font('helvetica', 'I', 9)
                    self.cell(0, 5, f'Zeitraum: {wahl_monat_name} {wahl_jahr}', 0, 1, 'C')
                    self.ln(3)
                def footer(self):
                    self.set_y(-12)
                    self.set_font('helvetica', 'I', 8)
                    self.cell(0, 10, f'Seite {self.page_no()}', 0, 0, 'C')

            def erstelle_pdf():
                pdf = KassenPDF()
                pdf.add_page()
                pdf.set_font('helvetica', 'B', 10)
                pdf.cell(0, 6, f'Kontostand (Gesamt): {kontostand_gesamt:,.2f} EUR', 0, 1)
                pdf.cell(0, 6, f'Saldo (Filter): {f_saldo:,.2f} EUR', 0, 1)
                pdf.ln(5)
                
                pdf.set_font('helvetica', 'B', 8)
                pdf.cell(20, 6, 'Datum', 1)
                pdf.cell(18, 6, 'Typ', 1)
                pdf.cell(22, 6, 'Betrag', 1)
                pdf.cell(35, 6, 'Kategorie', 1)
                pdf.cell(45, 6, 'Person', 1)
                pdf.ln()
                
                pdf.set_font('helvetica', '', 8)
                for _, row in df_filtered.iterrows():
                    pdf.cell(20, 5, row["buchungs_datum"].strftime("%d.%m.%Y"), 1)
                    pdf.cell(18, 5, str(row["typ"]), 1)
                    pdf.cell(22, 5, f"{row['betrag']:,.2f}", 1)
                    pdf.cell(35, 5, str(row["kategorie"])[:20], 1)
                    pdf.cell(45, 5, str(row["person"])[:25], 1)
                    pdf.ln()
                return bytes(pdf.output())

            st.download_button(
                label="📥 PDF herunterladen",
                data=erstelle_pdf(),
                file_name=f"Kassenbericht_{wahl_monat_name}_{wahl_jahr}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        else:
            st.warning("Keine Daten für den Export vorhanden.")

    # ==========================================
    # TAB 6: LOGBUCH (REVISIONSSICHERHEIT)
    # ==========================================
    with tab_log:
        st.subheader("📜 Finanz-Logbuch (Änderungen & Löschungen)")
        st.caption("Hier siehst du lückenlos protokolliert, wer welche Buchung bearbeitet oder gelöscht hat.")
        
        try:
            log_res = supabase.table("kassenbuch_log").select("*").order("erstellt_am", desc=True).execute()
            log_daten = log_res.data if log_res.data else []
        except Exception as e:
            st.error(f"Fehler beim Laden des Logbuchs: {e}")
            log_daten = []
            
        if log_daten:
            df_log = pd.DataFrame(log_daten)
            df_log["erstellt_am"] = pd.to_datetime(df_log["erstellt_am"]).dt.strftime("%d.%m.%Y %H:%M:%S")
            
            st.dataframe(
                df_log[["erstellt_am", "aktion", "durchgefuehrt_von", "details"]],
                use_container_width=True,
                column_config={
                    "erstellt_am": "Zeitpunkt",
                    "aktion": "Aktion",
                    "durchgefuehrt_von": "Durchgeführt von",
                    "details": "Details"
                },
                hide_index=True
            )
        else:
            st.info("Bisher wurden keine Änderungen oder Löschungen im Kassenbuch vorgenommen.")