import customtkinter as ctk
from tkinter import messagebox
from diagramme import FinanceChartsFrame
from modules.mitglieder import (
    get_alle_mitglieder, 
    mitglied_hinzufuegen, 
    mitglied_loeschen, 
    mitglied_aktualisieren, 
    get_mitglied_by_id, 
    get_naechste_mitgliedsnummer,
    formatiere_datum_fuer_anzeige
)
import os
import tempfile
from datetime import datetime
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from fpdf import FPDF
from PIL import Image
from admin_panel import AdminManagementFrame
from update_check import check_for_updates
from login_window import LoginWindow
from finanzen import FinanceFrame, BeitragFrame
from inventar import InventoryContent, check_reminders
from adressbuch import AdressbuchWindow
from events_view import EventsWindow
from termine import TerminView
from todo_logic import perform_maintenance
from todos import TodoView
import threading
APP_VERSION = "1.0.4"

class MainDashboard(ctk.CTk):
    def __init__(self, vorname, role, user_id=None, hat_inventar_rechte=False):
        super().__init__()
        self.rolle = role
        self.vorname = vorname
        self.user_id = user_id
        self.hat_inventar_rechte = hat_inventar_rechte
        self.after(2000, lambda: check_reminders(self, self.user_id))
        threading.Thread(target=perform_maintenance, daemon=True).start()


        self.title("KrayFürAlle e.V")
        self.geometry("1920x1080")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==========================================
        # 1. SIDEBAR GRUNDGERÜST
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.lbl_user = ctk.CTkLabel(
            self.sidebar, 
            text=f"Hallo, {vorname}", 
            font=("Arial", 16, "bold")
        )
        self.lbl_user.pack(pady=20)
        
        # Scroll-Bereich für die Navigation
        self.sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.sidebar_scroll.pack(fill="both", expand=True)
        self.sidebar_scroll.grid_columnconfigure(0, weight=1)

        # Version Label (bleibt fest unten)
        self.lbl_version = ctk.CTkLabel(
            self.sidebar,
            text=f"Version {APP_VERSION}", 
            font=("Arial", 11, "italic"),
            text_color="gray"
        )
        self.lbl_version.pack(side="bottom", pady=20)

        # Hilfsvariablen für Rollen-Level
        roles = {"mitglied": 1, "kassenwart": 2, "vorstand": 3, "admin": 3}
        current_role_clean = str(self.rolle).strip().lower()
        current_level = roles.get(current_role_clean, 1)

        # ==========================================
        # 2. SEKTION: MITGLIEDER (Row 0 & 1)
        # ==========================================
        self.btn_mitglieder = ctk.CTkButton(
            self.sidebar_scroll, text="Mitglieder ▼", 
            command=self.toggle_mitglieder_menu, fg_color="transparent"
        )
        self.btn_mitglieder.grid(row=0, column=0, pady=(10, 5), padx=10, sticky="ew")
        
        self.menu_mitglieder = ctk.CTkFrame(self.sidebar_scroll, fg_color="transparent")
        self.menu_mitglieder.grid(row=1, column=0, sticky="ew")
        self.menu_mitglieder.grid_remove() # Startet versteckt
        
        self.create_smart_button("• Liste anzeigen", self.show_mitglieder, "mitglied", parent=self.menu_mitglieder)
        self.create_smart_button("• Neues Mitglied", self.add_member, "vorstand", parent=self.menu_mitglieder) 
        self.create_smart_button("• Statistik / PDF", self.show_stats, "vorstand", parent=self.menu_mitglieder)    
        self.create_smart_button("• Admin-Panel", self.show_admin_panel, "admin", parent=self.menu_mitglieder)

        # ==========================================
        # 3. SEKTION: FINANZEN (Row 2 & 3)
        # ==========================================
        self.menu_finanzen = ctk.CTkFrame(self.sidebar_scroll, fg_color="transparent")
        self.menu_finanzen.grid(row=3, column=0, sticky="ew")
        self.menu_finanzen.grid_remove() # Startet versteckt

        if current_level >= 2:
            self.btn_finanzen = ctk.CTkButton(
                self.sidebar_scroll, text="Finanzen ▼", 
                command=self.toggle_finanzen_menu, fg_color="transparent"
            )
            self.btn_finanzen.grid(row=2, column=0, pady=5, padx=10, sticky="ew")
            
            self.create_smart_button("• Bericht Kassenbuch", self.show_finanzen, "kassenwart", parent=self.menu_finanzen)
            self.create_smart_button("• Mitgliedsbeiträge", self.show_mitgliedsbeitraege, "kassenwart", parent=self.menu_finanzen)
            self.create_smart_button("• Finanzdiagramme", self.show_diagramme, "kassenwart", parent=self.menu_finanzen)
        else:
            self.btn_finanzen = ctk.CTkButton(
                self.sidebar_scroll, text="Finanzen 🔒", 
                state="disabled", fg_color="gray", text_color="white"
            )
            self.btn_finanzen.grid(row=2, column=0, pady=5, padx=10, sticky="ew")

        # ==========================================
        # 4. SEKTION: INVENTAR (Row 4 & 5)
        # ==========================================
        self.btn_inventar = ctk.CTkButton(
            self.sidebar_scroll, text="Inventar ▼", 
            command=self.toggle_inventar_menu, fg_color="transparent"
        )
        self.btn_inventar.grid(row=4, column=0, pady=5, padx=10, sticky="ew")

        self.menu_inventar = ctk.CTkFrame(self.sidebar_scroll, fg_color="transparent")
        self.menu_inventar.grid(row=5, column=0, sticky="ew")
        self.menu_inventar.grid_remove() # Startet versteckt

        self.create_inventory_button("• Bestandsliste", self.show_inventar_bestand, "mitglied", needs_rights=False, parent=self.menu_inventar)
        self.create_inventory_button("• Ausleihliste", self.show_inventar_ausleihe, "mitglied", needs_rights=True, parent=self.menu_inventar)
        self.create_inventory_button("• Rücknahme", self.show_inventar_ruecknahme, "mitglied", needs_rights=True, parent=self.menu_inventar)
        self.create_inventory_button("• Rechteverwaltung", self.show_inventar_rechte, "vorstand", needs_rights=False, parent=self.menu_inventar)

        # ==========================================
        # 5. SEKTION: ADRESSBUCH (Row 6)
        # ==========================================
        if current_role_clean in ["admin", "vorstand"]:
            self.btn_adressbuch = ctk.CTkButton(
                self.sidebar_scroll, text="Adressbuch", 
                command=self.show_adressbuch, fg_color="#1f6aa5"
            )
        else:
            self.btn_adressbuch = ctk.CTkButton(
                self.sidebar_scroll, text="Adressbuch 🔒", 
                state="disabled", fg_color="gray", text_color="white"
            )
        self.btn_adressbuch.grid(row=6, column=0, pady=5, padx=10, sticky="ew")

        # ==========================================
        # 6. SEKTION: EVENTS & TERMINE (Row 7 & 8)
        # ==========================================
        self.btn_events = ctk.CTkButton(
        self.sidebar_scroll, text="Events & Termine ▼", 
        command=self.toggle_events_menu, fg_color="transparent")

        self.btn_events.grid(row=7, column=0, pady=5, padx=10, sticky="ew")

        self.menu_events = ctk.CTkFrame(self.sidebar_scroll, fg_color="transparent")
        self.menu_events.grid(row=8, column=0, sticky="ew")
        self.menu_events.grid_remove() # Startet versteckt

        # Button 1 ruft show_events auf
        self.create_smart_button("• Übersicht", self.show_events, "mitglied", parent=self.menu_events)

        # Button 2 ruft show_termine auf (das ist der entscheidende Punkt!)
        self.create_smart_button("• Termine Übersicht", self.show_termine, "mitglied", parent=self.menu_events)
        # ==========================================
        # 7. SEKTION: TO-DOS (Row 9)
        # ==========================================
        self.btn_todos = ctk.CTkButton(
            self.sidebar_scroll, text="To-Dos", 
            command=lambda: self.show_view(TodoView), 
            fg_color="transparent"
        )
        self.btn_todos.grid(row=9, column=0, pady=5, padx=10, sticky="ew")

        # ==========================================
        # MAIN CONTENT BEREICH
        # ==========================================
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)


    # ==========================================
    # SMART-BUTTON ERSTELLUNG
    # ==========================================
    def create_inventory_button(self, text, command, min_role, needs_rights=False, parent=None):
        if parent is None:
            return

        roles = {"mitglied": 1, "kassenwart": 2, "vorstand": 3, "admin": 3}
        current_role_clean = str(self.rolle).strip().lower()
        current_level = roles.get(current_role_clean, 1)
        required_level = roles.get(str(min_role).strip().lower(), 1)
        
        is_staff = current_level >= 2
        
        if is_staff:
            has_access = True
        elif needs_rights:
            has_access = self.hat_inventar_rechte
        else:
            has_access = (current_level >= required_level)

        if has_access:
            ctk.CTkButton(parent, text=text, command=command, fg_color="#1f6aa5").pack(pady=5, padx=20, fill="x")
        else:
            ctk.CTkButton(parent, text=f"{text} 🔒", state="disabled", fg_color="gray", text_color="white").pack(pady=5, padx=20, fill="x")

    def create_smart_button(self, text, command, min_role, parent=None, pady=5):
        if parent is None:
            return

        roles = {"mitglied": 1, "kassenwart": 2, "vorstand": 3, "admin": 3}
        current_role_clean = str(self.rolle).strip().lower()
        required_role_clean = str(min_role).strip().lower()
        current_level = roles.get(current_role_clean, 1)
        required_level = roles.get(required_role_clean, 1)

        if current_level >= required_level:
            ctk.CTkButton(parent, text=text, command=command).pack(pady=pady, padx=20, fill="x")
        else:
            ctk.CTkButton(parent, text=f"{text} 🔒", state="disabled", fg_color="gray", text_color="white").pack(pady=pady, padx=20, fill="x")

    # ==========================================
    # TOGGLE MENÜ FUNKTIONEN (ANGEPASST AUF GRID)
    # ==========================================
    def toggle_mitglieder_menu(self):
        if self.menu_mitglieder.winfo_viewable():
            self.menu_mitglieder.grid_remove()
            self.btn_mitglieder.configure(text="Mitglieder ▼")
        else:
            self.menu_mitglieder.grid()
            self.btn_mitglieder.configure(text="Mitglieder ▲")

    def toggle_finanzen_menu(self):
        if self.menu_finanzen.winfo_viewable():
            self.menu_finanzen.grid_remove()
            self.btn_finanzen.configure(text="Finanzen ▼")
        else:
            self.menu_finanzen.grid()
            self.btn_finanzen.configure(text="Finanzen ▲")

    def toggle_inventar_menu(self):
        if self.menu_inventar.winfo_viewable():
            self.menu_inventar.grid_remove()
            self.btn_inventar.configure(text="Inventar ▼")
        else:
            self.menu_inventar.grid()
            self.btn_inventar.configure(text="Inventar ▲")

    def toggle_events_menu(self):
        if self.menu_events.winfo_viewable():
            self.menu_events.grid_remove()
            self.btn_events.configure(text="Events & Termine ▼")
        else:
            self.menu_events.grid()
            self.btn_events.configure(text="Events & Termine ▲")

    # ==========================================
    # ANSICHTEN WECHSELN
    # ==========================================
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_finanzen(self):
        self.clear_content()
        self.finance_view = FinanceFrame(self.content_frame, current_user_name=self.vorname)
        self.finance_view.pack(fill="both", expand=True, padx=10, pady=10)

    def show_mitgliedsbeitraege(self):
        self.clear_content()
        self.beitrag_view = BeitragFrame(self.content_frame, current_user_name=self.vorname)
        self.beitrag_view.pack(fill="both", expand=True, padx=10, pady=10)

    def show_diagramme(self):
        self.clear_content()
        self.charts_view = FinanceChartsFrame(self.content_frame)
        self.charts_view.pack(fill="both", expand=True, padx=10, pady=10)

    def show_inventar(self, active_tab="Materialbestand"):
        self.clear_content()
        self.inventory_view = InventoryContent(
            self.content_frame, 
            role=self.rolle, 
            user_id=self.user_id,
            hat_inventar_rechte=self.hat_inventar_rechte
        )
        self.inventory_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        mapping = {
            "Materialbestand": "bestand",
            "Ausleihe": "ausleihe",
            "Rücknahme": "rueckgabe",
            "Rechteverwaltung": "rights",
            "Einstellungen": "settings"
        }
        target = mapping.get(active_tab, "bestand")
        self.inventory_view.zeige_seite(target)

    def show_inventar_bestand(self):
        self.show_inventar("Materialbestand")

    def show_inventar_ausleihe(self):
        self.show_inventar("Ausleihe")

    def show_inventar_ruecknahme(self):
        self.show_inventar("Rücknahme")
        
    def show_inventar_rechte(self):
        self.show_inventar("Rechteverwaltung")

    # ==========================================
    # MITGLIEDER LOGIK
    # ==========================================
    def show_mitglieder(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="Mitgliederliste", font=("Arial", 20, "bold")).pack(pady=10)
        
        list_frame = ctk.CTkScrollableFrame(self.content_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = [("Name", 160), ("Nr.", 60), ("Email", 180), ("Telefon", 130), ("Status", 90), ("Rolle", 90)]
        
        for col_idx, (text, width) in enumerate(columns):
            lbl = ctk.CTkLabel(list_frame, text=text, width=width, font=("Arial", 12, "bold"), anchor="w")
            lbl.grid(row=0, column=col_idx, padx=10, pady=5, sticky="w")
            
        is_admin_oder_vorstand = str(self.rolle).strip().lower() in ["vorstand", "admin"]

        mitglieder = get_alle_mitglieder()
        if mitglieder:
            for row_idx, m in enumerate(mitglieder, start=1):
                name_btn = ctk.CTkButton(
                    list_frame, 
                    text=f"{m.get('vorname', '')} {m.get('nachname', '')}", 
                    width=160, 
                    fg_color="transparent", 
                    text_color=("#000000", "#FFFFFF"), 
                    anchor="w",
                    command=lambda aktuelle_m=m: self.show_details(aktuelle_m)
                )
                name_btn.grid(row=row_idx, column=0, padx=10, pady=4, sticky="w")
                
                ctk.CTkLabel(list_frame, text=m.get('mitgliedsnummer', '-'), width=60, anchor="w").grid(row=row_idx, column=1, padx=10, pady=4, sticky="w")
                ctk.CTkLabel(list_frame, text=m.get('email', '-'), width=180, anchor="w").grid(row=row_idx, column=2, padx=10, pady=4, sticky="w")
                ctk.CTkLabel(list_frame, text=m.get('telefonnummer', '-'), width=130, anchor="w").grid(row=row_idx, column=3, padx=10, pady=4, sticky="w")
                ctk.CTkLabel(list_frame, text=m.get('status', '-'), width=90, anchor="w").grid(row=row_idx, column=4, padx=10, pady=4, sticky="w")
                ctk.CTkLabel(list_frame, text=m.get('rolle', '-'), width=90, anchor="w").grid(row=row_idx, column=5, padx=10, pady=4, sticky="w")
                
                if is_admin_oder_vorstand:
                    bearbeiten_btn = ctk.CTkButton(
                        list_frame, text="Bearbeiten", width=80, fg_color="blue", 
                        command=lambda mid=m.get('id'): self.edit_member(mid)
                    )
                    bearbeiten_btn.grid(row=row_idx, column=6, padx=5, pady=4, sticky="e")
                    
                    loeschen_btn = ctk.CTkButton(
                        list_frame, text="Löschen", width=80, fg_color="red", 
                        command=lambda mid=m.get('id'): self.delete_member(mid)
                    )
                    loeschen_btn.grid(row=row_idx, column=7, padx=5, pady=4, sticky="e")

    def show_details(self, m):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text=f"Details: {m.get('vorname')} {m.get('nachname')}", font=("Arial", 20)).pack(pady=10)
        
        details_box = ctk.CTkFrame(self.content_frame)
        details_box.pack(pady=20, padx=20, fill="both", expand=True)
        
        info = [
            ("Geburtsdatum", formatiere_datum_fuer_anzeige(m.get('geburtsdatum'))),
            ("Beitrittsdatum", formatiere_datum_fuer_anzeige(m.get('beitrittsdatum'))),
            ("Adresse", f"{m.get('strasse')} {m.get('hausnummer')}, {m.get('plz')} {m.get('ort')} ({m.get('stadtteil')})"),
            ("Email", m.get('email')),
            ("Telefon", m.get('telefonnummer')),
            ("Geschlecht", m.get('geschlecht'))
        ]
        
        for label, val in info:
            ctk.CTkLabel(details_box, text=f"{label}: {val}", font=("Arial", 14)).pack(anchor="w", padx=20, pady=5)

    def show_admin_panel(self):
        self.clear_content()
        if str(self.rolle).strip().lower() in ["admin", "vorstand"]:
            admin_panel = AdminManagementFrame(self.content_frame, current_user_role=self.rolle)
            admin_panel.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.content_frame, text="Zugriff verweigert! Nur für Admins.", text_color="red").pack(pady=50)

    def add_member(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="Neues Mitglied anlegen", font=("Arial", 20)).pack(pady=10)
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame, label_text="Mitgliedsdaten")
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.entries = {}
        fields = ["Vorname", "Nachname", "Geburtsdatum", "Beitrittsdatum", "Strasse", "Hausnummer", "PLZ", "Ort", "Stadtteil", "Email", "Telefonnummer"]
        
        self.entry_nr = ctk.CTkEntry(scroll_frame, placeholder_text="Mitgliedsnummer")
        self.entry_nr.pack(pady=5, padx=10, fill="x")
        self.auto_nr = ctk.CTkCheckBox(scroll_frame, text="Automatisch vergeben", command=self.update_nr)
        self.auto_nr.pack(pady=5, padx=10)

        self.dropdown_status = ctk.CTkOptionMenu(scroll_frame, values=["aktiv", "passiv", "ehrenmitglied"])
        self.dropdown_status.pack(pady=5, padx=10, fill="x")

        for field in fields:
            entry = ctk.CTkEntry(scroll_frame, placeholder_text=field)
            entry.pack(pady=5, padx=10, fill="x")
            self.entries[field] = entry

        self.dropdown_geschlecht = ctk.CTkOptionMenu(scroll_frame, values=["männlich", "weiblich", "divers"])
        self.dropdown_geschlecht.pack(pady=5, padx=10, fill="x")
        self.dropdown_rolle = ctk.CTkOptionMenu(scroll_frame, values=["Mitglied", "Vorstand", "Kassenwart", "Admin"])
        self.dropdown_rolle.pack(pady=5, padx=10, fill="x")

        ctk.CTkButton(scroll_frame, text="Speichern", fg_color="green", command=self.save_member).pack(pady=20)
    def save_member(self):
        data = {
            "vorname": self.entries["Vorname"].get(),
            "nachname": self.entries["Nachname"].get(),
            "geburtsdatum": self.entries["Geburtsdatum"].get(),
            "beitrittsdatum": self.entries["Beitrittsdatum"].get(),
            "strasse": self.entries["Strasse"].get(),
            "hausnummer": self.entries["Hausnummer"].get(),
            "plz": self.entries["PLZ"].get(),
            "ort": self.entries["Ort"].get(),
            "stadtteil": self.entries["Stadtteil"].get(),
            "email": self.entries["Email"].get(),
            "telefonnummer": self.entries["Telefonnummer"].get(),
            "mitgliedsnummer": self.entry_nr.get(),
            "geschlecht": self.dropdown_geschlecht.get(),
            "rolle": self.dropdown_rolle.get(),
            "status": self.dropdown_status.get()
        }
        mitglied_hinzufuegen(data)
        messagebox.showinfo("Erfolg", "Mitglied wurde gespeichert.")
        self.show_mitglieder()

    def show_admin_panel(self):
        self.clear_content()
        if str(self.rolle).strip().lower() in ["admin", "vorstand"]:
            admin_panel = AdminManagementFrame(self.content_frame, current_user_role=self.rolle)
            admin_panel.pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.content_frame, text="Zugriff verweigert! Nur für Admins.", text_color="red").pack(pady=50)

    def add_member(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="Neues Mitglied anlegen", font=("Arial", 20)).pack(pady=10)
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame, label_text="Mitgliedsdaten")
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.entries = {}
        fields = ["Vorname", "Nachname", "Geburtsdatum", "Beitrittsdatum", "Strasse", "Hausnummer", "PLZ", "Ort", "Stadtteil", "Email", "Telefonnummer"]
        
        self.entry_nr = ctk.CTkEntry(scroll_frame, placeholder_text="Mitgliedsnummer")
        self.entry_nr.pack(pady=5, padx=10, fill="x")
        self.auto_nr = ctk.CTkCheckBox(scroll_frame, text="Automatisch vergeben", command=self.update_nr)
        self.auto_nr.pack(pady=5, padx=10)

        self.dropdown_status = ctk.CTkOptionMenu(scroll_frame, values=["aktiv", "passiv", "ehrenmitglied"])
        self.dropdown_status.pack(pady=5, padx=10, fill="x")

        for field in fields:
            entry = ctk.CTkEntry(scroll_frame, placeholder_text=field)
            entry.pack(pady=5, padx=10, fill="x")
            self.entries[field] = entry

        self.dropdown_geschlecht = ctk.CTkOptionMenu(scroll_frame, values=["männlich", "weiblich", "divers"])
        self.dropdown_geschlecht.pack(pady=5, padx=10, fill="x")
        
        self.dropdown_rolle = ctk.CTkOptionMenu(scroll_frame, values=["Mitglied", "Vorstand", "Kassenwart", "Admin"])
        self.dropdown_rolle.pack(pady=5, padx=10, fill="x")

        ctk.CTkButton(scroll_frame, text="Speichern", fg_color="green", command=self.save_member).pack(pady=20)

    def save_member(self):
        data = {
            "vorname": self.entries["Vorname"].get(),
            "nachname": self.entries["Nachname"].get(),
            "geburtsdatum": self.entries["Geburtsdatum"].get(),
            "beitrittsdatum": self.entries["Beitrittsdatum"].get(),
            "strasse": self.entries["Strasse"].get(),
            "hausnummer": self.entries["Hausnummer"].get(),
            "plz": self.entries["PLZ"].get(),
            "ort": self.entries["Ort"].get(),
            "stadtteil": self.entries["Stadtteil"].get(),
            "email": self.entries["Email"].get(),
            "telefonnummer": self.entries["Telefonnummer"].get(),
            "mitgliedsnummer": self.entry_nr.get(),
            "geschlecht": self.dropdown_geschlecht.get(),
            "rolle": self.dropdown_rolle.get(),
            "status": self.dropdown_status.get()
        }
        mitglied_hinzufuegen(data)
        messagebox.showinfo("Erfolg", "Mitglied wurde gespeichert.")
        self.show_mitglieder()

    def edit_member(self, mitglieder_id):
        m = get_mitglied_by_id(mitglieder_id)
        self.clear_content()
        
        ctk.CTkLabel(self.content_frame, text="Mitglied bearbeiten", font=("Arial", 20)).pack(pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame, label_text="Daten bearbeiten")
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.entries = {}
        field_mapping = {
            "Vorname": "vorname", "Nachname": "nachname", 
            "Geburtsdatum": "geburtsdatum", "Beitrittsdatum": "beitrittsdatum",
            "Strasse": "strasse", "Hausnummer": "hausnummer", 
            "PLZ": "plz", "Ort": "ort", 
            "Stadtteil": "stadtteil", "Email": "email", "Telefonnummer": "telefonnummer"
        }

        for label, db_key in field_mapping.items():
            entry = ctk.CTkEntry(scroll_frame, placeholder_text=label)
            
            # FIX: Wenn die Datenbank 'None' zurückgibt, machen wir einen leeren Text ("") daraus,
            # damit CustomTkinter nicht abstürzt.
            val = m.get(db_key) or ""
            
            if db_key in ["geburtsdatum", "beitrittsdatum"] and val:
                val = formatiere_datum_fuer_anzeige(val)
                
            entry.insert(0, str(val)) # Zur Sicherheit immer als Text (String) übergeben
            entry.pack(pady=5, padx=10, fill="x")
            self.entries[label] = entry

        self.dropdown_status = ctk.CTkOptionMenu(scroll_frame, values=["aktiv", "passiv", "ehrenmitglied"])
        # Auch hier sichern wir uns gegen 'None' ab
        self.dropdown_status.set(m.get('status') or 'aktiv')
        self.dropdown_status.pack(pady=5, padx=10, fill="x")

        self.dropdown_geschlecht = ctk.CTkOptionMenu(scroll_frame, values=["männlich", "weiblich", "divers"])
        self.dropdown_geschlecht.set(m.get('geschlecht') or 'männlich')
        self.dropdown_geschlecht.pack(pady=5, padx=10, fill="x")

        self.dropdown_rolle = ctk.CTkOptionMenu(scroll_frame, values=["Mitglied", "Vorstand", "Kassenwart", "Admin"])
        self.dropdown_rolle.set(m.get('rolle') or 'Mitglied')
        self.dropdown_rolle.pack(pady=5, padx=10, fill="x")

        ctk.CTkButton(
            scroll_frame, text="Änderungen speichern", fg_color="blue", 
            command=lambda: self.save_edit(mitglieder_id)
        ).pack(pady=20)

    def save_edit(self, mid):
        data = {
            "vorname": self.entries["Vorname"].get(),
            "nachname": self.entries["Nachname"].get(),
            "geburtsdatum": self.entries["Geburtsdatum"].get(),
            "beitrittsdatum": self.entries["Beitrittsdatum"].get(),
            "strasse": self.entries["Strasse"].get(),
            "hausnummer": self.entries["Hausnummer"].get(),
            "plz": self.entries["PLZ"].get(),
            "ort": self.entries["Ort"].get(),
            "stadtteil": self.entries["Stadtteil"].get(),
            "email": self.entries["Email"].get(),
            "telefonnummer": self.entries["Telefonnummer"].get(),
            "status": self.dropdown_status.get(),
            "geschlecht": self.dropdown_geschlecht.get(),
            "rolle": self.dropdown_rolle.get()  # FIX: Speichert die Rolle nun mit ab
        }
        
        mitglied_aktualisieren(mid, data)
        messagebox.showinfo("Erfolg", "Die Daten wurden erfolgreich gespeichert.")
        self.show_mitglieder()

    def update_nr(self):
        if self.auto_nr.get() == 1:
            self.entry_nr.configure(state="normal")
            self.entry_nr.delete(0, 'end')
            self.entry_nr.insert(0, get_naechste_mitgliedsnummer())
            self.entry_nr.configure(state="disabled")
        else:
            self.entry_nr.configure(state="normal")
            self.entry_nr.delete(0, 'end')

    def delete_member(self, mid):
        if messagebox.askyesno("Löschen", "Wirklich löschen?"):
            mitglied_loeschen(mid)
            self.show_mitglieder()

    def calculate_age(self, bdate_str):
        if not bdate_str: return -1
        try:
            # Falls das Datum als ISO-String oder mit Zeitstempel kommt, fangen wir Fehler ab
            if " " in bdate_str:
                bdate_str = bdate_str.split(" ")[0]
            bdate = datetime.strptime(bdate_str, "%Y-%m-%d")
            today = datetime.today()
            return today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
        except:
            return -1

    def show_stats(self):
        self.clear_content()
        ctk.CTkLabel(self.content_frame, text="Statistik & PDF Export", font=("Arial", 20, "bold")).pack(pady=10)

        if hasattr(self, 'fig') and self.fig:
            plt.close(self.fig)

        btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            btn_frame, text="📄 Mitgliederliste als PDF", fg_color="green", 
            command=self.export_mitgliederliste_pdf
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, text="📊 Statistik als PDF", fg_color="purple", 
            command=self.export_statistik_pdf
        ).pack(side="left", padx=10)

        mitglieder = get_alle_mitglieder()
        self.stats = {
            "alter": {"0-12": 0, "13-18": 0, "19-35": 0, "36-65": 0, "ab 66": 0, "Unbekannt": 0},
            "geschlecht": {"männlich": 0, "weiblich": 0, "divers": 0, "Unbekannt": 0}
        }

        for m in mitglieder:
            g = m.get('geschlecht')
            if g in self.stats["geschlecht"]: self.stats["geschlecht"][g] += 1
            else: self.stats["geschlecht"]["Unbekannt"] += 1

            alter = self.calculate_age(m.get('geburtsdatum'))
            if alter == -1: self.stats["alter"]["Unbekannt"] += 1
            elif alter <= 12: self.stats["alter"]["0-12"] += 1
            elif alter <= 18: self.stats["alter"]["13-18"] += 1
            elif alter <= 35: self.stats["alter"]["19-35"] += 1
            elif alter <= 65: self.stats["alter"]["36-65"] += 1
            else: self.stats["alter"]["ab 66"] += 1

        stats_frame = ctk.CTkFrame(self.content_frame)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        g_text = f"Geschlecht: Männlich ({self.stats['geschlecht']['männlich']}) | Weiblich ({self.stats['geschlecht']['weiblich']}) | Divers ({self.stats['geschlecht']['divers']})"
        ctk.CTkLabel(stats_frame, text=g_text, font=("Arial", 14, "bold")).pack(pady=5)
        
        a_text = f"Alter: Bis 12 ({self.stats['alter']['0-12']}) | 13-18 ({self.stats['alter']['13-18']}) | 19-35 ({self.stats['alter']['19-35']}) | 36-65 ({self.stats['alter']['36-65']}) | ab 66 ({self.stats['alter']['ab 66']})"
        ctk.CTkLabel(stats_frame, text=a_text, font=("Arial", 14, "bold")).pack(pady=5)

        self.chart_frame = ctk.CTkFrame(self.content_frame)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctrl_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(ctrl_frame, text="Diagramm-Typ:").pack(side="left", padx=10)
        
        self.chart_type = ctk.StringVar(value="Balkendiagramm")
        dropdown = ctk.CTkOptionMenu(ctrl_frame, variable=self.chart_type, values=["Balkendiagramm", "Kreisdiagramm"], command=self.draw_chart)
        dropdown.pack(side="left", padx=10)
        
        self.canvas_widget = None
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.draw_chart()

    def draw_chart(self, *args):
        from matplotlib.ticker import MaxNLocator
        
        if self.canvas_widget:
            self.canvas_widget.destroy()

        self.ax1.clear()
        self.ax2.clear()

        c_type = self.chart_type.get()
        
        if c_type == "Balkendiagramm":
            g_labels = list(self.stats["geschlecht"].keys())
            g_sizes = list(self.stats["geschlecht"].values())
            
            a_labels = list(self.stats["alter"].keys())
            a_sizes = list(self.stats["alter"].values())

            self.ax1.bar(g_labels, g_sizes, color=['#5C93D1', '#F28DA8', '#5DBB63', '#888888'])
            self.ax2.bar(a_labels, a_sizes, color='#FFA07A')
            
            self.ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
            self.ax2.yaxis.set_major_locator(MaxNLocator(integer=True))

        else:
            g_labels = [k for k, v in self.stats["geschlecht"].items() if v > 0]
            g_sizes = [v for v in self.stats["geschlecht"].values() if v > 0]
            
            a_labels = [k for k, v in self.stats["alter"].items() if v > 0]
            a_sizes = [v for v in self.stats["alter"].values() if v > 0]

            def autopct_format(values):
                def my_format(pct):
                    total = sum(values)
                    val = int(round(pct * total / 100.0))
                    return f'{pct:.1f}%\n({val})'
                return my_format

            if g_labels: 
                self.ax1.pie(g_sizes, labels=g_labels, autopct=autopct_format(g_sizes), 
                             colors=['#5C93D1', '#F28DA8', '#5DBB63', '#888888'])
            if a_labels: 
                self.ax2.pie(a_sizes, labels=a_labels, autopct=autopct_format(a_sizes), 
                             colors=['#FF9999','#66B2FF','#99FF99','#FFCC99','#c2c2f0', '#ffb3e6'])

        self.ax1.set_title("Geschlechterverteilung")
        self.ax2.set_title("Altersverteilung")
        self.fig.tight_layout()

        canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        canvas.draw()
        self.canvas_widget = canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

    def export_mitgliederliste_pdf(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], title="PDF speichern unter...")
        if not filepath: return
        
        pdf = FPDF(orientation="L")
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        
        # FIX: .encode('latin-1', 'replace').decode('latin-1') schützt vor Umlaut-Crashes
        pdf.cell(0, 10, "Mitgliederliste - KrayFürAlle e.V".encode('latin-1', 'replace').decode('latin-1'), new_y="NEXT", align="C")
        pdf.ln(5)

        pdf.set_font("helvetica", "B", 10)
        columns = [("Nr.", 20), ("Vorname", 40), ("Nachname", 40), ("Email", 70), ("Telefon", 40), ("Status", 30), ("Rolle", 30)]
        for name, width in columns:
            pdf.cell(width, 10, name.encode('latin-1', 'replace').decode('latin-1'), border=1)
        pdf.ln()

        pdf.set_font("helvetica", "", 10)
        mitglieder = get_alle_mitglieder()
        for m in mitglieder:
            pdf.cell(20, 10, str(m.get('mitgliedsnummer', '-')).encode('latin-1', 'replace').decode('latin-1'), border=1)
            pdf.cell(40, 10, str(m.get('vorname', '-')).encode('latin-1', 'replace').decode('latin-1'), border=1)
            pdf.cell(40, 10, str(m.get('nachname', '-')).encode('latin-1', 'replace').decode('latin-1'), border=1)
            pdf.cell(70, 10, str(m.get('email', '-')).encode('latin-1', 'replace').decode('latin-1'), border=1)
            pdf.cell(40, 10, str(m.get('telefonnummer', '-')).encode('latin-1', 'replace').decode('latin-1'), border=1)
            pdf.cell(30, 10, str(m.get('status', '-')).encode('latin-1', 'replace').decode('latin-1'), border=1)
            pdf.cell(30, 10, str(m.get('rolle', '-')).encode('latin-1', 'replace').decode('latin-1'), border=1)
            pdf.ln()

        pdf.output(filepath)
        messagebox.showinfo("Erfolg", f"Mitgliederliste wurde als PDF gespeichert:\n{filepath}")

    def export_statistik_pdf(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], title="PDF speichern unter...")
        if not filepath: return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Vereinsstatistik - KrayFürAlle e.V".encode('latin-1', 'replace').decode('latin-1'), new_y="NEXT", align="C")
        pdf.ln(10)

        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Zahlen & Daten:", new_y="NEXT")
        pdf.set_font("helvetica", "", 12)
        
        # FIX: Umlautsichere Konvertierung für statistische Auswertungen im Dokument
        txt_geschlecht = f"Männlich: {self.stats['geschlecht']['männlich']} | Weiblich: {self.stats['geschlecht']['weiblich']} | Divers: {self.stats['geschlecht']['divers']}"
        pdf.cell(0, 8, txt_geschlecht.encode('latin-1', 'replace').decode('latin-1'), new_y="NEXT")
        
        txt_alter1 = f"Alter 0-12: {self.stats['alter']['0-12']} | 13-18: {self.stats['alter']['13-18']} | 19-35: {self.stats['alter']['19-35']}"
        pdf.cell(0, 8, txt_alter1.encode('latin-1', 'replace').decode('latin-1'), new_y="NEXT")
        
        txt_alter2 = f"Alter 36-65: {self.stats['alter']['36-65']} | ab 66: {self.stats['alter']['ab 66']}"
        pdf.cell(0, 8, txt_alter2.encode('latin-1', 'replace').decode('latin-1'), new_y="NEXT")
        pdf.ln(10)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            temp_img = tmpfile.name
        
        try:
            self.fig.savefig(temp_img)
            pdf.image(temp_img, x=10, w=190)
        finally:
            if os.path.exists(temp_img):
                os.remove(temp_img)

        pdf.output(filepath)
        messagebox.showinfo("Erfolg", f"Statistik wurde als PDF gespeichert:\n{filepath}")

    def show_adressbuch(self):
        self.clear_content()
        # Hier erstellst du die Instanz
        self.adressbuch_view = AdressbuchWindow(self.content_frame, self.rolle)
        # Hier musst du denselben Namen zum Packen verwenden
        self.adressbuch_view.pack(fill="both", expand=True, padx=10, pady=10)

    def show_events(self):
        self.clear_content()
        # Hole ID ohne Default-1, damit es sauber bleibt
        aktuelle_id = getattr(self, "aktuelle_user_id", None)
        
        # Nur Events laden
        self.events_view = EventsWindow(self.content_frame, self.rolle, aktuelle_mitglieder_id=aktuelle_id)
        self.events_view.pack(fill="both", expand=True, padx=10, pady=10)

    def show_termine(self):
        self.clear_content()
        # Hole ID ohne Default-1
        aktuelle_id = getattr(self, "aktuelle_user_id", None)
        
        # Nur Termine laden
        self.termin_view = TerminView(self.content_frame, self.rolle, user_id=aktuelle_id)
        self.termin_view.pack(fill="both", expand=True, padx=10, pady=10)
    def show_view(self, view_class):
        # 1. Vorherigen Inhalt aus dem Main-Bereich löschen
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        view = view_class(self.content_frame, self.user_id)
        view.pack(fill="both", expand=True)

if __name__ == "__main__":
    check_for_updates() 
    app = LoginWindow() 
    app.mainloop()