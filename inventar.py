import os
from datetime import datetime, timedelta
import customtkinter as ctk
from tkinter import messagebox, filedialog
from supabase import create_client
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pywhatkit
import time


# --- KONFIGURATION ---
SUPABASE_URL = "https://ythubjdnercyeyfedsam.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl0aHViamRuZXJjeWV5ZmVkc2FtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MjgzNTgsImV4cCI6MjA5OTEwNDM1OH0.loeU2abylobRmPJvuHwdZLbHNyTL4qlKOtIRk-qZp34"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
def gui_to_db(date_str):
    """Konvertiert Datums-Eingaben (mit . / oder -) zu YYYY-MM-DD für die DB."""
    if not date_str or date_str.strip() == "": 
        return None
    
    # Trennzeichen vereinheitlichen: Punkte und Bindestriche zu Schrägstrichen machen
    clean_date = date_str.strip().replace('.', '/').replace('-', '/')
    
    try:
        return datetime.strptime(clean_date, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        # Hier geben wir dem User einen Hinweis, was er eingegeben hat
        raise ValueError(f"Datum '{date_str}' ist ungültig. Bitte Format DD.MM.YYYY oder DD/MM/YYYY nutzen.")
# --- FENSTER: ERINNERUNGS-EINSTELLUNGEN ---
class ReminderSettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, refresh_callback, role):
        super().__init__(master)
        self.role = role.lower().strip()
        self.title("Erinnerungs-Intervalle")
        self.geometry("400x350")
        self.grab_set()
        # ... (Rest der Logik bleibt gleich, hier nur beispielhaft)

class ReminderPopup(ctk.CTkToplevel):
    def __init__(self, master, warnings):
        super().__init__(master)
        self.title("Wichtige Erinnerungen")
        self.geometry("500x500")
        self.attributes("-topmost", True) # Legt das Fenster in den Vordergrund
        self.grab_set()
        
        ctk.CTkLabel(self, text="⚠️ Anstehende Fristen", font=("Arial", 18, "bold"), text_color="orange").pack(pady=(15, 5))
        ctk.CTkLabel(self, text="Folgende Materialien benötigen Aufmerksamkeit:").pack(pady=(0, 10))
        
        # Scrollbarer Bereich für die Warnungen
        scroll_frame = ctk.CTkScrollableFrame(self, width=400, height=250)
        scroll_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        for warning in warnings:
            # Roter Text für überfällige Dinge, gelb/weiß für anstehende
            color = "red" if "ÜBERFÄLLIG" in warning else "white"
            ctk.CTkLabel(scroll_frame, text=warning, text_color=color, anchor="w", justify="left").pack(fill="x", pady=2)
            
        ctk.CTkButton(self, text="Verstanden", command=self.destroy).pack(pady=15)
def check_reminders(master_window, user_id):
    print("--- DEBUG START: check_reminders ---")
    try:
        # 1. Einstellungen laden
        settings_res = supabase.table("einstellungen").select("*").eq("id", 1).execute()
        if not settings_res.data:
            print("DEBUG: Keine Einstellungen in DB gefunden (ID=1).")
            return
        
        settings = settings_res.data[0]
        print(f"DEBUG: Einstellungen geladen. Popup aktiv: {settings.get('benachrichtigung_popup')}")
        
        # ... [Hier dein Code für E-Mail/Telefon ... bleibt gleich] ...
        
        # 4. Inventardaten laden
        inventar_res = supabase.table("inventar").select("*").execute() 
        if not inventar_res.data:
            print("DEBUG: Inventar ist leer.")
            return
        
        warnings = []
        heute = datetime.now().date()
        print(f"DEBUG: Prüfe {len(inventar_res.data)} Items auf Fälligkeit...")
        
        for item in inventar_res.data:
            name = item.get("name", "Unbekannt")
            
            # Prüfdatum
            datum_pruefung_str = item.get("pruefdatum")
            if datum_pruefung_str:
                try:
                    datum_pruefung = datetime.strptime(datum_pruefung_str, "%Y-%m-%d").date()
                    delta = (datum_pruefung - heute).days
                    print(f"DEBUG: {name} (Prüfung) -> Delta: {delta} Tage")
                    if 0 <= delta <= int(settings.get("tage_vor_pruefung", 0)):
                        warnings.append(f"⚠️ {name}: Prüfung in {delta} Tagen")
                    elif delta < 0:
                        warnings.append(f"❌ {name}: Prüfung ist {abs(delta)} Tage ÜBERFÄLLIG!")
                except: pass
            
            # Ablaufdatum
            datum_ablauf_str = item.get("ablaufdatum")
            if datum_ablauf_str:
                try:
                    datum_ablauf = datetime.strptime(datum_ablauf_str, "%Y-%m-%d").date()
                    delta = (datum_ablauf - heute).days
                    print(f"DEBUG: {name} (Ablauf) -> Delta: {delta} Tage")
                    if 0 <= delta <= int(settings.get("tage_vor_ablauf", 0)):
                        warnings.append(f"⚠️ {name}: Läuft in {delta} Tagen ab")
                    elif delta < 0:
                        warnings.append(f"❌ {name}: Ist seit {abs(delta)} Tagen ABGELAUFEN!")
                except: pass
                    
        # 5. Warnungen ausgeben
        print(f"DEBUG: Anzahl Warnungen gefunden: {len(warnings)}")
        if warnings:
            if settings.get("benachrichtigung_popup", False):
                print("DEBUG: Popup wird jetzt angezeigt.")
                ReminderPopup(master_window, warnings)
            else:
                print("DEBUG: Warnings gefunden, aber Popup in Einstellungen deaktiviert.")
        else:
            print("DEBUG: Keine fälligen Items gefunden.")
            
    except Exception as e:
        print(f"CRITICAL ERROR in check_reminders: {e}")
def send_warning_email(warnings, empfaenger_email):
    # --- DEINE SMTP KONFIGURATION ---
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    absender_email = "deine.system.mail@gmail.com"
    absender_passwort = "DEIN_APP_PASSWORT"

    # E-Mail aufbauen
    msg = MIMEMultipart()
    msg['From'] = absender_email
    msg['To'] = empfaenger_email  # <--- Hier wird nun die Mail des Mitglieds genutzt
    msg['Subject'] = "⚠️ Wichtige Inventar-Erinnerungen!"

    # Text formatieren
    body = "Hallo,\n\nfolgende Materialien benötigen Aufmerksamkeit:\n\n"
    for w in warnings:
        body += f"- {w}\n"
    body += "\nBitte im System überprüfen.\nDein Inventar-Manager"

    msg.attach(MIMEText(body, 'plain'))

    # E-Mail versenden
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(absender_email, absender_passwort)
        server.send_message(msg)
        server.quit()
        print(f"E-Mail-Benachrichtigung erfolgreich an {empfaenger_email} gesendet!")
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}")
def send_warning_whatsapp(warnings, telefonnummer):
    # Text formatieren (WhatsApp unterstützt * für Fettgedruckt)
    body = "⚠️ *Wichtige Inventar-Erinnerungen!*\n\n"
    for w in warnings:
        body += f"- {w}\n"
    body += "\nBitte im System überprüfen."

    # Deutsche Nummern müssen oft das Format +49 haben. 
    # Falls in der DB "0176..." steht, wandeln wir es um:
    if telefonnummer.startswith("0"):
        telefonnummer = "+49" + telefonnummer[1:]
    elif not telefonnummer.startswith("+"):
        telefonnummer = "+" + telefonnummer

    try:
        print(f"Starte WhatsApp-Versand an {telefonnummer}...")
        # sendwhatmsg_instantly(Nummer, Nachricht, Wartezeit_bis_laden, Tab_schliessen, Zeit_bis_schliessen)
        pywhatkit.sendwhatmsg_instantly(telefonnummer, body, 15, True, 3)
        print("WhatsApp-Benachrichtigung erfolgreich gesendet!")
    except Exception as e:
        print(f"Fehler beim WhatsApp-Versand: {e}")
# --- FENSTER: ALLGEMEINE EINSTELLUNGEN ---
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, role):
        super().__init__(master)
        self.role = role.lower().strip()
        self.title("Einstellungen")
        self.geometry("400x550")
        self.grab_set()
        
        ctk.CTkLabel(self, text="Erinnerungseinstellungen", font=("Arial", 16, "bold")).pack(pady=10)
        
        # 1. Bisherige Textfelder für die Tage
        self.entries = {}
        fields = [("Tage vor Prüfung warnen", "tage_vor_pruefung"), ("Tage vor Ablauf warnen", "tage_vor_ablauf")]
        for label_text, key in fields:
            ctk.CTkLabel(self, text=label_text).pack(anchor="w", padx=20)
            entry = ctk.CTkEntry(self)
            entry.pack(fill="x", padx=20, pady=5)
            self.entries[key] = entry
            
        # 2. NEU: Checkboxen für die Benachrichtigungsart
        ctk.CTkLabel(self, text="Benachrichtigungsweg:", font=("Arial", 14, "bold")).pack(pady=(20, 5), anchor="w", padx=20)
        
        # Variablen zum Speichern des Zustands (True/False)
        self.notify_vars = {
            "popup": ctk.BooleanVar(value=True),  # Standardmäßig an
            "email": ctk.BooleanVar(value=False),
            "whatsapp": ctk.BooleanVar(value=False)
        }
        
        # Checkboxen rendern
        ctk.CTkCheckBox(self, text="Popup (beim Programmstart)", variable=self.notify_vars["popup"]).pack(anchor="w", padx=40, pady=5)
        ctk.CTkCheckBox(self, text="E-Mail", variable=self.notify_vars["email"]).pack(anchor="w", padx=40, pady=5)
        ctk.CTkCheckBox(self, text="WhatsApp", variable=self.notify_vars["whatsapp"]).pack(anchor="w", padx=40, pady=5)
        
        ctk.CTkButton(self, text="Speichern", fg_color="green", command=self.save_settings).pack(pady=30)

        # 3. Vorhandene Daten laden, wenn das Fenster öffnet
        self.load_settings()

    def load_settings(self):
        try:
            # Lade die Einstellungen (Wir gehen davon aus, dass die globale Einstellung die ID 1 hat)
            response = supabase.table("einstellungen").select("*").eq("id", 1).execute()
            
            if response.data:
                data = response.data[0]
                
                # Textfelder befüllen
                if data.get("tage_vor_pruefung") is not None:
                    self.entries["tage_vor_pruefung"].insert(0, str(data["tage_vor_pruefung"]))
                if data.get("tage_vor_ablauf") is not None:
                    self.entries["tage_vor_ablauf"].insert(0, str(data["tage_vor_ablauf"]))
                
                # Checkboxen setzen (mit Fallback, falls in der DB noch Null steht)
                self.notify_vars["popup"].set(data.get("benachrichtigung_popup", True))
                self.notify_vars["email"].set(data.get("benachrichtigung_email", False))
                self.notify_vars["whatsapp"].set(data.get("benachrichtigung_whatsapp", False))
                
        except Exception as e:
            print(f"Fehler beim Laden der Einstellungen: {e}")

    def save_settings(self):
        # 1. Textfelder auslesen (falls das Feld leer gelassen wird, auf "0" setzen)
        tage_pruefung = self.entries["tage_vor_pruefung"].get() or "0"
        tage_ablauf = self.entries["tage_vor_ablauf"].get() or "0"
        
        # 2. Checkboxen auslesen (Ergibt True oder False)
        notify_popup = self.notify_vars["popup"].get()
        notify_email = self.notify_vars["email"].get()
        notify_whatsapp = self.notify_vars["whatsapp"].get()
        
        # DEBUG-Ausgabe zur Kontrolle in der Konsole
        print(f"Einstellungen speichern:")
        print(f"Tage Prüfung: {tage_pruefung}, Tage Ablauf: {tage_ablauf}")
        print(f"Wege -> Popup: {notify_popup}, Mail: {notify_email}, WhatsApp: {notify_whatsapp}")
        
        try:
            # 3. Update-Befehl an Supabase senden
            supabase.table("einstellungen").update({
                "tage_vor_pruefung": int(tage_pruefung),
                "tage_vor_ablauf": int(tage_ablauf),
                "benachrichtigung_popup": notify_popup,
                "benachrichtigung_email": notify_email,
                "benachrichtigung_whatsapp": notify_whatsapp
            }).eq("id", 1).execute()
            
            messagebox.showinfo("Gespeichert", "Die Einstellungen wurden erfolgreich übernommen!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Speicherfehler", f"Fehler beim Speichern in Supabase:\n{e}")
            print(f"Supabase Fehler: {e}")

# --- FENSTER: MATERIAL HINZUFÜGEN ---
class AddMaterialWindow(ctk.CTkToplevel):
    def __init__(self, master, refresh_callback, role):
        super().__init__(master)
        self.refresh_callback = refresh_callback
        self.title("Neues Material")
        self.geometry("400x550")
        self.grab_set()

        ctk.CTkLabel(self, text="Neues Material anlegen", font=("Arial", 18, "bold")).pack(pady=10)

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Name des Materials", width=250)
        self.name_entry.pack(pady=5)

        self.menge_entry = ctk.CTkEntry(self, placeholder_text="Gesamtmenge (Zahl)", width=250)
        self.menge_entry.pack(pady=5)
        
        self.lagerort_entry = ctk.CTkEntry(self, placeholder_text="Lagerort", width=250)
        self.lagerort_entry.pack(pady=5)

        self.anschaffung_entry = ctk.CTkEntry(self, placeholder_text="Anschaffungsdatum (DD/MM/YYYY)", width=250)
        self.anschaffung_entry.pack(pady=5)

        self.ablauf_entry = ctk.CTkEntry(self, placeholder_text="Ablaufdatum (DD/MM/YYYY)", width=250)
        self.ablauf_entry.pack(pady=5)

        self.pruef_entry = ctk.CTkEntry(self, placeholder_text="Prüfdatum (DD/MM/YYYY)", width=250)
        self.pruef_entry.pack(pady=5)

        ctk.CTkButton(self, text="Speichern", fg_color="green", command=self.save_material).pack(pady=20)

    def save_material(self):
        try:
            data = {
                "name": self.name_entry.get().strip(),
                "menge_gesamt": int(self.menge_entry.get().strip()),
                "menge_verfuegbar": int(self.menge_entry.get().strip()),
                "menge_defekt": 0,
                "lagerort": self.lagerort_entry.get().strip(),
                # HIER IST DER UNTERSTRICH WICHTIG:
                "anschaffungs_datum": gui_to_db(self.anschaffung_entry.get()),
                "ablaufdatum": gui_to_db(self.ablauf_entry.get()),
                "pruefdatum": gui_to_db(self.pruef_entry.get()),
                "status": "Verfügbar"
            }
            supabase.table("inventar").insert(data).execute()
            self.refresh_callback()
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Eingabefehler", "Fehler in den Daten (evtl. Format oder Menge): " + str(e))
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")

# --- FENSTER: MATERIAL BEARBEITEN ---
class EditMaterialWindow(ctk.CTkToplevel):
    def __init__(self, master, item, refresh_callback, role):
        super().__init__(master)
        self.item = item
        self.refresh_callback = refresh_callback
        self.title("Material bearbeiten")
        self.geometry("400x650")
        self.grab_set()

        ctk.CTkLabel(self, text=f"Bearbeite: {item['name']}", font=("Arial", 18, "bold")).pack(pady=10)

        # Name & Menge
        ctk.CTkLabel(self, text="Name:").pack(anchor="w", padx=20)
        self.name_entry = ctk.CTkEntry(self, width=350)
        self.name_entry.insert(0, item.get("name", ""))
        self.name_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Gesamtmenge:").pack(anchor="w", padx=20)
        self.menge_entry = ctk.CTkEntry(self, width=350)
        self.menge_entry.insert(0, str(item.get("menge_gesamt", "")))
        self.menge_entry.pack(pady=(0, 10), padx=20)
        
        ctk.CTkLabel(self, text="Lagerort:").pack(anchor="w", padx=20)
        self.lagerort_entry = ctk.CTkEntry(self, width=350)
        self.lagerort_entry.insert(0, item.get("lagerort", ""))
        self.lagerort_entry.pack(pady=(0, 10), padx=20)

        # Datum-Felder: WICHTIG - UNTERSTRICH BEI ANSCHAFFUNG
        ctk.CTkLabel(self, text="Anschaffungsdatum (DD/MM/YYYY):").pack(anchor="w", padx=20)
        self.anschaffung_entry = ctk.CTkEntry(self, width=350)
        # Hier korrigiert auf "anschaffungs_datum"
        self.anschaffung_entry.insert(0, item.get("anschaffungs_datum", "") or "") 
        self.anschaffung_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Ablaufdatum (DD/MM/YYYY):").pack(anchor="w", padx=20)
        self.ablauf_entry = ctk.CTkEntry(self, width=350)
        self.ablauf_entry.insert(0, item.get("ablaufdatum", "") or "")
        self.ablauf_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Prüfdatum (DD/MM/YYYY):").pack(anchor="w", padx=20)
        self.pruef_entry = ctk.CTkEntry(self, width=350)
        self.pruef_entry.insert(0, item.get("pruefdatum", "") or "")
        self.pruef_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkButton(self, text="Änderungen speichern", fg_color="blue", command=self.update_material).pack(pady=20)

    def update_material(self):
        try:
            neu_menge = int(self.menge_entry.get().strip())
            diff = neu_menge - self.item.get('menge_gesamt', 0)
            neu_verfuegbar = self.item.get('menge_verfuegbar', 0) + diff

            data = {
                "name": self.name_entry.get().strip(),
                "menge_gesamt": neu_menge,
                "menge_verfuegbar": max(0, neu_verfuegbar),
                "lagerort": self.lagerort_entry.get().strip(),
                # Auch hier "anschaffungs_datum"
                "anschaffungs_datum": gui_to_db(self.anschaffung_entry.get()),
                "ablaufdatum": gui_to_db(self.ablauf_entry.get()),
                "pruefdatum": gui_to_db(self.pruef_entry.get())
            }
            supabase.table("inventar").update(data).eq("id", self.item['id']).execute()
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Fehler", f"Update fehlgeschlagen: {e}")
# --- FENSTER: AUSLEIHE ---
class AddAusleiheWindow(ctk.CTkToplevel):
    def __init__(self, master, refresh_callback, role):
        super().__init__(master)
        self.refresh_callback = refresh_callback
        self.title("Neue Ausleihe")
        self.geometry("400x550")
        self.grab_set()

        ctk.CTkLabel(self, text="Material ausleihen", font=("Arial", 18, "bold")).pack(pady=10)

        # Material-Auswahl
        self.material_data = {}
        try:
            res = supabase.table("inventar").select("*").gt("menge_verfuegbar", 0).execute()
            for m in res.data:
                self.material_data[m['name']] = m
        except Exception:
            pass

        material_names = list(self.material_data.keys()) if self.material_data else ["Kein Material verfügbar"]
        
        ctk.CTkLabel(self, text="Material:").pack(anchor="w", padx=20)
        self.material_combo = ctk.CTkComboBox(self, values=material_names, width=350)
        self.material_combo.pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Ausleiher (Name):").pack(anchor="w", padx=20)
        self.person_entry = ctk.CTkEntry(self, width=350)
        self.person_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Menge:").pack(anchor="w", padx=20)
        self.menge_entry = ctk.CTkEntry(self, width=350)
        self.menge_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Ausgegeben von (Dein Name/Kürzel):").pack(anchor="w", padx=20)
        self.issuer_entry = ctk.CTkEntry(self, width=350)
        self.issuer_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkLabel(self, text="Soll-Rückgabe (DD/MM/YYYY):").pack(anchor="w", padx=20)
        self.datum_entry = ctk.CTkEntry(self, width=350)
        self.datum_entry.pack(pady=(0, 10), padx=20)

        ctk.CTkButton(self, text="Ausleihe bestätigen", fg_color="green", command=self.save_ausleihe).pack(pady=20)

    def save_ausleihe(self):
        mat_name = self.material_combo.get()
        person = self.person_entry.get().strip()
        menge_str = self.menge_entry.get().strip()
        issuer = self.issuer_entry.get().strip()
        
        # Datums-Konvertierung mit der Hilfsfunktion gui_to_db
        try:
            rueckgabe_datum = gui_to_db(self.datum_entry.get())
        except ValueError:
            messagebox.showerror("Fehler", "Datum muss im Format DD/MM/YYYY sein.")
            return

        if not person or not menge_str or not issuer or not rueckgabe_datum or mat_name not in self.material_data:
            messagebox.showwarning("Fehler", "Bitte alle Felder vollständig ausfüllen.")
            return

        try:
            menge = int(menge_str)
            material = self.material_data[mat_name]

            if menge > material['menge_verfuegbar']:
                messagebox.showwarning("Fehler", f"Nur noch {material['menge_verfuegbar']} verfügbar!")
                return

            # 1. Ausleihe eintragen
            ausleihe_data = {
                "inventar_id": material['id'],
                "person_name": person,
                "menge": menge,
                "rueckgabe_soll": rueckgabe_datum,
                "status": "Aktiv",
                "ausgegeben_von": issuer 
            }
            supabase.table("ausleihen").insert(ausleihe_data).execute()

            # 2. Materialbestand aktualisieren
            neue_menge = material['menge_verfuegbar'] - menge
            supabase.table("inventar").update({"menge_verfuegbar": neue_menge}).eq("id", material['id']).execute()

            self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler bei Ausleihe: {e}")
# --- FENSTER: RÜCKGABE ---

class ReturnAusleiheWindow(ctk.CTkToplevel):
    def __init__(self, master, ausleihe_item, refresh_callback, role):
        super().__init__(master)
        self.ausleihe_item = ausleihe_item
        self.refresh_callback = refresh_callback
        self.role = role
        
        self.title("Material Rückgabe")
        self.geometry("400x600") # Etwas vergrößert für den Platz der Labels
        self.grab_set()

        mat_name = ausleihe_item.get('inventar', {}).get('name', 'Unbekannt')
        gesamt_geliehen = ausleihe_item.get('menge', 0)

        # Überschriften
        ctk.CTkLabel(self, text=f"Rücknahme: {mat_name}", font=("Arial", 18, "bold")).pack(pady=10)
        ctk.CTkLabel(self, text=f"Insgesamt geliehen: {gesamt_geliehen}", font=("Arial", 12)).pack(pady=5)

        # 1. Mitarbeiter-Feld
        ctk.CTkLabel(self, text="Rücknahme durch (Mitarbeiter):", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10, 0))
        self.mitarbeiter_entry = ctk.CTkEntry(self, width=350)
        self.mitarbeiter_entry.pack(pady=5, padx=20)
        
        # 2. Rückgeber-Feld
        ctk.CTkLabel(self, text="Name des Rückgebers:", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10, 0))
        self.rueckgeber_entry = ctk.CTkEntry(self, width=350)
        self.rueckgeber_entry.insert(0, ausleihe_item.get('person_name', ''))
        self.rueckgeber_entry.pack(pady=5, padx=20)

        # 3. Intakt-Feld
        ctk.CTkLabel(self, text="Anzahl intakt zurückgegeben:", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10, 0))
        self.intakt_entry = ctk.CTkEntry(self, width=350)
        self.intakt_entry.insert(0, str(gesamt_geliehen))
        self.intakt_entry.pack(pady=5, padx=20)

        # 4. Defekt-Feld
        ctk.CTkLabel(self, text="Anzahl defekt zurückgegeben:", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10, 0))
        self.defekt_entry = ctk.CTkEntry(self, width=350)
        self.defekt_entry.insert(0, "0")
        self.defekt_entry.pack(pady=5, padx=20)

        # 5. Schaden-Feld
        ctk.CTkLabel(self, text="Schadensbericht (falls defekt):", font=("Arial", 11)).pack(anchor="w", padx=20, pady=(10, 0))
        self.schaden_entry = ctk.CTkEntry(self, width=350)
        self.schaden_entry.pack(pady=5, padx=20)

        ctk.CTkButton(self, text="Rücknahme bestätigen", fg_color="green", command=self.process_return).pack(pady=20)

    # Die Methode process_return bleibt unverändert wie in deinem Original-Code
    def process_return(self):
        try:
            intakt = int(self.intakt_entry.get() or 0)
            defekt = int(self.defekt_entry.get() or 0)
            if intakt + defekt != self.ausleihe_item['menge']:
                messagebox.showwarning("Fehler", f"Summe muss {self.ausleihe_item['menge']} ergeben.")
                return

            supabase.table("ausleihen").update({
                "status": "Abgeschlossen",
                "ruecknahme_durch": self.mitarbeiter_entry.get().strip(),
                "rueckgeber_name": self.rueckgeber_entry.get().strip(),
                "schadensbericht": self.schaden_entry.get().strip() if defekt > 0 else "Keine"
            }).eq("id", self.ausleihe_item['id']).execute()

            mat_id = self.ausleihe_item['inventar_id']
            mat_res = supabase.table("inventar").select("menge_verfuegbar, menge_defekt").eq("id", mat_id).execute()
            if mat_res.data:
                mat = mat_res.data[0]
                supabase.table("inventar").update({
                    "menge_verfuegbar": mat['menge_verfuegbar'] + intakt,
                    "menge_defekt": mat['menge_defekt'] + defekt
                }).eq("id", mat_id).execute()
            
            self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Fehler", f"Rückgabe fehlgeschlagen: {e}")

# --- HAUPTKLASSE INVENTORY CONTENT ---
class InventoryContent(ctk.CTkFrame):
    def __init__(self, master, role, user_id, hat_inventar_rechte=False, **kwargs):
        super().__init__(master, **kwargs)
        
        self.user_id = user_id
        self.hat_inventar_rechte = hat_inventar_rechte
        self.role = str(role).lower().strip() 
        self.role_level = {"admin": 3, "vorstand": 2, "mitglied": 1}.get(self.role, 0)
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.show_bestand()

        # Erinnerungen beim Start prüfen (nach 2 Sekunden, damit das Fenster geladen ist)
        
    def format_date_to_ui(self, date_str):
        """Wandelt DB-Format (YYYY-MM-DD) in (DD.MM.YYYY) um."""
        if not date_str or date_str == "-" or date_str == "":
            return "-"
        try:
            # Ersetzt / durch - falls nötig und parst das Datum
            return datetime.strptime(date_str.replace("/", "-"), "%Y-%m-%d").strftime("%d.%m.%Y")
        except:
            return date_str

    def has_permission(self, min_level, needs_special_rights=False):
        """Zentrale Rechteprüfung."""
        
        # 1. Absoluter Admin-Bypass: Wenn Admin, dann ist alles erlaubt.
        if self.role == "admin":
            return True
            
        # 2. Prüfe auf das Level, das in __init__ berechnet wurde.
        if self.role_level >= min_level:
            return True
            
        # 3. Prüfe auf spezielle Rechte.
        if needs_special_rights and self.hat_inventar_rechte:
            return True
            
        return False

    def clear_content(self):
        for widget in self.content_frame.winfo_children(): 
            widget.destroy()

    def zeige_seite(self, target):
        """Zentraler Router."""
        if target == "bestand": self.show_bestand()
        elif target == "ausleihe": self.show_ausleihe()
        elif target == "rueckgabe": self.show_rueckgabe()
        elif target == "rights" and self.has_permission(3): self.show_rechte()
        else: messagebox.showerror("Fehler", "Keine Berechtigung.")

    # --- PDF EXPORT ---
    def export_to_pdf(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Dateien", "*.pdf")],
            title="Inventarliste speichern unter..."
        )
        if not file_path: 
            return

        try:
            response = supabase.table("inventar").select("*").execute()
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, txt="Inventarliste", ln=True, align='C')
            pdf.set_font("Arial", size=9)
            pdf.ln(5)
            
            # Header
            pdf.cell(50, 10, "Name", border=1)
            pdf.cell(20, 10, "Verf.", border=1)
            pdf.cell(20, 10, "Defekt", border=1)
            pdf.cell(30, 10, "Ablaufdatum", border=1)
            pdf.cell(30, 10, "Pruefdatum", border=1)
            pdf.cell(40, 10, "Status", border=1, ln=True)

            # Zeilen befüllen
            for item in response.data:
                pdf.cell(50, 10, str(item.get("name", ""))[:25], border=1)
                pdf.cell(20, 10, str(item.get("menge_verfuegbar", 0)), border=1)
                pdf.cell(20, 10, str(item.get("menge_defekt", 0)), border=1)
                
                ablauf = item.get("ablaufdatum", "")
                pruefung = item.get("pruefdatum", "")
                pdf.cell(30, 10, str(ablauf) if ablauf else "-", border=1)
                pdf.cell(30, 10, str(pruefung) if pruefung else "-", border=1)
                
                pdf.cell(40, 10, str(item.get("status", "")), border=1, ln=True)

            pdf.output(file_path)
            if os.path.exists(file_path):
                try: 
                    os.startfile(file_path) 
                except: 
                    messagebox.showinfo("Gespeichert", f"Datei gespeichert unter:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Fehler", f"PDF Export fehlgeschlagen: {e}")

    # --- MATERIALBESTAND ANSICHT ---
    def show_bestand(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="Materialbestand", font=("Arial", 20, "bold")).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        if self.has_permission(2, needs_special_rights=True):
            ctk.CTkButton(btn_frame, text="+ Material", fg_color="green", width=120,
                          command=lambda: AddMaterialWindow(self, self.show_bestand, self.role)).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="PDF Export", fg_color="gray", width=120,
                      command=self.export_to_pdf).pack(side="left", padx=5)
        
        if self.has_permission(3):
            ctk.CTkButton(btn_frame, text="Einstellungen", fg_color="orange", width=120,
                          command=lambda: SettingsWindow(self, self.role)).pack(side="left", padx=5)
            
        self.scroll = ctk.CTkScrollableFrame(self.content_frame)
        self.scroll.pack(fill="both", expand=True, pady=10)
        self.load_inventory_data()

    def load_inventory_data(self):
        try:
            response = supabase.table("inventar").select("*").order("name").execute()
            for item in response.data:
                row = ctk.CTkFrame(self.scroll, fg_color="gray20")
                row.pack(fill="x", pady=2, padx=5)
                
                # Hier nutzen wir die neue Formatierungs-Funktion
                ablauf = self.format_date_to_ui(item.get('ablaufdatum'))
                pruef = self.format_date_to_ui(item.get('pruefdatum'))
                
                info = f"{item['name']} | Verfügbar: {item.get('menge_verfuegbar', 0)} | Defekt: {item.get('menge_defekt', 0)} | Ablauf: {ablauf} | Prüfung: {pruef}"
                ctk.CTkLabel(row, text=info, anchor="w").pack(side="left", padx=10, fill="x", expand=True)

                # Werkzeuge / Aktionen
                if self.has_permission(2, needs_special_rights=True):
                    if item.get('menge_defekt', 0) > 0:
                        ctk.CTkButton(row, text="Reparieren🔧", width=40, fg_color="orange", 
                                      command=lambda i=item: self.repair_item(i)).pack(side="right", padx=5)
                    ctk.CTkButton(row, text="Bearbeiten✏️", width=40, fg_color="blue", 
                                  command=lambda i=item: EditMaterialWindow(self, i, self.show_bestand, self.role)).pack(side="right", padx=5)
                    ctk.CTkButton(row, text="Löschen🗑️", width=40, fg_color="red", 
                                  command=lambda i=item: self.delete_item(i)).pack(side="right", padx=5)
        except Exception as e: 
            ctk.CTkLabel(self.scroll, text=f"Fehler: {e}").pack()

    def repair_item(self, item):
        """Setzt Defekte zurück und verschiebt Mengen wieder nach 'verfügbar'."""
        try:
            supabase.table("inventar").update({
                "menge_defekt": 0, 
                "menge_verfuegbar": item['menge_gesamt'], 
                "status": "Verfügbar"
            }).eq("id", item['id']).execute()
            self.show_bestand()
        except Exception as e: 
            messagebox.showerror("Fehler", str(e))

    def delete_item(self, item):
        if messagebox.askyesno("Löschen", f"Wirklich '{item['name']}' unwiderruflich aus dem Bestand löschen?"):
            try:
                supabase.table("inventar").delete().eq("id", item['id']).execute()
                self.show_bestand()
            except Exception as e:
                messagebox.showerror("Fehler", f"Löschen fehlgeschlagen: {e}")

    # --- AUSLEIHE ANSICHT ---
    def show_ausleihe(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="Aktive Ausleihen", font=("Arial", 20, "bold")).pack(pady=10)

        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(pady=10)

        if self.has_permission(2, needs_special_rights=True):
            # FIX: self.role hinzugefügt
            ctk.CTkButton(btn_frame, text="Neue Ausleihe", fg_color="green", width=150,
                          command=lambda: AddAusleiheWindow(self, self.show_ausleihe, self.role)).pack()
                          
        self.ausleih_scroll = ctk.CTkScrollableFrame(self.content_frame)
        self.ausleih_scroll.pack(fill="both", expand=True, pady=10)

        try:
            res = supabase.table("ausleihen").select("*, inventar(name)").eq("status", "Aktiv").execute()
            if not res.data:
                ctk.CTkLabel(self.ausleih_scroll, text="Aktuell ist nichts verliehen.", text_color="gray").pack(pady=20)
            
            for item in res.data:
                row = ctk.CTkFrame(self.ausleih_scroll, fg_color="gray20")
                row.pack(fill="x", pady=2, padx=5)
                
                try: 
                    soll_datum = datetime.strptime(item['rueckgabe_soll'], "%Y-%m-%d").strftime("%d.%m.%Y")
                except: 
                    soll_datum = item['rueckgabe_soll']

                mat_name = item['inventar']['name'] if item.get('inventar') else "Unbekannt"
                ausgeber = item.get('ausgegeben_von') or "Unbekannt"
                
                info = f"An: {item['person_name']} (von: {ausgeber}) | {item['menge']}x {mat_name} | Rückgabe: {soll_datum}"
                ctk.CTkLabel(row, text=info, anchor="w").pack(side="left", padx=10, fill="x", expand=True)
        except Exception as e:
            ctk.CTkLabel(self.ausleih_scroll, text=f"Fehler beim Laden der Ausleihen: {e}").pack()

    # --- RÜCKGABE ANSICHT ---
    def show_rueckgabe(self): 
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="Offene Ausleihen zur Rücknahme", font=("Arial", 20, "bold")).pack(pady=10)

        self.rueckgabe_scroll = ctk.CTkScrollableFrame(self.content_frame)
        self.rueckgabe_scroll.pack(fill="both", expand=True, pady=10)

        try:
            res = supabase.table("ausleihen").select("*, inventar(name)").eq("status", "Aktiv").execute()
            
            if not res.data:
                ctk.CTkLabel(self.rueckgabe_scroll, text="Keine offenen Ausleihen vorhanden.", text_color="gray").pack(pady=20)
            
            for item in res.data:
                row = ctk.CTkFrame(self.rueckgabe_scroll, fg_color="gray20")
                row.pack(fill="x", pady=2, padx=5)
                
                try: 
                    soll_datum = datetime.strptime(item['rueckgabe_soll'], "%Y-%m-%d").strftime("%d.%m.%Y")
                except: 
                    soll_datum = item['rueckgabe_soll']

                mat_name = item['inventar']['name'] if item.get('inventar') else "Unbekannt"
                ausgeber = item.get('ausgegeben_von') or "Unbekannt"
                
                info = f"Von: {item['person_name']} | {item['menge']}x {mat_name} (Ausgegeben von: {ausgeber}) | Soll-Rückgabe: {soll_datum}"
                ctk.CTkLabel(row, text=info, anchor="w").pack(side="left", padx=10, fill="x", expand=True)

                # Rücknahme-Button für berechtigte Personen
                if self.has_permission(2, needs_special_rights=True):
                    # FIX: 'i=item' sowie 'i' und 'self.role' hinzugefügt
                    ctk.CTkButton(row, text="↩️ Rücknahme", width=100, fg_color="green",
                                  command=lambda i=item: ReturnAusleiheWindow(self, i, self.show_rueckgabe, self.role)).pack(side="right", padx=5)
        except Exception as e:
            ctk.CTkLabel(self.rueckgabe_scroll, text=f"Fehler beim Laden der Rückgaben: {e}").pack()

    # --- INVENTAR-RECHTEVERWALTUNG (NUR FÜR ADMINS) ---
    def show_rechte(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="Sonderrechte Materialverwaltung", font=("Arial", 20, "bold")).pack(pady=10)
        ctk.CTkButton(self.content_frame, text="Aktualisieren", command=self.load_members).pack(pady=5)
        
        self.rights_scroll = ctk.CTkScrollableFrame(self.content_frame)
        self.rights_scroll.pack(fill="both", expand=True, pady=10)
        self.load_members()

    def load_members(self):
        for widget in self.rights_scroll.winfo_children(): 
            widget.destroy()
        try:
            response = supabase.table("mitglieder").select("*").order("nachname").execute()
            for user in response.data:
                # Admins müssen ihre eigenen Rechte nicht verwalten
                if user.get("role", "").lower() == "admin":
                    continue
                    
                row = ctk.CTkFrame(self.rights_scroll)
                row.pack(fill="x", pady=2, padx=5)
                
                ist = bool(user.get('hat_inventar_rechte', False))
                ctk.CTkLabel(row, text=f"{user['vorname']} {user['nachname']} ({user.get('role', 'Mitglied')})").pack(side="left", padx=10)
                
                ctk.CTkButton(row, text="Sperren" if ist else "Freischalten", 
                              fg_color="red" if ist else "green",
                              width=100,
                              command=lambda u=user['id'], s=not ist: self.toggle_material_access(u, s)).pack(side="right", padx=5)
        except Exception as e:
            ctk.CTkLabel(self.rights_scroll, text=f"Fehler beim Laden der Mitglieder: {e}").pack()

    def toggle_material_access(self, uid, status):
        """Aktiviert oder deaktiviert die `hat_inventar_rechte`-Flag in der DB."""
        try:
            supabase.table("mitglieder").update({"hat_inventar_rechte": status}).eq("id", uid).execute()
            self.load_members()
        except Exception as e:
            messagebox.showerror("Fehler", f"Rechte-Update fehlgeschlagen: {e}")
