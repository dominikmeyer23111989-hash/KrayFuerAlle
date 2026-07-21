import streamlit as st
from database import supabase
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

def show():
    st.header("💰 Finanzen, Kassenbuch & Beitragsverwaltung")
    
    # 1. Rechteprüfung (Nur Admin, Vorstand, Kassenwart)
    user_rolle = st.session_state.get("user_rolle", "").lower()
    erlaubte_rollen = ["admin", "administrator", "vorstand", "kassenwart"]
    
    if user_rolle not in erlaubte_rollen:
        st.error("⛔ Zugriff verweigert. Dieser Bereich ist nur für Admin, Vorstand und Kassenwart zugänglich.")
        return

    # Tabs definieren (inkl. dem neuen Beitrags-Tab)
    tab_buchungen, tab_neu, tab_beitraege, tab_statistik, tab_pdf = st.tabs([
        "📖 Kassenbuch & Übersicht", 
        "➕ Buchung erfassen", 
        "🏷️ Beiträge & Zahlungsstatus",
        "📊 Diagramme & Analyse", 
        "📄 PDF-Export"
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
    # GLOBALER KONTOSTAND & FILTER (Monat / Jahr)
    # ==========================================
    st.sidebar.divider()
    st.sidebar.subheader("📅 Finanz-Filter")
    
    # Allzeit-Kontostand berechnen
    if not df.empty:
        gesamt_einnahmen = df[df["typ"] == "Einnahme"]["betrag"].sum()
        gesamt_ausgaben = df[df["typ"] == "Ausgabe"]["betrag"].sum()
        kontostand_gesamt = gesamt_einnahmen - gesamt_ausgaben
    else:
        kontostand_gesamt = 0.0

    st.sidebar.metric("💳 Ist-Stand Konto (Gesamt)", f"{kontostand_gesamt:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))

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
    # TAB 1: KASSENBUCH & ÜBERSICHT
    # ==========================================
    with tab_buchungen:
        st.subheader(f"Buchungsübersicht ({wahl_monat_name} {wahl_jahr})")
        
        if not df_filtered.empty:
            f_einnahmen = df_filtered[df_filtered["typ"] == "Einnahme"]["betrag"].sum()
            f_ausgaben = df_filtered[df_filtered["typ"] == "Ausgabe"]["betrag"].sum()
            f_saldo = f_einnahmen - f_ausgaben

            col1, col2, col3 = st.columns(3)
            col1.metric("Einnahmen (Filter)", f"{f_einnahmen:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            col2.metric("Ausgaben (Filter)", f"{f_ausgaben:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            col3.metric("Saldo (Filter)", f"{f_saldo:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.divider()

            df_anzeige = df_filtered[["buchungs_datum", "typ", "betrag", "kategorie", "person", "verwendungszweck", "entgegengenommen_von"]].copy()
            df_anzeige["buchungs_datum"] = df_anzeige["buchungs_datum"].dt.strftime("%d/%m/%Y")
            df_anzeige["betrag"] = df_anzeige["betrag"].map(lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            
            st.dataframe(
                df_anzeige,
                use_container_width=True,
                column_config={
                    "buchungs_datum": "Datum",
                    "typ": "Typ",
                    "betrag": "Betrag",
                    "kategorie": "Kategorie",
                    "person": "Person / Mitglied",
                    "verwendungszweck": "Verwendungszweck",
                    "entgegengenommen_von": "Erfasst von"
                },
                hide_index=True
            )
        else:
            st.info("Keine Buchungen für den ausgewählten Zeitraum gefunden.")

    # ==========================================
    # TAB 2: BUCHUNG ERFASSEN
    # ==========================================
    with tab_neu:
        st.subheader("Neue Einnahme oder Ausgabe eintragen")
        
        # Mitglieder für Dropdown laden
        try:
            m_res = supabase.table("mitglieder").select("id, vorname, nachname, mitgliedsnummer").execute()
            mitglieder_liste = m_res.data if m_res.data else []
        except:
            mitglieder_liste = []

        mitglied_optionen = {f"{m['vorname']} {m['nachname']} (Nr: {m.get('mitgliedsnummer', 'N/A')})": m['id'] for m in mitglieder_liste}
        
        with st.form("kassenbuch_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                buchungs_datum = st.date_input("Buchungsdatum", value=datetime.today())
                typ = st.selectbox("Buchungstyp", ["Einnahme", "Ausgabe"])
                betrag = st.number_input("Betrag in €", min_value=0.01, step=1.00, format="%.2f")
                kategorie = st.selectbox("Kategorie", [
                    "Mitgliedsbeitrag", "Spende", "Veranstaltung", "Material & Equipment", 
                    "Miete & Nebenkosten", "Gebühren & Bank", "Sonstige Einnahmen", "Sonstige Ausgaben"
                ])
            with col_b:
                is_mitglied_zuordnung = starten_mit = st.checkbox("Mitglied zuordnen?", value=(kategorie == "Mitgliedsbeitrag"))
                
                selected_mitglied_id = None
                person_name = ""
                
                if mitglied_optionen and is_mitglied_zuordnung:
                    wahl_m = st.selectbox("Mitglied auswählen", list(mitglied_optionen.keys()))
                    selected_mitglied_id = mitglied_optionen[wahl_m]
                    # Namen automatisch ermitteln
                    m_data = next((m for m in mitglieder_liste if m['id'] == selected_mitglied_id), None)
                    if m_data:
                        person_name = f"{m_data['vorname']} {m_data['nachname']}"
                else:
                    person_name = st.text_input("Name der Person / Firma *")

                verwendungszweck = st.text_area("Verwendungszweck / Bemerkung")
                entgegengenommen_von = st.text_input("Entgegengenommen / Gebucht von *", value=st.session_state.get("vorname", "Vorstand"))
                beitrags_zeitraum = st.text_input("Beitragszeitraum (z.B. Jahr 2026)", value=wahl_jahr)

            submitted = st.form_submit_button("Buchung speichern", type="primary")
            
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
                        "beitrags_zeitraum": beitrags_zeitraum if beitrags_zeitraum else None
                    }
                    try:
                        supabase.table("kassenbuch").insert(neue_buchung).execute()
                        st.success(f"Buchung über {betrag:.2f} € erfolgreich gespeichert!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Speichern in Supabase: {e}")

    # ==========================================
    # TAB 3: BEITRÄGE & ZAHLUNGSSTATUS
    # ==========================================
    with tab_beitraege:
        st.subheader(f"🏷️ Beitragsätze & Zahlungsstatus für das Jahr {wahl_jahr}")
        
        # 1. Beitragssätze verwalten
        with st.expander("⚙️ Beitragssätze konfigurieren (Preise festlegen)"):
            try:
                b_res = supabase.table("beitragssaetze").select("*").execute()
                saetze = b_res.data if b_res.data else []
            except:
                saetze = []

            # Anzeige der aktuellen Sätze
            if saetze:
                df_saetze = pd.DataFrame(saetze)
                st.dataframe(df_saetze[["typ", "betrag"]], hide_index=True, use_container_width=True)
            else:
                st.info("Noch keine Beitragssätze hinterlegt.")

            # Neuen Satz hinzufügen oder aktualisieren
            with st.form("satz_form"):
                st.markdown("**Beitragssatz hinzufügen oder aktualisieren**")
                s_typ = st.text_input("Bezeichnung (z.B. Vollmitglied, Ermäßigt, Passiv)")
                s_betrag = st.number_input("Betrag in €", min_value=0.0, step=5.0)
                s_submit = st.form_submit_button("Beitragssatz speichern")
                
                if s_submit and s_typ:
                    try:
                        # Upsert über den eindeutigen Key 'typ'
                        supabase.table("beitragssaetze").upsert({
                            "typ": s_typ.strip(),
                            "betrag": float(s_betrag)
                        }, on_conflict="typ").execute()
                        st.success(f"Beitragssatz '{s_typ}' erfolgreich gespeichert!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Speichern des Satzes: {e}")

        st.divider()
        st.subheader(f"📋 Wer hat für das Jahr {wahl_jahr} bezahlt?")

        # Alle Mitglieder laden
        try:
            mitglieder_res = supabase.table("mitglieder").select("id, vorname, nachname, mitgliedsnummer, rolle").execute()
            alle_mitglieder = mitglieder_res.data if mitglieder_res.data else []
        except:
            alle_mitglieder = []

        # Alle Kassenbuch-Zahlungen für den Beitragszeitraum laden
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
                
                # Prüfen, ob für dieses Mitglied im gewählten Jahr eine Beitragszahlung existiert
                bezahlt_eintrag = next((z for z in zahlungen_liste if z.get("mitglied_id") == m_id and str(wahl_jahr) in str(z.get("beitrags_zeitraum", ""))), None)
                
                if bezahlt_eintrag:
                    status = "✅ Bezahlten"
                    betrag_bezahlt = bezahlt_eintrag["betrag"]
                    datum_bezahlt = bezahlt_bezahlt_datum = bezahlt_eintrag["buchungs_datum"]
                else:
                    status = "❌ Offen"
                    betrag_bezahlt = 0.0
                    datum_bezahlt = "-"

                status_daten.append({
                    "id": m_id,
                    "Mitglieds-Nr": m_nr,
                    "Name": m_name,
                    "Status": status,
                    "Bezahlter Betrag": f"{betrag_bezahlt:,.2f} €" if betrag_bezahlt > 0 else "-",
                    "Zahlungsdatum": datum_bezahlt
                })

            df_status = pd.DataFrame(status_daten)
            
            # Kennzahlen oben anzeigen
            anzahl_gesamt = len(df_status)
            anzahl_bezahlt = len(df_status[df_status["Status"].str.contains("Bezahlt")])
            anzahl_offen = anzahl_gesamt - anzahl_bezahlt

            c1, c2, c3 = st.columns(3)
            c1.metric("Mitglieder gesamt", anzahl_gesamt)
            c2.metric("Beitrag bezahlt", anzahl_bezahlt, delta_color="normal")
            c3.metric("Ausstehend (Offen)", anzahl_offen, delta_color="inverse")

            st.dataframe(df_status[["Mitglieds-Nr", "Name", "Status", "Bezahlter Betrag", "Zahlungsdatum"]], use_container_width=True, hide_index=True)

            st.markdown("### ⚡ Schnell-Erfassung: Mitglied als 'Bezahlt' markieren")
            with st.form("schnell_bezahlt_form"):
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    offene_mitglieder = {f"{m['Name']} (Nr: {m['Mitglieds-Nr']})": m['id'] for m in status_daten if "Offen" in m["Status"]}
                    if offene_mitglieder:
                        w_mitglied = st.selectbox("Mitglied (nur Offene)", list(offene_mitglieder.keys()))
                        ziel_m_id = offene_mitglieder[w_mitglied]
                    else:
                        ziel_m_id = None
                        st.info("Alle Mitglieder haben bezahlt! 🎉")
                with col_s2:
                    # Betrag aus Beitragssätzen vorbelegen falls vorhanden
                    satz_optionen = {s['typ']: s['betrag'] for s in saetze} if saetze else {"Standardbeitrag": 50.0}
                    w_satz_typ = st.selectbox("Beitragstyp", list(satz_optionen.keys())) if satz_optionen else "Beitrag"
                    standard_betrag = satz_optionen.get(w_satz_typ, 50.0) if satz_optionen else 50.0
                    
                    b_betrag = st.number_input("Betrag in €", value=float(standard_betrag), min_value=0.0)
                with col_s3:
                    b_datum = st.date_input("Eingangsdatum", value=datetime.today())
                    
                s_b_submit = st.form_submit_button("Beitrag als eingegangen buchen", type="primary")
                
                if s_b_submit and ziel_m_id:
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
                        "beitrags_zeitraum": str(wahl_jahr)
                    }
                    try:
                        supabase.table("kassenbuch").insert(neue_einnahme).execute()
                        st.success(f"Beitrag für {m_voller_name} erfolgreich verbucht!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler beim Verbuchen: {e}")
        else:
            st.info("Keine Mitglieder in der Datenbank gefunden.")

    # ==========================================
    # TAB 4: DIAGRAMME & ANALYSE
    # ==========================================
    with tab_statistik:
        st.subheader("📊 Finanzstatistiken & Diagramme")
        
        if not df_filtered.empty:
            diag_typ = st.selectbox("Diagramm-Typ wählen", ["Balkendiagramm (Einnahmen vs. Ausgaben)", "Kreisdiagramm (Kategorien)", "Liniendiagramm (Verlauf)"])
            
            fig, ax = plt.subplots(figsize=(9, 5))
            
            if "Balkendiagramm" in diag_typ:
                summen = df_filtered.groupby("typ")["betrag"].sum()
                summen.plot(kind="bar", ax=ax, color=["#2ca02c", "#d62728"], edgecolor="black")
                ax.set_title(f"Einnahmen vs. Ausgaben ({wahl_monat_name} {wahl_jahr})")
                ax.set_ylabel("Euro (€)")
                plt.xticks(rotation=0)
                
            elif "Kreisdiagramm" in diag_typ:
                kat_typ = st.radio("Nach welchen Buchungen filtern?", ["Ausgaben", "Einnahmen"])
                sub_df = df_filtered[df_filtered["typ"] == ("Ausgabe" if kat_typ == "Ausgaben" else "Einnahme")]
                
                if not sub_df.empty:
                    kat_summen = sub_df.groupby("kategorie")["betrag"].sum()
                    kat_summen.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90, cmap="Set3")
                    ax.set_ylabel("")
                    ax.set_title(f"{kat_typ}-Verteilung nach Kategorien")
                else:
                    st.info("Keine Daten für dieses Kreisdiagramm im gewählten Zeitraum.")
                    
            elif "Liniendiagramm" in diag_typ:
                df_sorted = df_filtered.sort_values("buchungs_datum")
                df_sorted["vorzeichen_betrag"] = df_sorted.apply(lambda row: row["betrag"] if row["typ"] == "Einnahme" else -row["betrag"], axis=1)
                df_sorted["kumuliert"] = df_sorted["vorzeichen_betrag"].cumsum()
                
                ax.plot(df_sorted["buchungs_datum"], df_sorted["kumuliert"], marker="o", linestyle="-", color="#1f77b4")
                ax.set_title(f"Verlauf des Kassenbestands im gewählten Zeitraum")
                ax.set_ylabel("Saldo (€)")
                plt.xticks(rotation=45)

            st.pyplot(fig)
        else:
            st.info("Keine Daten für Diagramme im gewählten Zeitraum vorhanden.")

    # ==========================================
    # TAB 5: PDF-EXPORT
    # ==========================================
    with tab_pdf:
        st.subheader("📄 Kassenbericht als PDF exportieren")
        st.markdown(f"Erstelle einen offiziellen Kassenbericht für den Zeitraum: **{wahl_monat_name} {wahl_jahr}**.")
        
        if not df_filtered.empty:
            class KassenPDF(FPDF):
                def header(self):
                    self.set_font('helvetica', 'B', 15)
                    self.cell(0, 10, 'KrayFürAlle e.V. - Offizieller Kassenbericht', 0, 1, 'C')
                    self.set_font('helvetica', 'I', 10)
                    self.cell(0, 6, f'Zeitraum: {wahl_monat_name} {wahl_jahr}', 0, 1, 'C')
                    self.ln(5)

                def footer(self):
                    self.set_y(-15)
                    self.set_font('helvetica', 'I', 8)
                    self.cell(0, 10, f'Erstellt am {datetime.today().strftime("%d.%m.%Y")} - Seite {self.page_no()}', 0, 0, 'C')

            def erstelle_kassen_pdf():
                pdf = KassenPDF()
                pdf.add_page()
                
                pdf.set_font('helvetica', 'B', 12)
                pdf.cell(0, 8, '1. Finanzübersicht', 0, 1)
                pdf.set_font('helvetica', '', 10)
                pdf.cell(0, 6, f'Gesamter Kontostand (Allzeit): {kontostand_gesamt:,.2f} EUR', 0, 1)
                pdf.cell(0, 6, f'Einnahmen im Zeitraum: {f_einnahmen:,.2f} EUR', 0, 1)
                pdf.cell(0, 6, f'Ausgaben im Zeitraum: {f_ausgaben:,.2f} EUR', 0, 1)
                pdf.cell(0, 6, f'Saldo im Zeitraum: {f_saldo:,.2f} EUR', 0, 1)
                pdf.ln(8)
                
                pdf.set_font('helvetica', 'B', 12)
                pdf.cell(0, 8, '2. Buchungsdetails', 0, 1)
                pdf.set_font('helvetica', 'B', 8)
                
                pdf.cell(22, 7, 'Datum', 1)
                pdf.cell(20, 7, 'Typ', 1)
                pdf.cell(25, 7, 'Betrag', 1)
                pdf.cell(38, 7, 'Kategorie', 1)
                pdf.cell(45, 7, 'Person', 1)
                pdf.cell(40, 7, 'Zweck', 1)
                pdf.ln()
                
                pdf.set_font('helvetica', '', 8)
                for _, row in df_filtered.iterrows():
                    d_str = row["buchungs_datum"].strftime("%d/%m/%Y")
                    t_str = str(row["typ"])
                    b_str = f"{row['betrag']:,.2f} EUR"
                    k_str = str(row["kategorie"])
                    p_str = str(row["person"])
                    z_str = str(row["verwendungszweck"] or "-")
                    
                    pdf.cell(22, 6, d_str, 1)
                    pdf.cell(20, 6, t_str, 1)
                    pdf.cell(25, 6, b_str, 1)
                    pdf.cell(38, 6, k_str[:22], 1)
                    pdf.cell(45, 6, p_str[:26], 1)
                    pdf.cell(40, 6, z_str[:24], 1)
                    pdf.ln()
                    
                return bytes(pdf.output())

            pdf_bytes = erstelle_kassen_pdf()
            
            st.download_button(
                label="📥 Kassenbericht-PDF herunterladen",
                data=pdf_bytes,
                file_name=f"Kassenbericht_{wahl_monat_name}_{wahl_jahr}.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.warning("Keine Buchungen für den Export im gewählten Zeitraum vorhanden.")