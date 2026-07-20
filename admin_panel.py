import customtkinter as ctk
from tkinter import messagebox
from modules.auth import update_user_role

class AdminManagementFrame(ctk.CTkFrame):
    def __init__(self, master, current_user_role):
        super().__init__(master)
        self.current_user_role = current_user_role
        
        # Überschrift
        ctk.CTkLabel(self, text="Mitglieder- & Rollenverwaltung", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Hier würden wir jetzt alle Mitglieder aus der DB laden
        # Beispielhaft: Eine ScrollableFrame für die Liste
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=600, height=400)
        self.scroll_frame.pack(pady=20, padx=20)
        
        self.load_members()

    def load_members(self):
        # 1. Mitglieder laden (Supabase Call)
        # res = supabase.table("mitglieder").select("*").execute()
        # 2. Für jedes Mitglied eine Zeile erstellen:
        # Beispiel: 
        self.add_member_row("Max Mustermann", "Mitglied-123", "mitglied")

    def add_member_row(self, name, mitgliedsnummer, aktuelle_rolle):
        row = ctk.CTkFrame(self.scroll_frame)
        row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row, text=name, width=150).pack(side="left", padx=10)
        
        # Rollen-Dropdown
        role_menu = ctk.CTkOptionMenu(row, values=["mitglied", "vorstand", "admin"])
        role_menu.set(aktuelle_rolle)
        role_menu.pack(side="left", padx=10)
        
        # Button zum Speichern
        ctk.CTkButton(row, text="Speichern", width=80, 
                      command=lambda: self.save_role(mitgliedsnummer, role_menu.get())).pack(side="left", padx=10)

    def save_role(self, mitgliedsnummer, neue_rolle):
        # Hier kommt der Berechtigungs-Check
        if self.current_user_role != "admin" and neue_rolle == "admin":
            messagebox.showerror("Fehler", "Nur Admins können Admin-Rechte vergeben!")
            return
            
        erfolg, msg = update_user_role(mitgliedsnummer, neue_rolle)
        if erfolg:
            messagebox.showinfo("Erfolg", msg)
        else:
            messagebox.showerror("Fehler", msg)