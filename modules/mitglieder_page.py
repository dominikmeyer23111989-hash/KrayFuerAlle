import streamlit as str_alias
from database import supabase
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

def show():
    str_alias.header("👥 Mitglieder- & Rollenverwaltung & Auswertung")
    
    is_admin_or_vorstand = str_alias.session_state.get("user_rolle", "").lower() in ["admin", "administrator", "vorstand"]
    current_user_id = str_alias.session_state.get("user_id")
    
    if is_admin_or_vorstand:
        tab_liste, tab_neu, tab_bearbeiten, tab_statistik = str_alias.tabs([
            "📋 Mitgliederliste", 
            "➕ Neues Mitglied", 
            "⚙️ Bearbeiten & Löschen",
            "📊 Auswertung & PDF"
        ])
    else:
        tab_liste, tab_bearbeiten = str_alias.tabs([
            "📋 Mitgliederliste", 
            "👤 Mein Profil bearbeiten"
        ])
        tab_neu = None
        tab_statistik = None
    
    # Universelle Hilfsfunktion: Reihenfolge Tag -> Monat -> Jahr
    def datum_auswahl(titel, key_prefix, initial_date=None, min_jahr=1900):
        str_alias.markdown(f"**{titel}**")
        if not initial_date:
            initial_date = datetime.today()
        
        current_year = datetime.today().year + 1
        jahre = list(range(current_year, min_jahr - 1, -1))
        
        init_jahr = initial_date.year if initial_date.year in jahre else datetime.today().year
        init_monat = initial_date.month
        init_tag = initial_date.day
        
        c1, c2, c3 = str_alias.columns(3)
        
        with c1:
            tag = str_alias.selectbox("Tag", list(range(1, 32)), index=min(init_tag-1, 30), key=f"{key_prefix}_tag")
        
        monate_dict = {
            1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
            7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
        }
        
        with c2:
            monat_name = str_alias.selectbox("Monat", list(monate_dict.values()), index=init_monat-1, key=f"{key_prefix}_monat")
            monat = [k for k, v in monate_dict.items() if v == monat_name][0]
        
        with c3:
            jahr = str_alias.selectbox("Jahr", jahre, index=jahre.index(init_jahr), key=f"{key_prefix}_jahr")
        
        try:
            return datetime(jahr, monat, tag)
        except ValueError:
            str_alias.error(f"Ungültiges Datum für {titel} (z.B. 31. im Februar). Bitte korrigieren.")
            return initial_date

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
            return "Keine Angabe"
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
        str_alias.subheader("Übersicht aller Vereinsmitglieder")
        try:
            sichere_spalten = "id, mitgliedsnummer, vorname, nachname, geburtsdatum, geschlecht, email, telefonnummer, strasse, plz, ort, beitrittsdatum, rolle, status, ist_gesperrt, hat_inventar_rechte"
            res = supabase.table("mitglieder").select(sichere_spalten).execute()
            mitglieder = res.data if res.data else []
            
            if mitglieder:
                for m in mitglieder:
                    b_datum = m.get("beitrittsdatum")
                    if b_datum:
                        try:
                            if "T" in str(b_datum): b_datum = str(b_datum).split("T")[0]
                            elif " " in str(b_datum): b_datum = str(b_datum).split(" ")[0]
                            m["beitrittsdatum"] = datetime.strptime(b_datum, "%Y-%m-%d").strftime("%d/%m/%Y")
                        except Exception:
                            pass
                    
                    g_datum = m.get("geburtsdatum")
                    if g_datum:
                        try:
                            if "T" in str(g_datum): g_datum = str(g_datum).split("T")[0]
                            elif " " in str(g_datum): g_datum = str(g_datum).split(" ")[0]
                            m["geburtsdatum"] = datetime.strptime(g_datum, "%Y-%m-%d").strftime("%d/%m/%Y")
                        except Exception:
                            pass

                col1, col2 = str_alias.columns([1, 3])
                col1.metric("Gesamtmitglieder", len(mitglieder))
                
                str_alias.dataframe(
                    mitglieder, 
                    use_container_width=True,
                    column_config={
                        "id": "ID",
                        "mitgliedsnummer": "Mitglieds-Nr",
                        "vorname": "Vorname",
                        "nachname": "Nachname",
                        "geburtsdatum": "Geburtsdatum (DD/MM/YYYY)",
                        "geschlecht": "Geschlecht",
                        "email": "E-Mail",
                        "telefonnummer": "Telefon",
                        "rolle": "Rolle",
                        "status": "Status",
                        "ist_gesperrt": "Gesperrt",
                        "hat_inventar_rechte": "Inventar-Rechte",
                        "beitrittsdatum": "Eintritt (DD/MM/YYYY)"
                    },
                    hide_index=True
                )
            else:
                str_alias.info("Keine Mitglieder in der Datenbank gefunden.")
        except Exception as e:
            str_alias.error(f"Fehler beim Laden der Mitgliederliste: {e}")

    # ==========================================
    # 2. NEUES MITGLIED ANLEGEN (Nur Admin/Vorstand)
    # ==========================================
    if is_admin_or_vorstand and tab_neu is not None:
        with tab_neu:
            str_alias.subheader("Neues Mitglied registrieren")
            
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

            with str_alias.form("neues_mitglied_form"):
                auto_nr_aktiv = str_alias.checkbox("Mitgliedsnummer automatisch vergeben (ab 1)", value=True)
                
                if auto_nr_aktiv:
                    mitgliedsnummer = str_alias.text_input("Mitgliedsnummer (automatisch)", value=naechste_nr, disabled=True)
                    final_mitgliedsnummer = naechste_nr
                else:
                    final_mitgliedsnummer = str_alias.text_input("Mitgliedsnummer (manuell)", value=naechste_nr)

                col1, col2 = str_alias.columns(2)
                with col1:
                    vorname = str_alias.text_input("Vorname *")
                    nachname = str_alias.text_input("Nachname *")
                    geburtsdatum_obj = datum_auswahl("Geburtsdatum", "neu_geb", datetime(1990, 1, 1), 1900)
                    geschlecht = str_alias.selectbox("Geschlecht", ["männlich", "weiblich", "divers"])
                    email = str_alias.text_input("E-Mail-Adresse")
                    telefon = str_alias.text_input("Telefonnummer")
                with col2:
                    strasse = str_alias.text_input("Straße & Hausnummer")
                    plz = str_alias.text_input("PLZ")
                    ort = str_alias.text_input("Ort")
                    beitrittsdatum_obj = datum_auswahl("Eintrittsdatum", "neu_beitritt", datetime.today(), 1900)
                    rolle = str_alias.selectbox("Rolle", ["mitglied", "kassenwart", "vorstand", "admin"])
                    status = str_alias.selectbox("Status", ["aktiv", "passiv", "ehrenmitglied"])
                    ist_gesperrt = str_alias.checkbox("Mitglied gesperrt")
                    inventar_rechte = str_alias.checkbox("Spezielle Inventar-Rechte vergeben")
                
                submitted = str_alias.form_submit_button("Mitglied speichern", type="primary")
                
                if submitted:
                    if not vorname or not nachname:
                        str_alias.error("Vorname und Nachname sind Pflichtfelder!")
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
                            "beitrittsdatum": beitrittsdatum_obj.strftime("%Y-%m-%d"),
                            "rolle": rolle,
                            "status": status,
                            "ist_gesperrt": ist_gesperrt,
                            "hat_inventar_rechte": inventar_rechte
                        }
                        try:
                            supabase.table("mitglieder").insert(neuer_datensatz).execute()
                            str_alias.success(f"Mitglied {vorname} {nachname} (Nr. {final_mitgliedsnummer}) wurde erfolgreich angelegt!")
                            str_alias.rerun()
                        except Exception as e:
                            str_alias.error(f"Fehler beim Speichern in Supabase: {e}")

    # ==========================================
    # 3. BEARBEITEN / MEIN PROFIL
    # ==========================================
    with tab_bearbeiten:
        if is_admin_or_vorstand:
            str_alias.subheader("Mitglied bearbeiten oder löschen (Admin-Ansicht)")
            try:
                res = supabase.table("mitglieder").select("id, mitgliedsnummer, vorname, nachname, email").execute()
                mitglieder_liste = res.data if res.data else []
                
                if mitglieder_liste:
                    auswahl_dict = {
                        f"{m.get('mitgliedsnummer', '---')} - {m.get('vorname', '')} {m.get('nachname', '')}": m['id'] 
                        for m in mitglieder_liste
                    }
                    gewähltes_label = str_alias.selectbox("Mitglied auswählen", options=list(auswahl_dict.keys()))
                    
                    if gewähltes_label:
                        selected_id = auswahl_dict[gewähltes_label]
                        detail_res = supabase.table("mitglieder").select("*").eq("id", selected_id).single().execute()
                        m_data = detail_res.data
                        
                        if m_data:
                            with str_alias.form("edit_mitglied_admin_form"):
                                e_mitgliedsnummer = str_alias.text_input("Mitgliedsnummer", value=str(m_data.get("mitgliedsnummer", "")))
                                col1, col2 = str_alias.columns(2)
                                with col1:
                                    e_vorname = str_alias.text_input("Vorname", value=m_data.get("vorname", ""))
                                    e_nachname = str_alias.text_input("Nachname", value=m_data.get("nachname", ""))
                                    
                                    g_str = m_data.get("geburtsdatum")
                                    g_val = datetime.strptime(g_str.split("T")[0], "%Y-%m-%d") if g_str else datetime(1990, 1, 1)
                                    e_geburtsdatum = datum_auswahl("Geburtsdatum", "admin_edit_geb", g_val, 1900)
                                    
                                    akt_geschlecht = m_data.get("geschlecht", "männlich")
                                    g_optionen = ["männlich", "weiblich", "divers"]
                                    g_idx = g_optionen.index(akt_geschlecht) if akt_geschlecht in g_optionen else 0
                                    e_geschlecht = str_alias.selectbox("Geschlecht", g_optionen, index=g_idx)
                                    
                                    e_email = str_alias.text_input("E-Mail", value=m_data.get("email", "") or "")
                                    e_telefon = str_alias.text_input("Telefonnummer", value=m_data.get("telefonnummer", "") or "")
                                with col2:
                                    e_strasse = str_alias.text_input("Straße & Hausnummer", value=m_data.get("strasse", "") or "")
                                    e_plz = str_alias.text_input("PLZ", value=m_data.get("plz", "") or "")
                                    e_ort = str_alias.text_input("Ort", value=m_data.get("ort", "") or "")
                                    
                                    b_str = m_data.get("beitrittsdatum")
                                    b_val = datetime.strptime(b_str.split("T")[0], "%Y-%m-%d") if b_str else datetime.today()
                                    e_beitrittsdatum = datum_auswahl("Eintrittsdatum", "admin_edit_beitritt", b_val, 1900)
                                    
                                    aktuelle_rolle = m_data.get("rolle", "mitglied")
                                    rollen_optionen = ["mitglied", "kassenwart", "vorstand", "admin"]
                                    rollen_index = rollen_optionen.index(aktuelle_rolle) if aktuelle_rolle in rollen_optionen else 0
                                    e_rolle = str_alias.selectbox("Rolle", rollen_optionen, index=rollen_index)
                                    
                                    aktueller_status = m_data.get("status", "aktiv")
                                    status_optionen = ["aktiv", "passiv", "ehrenmitglied"]
                                    status_index = status_optionen.index(aktueller_status) if aktueller_status in status_optionen else 0
                                    e_status = str_alias.selectbox("Status", status_optionen, index=status_index)
                                    
                                    e_gesperrt = str_alias.checkbox("Mitglied gesperrt", value=m_data.get("ist_gesperrt", False))
                                    e_inventar = str_alias.checkbox("Inventar-Rechte", value=m_data.get("hat_inventar_rechte", False))
                                    
                                col_save, col_del = str_alias.columns(2)
                                with col_save:
                                    save_btn = str_alias.form_submit_button("Änderungen speichern", type="primary")
                                with col_del:
                                    delete_btn = str_alias.form_submit_button("Mitglied löschen", type="secondary")
                                    
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
                                        "beitrittsdatum": e_beitrittsdatum.strftime("%Y-%m-%d"),
                                        "rolle": e_rolle,
                                        "status": e_status,
                                        "ist_gesperrt": e_gesperrt,
                                        "hat_inventar_rechte": e_inventar
                                    }
                                    try:
                                        supabase.table("mitglieder").update(update_daten).eq("id", selected_id).execute()
                                        str_alias.success("Mitgliederdaten erfolgreich aktualisiert!")
                                        str_alias.rerun()
                                    except Exception as e:
                                        str_alias.error(f"Fehler beim Aktualisieren: {e}")
                                        
                                if delete_btn:
                                    try:
                                        supabase.table("mitglieder").delete().eq("id", selected_id).execute()
                                        str_alias.success("Mitglied wurde erfolgreich gelöscht.")
                                        str_alias.rerun()
                                    except Exception as e:
                                        str_alias.error(f"Fehler beim Löschen: {e}")
                else:
                    str_alias.info("Keine Mitglieder vorhanden.")
            except Exception as e:
                str_alias.error(f"Fehler beim Laden der Mitgliederdaten: {e}")
        else:
            str_alias.subheader("Mein Profil bearbeiten")
            if not current_user_id:
                str_alias.error("Kein Benutzer-Kontext gefunden.")
            else:
                try:
                    detail_res = supabase.table("mitglieder").select("*").eq("id", current_user_id).single().execute()
                    m_data = detail_res.data
                    
                    if m_data:
                        with str_alias.form("edit_eigenes_profil_form"):
                            str_alias.info("Du kannst deine persönlichen Daten hier anpassen. Die Mitgliedsnummer ist fest zugewiesen.")
                            str_alias.text_input("Mitgliedsnummer (gesperrt)", value=str(m_data.get("mitgliedsnummer", "")), disabled=True)
                            
                            col1, col2 = str_alias.columns(2)
                            with col1:
                                e_vorname = str_alias.text_input("Vorname", value=m_data.get("vorname", ""))
                                e_nachname = str_alias.text_input("Nachname", value=m_data.get("nachname", ""))
                                
                                g_str = m_data.get("geburtsdatum")
                                g_val = datetime.strptime(g_str.split("T")[0], "%Y-%m-%d") if g_str else datetime(1990, 1, 1)
                                e_geburtsdatum = datum_auswahl("Geburtsdatum", "profil_edit_geb", g_val, 1900)
                                
                                akt_geschlecht = m_data.get("geschlecht", "männlich")
                                g_optionen = ["männlich", "weiblich", "divers"]
                                g_idx = g_optionen.index(akt_geschlecht) if akt_geschlecht in g_optionen else 0
                                e_geschlecht = str_alias.selectbox("Geschlecht", g_optionen, index=g_idx)
                                
                                e_email = str_alias.text_input("E-Mail", value=m_data.get("email", "") or "")
                                e_telefon = str_alias.text_input("Telefonnummer", value=m_data.get("telefonnummer", "") or "")
                            with col2:
                                e_strasse = str_alias.text_input("Straße & Hausnummer", value=m_data.get("strasse", "") or "")
                                e_plz = str_alias.text_input("PLZ", value=m_data.get("plz", "") or "")
                                e_ort = str_alias.text_input("Ort", value=m_data.get("ort", "") or "")
                                str_alias.text_input("Rolle (gesperrt)", value=m_data.get("rolle", "mitglied"), disabled=True)
                                str_alias.text_input("Status (gesperrt)", value=m_data.get("status", "aktiv"), disabled=True)
                                
                            save_btn = str_alias.form_submit_button("Änderungen speichern", type="primary")
                            
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
                                    str_alias.success("Deine Profil-Daten wurden erfolgreich aktualisiert!")
                                    str_alias.rerun()
                                except Exception as e:
                                    str_alias.error(f"Fehler beim Aktualisieren: {e}")
                except Exception as e:
                    str_alias.error(f"Fehler beim Laden deines Profils: {e}")

    # ==========================================
    # 4. AUSWERTUNG & PDF EXPORT (Nur Admin/Vorstand)
    # ==========================================
    if is_admin_or_vorstand and tab_statistik is not None:
        with tab_statistik:
            str_alias.subheader("📊 Mitglieder-Auswertung & Berichte")
            
            try:
                res = supabase.table("mitglieder").select("*").execute()
                daten = res.data if res.data else []
                
                if daten:
                    df = pd.DataFrame(daten)
                    df["alter"] = df["geburtsdatum"].apply(berechne_alter)
                    df["altersgruppe"] = df["alter"].apply(get_altersgruppe)
                    
                    col_wahl1, col_wahl2 = str_alias.columns(2)
                    with col_wahl1:
                        diagramm_typ = str_alias.radio("Diagramm-Typ wählen", ["Balkendiagramm", "Kreisdiagramm"])
                    with col_wahl2:
                        kategorie_wahl = str_alias.selectbox("Auswertung nach", ["Altersgruppen", "Geschlecht", "Status"])
                    
                    str_alias.divider()
                    
                    if kategorie_wahl == "Altersgruppen":
                        reihenfolge = ["0-12 Jahre", "13-18 Jahre", "18-35 Jahre", "35-65 Jahre", "Über 65 Jahre", "Keine Angabe"]
                        counts = df["altersgruppe"].value_counts().reindex(reihenfolge, fill_value=0)
                        titel = "Altersverteilung der Mitglieder"
                    elif kategorie_wahl == "Geschlecht":
                        counts = df["geschlecht"].value_counts(dropna=False)
                        counts.index = counts.index.fillna("Keine Angabe")
                        titel = "Geschlechterverteilung der Mitglieder"
                    else:
                        counts = df["status"].value_counts(dropna=False)
                        counts.index = counts.index.fillna("Keine Angabe")
                        titel = "Mitglieder-Statusverteilung"

                    fig, ax = plt.subplots(figsize=(8, 5))
                    if diagramm_typ == "Balkendiagramm":
                        counts.plot(kind="bar", ax=ax, color="#1f77b4", edgecolor="black")
                        ax.set_ylabel("Anzahl")
                        plt.xticks(rotation=45, ha="right")
                    else:
                        counts.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90, cmap="Pastel1")
                        ax.set_ylabel("")
                        
                    ax.set_title(titel)
                    str_alias.pyplot(fig)
                    
                    str_alias.divider()
                    str_alias.subheader("📄 PDF-Bericht Export")
                    str_alias.markdown("Generiere einen kompakten PDF-Gesamtbericht der Mitgliederliste und der statistischen Auswertung.")
                    
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
                        
                        pdf.set_font('helvetica', 'B', 12)
                        pdf.cell(0, 10, '2. Detaillierte Mitgliederliste', 0, 1)
                        pdf.set_font('helvetica', 'B', 9)
                        
                        pdf.cell(15, 8, 'Nr', 1)
                        pdf.cell(40, 8, 'Name', 1)
                        pdf.cell(30, 8, 'Status', 1)
                        pdf.cell(45, 8, 'E-Mail', 1)
                        pdf.cell(30, 8, 'Rolle', 1)
                        pdf.cell(30, 8, 'Gesperrt', 1)
                        pdf.ln()
                        
                        pdf.set_font('helvetica', '', 9)
                        for m in daten:
                            nr = str(m.get("mitgliedsnummer", ""))
                            name = f"{m.get('vorname', '')} {m.get('nachname', '')}"
                            status = str(m.get("status", "aktiv"))
                            mail = str(m.get("email", "") or "")
                            rolle = str(m.get("rolle", ""))
                            gesperrt = "Ja" if m.get("ist_gesperrt") else "Nein"
                            
                            pdf.cell(15, 7, nr, 1)
                            pdf.cell(40, 7, name[:22], 1)
                            pdf.cell(30, 7, status[:15], 1)
                            pdf.cell(45, 7, mail[:24], 1)
                            pdf.cell(30, 7, rolle[:15], 1)
                            pdf.cell(30, 7, gesperrt, 1)
                            pdf.ln()
                            
                        return bytes(pdf.output())

                    pdf_data = generate_pdf()
                    
                    str_alias.download_button(
                        label="📥 PDF-Gesamtbericht herunterladen",
                        data=pdf_data,
                        file_name=f"Mitgliederbericht_{datetime.today().strftime('%Y-%m-%d')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    str_alias.info("Keine Daten für eine Auswertung vorhanden.")
            except Exception as e:
                str_alias.error(f"Fehler bei der Auswertung oder PDF-Generierung: {e}")