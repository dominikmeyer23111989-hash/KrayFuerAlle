import streamlit as str_alias
from database import supabase
from datetime import datetime, time
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

def show():
    str_alias.header("👥 Mitglieder-, Rollen- & Abwesenheitsverwaltung")
    
    is_admin_or_vorstand = str_alias.session_state.get("user_rolle", "").lower() in ["admin", "administrator", "vorstand"]
    current_user_id = str_alias.session_state.get("user_id")
    
    # Tabs dynamisch je nach Rolle anpassen (inkl. Abwesenheiten)
    if is_admin_or_vorstand:
        tab_liste, tab_neu, tab_bearbeiten, tab_statistik, tab_abw = str_alias.tabs([
            "📋 Mitgliederliste", 
            "➕ Neues Mitglied", 
            "⚙️ Bearbeiten & Löschen",
            "📊 Auswertung & PDF",
            "📅 Abwesenheiten"
        ])
    else:
        tab_liste, tab_bearbeiten, tab_abw = str_alias.tabs([
            "📋 Mitgliederliste", 
            "👤 Mein Profil bearbeiten",
            "📅 Abwesenheiten"
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
            str_alias.error(f"Ungültiges Datum für {titel}. Bitte korrigieren.")
            return initial_date

    # Hilfsfunktion zur Altersberechnung
    def berechne_alter(geburtsdatum_str):
        if not geburtsdatum_str:
            return None
        try:
            g_str = str(geburtsdatum_str).split("T")[0].split(" ")[0]
            geb_dat = datetime.strptime(g_str, "%Y-%m-%d")
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
                    for feld in ["beitrittsdatum", "geburtsdatum"]:
                        val = m.get(feld)
                        if val:
                            try:
                                v_str = str(val).split("T")[0].split(" ")[0]
                                m[feld] = datetime.strptime(v_str, "%Y-%m-%d").strftime("%d.%m.%Y")
                            except Exception:
                                pass

                str_alias.metric("Gesamtmitglieder", len(mitglieder))
                str_alias.dataframe(
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
                        "status": "Status",
                        "ist_gesperrt": "Gesperrt",
                        "hat_inventar_rechte": "Inventar-Rechte",
                        "beitrittsdatum": "Eintritt"
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
                existing_nums = {int(m.get("mitgliedsnummer")) for m in (res.data or []) if m.get("mitgliedsnummer") and str(m.get("mitgliedsnummer")).isdigit()}
                n = 1
                while n in existing_nums:
                    n += 1
                naechste_nr = str(n)
            except Exception:
                naechste_nr = "1"

            auto_nr_aktiv = str_alias.checkbox("Mitgliedsnummer automatisch vergeben", value=True, key="auto_nr_checkbox")

            with str_alias.form("neues_mitglied_form"):
                final_mitgliedsnummer = naechste_nr if auto_nr_aktiv else str_alias.text_input("Mitgliedsnummer", value=naechste_nr)

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
                
                if str_alias.form_submit_button("Mitglied speichern", type="primary"):
                    if not vorname or not nachname:
                        str_alias.error("Vorname und Nachname sind Pflichtfelder!")
                    else:
                        neuer_datensatz = {
                            "mitgliedsnummer": final_mitgliedsnummer,
                            "vorname": vorname,
                            "nachname": nachname,
                            "geburtsdatum": geburtsdatum_obj.strftime("%Y-%m-%d"),
                            "geschlecht": geschlecht,
                            "email": email or None,
                            "telefonnummer": telefon or None,
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
                            str_alias.success(f"Mitglied {vorname} {nachname} erfolgreich angelegt!")
                            str_alias.rerun()
                        except Exception as e:
                            str_alias.error(f"Fehler beim Speichern: {e}")

    # ==========================================
    # 3. BEARBEITEN / MEIN PROFIL
    # ==========================================
    with tab_bearbeiten:
        if is_admin_or_vorstand:
            str_alias.subheader("Mitglied bearbeiten oder löschen (Admin-Ansicht)")
            try:
                res = supabase.table("mitglieder").select("id, mitgliedsnummer, vorname, nachname").execute()
                mitglieder_liste = res.data if res.data else []
                
                if mitglieder_liste:
                    auswahl_dict = {f"{m.get('mitgliedsnummer', '---')} - {m.get('vorname', '')} {m.get('nachname', '')}": m['id'] for m in mitglieder_liste}
                    gewähltes_label = str_alias.selectbox("Mitglied auswählen", options=list(auswahl_dict.keys()))
                    
                    if gewähltes_label:
                        selected_id = auswahl_dict[gewähltes_label]
                        m_data = supabase.table("mitglieder").select("*").eq("id", selected_id).single().execute().data
                        
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
                                    g_opt = ["männlich", "weiblich", "divers"]
                                    e_geschlecht = str_alias.selectbox("Geschlecht", g_opt, index=g_opt.index(akt_geschlecht) if akt_geschlecht in g_opt else 0)
                                    
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
                                    r_opt = ["mitglied", "kassenwart", "vorstand", "admin"]
                                    e_rolle = str_alias.selectbox("Rolle", r_opt, index=r_opt.index(aktuelle_rolle) if aktuelle_rolle in r_opt else 0)
                                    
                                    aktueller_status = m_data.get("status", "aktiv")
                                    s_opt = ["aktiv", "passiv", "ehrenmitglied"]
                                    e_status = str_alias.selectbox("Status", s_opt, index=s_opt.index(aktueller_status) if aktueller_status in s_opt else 0)
                                    
                                    e_gesperrt = str_alias.checkbox("Mitglied gesperrt", value=m_data.get("ist_gesperrt", False))
                                    e_inventar = str_alias.checkbox("Inventar-Rechte", value=m_data.get("hat_inventar_rechte", False))
                                    
                                col_save, col_del = str_alias.columns(2)
                                with col_save:
                                    save_btn = str_alias.form_submit_button("Änderungen speichern", type="primary")
                                with col_del:
                                    delete_btn = str_alias.form_submit_button("Mitglied löschen", type="secondary")
                                    
                                if save_btn:
                                    update_daten = {
                                        "mitgliedsnummer": e_mitgliedsnummer, "vorname": e_vorname, "nachname": e_nachname,
                                        "geburtsdatum": e_geburtsdatum.strftime("%Y-%m-%d"), "geschlecht": e_geschlecht,
                                        "email": e_email or None, "telefonnummer": e_telefon or None,
                                        "strasse": e_strasse or None, "plz": e_plz or None, "ort": e_ort or None,
                                        "beitrittsdatum": e_beitrittsdatum.strftime("%Y-%m-%d"), "rolle": e_rolle,
                                        "status": e_status, "ist_gesperrt": e_gesperrt, "hat_inventar_rechte": e_inventar
                                    }
                                    try:
                                        supabase.table("mitglieder").update(update_daten).eq("id", selected_id).execute()
                                        str_alias.success("Daten aktualisiert!")
                                        str_alias.rerun()
                                    except Exception as e:
                                        str_alias.error(f"Fehler: {e}")
                                        
                                if delete_btn:
                                    try:
                                        supabase.table("mitglieder").delete().eq("id", selected_id).execute()
                                        str_alias.success("Mitglied gelöscht.")
                                        str_alias.rerun()
                                    except Exception as e:
                                        str_alias.error(f"Fehler: {e}")
                else:
                    str_alias.info("Keine Mitglieder vorhanden.")
            except Exception as e:
                str_alias.error(f"Fehler beim Laden: {e}")
        else:
            str_alias.subheader("Mein Profil bearbeiten")
            if current_user_id:
                try:
                    m_data = supabase.table("mitglieder").select("*").eq("id", current_user_id).single().execute().data
                    if m_data:
                        with str_alias.form("edit_eigenes_profil_form"):
                            str_alias.text_input("Mitgliedsnummer (gesperrt)", value=str(m_data.get("mitgliedsnummer", "")), disabled=True)
                            col1, col2 = str_alias.columns(2)
                            with col1:
                                e_vorname = str_alias.text_input("Vorname", value=m_data.get("vorname", ""))
                                e_nachname = str_alias.text_input("Nachname", value=m_data.get("nachname", ""))
                                g_str = m_data.get("geburtsdatum")
                                g_val = datetime.strptime(g_str.split("T")[0], "%Y-%m-%d") if g_str else datetime(1990, 1, 1)
                                e_geburtsdatum = datum_auswahl("Geburtsdatum", "profil_edit_geb", g_val, 1900)
                                akt_g = m_data.get("geschlecht", "männlich")
                                g_opt = ["männlich", "weiblich", "divers"]
                                e_geschlecht = str_alias.selectbox("Geschlecht", g_opt, index=g_opt.index(akt_g) if akt_g in g_opt else 0)
                                e_email = str_alias.text_input("E-Mail", value=m_data.get("email", "") or "")
                                e_telefon = str_alias.text_input("Telefonnummer", value=m_data.get("telefonnummer", "") or "")
                            with col2:
                                e_strasse = str_alias.text_input("Straße & Hausnummer", value=m_data.get("strasse", "") or "")
                                e_plz = str_alias.text_input("PLZ", value=m_data.get("plz", "") or "")
                                e_ort = str_alias.text_input("Ort", value=m_data.get("ort", "") or "")
                                
                            if str_alias.form_submit_button("Änderungen speichern", type="primary"):
                                update_daten = {
                                    "vorname": e_vorname, "nachname": e_nachname,
                                    "geburtsdatum": e_geburtsdatum.strftime("%Y-%m-%d"), "geschlecht": e_geschlecht,
                                    "email": e_email or None, "telefonnummer": e_telefon or None,
                                    "strasse": e_strasse or None, "plz": e_plz or None, "ort": e_ort or None
                                }
                                supabase.table("mitglieder").update(update_daten).eq("id", current_user_id).execute()
                                str_alias.success("Profil aktualisiert!")
                                str_alias.rerun()
                except Exception as e:
                    str_alias.error(f"Fehler: {e}")

    # ==========================================
    # 4. AUSWERTUNG & PDF EXPORT (Nur Admin/Vorstand)
    # ==========================================
    if is_admin_or_vorstand and tab_statistik is not None:
        with tab_statistik:
            str_alias.subheader("📊 Mitglieder-Auswertung & Berichte")
            try:
                daten = supabase.table("mitglieder").select("*").execute().data or []
                if daten:
                    df = pd.DataFrame(daten)
                    df["alter"] = df["geburtsdatum"].apply(berechne_alter)
                    df["altersgruppe"] = df["alter"].apply(get_altersgruppe)
                    
                    c1, c2 = str_alias.columns(2)
                    diag_typ = c1.radio("Diagramm-Typ", ["Balkendiagramm", "Kreisdiagramm"])
                    kategorie = c2.selectbox("Auswertung nach", ["Altersgruppen", "Geschlecht", "Status"])
                    
                    str_alias.divider()
                    if kategorie == "Altersgruppen":
                        counts = df["altersgruppe"].value_counts().reindex(["0-12 Jahre", "13-18 Jahre", "18-35 Jahre", "35-65 Jahre", "Über 65 Jahre", "Keine Angabe"], fill_value=0)
                        titel = "Altersverteilung"
                    elif kategorie == "Geschlecht":
                        counts = df["geschlecht"].value_counts(dropna=False).fillna("Keine Angabe")
                        titel = "Geschlechterverteilung"
                    else:
                        counts = df["status"].value_counts(dropna=False).fillna("Keine Angabe")
                        titel = "Statusverteilung"

                    fig, ax = plt.subplots(figsize=(8, 5))
                    if diag_typ == "Balkendiagramm":
                        counts.plot(kind="bar", ax=ax, color="#1f77b4", edgecolor="black")
                        plt.xticks(rotation=45, ha="right")
                    else:
                        counts.plot(kind="pie", ax=ax, autopct="%1.1f%%", startangle=90, cmap="Pastel1")
                        ax.set_ylabel("")
                    ax.set_title(titel)
                    str_alias.pyplot(fig)
                    
                    str_alias.divider()
                    str_alias.subheader("📄 PDF-Bericht Export")
                    
                    class PDF(FPDF):
                        def header(self):
                            self.set_font('helvetica', 'B', 15)
                            self.cell(0, 10, 'Mitgliederbericht', 0, 1, 'C')
                        def footer(self):
                            self.set_y(-15)
                            self.set_font('helvetica', 'I', 8)
                            self.cell(0, 10, f'Erstellt am {datetime.today().strftime("%d.%m.%Y")} - Seite {self.page_no()}', 0, 0, 'C')

                    def generate_pdf():
                        pdf = PDF()
                        pdf.add_page()
                        pdf.set_font('helvetica', 'B', 12)
                        pdf.cell(0, 10, f'Gesamtanzahl Mitglieder: {len(df)}', 0, 1)
                        pdf.ln(5)
                        pdf.cell(0, 10, 'Mitgliederliste:', 0, 1)
                        pdf.set_font('helvetica', 'B', 9)
                        pdf.cell(15, 8, 'Nr', 1)
                        pdf.cell(45, 8, 'Name', 1)
                        pdf.cell(30, 8, 'Status', 1)
                        pdf.cell(50, 8, 'E-Mail', 1)
                        pdf.cell(30, 8, 'Rolle', 1)
                        pdf.ln()
                        pdf.set_font('helvetica', '', 9)
                        for m in daten:
                            pdf.cell(15, 7, str(m.get("mitgliedsnummer", "")), 1)
                            pdf.cell(45, 7, f"{m.get('vorname', '')} {m.get('nachname', '')}"[:25], 1)
                            pdf.cell(30, 7, str(m.get("status", ""))[:15], 1)
                            pdf.cell(50, 7, str(m.get("email", "") or "")[:28], 1)
                            pdf.cell(30, 7, str(m.get("rolle", ""))[:15], 1)
                            pdf.ln()
                        return bytes(pdf.output())

                    str_alias.download_button("📥 PDF-Bericht herunterladen", generate_pdf(), f"Mitgliederbericht_{datetime.today().strftime('%Y-%m-%d')}.pdf", "application/pdf", type="primary")
                else:
                    str_alias.info("Keine Daten vorhanden.")
            except Exception as e:
                str_alias.error(f"Fehler: {e}")

    # ==========================================
    # 5. ABWESENHEITEN (Neu gemäß Supabase Schema)
    # ==========================================
    with tab_abw:
        str_alias.subheader("📅 Abwesenheiten & Urlaub")
        
        # Formular zum eintragen neuer Abwesenheiten
        with str_alias.form("abwesenheit_form"):
            str_alias.markdown("### Neue Abwesenheit eintragen")
            
            # Name des Mitglieds ermitteln
            ein_name = ""
            if current_user_id:
                try:
                    u_dat = supabase.table("mitglieder").select("vorname, nachname").eq("id", current_user_id).single().execute().data
                    if u_dat:
                        ein_name = f"{u_dat.get('vorname', '')} {u_dat.get('nachname', '')}".strip()
                except Exception:
                    pass
            
            if is_admin_or_vorstand:
                # Admins können für alle oder sich selbst eintragen
                try:
                    alle_m = supabase.table("mitglieder").select("id, vorname, nachname").execute().data or []
                    m_optionen = {f"{m.get('vorname')} {m.get('nachname')}": m.get('id') for m in alle_m}
                    gew_name = str_alias.selectbox("Mitglied auswählen", list(m_optionen.keys()))
                    final_user_id = m_optionen[gew_name] if gew_name else current_user_id
                    final_mitglied_name = gew_name
                except Exception:
                    final_user_id = current_user_id or "admin"
                    final_mitglied_name = ein_name or "Admin"
            else:
                final_user_id = current_user_id or "unbekannt"
                final_mitglied_name = ein_name or "Mitglied"
                str_alias.info(getragen_info := f"Eintrag für: **{final_mitglied_name}**")

            c1, c2 = str_alias.columns(2)
            with c1:
                von_datum = str_alias.date_input("Von Datum", value=datetime.today())
            with c2:
                bis_datum = str_alias.date_input("Bis Datum", value=datetime.today())
                
            uhrzeit_aktiv = str_alias.checkbox("Nur bestimmte Uhrzeiten (z. B. Teildienst / Stundenweise)")
            von_uhrzeit = None
            bis_uhrzeit = None
            
            if uhrzeit_aktiv:
                uc1, uc2 = str_alias.columns(2)
                with uc1:
                    von_uhrzeit = str_alias.time_input("Von Uhrzeit", value=time(8, 0))
                with uc2:
                    bis_uhrzeit = str_alias.time_input("Bis Uhrzeit", value=time(16, 0))
            
            grund = str_alias.selectbox("Grund / Art", ["Urlaub", "Krankheit", "Fortbildung / Lehrgang", "Dienstbefreiung", "Sonstiges"])
            
            if str_alias.form_submit_button("Abwesenheit speichern", type="primary"):
                if bis_datum < von_datum:
                    str_alias.error("Das Bis-Datum kann nicht vor dem Von-Datum liegen!")
                else:
                    payload = {
                        "user_id": str(final_user_id),
                        "mitglied_name": final_mitglied_name,
                        "von_datum": von_datum.strftime("%Y-%m-%d"),
                        "bis_datum": bis_datum.strftime("%Y-%m-%d"),
                        "von_uhrzeit": von_uhrzeit.strftime("%H:%M:%S") if von_uhrzeit else None,
                        "bis_uhrzeit": bis_uhrzeit.strftime("%H:%M:%S") if bis_uhrzeit else None,
                        "grund": grund
                    }
                    try:
                        supabase.table("abwesenheiten").insert(payload).execute()
                        str_alias.success("Abwesenheit erfolgreich eingetragen!")
                        str_alias.rerun()
                    except Exception as e:
                        str_alias.error(f"Fehler beim Speichern der Abwesenheit: {e}")

        str_alias.divider()
        str_alias.markdown("### 📋 Aktuelle & Kommende Abwesenheiten")
        
        try:
            abw_res = supabase.table("abwesenheiten").select("*").order("von_datum", desc=False).execute()
            abw_liste = abw_res.data if abw_res.data else []
            
            if abw_liste:
                # Formatierung für die Anzeige
                for a in abw_liste:
                    for d_feld in ["von_datum", "bis_datum"]:
                        if a.get(d_feld):
                            try:
                                a[d_feld] = datetime.strptime(str(a[d_feld]).split("T")[0], "%Y-%m-%d").strftime("%d.%m.%Y")
                            except Exception:
                                pass
                
                str_alias.dataframe(
                    abw_liste,
                    use_container_width=True,
                    column_config={
                        "id": "ID",
                        "user_id": "User-ID",
                        "mitglied_name": "Name",
                        "von_datum": "Von",
                        "bis_datum": "Bis",
                        "von_uhrzeit": "Von Uhrzeit",
                        "bis_uhrzeit": "Bis Uhrzeit",
                        "grund": "Grund",
                        "erstellt_am": "Erstellt am"
                    },
                    hide_index=True
                )
                
                # Lösch-Option für Einträge
                if is_admin_or_vorstand:
                    str_alias.markdown("#### Abwesenheit löschen")
                    loesch_dict = {f"{a.get('mitglied_name', 'Unbekannt')} ({a.get('von_datum')} bis {a.get('bis_datum')} - {a.get('grund')} )": a.get('id') for a in abw_liste}
                    zu_loeschen = str_alias.selectbox("Eintrag zum Löschen wählen", options=list(loesch_dict.keys()))
                    if str_alias.button("Ausgewählte Abwesenheit löschen", type="secondary"):
                        try:
                            target_id = loesch_dict[zu_loeschen]
                            supabase.table("abwesenheiten").delete().eq("id", target_id).execute()
                            str_alias.success("Abwesenheit gelöscht.")
                            str_alias.rerun()
                        except Exception as e:
                            str_alias.error(f"Fehler beim Löschen: {e}")
            else:
                str_alias.info("Aktuell sind keine Abwesenheiten eingetragen.")
        except Exception as e:
            str_alias.error(f"Fehler beim Laden der Abwesenheiten: {e}")