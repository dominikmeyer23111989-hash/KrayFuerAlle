import customtkinter as ctk
from tkinter import messagebox
from modules.auth import (
    login_user, 
    finde_email_zu_benutzer, 
    passwort_zuruecksetzen, 
    passwort_zuruecksetzen_mit_sicherheitsfrage,
    erstes_passwort_setzen  # Deine eigene Funktion für die Account-Erstellung!
)
from database import supabase
from termine import run_startup_reminders


class RegisterWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Konto aktivieren")
        self.geometry("350x450")
        
        # Fenster im Vordergrund halten
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text="Account aktivieren", font=("Arial", 16, "bold")).pack(pady=20)
        
        self.entry_ident = ctk.CTkEntry(self, placeholder_text="Mitglieds-Nr, E-Mail oder Tel")
        self.entry_ident.pack(pady=10)
        
        self.entry_pw = ctk.CTkEntry(self, placeholder_text="Neues Passwort", show="*")
        self.entry_pw.pack(pady=10)

        self.entry_frage = ctk.CTkEntry(self, placeholder_text="Sicherheitsfrage (z.B. Haustier?)", width=250)
        self.entry_frage.pack(pady=10)
        
        self.entry_antwort = ctk.CTkEntry(self, placeholder_text="Antwort zur Sicherheitsfrage", width=250)
        self.entry_antwort.pack(pady=10)

        ctk.CTkButton(self, text="Konto freischalten", command=self.do_register).pack(pady=20)

    def do_register(self):
        ident = self.entry_ident.get().strip()
        pw = self.entry_pw.get().strip()
        frage = self.entry_frage.get().strip()
        antwort = self.entry_antwort.get().strip()

        if not all([ident, pw, frage, antwort]):
            messagebox.showerror("Fehler", "Bitte fülle alle Felder aus!")
            return

        # 1. Supabase Auth Account & Benutzer-Eintrag über deine auth.py erstellen
        erfolg, msg = erstes_passwort_setzen(ident, pw)
        
        if erfolg:
            # 2. Wenn das geklappt hat, updaten wir noch die Sicherheitsfrage in 'mitglieder'
            try:
                query = f"email.eq.{ident},telefonnummer.eq.{ident},mitgliedsnummer.eq.{ident}"
                supabase.table("mitglieder").update({
                    "sicherheitsfrage": frage,
                    "sicherheitsantwort": antwort
                }).or_(query).execute()
                
                messagebox.showinfo("Erfolg", msg) # msg ist hier "Account erfolgreich aktiviert!..."
                self.destroy()
            except Exception as e:
                messagebox.showwarning("Teilerfolg", f"Account wurde erstellt, aber Sicherheitsfrage konnte nicht gespeichert werden.\nFehler: {e}")
                self.destroy()
        else:
            # Zeigt die Fehlermeldung aus deiner auth.py an
            messagebox.showerror("Fehler", msg)


class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("KrayFürAlle e.V. Login")
        self.geometry("300x400") 
        
        ctk.CTkLabel(self, text="Vereins-Login", font=("Arial", 16, "bold")).pack(pady=20)

        self.entry_user = ctk.CTkEntry(self, placeholder_text="User/Tel/Mail")
        self.entry_user.pack(pady=10)
        
        self.entry_pass = ctk.CTkEntry(self, placeholder_text="Passwort", show="*")
        self.entry_pass.pack(pady=10)
        
        ctk.CTkButton(self, text="Anmelden", command=self.do_login).pack(pady=10)
        
        ctk.CTkButton(self, text="Passwort vergessen?", 
                      command=self.dialog_passwort_vergessen, 
                      fg_color="transparent", 
                      text_color="gray").pack(pady=(5, 0))
                      
        # BUTTON FÜR DIE AKTIVIERUNG
        ctk.CTkButton(self, text="Erster Login? Konto aktivieren", 
                      command=self.open_register, 
                      fg_color="transparent", 
                      text_color="#1f538d").pack(pady=(0, 5))

    def do_login(self):
        user_val = self.entry_user.get()
        pw_val = self.entry_pass.get()
        result = login_user(user_val, pw_val)
        
        if result["success"]:
            email = finde_email_zu_benutzer(user_val)
            try:
                # 1. Spalte 'hat_inventar_rechte' zum SELECT hinzufügen
                data = supabase.table("mitglieder").select("id, vorname, rolle, hat_inventar_rechte").eq("email", email).single().execute()
                user_data = data.data
                print(f"DEBUG: Datenbank sagt für User {email}: Rolle ist '{user_data.get('rolle')}'")
                
                # 2. Werte extrahieren
                user_id = user_data.get("id")
                vorname = user_data.get("vorname", "Mitglied")
                rolle = user_data.get("rolle", "mitglied")
                # 3. Den booleschen Wert holen (Default False, falls das Feld leer ist)
                hat_inventar_rechte = user_data.get("hat_inventar_rechte", False) 

            except Exception as e:
                print("Fehler beim Laden der User-Daten im Login:", e)
                user_id = None
                vorname = "Mitglied"
                rolle = "mitglied"
                hat_inventar_rechte = False # Fallback bei Fehler
            
            self.withdraw()
            
            from main_dashboard import MainDashboard
            
            # 4. Übergabe der neuen Variable an das Dashboard
            dashboard = MainDashboard(
                vorname=vorname, 
                role=rolle, 
                user_id=user_id, 
                hat_inventar_rechte=hat_inventar_rechte
            ) 
            run_startup_reminders(dashboard, rolle, user_id)
            dashboard.mainloop()
            self.destroy()
        else:
            messagebox.showerror("Fehler", result["message"])

    def open_register(self):
        RegisterWindow(self)

    def dialog_passwort_vergessen(self):
        ident = ctk.CTkInputDialog(text="Bitte E-Mail, Tel oder Mitgliedsnummer eingeben:", title="Passwort Reset").get_input()
        if not ident: return
        
        ident = ident.strip()
        
        try:
            # Zuerst holen wir nur die Frage aus der Datenbank, um sie dem User anzuzeigen
            res = supabase.table("mitglieder").select("sicherheitsfrage").or_(f"email.eq.{ident},telefonnummer.eq.{ident},mitgliedsnummer.eq.{ident}").execute()
            
            if res.data and len(res.data) > 0:
                frage = res.data[0].get("sicherheitsfrage")
                
                if not frage:
                    messagebox.showerror("Fehler", "Für diesen Benutzer ist keine Sicherheitsfrage hinterlegt.")
                    return

                # Wir fragen nach der Antwort und dem neuen Passwort
                antwort = ctk.CTkInputDialog(text=f"Frage: {frage}\nAntwort:", title="Sicherheitsfrage").get_input()
                if not antwort: return
                
                neues_pw = ctk.CTkInputDialog(text="Neues Passwort:", title="Neues Passwort").get_input()
                if not neues_pw: return
                
                # Wir übergeben die Daten an deine auth.py Funktion
                erfolg, msg = passwort_zuruecksetzen_mit_sicherheitsfrage(ident, antwort, neues_pw)
                
                if erfolg: 
                    messagebox.showinfo("Erfolg", msg)
                else: 
                    messagebox.showerror("Fehler", msg)
            
            else:
                messagebox.showerror("Fehler", "Benutzer nicht gefunden. Bitte Eingabe prüfen.")

        except Exception as e:
            messagebox.showerror("Fehler", f"Technischer Fehler: {e}")

if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()