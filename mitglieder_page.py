import streamlit as st
from database import supabase
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

def show():
    st.header("👥 Mitglieder- & Rollenverwaltung & Auswertung")
    
    is_admin_or_vorstand = st.session_state.get("user_rolle", "").lower() in ["admin", "administrator", "vorstand"]
    current_user_id = st.session_state.get("user_id")
    
    if is_admin_or_vorstand:
        tab_liste, tab_neu, tab_bearbeiten, tab_statistik = st.tabs([
            "📋 Mitgliederliste", 
            "➕ Neues Mitglied", 
            "⚙️ Bearbeiten & Löschen",
            "📊 Auswertung & PDF"
        ])
    else:
        tab_liste, tab_bearbeiten = st.tabs([
            "📋 Mitgliederliste", 
            "👤 Mein Profil bearbeiten"
        ])
        tab_neu = None
        tab_statistik = None
    
    # Hilfsfunktion zur Altersberechnung
    def berechne_alter(geburtsdatum_str):
        if not geburtsdatum_str:
            return None
        try:
            if "T" in str(geburtsdatum_str):
                geburtsdatum_str = str(geburtsdatum_str).split("T")[0]
            elif " " in str(geburtsdatum_str):
                geburtsdatum_str = str(geburtsdatum_str).split(" ")[0]
            geb_dat = datetime.strptime(geburtsdatum_str, "%Y-%m-%d")
            heute = datetime.today()
            return heute.year - geb_dat.year - ((heute.month, heute.day) < (geb_dat.month, geb_dat.day))
        except Exception:
            return None

    def get_altersgruppe(alter):
        if alter is None:
            return "Kein Angabe"
        elif alter <= 12:
            return "0-12 Jahre"
        elif alter <= 18:
            return "13-18 Jahre"
        elif alter <= 35:
            return "18-35 Jahre"
        elif alter <= 65:
            return "35-65 Jahre"
        else:
            return "Über 65 Jahre"

    # ==========================================
    # 1. MITGLIEDERLISTE
    # ==========================================
    with tab_liste:
        st.subheader("Übersicht aller Vereinsmitglieder")
        try:
            res = supabase.table("mitglieder").select("*").execute()
            mitglieder = res.data if res.data else []
            
            if mitglieder:
                for m in mitglieder:
                    e_datum = m.get("eintrittsdatum")
                    if e_datum:
                        try:
                            if "T" in str(e_datum): e_datum = str(e_datum).split("T")[0]
                            elif " " in str(e_datum): e_datum = str(e_datum).split(" ")[0]
                            m["eintrittsdatum"] = datetime.strptime(e_datum, "%Y-%m-%d").strftime("%d/%m/%Y")
                        except Exception:
                            pass

                col1, col2 = st.columns([1, 3])
                col1.metric("Gesamtmitglieder", len(mitglieder))
                
                st.dataframe(
                    mitglieder, 
                    use_container_width=True,
                    column_config={
                        "id": "ID",
                        "mitgliedsnummer": "Mitglieds-Nr",
                        "vorname": "Vorname",
                        "nachname": "Nachname",
                        "geburtsdatum": "Geburtsdatum",
                        "geschlecht": "Geschlecht",
                        "email": "E-Mail",
                        "telefonnummer": "Telefon",
                        "rolle": "Rolle",
                        "hat_inventar_rechte": "Inventar-Rechte",
                        "eintrittsdatum": "Eintritt (DD/MM/YYYY)"
                    },
                    hide_index=True
                )
            else:
                st.info("Keine Mitglieder in der Datenbank gefunden.")
        except Exception as e:
            st.error(f"Fehler beim Laden der Mitgliederliste: {e}")

    # ==========================================
    # 2. NEUES MITGLIED ANLEGEN (Nur Admin/Vorstand)
    # ==========================================
    if is_admin_or_vorstand and tab_neu is not None:
        with tab_neu:
            st.subheader("Neues Mitglied registrieren")
            
            try:
                res = supabase.table("mitglieder").select("mitgliedsnummer").execute()
                existing_nums = set()
                if res.data:
                    for m in res.data:
                        nr = m.get("mitgliedsnummer")
                        if nr and str(nr).isdigit():
                            existing_nums.add(int(nr))
                
                n = 1
                while n in existing_nums:
                    n += 1
                naechste_nr = str(n)
            except Exception:
                naechste_nr = "1"

            with st.form("neues_mitglied_form"):
                auto_nr_aktiv = st.checkbox("Mitgliedsnummer automatisch vergeben (ab 1)", value=True)
                
                if auto_nr_aktiv:
                    mitgliedsnummer = st.text_input("Mitgliedsnummer (automatisch)", value=naechste_nr, disabled=True)
                    final_mitgliedsnummer = naechste_nr
                else:
                    final_mitgliedsnummer = st.text_input("Mitgliedsnummer (manuell)", value=naechste_nr)

                col1, col2 = st.columns(2)
                with col1:
                    vorname = st.text_input("Vorname *")
                    nachname = st.text_input("Nachname *")
                    geburtsdatum_obj = st.date_input("Geburtsdatum", value=datetime(1990, 1, 1))
                    geschlecht = st.selectbox("Geschlecht", ["männlich", "weiblich", "divers"])
                    email = st.text_input("E-Mail-Adresse")
                    telefon = st.text_input("Telefonnummer")
                with col2:
                    strasse = st.text_input("Straße & Hausnummer")
                    plz = st.text_input("PLZ")
                    ort = st.text_input("Ort")
                    eintrittsdatum_obj = st.date_input("Eintrittsdatum", value=datetime.today())
                    rolle = st.selectbox("Rolle", ["mitglied", "kassenwart", "vorstand", "admin"])
                    inventar_rechte = st.checkbox("Spezielle Inventar-Rechte vergeben")
                    
                submitted = st.form_submit_button("Mitglied speichern", type="primary")
                
                if submitted:
                    if not vorname or not nachname:
                        st.error("Vorname und Nachname sind Pflichtfelder!")
                    else:
                        neuer_datensatz = {
                            "mitgliedsnummer": final_mitgliedsnummer,
                            "vorname": vorname,
                            "nachname": nachname,
                            "geburtsdatum": geburtsdatum_obj.strftime("%Y-%m-%d"),
                            "geschlecht": geschlecht,
                            "email": email if email else None,
                            "telefonnummer": telefon if telefon else None,
                            "strasse": strasse,
                            "plz": plz,
                            "ort": ort,
                            "eintrittsdatum": eintrittsdatum_obj.strftime("%Y-%m-%d"),
                            "rolle": rolle,
                            "hat_inventar_rechte": inventar_rechte
                        }
                        try:
                            supabase.table("mitglieder").insert(neuer_datensatz).execute()
                            st.success(f"Mitglied {vorname} {nachname} (Nr. {final_mitgliedsnummer}) wurde erfolgreich angelegt!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Speichern in Supabase: {e}")

    # ==========================================
    # 3. BEARBEITEN / MEIN PROFIL
    # ==========================================
    with tab_bearbeiten:
        if is_admin_or_vorstand:
            st.subheader("Mitglied bearbeiten oder löschen (Admin-Ansicht)")
            try:
                res = supabase.table("mitglieder").select("id, mitgliedsnummer, vorname, nachname, email").execute()
                mitglieder_liste = res.data if res.data else []
                
                if mitglieder_liste:
                    auswahl_dict = {
                        f"{m.get('mitgliedsnummer', '---')} - {m.get('vorname', '')} {m.get('nachname', '')}": m['id'] 
                        for m in mitglieder_liste
                    }
                    gewähltes_label = st.selectbox("Mitglied auswählen", options=list(auswahl_dict.keys()))
                    
                    if gewähltes_label:
                        selected_id = auswahl_dict[gewähltes_label]
                        detail_res = supabase.table("mitglieder").select("*").eq("id", selected_id).single().execute()
                        m_data = detail_res.data
                        
                        if m_data:
                            with st.form("edit_mitglied_admin_form"):
                                e_mitgliedsnummer = st.text_input("Mitgliedsnummer", value=str(m_data.get("mitgliedsnummer", "")))
                                col1, col2 = st.columns(2)
                                with col1:
                                    e_vorname = st.text_input("Vorname", value=m_data.get("vorname", ""))
                                    e_nachname = st.text_input("Nachname", value=m_data.get("nachname", ""))
                                    
                                    # Datum parsen
                                    g_str = m_data.get("geburtsdatum")
                                    g_val = datetime.strptime(g_str.split("T")[0], "%Y-%m-%d") if g_str else datetime(1990, 1, 1)
                                    e_geburtsdatum = st.date_input("Geburtsdatum", value=g_val)
                                    
                                    akt_geschlecht = m_data.get("geschlecht", "männlich")
                                    g_optionen = ["männlich", "weiblich", "divers"]
                                    g_idx = g_optionen.index(akt_geschlecht) if akt_geschlecht in g_optionen else 0
                                    e_geschlecht = st.selectbox("Geschlecht", g_optionen, index=g_idx)
                                    
                                    e_email = st.text_input("E-Mail", value=m_data.get("email", "") or "")
                                    e_telefon = st.text_input("Telefonnummer", value=m_data.get("telefonnummer", "") or "")
                                with col2:
                                    e_strasse = st.text_input("Straße & Hausnummer", value=m_data.get("strasse", "") or "")
                                    e_plz = st.text_input("PLZ", value=m_data.get("plz", "") or "")
                                    e_ort = st.text_input("Ort", value=m_data.get("ort", "") or "")
                                    
                                    aktuelle_rolle = m_data.get("rolle", "mitglied")
                                    rollen_optionen = ["mitglied", "kassenwart", "vorstand", "admin"]
                                    rollen_index = rollen_optionen.index(aktuelle_rolle) if aktuelle_rolle in rollen_optionen else 0
                                    
                                    e_rolle = st.selectbox("Rolle", rollen_optionen, index=rollen_index)
                                    e_inventar = st.checkbox("Inventar-Rechte", value=m_data.get("hat_inventar_rechte", False))
                                    
                                col_save, col_del = st.columns(2)
                                with col_save:
                                    save_btn = st.form_submit_button("Änderungen speichern", type="primary")
                                with col_del:
                                    delete_btn = st.form_submit_button("Mitglied löschen", type="secondary")
                                    
                                if save_btn:
                                    update_daten = {
                                        "mitgliedsnummer": e_mitgliedsnummer,
                                        "vorname": e_vorname,
                                        "nachname": e_nachname,
                                        "geburtsdatum": e_geburtsdatum.strftime("%Y-%m-%d"),
                                        "geschlecht": e_geschlecht,
                                        "email": e_email if e_email else None,
                                        "telefonnummer": e_telefon if e_telefon else None,
                                        "strasse": e_strasse if e_strasse else None,
                                        "plz": e_plz if e_plz else None,
                                        "ort": e_ort if e_ort else None,
                                        "rolle": e_rolle,
                                        "hat_inventar_rechte": e_inventar
                                    }
                                    try:
                                        supabase.table("mitglieder").update(update_daten).eq("id", selected_id).execute()
                                        st.success("Mitgliederdaten erfolgreich aktualisiert!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Fehler beim Aktualisieren: {e}")
                                        
                                if delete_btn:
                                    try:
                                        supabase.table("mitglieder").delete().eq("id", selected_id).execute()
                                        st.success("Mitglied wurde erfolgreich gelöscht.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Fehler beim Löschen: {e}")
                else:
                    st.info("Keine Mitglieder vorhanden.")
            except Exception as e:
                st.error(f"Fehler beim Laden der Mitgliederdaten: {e}")
        else:
            st.subheader("Mein Profil bearbeiten")
            if not current_user_id:
                st.error("Kein Benutzer-Kontext gefunden.")
            else:
                try:
                    detail_res = supabase.table("mitglieder").select("*").eq("id", current_user_id).single().execute()
                    m_data = detail_res.data
                    
                    if m_data:
                        with st.form("edit_eigenes_profil_form"):
                            st.info("Du kannst deine persönlichen Daten hier anpassen. Die Mitgliedsnummer ist fest zugewiesen.")
                            st.text_input("Mitgliedsnummer (gesperrt)", value=str(m_data.get("mitgliedsnummer", "")), disabled=True)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                e_vorname = st.text_input("Vorname", value=m_data.get("vorname", ""))
                                e_nachname = st.text_input("Nachname", value=m_data.get("nachname", ""))
                                
                                g_str = m_data.get("geburtsdatum")
                                g_val = datetime.strptime(g_str.split("T")[0], "%Y-%m-%d") if g_str else datetime(1990, 1, 1)
                                e_geburtsdatum = st.date_input("Geburtsdatum", value=g_val)
                                
                                akt_geschlecht = m_data.get("geschlecht", "männlich")
                                g_optionen = ["männlich", "weiblich", "divers"]
                                g_idx = g_optionen.index(akt_geschlecht) if akt_geschlecht in g_optionen else 0
                                e_geschlecht = st.selectbox("Geschlecht", g_optionen, index=g_idx)
                                
                                e_email = st.text_input("E-Mail", value=m_data.get("email", "") or "")
                                e_telefon = st.text_input("Telefonnummer", value=m_data.get("telefonnummer", "") or "")
                            with col2:
                                e_strasse = st.text_input("Straße & Hausnummer", value=m_data.get("strasse", "") or "")
                                e_plz = st.text_input("PLZ", value=m_data.get("plz", "") or "")
                                e_ort = st.text_input("Ort", value=m_data.get("ort", "") or "")
                                st.text_input("Rolle (gesperrt)", value=m_data.get("rolle", "mitglied"), disabled=True)
                                
                            save_btn = st.form_submit_button("Änderungen speichern", type="primary")
                            
                            if save_btn:
                                update_daten = {
                                    "vorname": e_vorname,
                                    "nachname": e_nachname,
                                    "geburtsdatum": e_geburtsdatum.strftime("%Y-%m-%d"),
                                    "geschlecht": e_geschlecht,
                                    "email": e_email if e_email else None,
                                    "telefonnummer": e_telefon if e_telefon else None,
                                    "strasse": e_strasse if e_strasse else None,
                                    "plz": e_plz if e_plz else None,
                                    "ort": e_ort if e_ort else None
                                }
                                try:
                                    supabase.table("mitglieder").update(update_daten).eq("id", current_user_id).execute()
                                    st.success("Deine Profil-Daten wurden erfolgreich aktualisiert!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Fehler beim Aktualisieren: {e}")
                except Exception as e:
                    st.error(f"Fehler beim Laden deines Profils: {e}")

    # ==========================================
    # 4. AUSWERTUNG & PDF EXPORT (Nur Admin/Vorstand)
    # ==========================================
    if is_admin_or_vorstand and tab_statistik is not None:
        with tab_statistik:
            st.subheader("📊 Mitglieder-Auswertung & Berichte")
            
            try:
                res = supabase.table("mitglieder").select("*").execute()
                daten = res.data if res.data else []
                
                if daten:
                    # Aufbereitung für Pandas
                    df = pd.DataFrame(daten)
                    df["alter"] = df["geburtsdatum"].apply(berechne_alter)
                    df["altersgruppe"] = df["alter"].apply(get_altersgruppe)
                    
                    col_wahl1, col_wahl2 = st.columns(2)
                    with col_wahl1:
                        diagramm_typ = st.radio("Diagramm-Typ wählen", ["Balkendiagramm", "Kreisdiagramm"])
                    with col_wahl2:
                        kategorie_wahl = st.selectbox("Auswertung nach", ["Altersgruppen", "Geschlecht"])
                    
                    st.divider()
                    
                    # Daten aggregieren
                    if kategorie_wahl == "Altersgruppen":
                        reihenfolge = ["0-12 Jahre", "13-18 Jahre", "18-35 Jahre", "35-65 Jahre", "Über 65 Jahre", "Kein Angabe"]
                        counts = df["altersgruppe"].value_counts().reindex(reihenfolge, fill_value=0)
                        titel = "Altersverteilung der Mitglieder"
                    else:
                        counts = df["geschlecht"].value_counts(dropna=False)
                        counts.index = counts.index.fillna("Keine Angabe")
                        titel = "Geschlechterverteilung der Mitglieder"

                    # Chart zeichnen mit Matplotlib
                    fig, ax = plt.subplots(figsize=(8, 5))
                    if diagramm_typ == "Balkendiagramm":
                        counts.plot(kind="bar", ax=ax, color="#1f77b4", edgecolor="black")
                        ax.set_ylabel("Anzahl")
                        plt.xticks(rotation=45, ha="right")
                    else:
                        counts.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90, cmap="Pastel1")
                        ax.set_ylabel("")
                        
                    ax.set_title(titel)
                    st.pyplot(fig)
                    
                    st.divider()
                    st.subheader("📄 PDF-Export")
                    st.markdown("Generiere einen kompakten PDF-Bericht der Mitgliederliste und der statistischen Auswertung.")
                    
                    # PDF Generation Logik
                    class PDF(FPDF):
                        def header(self):
                            self.set_font('helvetica', 'B', 15)
                            self.cell(0, 10, 'KrayFürAlle e.V. - Mitgliederbericht', 0, 1, 'C')
                            self.ln(5)

                        def footer(self):
                            self.set_y(-15)
                            self.set_font('helvetica', 'I', 8)
                            self.cell(0, 10, f'Erstellt am {datetime.today().strftime("%d.%m.%Y")} - Seite {self.page_no()}', 0, 0, 'C')

                    def generate_pdf():
                        pdf = PDF()
                        pdf.add_page()
                        
                        # Statistik-Zusammenfassung ins PDF schreiben
                        pdf.set_font('helvetica', 'B', 12)
                        pdf.cell(0, 10, '1. Statistische Zusammenfassung', 0, 1)
                        pdf.set_font('helvetica', '', 10)
                        pdf.cell(0, 8, f'Gesamtanzahl Mitglieder: {len(df)}', 0, 1)
                        pdf.ln(3)
                        
                        pdf.set_font('helvetica', 'B', 10)
                        pdf.cell(0, 6, 'Altersgruppen:', 0, 1)
                        pdf.set_font('helvetica', '', 10)
                        for k, v in df["altersgruppe"].value_counts().items():
                            pdf.cell(0, 6, f' - {k}: {v} Mitglieder', 0, 1)
                            
                        pdf.ln(3)
                        pdf.set_font('helvetica', 'B', 10)
                        pdf.cell(0, 6, 'Geschlechter:', 0, 1)
                        pdf.set_font('helvetica', '', 10)
                        for k, v in df["geschlecht"].value_counts(dropna=False).items():
                            geschlecht_label = str(k) if k else "Keine Angabe"
                            pdf.cell(0, 6, f' - {geschlecht_label}: {v} Mitglieder', 0, 1)

                        pdf.ln(10)
                        
                        # Mitgliederliste Tabelle ins PDF schreiben
                        pdf.set_font('helvetica', 'B', 12)
                        pdf.cell(0, 10, '2. Detaillierte Mitgliederliste', 0, 1)
                        pdf.set_font('helvetica', 'B', 9)
                        
                        # Tabellenkopf
                        pdf.cell(20, 8, 'Nr', 1)
                        pdf.cell(45, 8, 'Name', 1)
                        pdf.cell(35, 8, 'Telefon', 1)
                        pdf.cell(50, 8, 'E-Mail', 1)
                        pdf.cell(40, 8, 'Rolle', 1)
                        pdf.ln()
                        
                        pdf.set_font('helvetica', '', 9)
                        for m in daten:
                            nr = str(m.get("mitgliedsnummer", ""))
                            name = f"{m.get('vorname', '')} {m.get('nachname', '')}"
                            tel = str(m.get("telefonnummer", "") or "")
                            mail = str(m.get("email", "") or "")
                            rolle = str(m.get("rolle", ""))
                            
                            pdf.cell(20, 7, nr, 1)
                            pdf.cell(45, 7, name[:24], 1)
                            pdf.cell(35, 7, tel[:18], 1)
                            pdf.cell(50, 7, mail[:26], 1)
                            pdf.cell(40, 7, rolle[:20], 1)
                            pdf.ln()
                            
                        return bytes(pdf.output())

                    pdf_data = generate_pdf()
                    
                    st.download_button(
                        label="📥 PDF-Bericht herunterladen",
                        data=pdf_data,
                        file_name=f"Mitgliederbericht_{datetime.today().strftime('%Y-%m-%d')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.info("Keine Daten für eine Auswertung vorhanden.")
            except Exception as e:
                st.error(f"Fehler bei der Auswertung oder PDF-Generierung: {e}")