import customtkinter as ctk
from tkinter import messagebox
from database import supabase 

class AdressbuchWindow(ctk.CTkFrame):
    def __init__(self, master, role):
        super().__init__(master)
        self.role = role
        
        ctk.CTkLabel(self, text="Adressbuch", font=("Arial", 20, "bold")).pack(pady=10)
        
        if self.role in ["admin", "vorstand"]:
            ctk.CTkButton(self, text="+ Kontakt hinzufügen", fg_color="green", 
                          command=self.open_modal).pack(pady=10)
        
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.load_contacts()

    def load_contacts(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        try:
            # Wir nutzen wieder das globale, sauber importierte supabase-Objekt
            res = supabase.table("adressbuch").select("*").order("nachname").execute()
            contacts = res.data
            
            for item in contacts:
                frame = ctk.CTkFrame(self.list_frame)
                frame.pack(fill="x", pady=5, padx=5)
                
                name_text = f"{item['nachname']}, {item['vorname']} ({item['kategorie']})"
                ctk.CTkLabel(frame, text=name_text, font=("Arial", 14, "bold")).pack(side="left", padx=10)
                
                if self.role in ["admin", "vorstand"]:
                    ctk.CTkButton(frame, text="Bearbeiten", width=80, 
                                  command=lambda i=item: self.open_modal(i)).pack(side="right", padx=5)
                    ctk.CTkButton(frame, text="Löschen", width=80, fg_color="red",
                                  command=lambda i=item: self.delete_contact(i['id'])).pack(side="right", padx=5)
                
                ctk.CTkLabel(frame, text=f"Tel: {item.get('telefon', '-')} | E-Mail: {item.get('email', '-')}").pack(side="right", padx=10)

        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Kontakte nicht laden: {e}")

    def delete_contact(self, contact_id):
        if messagebox.askyesno("Löschen", "Kontakt wirklich löschen?"):
            supabase.table("adressbuch").delete().eq("id", contact_id).execute()
            self.load_contacts()

    def open_modal(self, contact=None):
        ContactModalWindow(self, contact, self.load_contacts)


class ContactModalWindow(ctk.CTkToplevel):
    def __init__(self, master, contact, refresh_callback):
        super().__init__(master)
        self.title("Kontakt bearbeiten / erstellen")
        
        # Fenster breiter und kompakter machen, damit alles ohne Scrollen passt
        self.geometry("750x480")
        self.resizable(False, False) # Verhindert unschöne Layout-Verschiebungen
        self.grab_set()
        
        self.contact = contact
        self.refresh_callback = refresh_callback
        self.fields = {}
        
        # Haupt-Container für das Grid-Layout
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Spaltengewichtung definieren (50% / 50% Aufteilung)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        
        # Kleine Hilfsfunktion, um Schreibarbeit bei den Grid-Feldern zu sparen
        def create_grid_field(label_text, key, row, col):
            # Frame hält Label und Entry sauber pro Zelle zusammen
            cell_frame = ctk.CTkFrame(main_container, fg_color="transparent")
            cell_frame.grid(row=row, column=col, padx=15, pady=8, sticky="ew")
            
            lbl = ctk.CTkLabel(cell_frame, text=label_text, anchor="w", font=("Arial", 12, "bold"))
            lbl.pack(fill="x")
            
            entry = ctk.CTkEntry(cell_frame, height=32)
            if contact and key in contact:
                entry.insert(0, contact[key] or "")
            entry.pack(fill="x", pady=(2, 0))
            self.fields[key] = entry

        # --- Zeile 0: Name ---
        create_grid_field("Vorname", "vorname", 0, 0)
        create_grid_field("Nachname", "nachname", 0, 1)
        
        # --- Zeile 1: Primäre Kontaktdaten ---
        create_grid_field("Telefon", "telefon", 1, 0)
        create_grid_field("E-Mail", "email", 1, 1)
        
        # --- Zeile 2: Fax & Kategorie ---
        create_grid_field("Fax", "fax", 2, 0)
        
        # Kategorie als ComboBox im Grid
        kat_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        kat_frame.grid(row=2, column=1, padx=15, pady=8, sticky="ew")
        ctk.CTkLabel(kat_frame, text="Kategorie", anchor="w", font=("Arial", 12, "bold")).pack(fill="x")
        
        self.kat_combo = ctk.CTkComboBox(kat_frame, values=["Behörde", "Künstler", "Aussteller", "Verleiher", "Sonstiges"], height=32)
        self.kat_combo.pack(fill="x", pady=(2, 0))
        if contact:
            self.kat_combo.set(contact.get("kategorie", "Sonstiges"))
            
        # --- Zeile 3: Anschrift ---
        create_grid_field("Adresse / Straße", "adresse", 3, 0)
        create_grid_field("Zimmer / Büro", "zimmer", 3, 1)
        
        # --- Zeile 4: Erreichbarkeit (Geht über die volle Breite) ---
        err_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        err_frame.grid(row=4, column=0, columnspan=2, padx=15, pady=8, sticky="ew")
        ctk.CTkLabel(err_frame, text="Erreichbarkeit (z.B. Mo-Fr 8-12 Uhr)", anchor="w", font=("Arial", 12, "bold")).pack(fill="x")
        
        entry_err = ctk.CTkEntry(err_frame, height=32)
        if contact and "erreichbarkeit" in contact:
            entry_err.insert(0, contact["erreichbarkeit"] or "")
        entry_err.pack(fill="x", pady=(2, 0))
        self.fields["erreichbarkeit"] = entry_err
        
        # --- Zeile 5: Speichern Button ---
        btn_speichern = ctk.CTkButton(
            main_container, 
            text="Kontakt speichern", 
            fg_color="green", 
            hover_color="#005c00",
            font=("Arial", 14, "bold"),
            height=40,
            command=self.save_contact
        )
        btn_speichern.grid(row=5, column=0, columnspan=2, pady=(25, 0), padx=15, sticky="ew")

    def save_contact(self):
        data = {k: v.get() for k, v in self.fields.items()}
        data["kategorie"] = self.kat_combo.get()
        
        if self.contact:
            supabase.table("adressbuch").update(data).eq("id", self.contact['id']).execute()
        else:
            supabase.table("adressbuch").insert(data).execute()
            
        self.refresh_callback()
        self.destroy()