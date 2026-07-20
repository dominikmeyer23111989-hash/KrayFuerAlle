import customtkinter as ctk
from datetime import datetime, timedelta
from database import supabase 

# --- HILFSFUNKTIONEN FÜR DAS DATUM ---
def to_db_date(date_str):
    """Wandelt verschiedene Datumsformate (Eingabe) in YYYY-MM-DD (Datenbank) um."""
    if not date_str or date_str.strip() == "":
        return None  # Leeres Feld abfangen
        
    date_str = date_str.strip()
    
    erlaubte_formate = [
        "%d/%m/%Y",  # 19/07/2026 
        "%d.%m.%Y",  # 19.07.2026 
        "%Y-%m-%d",  # 2026-07-19 
        "%d-%m-%Y"   # 19-07-2026 
    ]
    
    for fmt in erlaubte_formate:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    return None

def to_view_date(date_str):
    """Wandelt YYYY-MM-DD (Datenbank) in TT/MM/JJJJ (Anzeige) um."""
    if not date_str: return ""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return date_str

class TodoView(ctk.CTkFrame):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id
        self.members_data = [] 
        
        # Toggle Menü Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(btn_frame, text="Neues To-Do", command=self.show_new).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Status & Liste", command=self.show_status).pack(side="left", padx=5)
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        self.show_status()

    # --- Mitglieder laden ---
    def get_members_from_db(self):
        response = supabase.table("mitglieder").select("id, vorname, nachname").execute()
        self.members_data = response.data
        
        for m in self.members_data:
            v = m.get('vorname') or ""
            n = m.get('nachname') or ""
            m['name'] = f"{v} {n}".strip() 
            
        return [m['name'] for m in self.members_data]

    # ==========================================
    # NEUES TO-DO ERSTELLEN
    # ==========================================
    def show_new(self):
        self.clear_container()
        ctk.CTkLabel(self.container, text="Neues To-Do erstellen", font=("Arial", 16, "bold")).pack(pady=10)
        
        self.entry_titel = ctk.CTkEntry(self.container, placeholder_text="Titel")
        self.entry_titel.pack(pady=5, padx=20, fill="x")
        
        self.entry_desc = ctk.CTkEntry(self.container, placeholder_text="Beschreibung")
        self.entry_desc.pack(pady=5, padx=20, fill="x")
        
        self.entry_deadline = ctk.CTkEntry(self.container, placeholder_text="Deadline (TT/MM/JJJJ)")
        self.entry_deadline.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(self.container, text="Zuweisen an (Mehrfachauswahl möglich):").pack(pady=(10, 0))
        self.member_scroll = ctk.CTkScrollableFrame(self.container, height=120)
        self.member_scroll.pack(pady=5, padx=20, fill="x")
        
        self.checkbox_vars = {} 
        self.get_members_from_db() 
        
        for member in self.members_data:
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(self.member_scroll, text=member['name'], variable=var)
            chk.pack(anchor="w", pady=2, padx=5)
            self.checkbox_vars[member['id']] = var

        ctk.CTkButton(self.container, text="Speichern", command=self.save_todo).pack(pady=20)

    def save_todo(self):
        titel = self.entry_titel.get()
        desc = self.entry_desc.get()
        raw_date = self.entry_deadline.get()
        
        deadline = to_db_date(raw_date)
        if not deadline:
            print("Fehler: Bitte das Datum im Format TT/MM/JJJJ eingeben!")
            return
            
        selected_ids = [m_id for m_id, var in self.checkbox_vars.items() if var.get()]
        
        if titel and selected_ids:
            for m_id in selected_ids:
                data = {
                    "titel": titel, 
                    "beschreibung": desc, 
                    "deadline": deadline,
                    "zugewiesen_an": m_id,
                    "erstellt_von": self.user_id, 
                    "status": "Offen"
                }
                supabase.table("todo").insert(data).execute()
                
            self.show_status()
        else:
            print("Fehler: Bitte Titel eingeben und mindestens ein Mitglied auswählen!")

    # ==========================================
    # TO-DO LISTE & BEARBEITEN
    # ==========================================
    def show_status(self):
        self.clear_container()
        self.cleanup_todos()
        self.scroll = ctk.CTkScrollableFrame(self.container)
        self.scroll.pack(fill="both", expand=True)
        self.load_todos()

    def load_todos(self):
        data = supabase.table("todo").select("*").execute()
        
        if not self.members_data:
            self.get_members_from_db()
        member_dict = {m['id']: m['name'] for m in self.members_data}
        
        for item in data.data:
            card = ctk.CTkFrame(self.scroll)
            card.pack(fill="x", pady=5, padx=5)
            
            display_date = to_view_date(item.get('deadline', ''))
            assigned_name = member_dict.get(item.get('zugewiesen_an'), "Unbekannt")
            
            # Text-Container (Links) für 2 Zeilen Text
            text_frame = ctk.CTkFrame(card, fg_color="transparent")
            text_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
            
            # 1. Zeile: Wichtige Infos (Fett)
            info_text = f"{item['titel']} | Status: {item['status']} | Bis: {display_date} | @{assigned_name}"
            ctk.CTkLabel(text_frame, text=info_text, font=("Arial", 14, "bold"), anchor="w").pack(fill="x")
            
            # 2. Zeile: Beschreibung (Grau)
            beschreibung = item.get('beschreibung', '')
            if beschreibung:
                ctk.CTkLabel(text_frame, text=beschreibung, text_color="gray", anchor="w").pack(fill="x")
            
            # Button (Rechts)
            ctk.CTkButton(card, text="Optionen", width=80, 
                          command=lambda i=item: self.open_popup(i)).pack(side="right", padx=10)

    def open_popup(self, item):
        popup = ctk.CTkToplevel(self)
        popup.title("Bearbeiten")
        
        # Fenster etwas höher, um Platz für die Beschreibung zu machen
        popup.geometry("350x300") 
        popup.transient(self.winfo_toplevel()) 
        popup.grab_set() 
        popup.focus_force() 
        
        # Titel der Aufgabe
        ctk.CTkLabel(popup, text=f"{item['titel']}", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        
        # Beschreibung im Popup anzeigen
        beschreibung = item.get('beschreibung', '')
        if beschreibung:
            ctk.CTkLabel(popup, text=beschreibung, text_color="gray", wraplength=300).pack(pady=(0, 15))
        else:
            ctk.CTkLabel(popup, text="(Keine Beschreibung hinterlegt)", text_color="gray").pack(pady=(0, 15))
        
        # Status ändern
        status_var = ctk.StringVar(value=item['status'])
        ctk.CTkOptionMenu(popup, variable=status_var, values=["Offen", "In Bearbeitung", "Erledigt"]).pack(pady=5)
        
        ctk.CTkButton(popup, text="Aufgabe übertragen", fg_color="orange", 
                      command=lambda: self.ask_transfer(item, popup)).pack(pady=5)
                      
        ctk.CTkButton(popup, text="Speichern", 
                      command=lambda: self.update_status(item, status_var.get(), popup)).pack(pady=5)

    def ask_transfer(self, item, parent_popup):
        transfer_popup = ctk.CTkToplevel(self)
        transfer_popup.title("Aufgabe übertragen")
        
        transfer_popup.geometry("350x200") 
        transfer_popup.transient(self.winfo_toplevel()) 
        transfer_popup.grab_set() 
        transfer_popup.focus_force() 
        
        ctk.CTkLabel(transfer_popup, text=f"Übertrage an:").pack(pady=10)
        
        member_names = [m['name'] for m in self.members_data]
        target_var = ctk.CTkOptionMenu(transfer_popup, values=member_names)
        target_var.pack(pady=5, padx=20)
        
        def confirm_transfer():
            selected_name = target_var.get()
            new_member_id = next((m['id'] for m in self.members_data if m['name'] == selected_name), None)
            if new_member_id:
                supabase.table("todo").update({"zugewiesen_an": new_member_id}).eq("id", item['id']).execute()
                transfer_popup.destroy()
                parent_popup.destroy()
                self.show_status()

        ctk.CTkButton(transfer_popup, text="Bestätigen", command=confirm_transfer).pack(pady=20)

    # ==========================================
    # DATENBANK UPDATE / CLEANUP
    # ==========================================
    def update_status(self, item, new_status, popup):
        update_data = {"status": new_status}
        if new_status == "Erledigt":
            update_data["finished_at"] = datetime.now().isoformat()
        supabase.table("todo").update(update_data).eq("id", item['id']).execute()
        popup.destroy()
        self.show_status()

    def cleanup_todos(self):
        sechs_monate_her = (datetime.now() - timedelta(days=180)).isoformat()
        supabase.table("todo").delete().eq("status", "Erledigt").lt("finished_at", sechs_monate_her).execute()

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()