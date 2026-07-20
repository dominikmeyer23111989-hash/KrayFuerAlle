import customtkinter as ctk
from tkinter import messagebox, filedialog
from supabase import create_client
from datetime import datetime
import smtplib
import os
import json
from email.message import EmailMessage
from fpdf import FPDF
import traceback

URL = "https://ythubjdnercyeyfedsam.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl0aHViamRuZXJjeWV5ZmVkc2FtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MjgzNTgsImV4cCI6MjA5OTEwNDM1OH0.loeU2abylobRmPJvuHwdZLbHNyTL4qlKOtIRk-qZp34"

supabase = create_client(URL, KEY)

class EmailComposer(ctk.CTkToplevel):
    def __init__(self, parent, termin, mitglieder):
        super().__init__(parent)
        self.parent = parent
        self.termin = termin
        self.mitglieder = mitglieder
        self.zusatz_anhaenge = []
        
        self.title(f"Einladungen versenden: {termin['titel']}")
        self.geometry("550x700")
        self.attributes("-topmost", True)
        
        # --- 1. Termin Details ---
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(info_frame, text=f"Termin: {termin['titel']}", font=("Arial", 18, "bold")).pack(pady=(10, 5))
        ctk.CTkLabel(info_frame, text=f"Datum: {termin['datum']} | Zeit: {termin.get('uhrzeit_von', '')} - {termin.get('uhrzeit_bis', '')} Uhr", font=("Arial", 14)).pack(pady=(0, 10))

        # --- 2. Empfänger Auswahl (Gruppiert) ---
        ctk.CTkLabel(self, text="Empfänger auswählen:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=350)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.checkboxes = {}
        
        # Mitglieder nach Rolle gruppieren
        gruppen = {}
        for m in self.mitglieder:
            rolle = m.get('rolle')
            if not rolle:
                rolle = "Mitglied"
            rolle = str(rolle).strip().capitalize()
            
            if rolle not in gruppen:
                gruppen[rolle] = []
            gruppen[rolle].append(m)
            
        # Checkboxen im UI erstellen
        for rolle in sorted(gruppen.keys()):
            ctk.CTkLabel(self.scroll_frame, text=f"--- {rolle} ---", font=("Arial", 12, "bold"), text_color="gray").pack(anchor="w", pady=(10, 2))
            
            for m in gruppen[rolle]:
                name = f"{m.get('vorname', '')} {m.get('nachname', '')}".strip()
                email = m.get('email', '')
                
                if email:
                    var = ctk.BooleanVar(value=True)
                    cb = ctk.CTkCheckBox(self.scroll_frame, text=f"{name} ({email})", variable=var)
                    cb.pack(anchor="w", padx=10, pady=2)
                    self.checkboxes[email] = var

        # --- 3. Anhänge hinzufügen ---
        attach_frame = ctk.CTkFrame(self, fg_color="transparent")
        attach_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_attach = ctk.CTkButton(attach_frame, text="📄 Tagesordnung / Datei anhängen", command=self.add_attachment)
        self.btn_attach.pack(side="left", padx=5)
        
        self.lbl_attachments = ctk.CTkLabel(attach_frame, text="Keine zusätzlichen Anhänge", text_color="gray")
        self.lbl_attachments.pack(side="left", padx=10)

        # --- 4. Senden Button ---
        self.btn_send = ctk.CTkButton(self, text="🚀 Ausgewählte Mails jetzt senden", fg_color="green", font=("Arial", 14, "bold"), height=40, command=self.send_mails)
        self.btn_send.pack(fill="x", padx=10, pady=20)

    # LÖSUNG 1: PDF Erstellung in den EmailComposer verschoben, wo sie hingehört!
    def create_pdf(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Vereinseinladung", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Termin: {self.termin['titel']}", ln=True)
        pdf.cell(200, 10, txt=f"Datum: {self.termin['datum']}", ln=True)
        pdf.cell(200, 10, txt=f"Zeit: {self.termin.get('uhrzeit_von', '')} - {self.termin.get('uhrzeit_bis', '')} Uhr", ln=True)
        
        filename = f"Termin_{self.termin['id']}.pdf"
        pdf.output(filename)
        return filename

    def add_attachment(self):
        dateien = filedialog.askopenfilenames(title="Anhänge auswählen", filetypes=[("PDF Dateien", "*.pdf"), ("Alle Dateien", "*.*")])
        if dateien:
            self.zusatz_anhaenge.extend(dateien)
            anzahl = len(self.zusatz_anhaenge)
            self.lbl_attachments.configure(text=f"{anzahl} Datei(en) angehängt", text_color="green")

    def send_mails(self):
        empfaenger_liste = [email for email, var in self.checkboxes.items() if var.get() == True]
        
        if not empfaenger_liste:
            messagebox.showwarning("Achtung", "Es wurde kein Empfänger ausgewählt.")
            return

        pdf_file = self.create_pdf() # Greift jetzt auf die eigene Funktion zu!

        absender_mail = "dein-verein@gmail.com"  # BITTE ANPASSEN
        absender_passwort = "hier-dein-app-passwort" # BITTE ANPASSEN
        
        self.btn_send.configure(text="Sende Mails... Bitte warten!", state="disabled")
        self.update()

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(absender_mail, absender_passwort)
                for email in empfaenger_liste:
                    msg = EmailMessage()
                    msg['Subject'] = f"Einladung: {self.termin['titel']}"
                    msg['From'] = absender_mail
                    msg['To'] = email
                    msg.set_content(f"Hallo,\n\nanbei erhältst du die Informationen sowie eventuelle Unterlagen zum anstehenden Termin '{self.termin['titel']}' am {self.termin['datum']}.\n\nMit freundlichen Grüßen,\nDein Vorstand")

                    with open(pdf_file, 'rb') as f:
                        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(pdf_file))
                        
                    for datei in self.zusatz_anhaenge:
                        with open(datei, 'rb') as f:
                            endung = datei.split('.')[-1].lower()
                            msg.add_attachment(f.read(), maintype='application', subtype=endung, filename=os.path.basename(datei))

                    smtp.send_message(msg)
                    
            messagebox.showinfo("Erfolg", f"Die Einladungen wurden erfolgreich an {len(empfaenger_liste)} Mitglieder versendet!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Fehler beim Senden", f"Es gab ein Problem beim Mailversand:\n{e}")
            self.btn_send.configure(text="🚀 Ausgewählte Mails jetzt senden", state="normal")


class TerminView(ctk.CTkFrame):
    def __init__(self, master, rolle, user_id):
        super().__init__(master)
        self.rolle = rolle
        self.user_id = user_id
        self.active_windows = [] 
        
        ctk.CTkLabel(self, text="Terminverwaltung", font=("Arial", 20, "bold")).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", pady=5)
        
        is_admin_vorstand = str(self.rolle).strip().lower() in ["admin", "vorstand"]
        
        if is_admin_vorstand:
            ctk.CTkButton(btn_frame, text="+ Neuer Termin", command=self.add_termin_form, fg_color="green").pack(side="left", padx=5)
            
        ctk.CTkButton(btn_frame, text="Teilnehmer-Übersicht", command=self.show_teilnahmen_uebersicht, fg_color="blue").pack(side="left", padx=5)
        
        if is_admin_vorstand:
            ctk.CTkButton(btn_frame, text="⚙️ Einstellungen", command=self.open_settings, fg_color="gray").pack(side="left", padx=5)
        
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.load_termine()
        self.check_reminders()

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"reminder_days": 3} 

    def save_settings(self, days):
        with open("settings.json", "w") as f:
            json.dump({"reminder_days": days}, f)
        messagebox.showinfo("Gespeichert", f"Du wirst nun {days} Tage vor einem Termin erinnert!")

    def open_settings(self):
        self.settings_win = ctk.CTkToplevel(self)
        self.settings_win.title("Einstellungen")
        self.settings_win.geometry("300x200")
        self.settings_win.attributes("-topmost", True)
        
        current_days = self.load_settings().get("reminder_days", 3)
        
        ctk.CTkLabel(self.settings_win, text="Erinnerung vor Termin (in Tagen):", font=("Arial", 14)).pack(pady=(30, 10))
        
        self.entry_days = ctk.CTkEntry(self.settings_win, width=100, justify="center")
        self.entry_days.insert(0, str(current_days))
        self.entry_days.pack(pady=5)
        
        ctk.CTkButton(self.settings_win, text="Speichern", fg_color="green", command=self.save_settings_ui).pack(pady=20)

    def save_settings_ui(self):
        try:
            days = int(self.entry_days.get())
            if days < 0:
                raise ValueError
            self.save_settings(days)
            self.settings_win.destroy()
        except ValueError:
            messagebox.showerror("Fehler", "Bitte eine gültige positive Zahl eingeben.")

    def check_reminders(self):
        is_admin_vorstand = str(self.rolle).strip().lower() in ["admin", "vorstand"]
        if not is_admin_vorstand:
            return

        today = datetime.now()
        termine_response = supabase.table("termine").select("*").execute()
        mitglieder_response = supabase.table("mitglieder").select("vorname, nachname, email, rolle").eq("status", "aktiv").execute()
        
        settings = self.load_settings()
        reminder_days = settings.get("reminder_days", 3)
        
        for t in termine_response.data:
            try:
                t_date = datetime.strptime(t['datum'], "%Y-%m-%d")
                if 0 <= (t_date - today).days <= reminder_days:
                    composer = EmailComposer(self, t, mitglieder_response.data)
                    self.active_windows.append(composer)
            except Exception as e:
                # LÖSUNG 3: Fehler sichtbar machen, statt sie zu verstecken!
                print(f"[DEBUG] check_reminders Datumsfehler bei Termin {t.get('titel', 'Unbekannt')}: {e}")

    def load_termine(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        response = supabase.table("termine").select("*").order("datum").execute()
        termine = response.data
        is_admin_vorstand = str(self.rolle).strip().lower() in ["admin", "vorstand"]

        for t in termine:
            if t.get('sichtbarkeit') == 'vorstand' and not is_admin_vorstand:
                continue 

            frame = ctk.CTkFrame(self.scroll_frame)
            frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(frame, text=f"{t['datum']} | {t['titel']}", font=("Arial", 14)).pack(side="left", padx=10)
            
            status_frame = ctk.CTkFrame(frame, fg_color="transparent")
            status_frame.pack(side="right", padx=5)

            if is_admin_vorstand:
                ctk.CTkButton(status_frame, text="✏️", width=30, fg_color="orange", 
                              command=lambda t=t: self.edit_termin_form(t)).pack(side="left", padx=2)
                ctk.CTkButton(status_frame, text="🗑️", width=30, fg_color="red", 
                              command=lambda tid=t['id']: self.delete_termin(tid)).pack(side="left", padx=2)

            for status in ["kann", "kann nicht", "unsicher"]:
                ctk.CTkButton(status_frame, text=status, width=60, 
                              command=lambda s=status, tid=t['id']: self.set_status(tid, s)).pack(side="left", padx=2)

    def set_status(self, termin_id, status):
        target_user_id = self.user_id
        if self.rolle == "admin" and target_user_id is None:
            target_user_id = 7
            
        if target_user_id is None:
            messagebox.showerror("Fehler", "Keine gültige Benutzer-ID gefunden.")
            return

        try:
            tid = int(termin_id)
            uid = int(target_user_id)
            
            supabase.table("teilnahmen").delete().eq("termin_id", tid).eq("user_id", uid).execute()
            supabase.table("teilnahmen").insert({"termin_id": tid, "user_id": uid, "status": status}).execute()
            
            self.load_termine()
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Datenbank-Fehler: {e}")
            print(f"[DEBUG] Fehlerdetails: {e}")

    def show_teilnahmen_uebersicht(self):
        self.teilnahmen_win = ctk.CTkToplevel(self)
        self.teilnahmen_win.title("Teilnehmer-Übersicht")
        self.teilnahmen_win.geometry("500x500")
        self.teilnahmen_win.attributes("-topmost", True)
        
        res = supabase.table("teilnahmen").select("*, termine(titel, sichtbarkeit)").execute()
        mitglieder_res = supabase.table("mitglieder").select("*").execute()
        
        user_dict = {}
        for m in mitglieder_res.data:
            uid = str(m.get('user_id') or m.get('id', ''))
            user_dict[uid] = f"{m.get('vorname', '')} {m.get('nachname', '')}".strip()
            
        scroll = ctk.CTkScrollableFrame(self.teilnahmen_win)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        is_admin_vorstand = str(self.rolle).strip().lower() in ["admin", "vorstand"]
        
        termine_gruppiert = {}
        for item in res.data:
            termin_info = item.get('termine')
            if not termin_info:
                continue
                
            titel = termin_info.get('titel', 'Unbekannt')
            sichtbarkeit = termin_info.get('sichtbarkeit', 'alle')
            
            if sichtbarkeit == 'vorstand' and not is_admin_vorstand:
                continue
                
            if titel not in termine_gruppiert:
                termine_gruppiert[titel] = []
                
            user_id = str(item.get('user_id', ''))
            name = user_dict.get(user_id, "Unbekanntes Mitglied")
            status = item.get('status', 'unbekannt')
            
            termine_gruppiert[titel].append({"name": name, "status": status})

        for titel, teilnehmer_liste in termine_gruppiert.items():
            ctk.CTkLabel(scroll, text=f"📌 {titel}", font=("Arial", 16, "bold")).pack(anchor="w", pady=(15, 5))
            
            for t in teilnehmer_liste:
                status = t['status'].lower()
                if "kann nicht" in status:
                    farbe = "#ff6666" 
                elif "unsicher" in status:
                    farbe = "#ffcc00" 
                else:
                    farbe = "#66cc66" 
                    
                ctk.CTkLabel(scroll, text=f"   • {t['name']}: {t['status'].capitalize()}", text_color=farbe, font=("Arial", 13)).pack(anchor="w", padx=10)

    def add_termin_form(self):
        self.dialog = ctk.CTkToplevel(self)
        self.dialog.title("Neuer Termin")
        self.dialog.geometry("350x450")
        self.dialog.attributes("-topmost", True)

        ctk.CTkLabel(self.dialog, text="Titel:").pack(pady=(10, 0))
        self.entry_titel = ctk.CTkEntry(self.dialog, width=250)
        self.entry_titel.pack(pady=5)
        
        ctk.CTkLabel(self.dialog, text="Datum (TT.MM.JJJJ):").pack(pady=(10, 0))
        self.entry_datum = ctk.CTkEntry(self.dialog, width=250)
        self.entry_datum.pack(pady=5)

        ctk.CTkLabel(self.dialog, text="Uhrzeit von (z.B. 18:00):").pack(pady=(10, 0))
        self.entry_von = ctk.CTkEntry(self.dialog, width=250)
        self.entry_von.pack(pady=5)

        ctk.CTkLabel(self.dialog, text="Uhrzeit bis (z.B. 20:00):").pack(pady=(10, 0))
        self.entry_bis = ctk.CTkEntry(self.dialog, width=250)
        self.entry_bis.pack(pady=5)

        ctk.CTkLabel(self.dialog, text="Sichtbarkeit:").pack(pady=(10, 0))
        self.opt_sicht = ctk.CTkOptionMenu(self.dialog, values=["Alle", "Nur Vorstand"], width=250)
        self.opt_sicht.pack(pady=5)
        
        ctk.CTkButton(self.dialog, text="Speichern", fg_color="green", command=self.save_termin).pack(pady=20)

    def save_termin(self):
        raw_datum = self.entry_datum.get()
        try:
            parts = raw_datum.split('.')
            if len(parts) != 3:
                raise ValueError("Falsches Format")
            formatted_datum = f"{parts[2]}-{parts[1]}-{parts[0]}"
        except:
            messagebox.showerror("Fehler", "Bitte das Datum im Format TT.MM.JJJJ eingeben")
            return

        val_sicht = "vorstand" if self.opt_sicht.get() == "Nur Vorstand" else "alle"
        
        data = {
            "titel": self.entry_titel.get(),
            "datum": formatted_datum,
            "uhrzeit_von": self.entry_von.get(),
            "uhrzeit_bis": self.entry_bis.get(),
            "sichtbarkeit": val_sicht
        }
        
        try:
            supabase.table("termine").insert(data).execute()
            self.dialog.destroy()
            self.load_termine()
            messagebox.showinfo("Erfolg", "Termin wurde gespeichert!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Datenbank-Fehler: {e}")

    def delete_termin(self, termin_id):
        if messagebox.askyesno("Löschen?", "Willst du diesen Termin wirklich unwiderruflich löschen?"):
            try:
                supabase.table("teilnahmen").delete().eq("termin_id", termin_id).execute()
                supabase.table("termine").delete().eq("id", termin_id).execute()
                
                self.load_termine()
                messagebox.showinfo("Erfolg", "Termin wurde gelöscht.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Löschen: {e}")

    def edit_termin_form(self, termin):
        self.edit_dialog = ctk.CTkToplevel(self)
        self.edit_dialog.title(f"Bearbeiten: {termin['titel']}")
        self.edit_dialog.geometry("350x450")
        self.edit_dialog.attributes("-topmost", True)

        ctk.CTkLabel(self.edit_dialog, text="Titel:").pack(pady=(10, 0))
        self.e_titel = ctk.CTkEntry(self.edit_dialog, width=250)
        self.e_titel.insert(0, termin['titel'])
        self.e_titel.pack(pady=5)
        
        y, m, d = termin['datum'].split('-')
        datum_str = f"{d}.{m}.{y}"
        
        ctk.CTkLabel(self.edit_dialog, text="Datum (TT.MM.JJJJ):").pack(pady=(10, 0))
        self.e_datum = ctk.CTkEntry(self.edit_dialog, width=250)
        self.e_datum.insert(0, datum_str)
        self.e_datum.pack(pady=5)

        ctk.CTkLabel(self.edit_dialog, text="Uhrzeit von:").pack(pady=(10, 0))
        self.e_von = ctk.CTkEntry(self.edit_dialog, width=250)
        self.e_von.insert(0, termin.get('uhrzeit_von', ''))
        self.e_von.pack(pady=5)

        ctk.CTkLabel(self.edit_dialog, text="Uhrzeit bis:").pack(pady=(10, 0))
        self.e_bis = ctk.CTkEntry(self.edit_dialog, width=250)
        self.e_bis.insert(0, termin.get('uhrzeit_bis', ''))
        self.e_bis.pack(pady=5)
        
        ctk.CTkButton(self.edit_dialog, text="Speichern", fg_color="green", 
                      command=lambda: self.update_termin(termin['id'])).pack(pady=20)

    def update_termin(self, termin_id):
        raw_datum = self.e_datum.get()
        try:
            parts = raw_datum.split('.')
            formatted_datum = f"{parts[2]}-{parts[1]}-{parts[0]}"
        except:
            messagebox.showerror("Fehler", "Datumsformat muss TT.MM.JJJJ sein!")
            return

        data = {
            "titel": self.e_titel.get(),
            "datum": formatted_datum,
            "uhrzeit_von": self.e_von.get(),
            "uhrzeit_bis": self.e_bis.get()
        }
        
        try:
            supabase.table("termine").update(data).eq("id", termin_id).execute()
            self.edit_dialog.destroy()
            self.load_termine()
            messagebox.showinfo("Erfolg", "Termin wurde aktualisiert!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")

# --------- OUTSIDE THE CLASS ---------

def run_startup_reminders(parent, rolle, user_id):
    is_admin_vorstand = str(rolle).strip().lower() in ["admin", "vorstand"]
    if not is_admin_vorstand:
        return []

    today = datetime.now()
    active_composers = [] # LÖSUNG 2: Fenster in Liste speichern, damit sie nicht verschwinden
    
    try:
        termine_response = supabase.table("termine").select("*").execute()
        mitglieder_response = supabase.table("mitglieder").select("vorname, nachname, email, rolle").eq("status", "aktiv").execute()
        
        settings = {"reminder_days": 3}
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
        reminder_days = settings.get("reminder_days", 3)
        
        for t in termine_response.data:
            try:
                t_date = datetime.strptime(t['datum'], "%Y-%m-%d")
                if 0 <= (t_date - today).days <= reminder_days:
                    composer = EmailComposer(parent, t, mitglieder_response.data)
                    active_composers.append(composer)
            except Exception as e: 
                print(f"[DEBUG] Datum parsing fehler bei Start: {e}")
                
        return active_composers # Wichtig: Die Liste zurückgeben
        
    except Exception as e:
        print(f"[DEBUG] Fehler beim Start-Check: {e}")
        traceback.print_exc()
        return []