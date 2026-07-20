import customtkinter as ctk
from tkinter import messagebox
from database import supabase  
import webbrowser
from urllib.parse import quote
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
from tkinter import simpledialog

def format_date(date_str):
    """Wandelt YYYY-MM-DD in DD/MM/YYYY um. Gibt bei leeren Werten einen Leerstring zurück."""
    if not date_str:
        return ""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def parse_flexible_date(date_str):
    # Ersetzt alle Punkte durch Slashes, um ein einheitliches Format zu haben
    normalized_date = date_str.replace('.', '/')
    try:
        # Parsen des normalisierten Datums
        return datetime.strptime(normalized_date, '%d/%m/%Y')
    except ValueError:
        return "Ungültiges Datumsformat"


# --- Neue Klasse: Adressbuch Modal ---
class AddressBookModal(ctk.CTkToplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.title("Adressbuch wählen")
        self.geometry("350x250")
        self.grab_set()
        self.callback = callback
        
        ctk.CTkLabel(self, text="Quelle wählen:", font=("Arial", 12)).pack(pady=(10, 0))
        self.source_var = ctk.StringVar(value="Mitglieder")
        self.radio_mitglieder = ctk.CTkRadioButton(self, text="Mitglieder", variable=self.source_var, value="Mitglieder", command=self.load_data)
        self.radio_mitglieder.pack(pady=5)
        self.radio_extern = ctk.CTkRadioButton(self, text="Behörden/Kontakte", variable=self.source_var, value="Kontakte", command=self.load_data)
        self.radio_extern.pack(pady=5)
        
        self.combo_items = ctk.CTkComboBox(self, values=["Bitte warten..."], width=250)
        self.combo_items.pack(pady=10)
        
        ctk.CTkButton(self, text="Übernehmen", fg_color="green", command=self.apply_selection).pack(pady=10)
        
        self.load_data()

    def load_data(self):
        source = self.source_var.get()
        try:
            if source == "Mitglieder":
                # Abfrage für Mitglieder
                res = supabase.table("mitglieder").select("vorname, nachname").order("nachname").execute()
            else:
                # Abfrage für dein Adressbuch
                res = supabase.table("adressbuch").select("vorname, nachname").order("nachname").execute()
            
            # Formatierung: Wir bauen Vorname + Nachname zusammen
            # (m.get('vorname') or '') verhindert Fehler, falls Vorname mal leer ist
            names = [f"{m.get('vorname') or ''} {m['nachname']}".strip() for m in res.data]
            
            if names:
                self.combo_items.configure(values=names)
                self.combo_items.set(names[0])
            else:
                self.combo_items.configure(values=["Keine Einträge gefunden"])
                
        except Exception as e:
            print(f"Fehler beim Laden von {source}: {e}")
            self.combo_items.configure(values=["Fehler beim Laden"])

    def apply_selection(self):
        selected = self.combo_items.get()
        if selected and selected not in ["Bitte warten...", "Keine Einträge gefunden", "Fehler beim Laden"]:
            self.callback(selected)
        self.destroy()

# --- Modal-Klassen ---

class EventRightsModal(ctk.CTkToplevel):
    # ... (Bleibt unverändert wie in deinem Code)
    def __init__(self, master, event_id):
        super().__init__(master)
        self.title("Event-Freigaben steuern")
        self.geometry("450x500")
        self.grab_set()
        self.event_id = event_id
        
        ctk.CTkLabel(self, text="Mitglieder für Bearbeitung freischalten", font=("Arial", 14, "bold")).pack(pady=10)
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=15)
        self.load_rights_list()

    def load_rights_list(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        try:
            mitglieder = supabase.table("mitglieder").select("id, vorname, nachname").execute().data
            freigaben = supabase.table("event_freigaben").select("mitglied_id").eq("event_id", self.event_id).execute().data
            freigeschaltete_ids = [f['mitglied_id'] for f in freigaben]
            
            for m in mitglieder:
                frame = ctk.CTkFrame(self.scroll)
                frame.pack(fill="x", pady=3, padx=2)
                name = f"{m['vorname']} {m['nachname']}"
                ctk.CTkLabel(frame, text=name, font=("Arial", 12)).pack(side="left", padx=10)
                
                ist_freigegeben = m['id'] in freigeschaltete_ids
                btn = ctk.CTkButton(
                    frame, 
                    text="Entziehen" if ist_freigegeben else "Freigeben",
                    fg_color="red" if ist_freigegeben else "green",
                    width=80,
                    command=lambda mid=m['id'], active=ist_freigegeben: self.toggle_permission(mid, active)
                )
                btn.pack(side="right", padx=5, pady=5)
        except Exception as e:
            print("Fehler bei Rechteverwaltung:", e)

    def toggle_permission(self, mitglied_id, active):
        if active:
            supabase.table("event_freigaben").delete().eq("event_id", self.event_id).eq("mitglied_id", mitglied_id).execute()
        else:
            supabase.table("event_freigaben").insert({"event_id": self.event_id, "mitglied_id": mitglied_id}).execute()
        self.load_rights_list()


class SchichtenManagementModal(ctk.CTkToplevel):
    # ... (Bleibt unverändert wie in deinem Code)
    def __init__(self, master, event_id, refresh_parent_callback):
        super().__init__(master)
        self.title("Schichtplan verwalten")
        self.geometry("600x600")
        self.grab_set()
        
        self.event_id = event_id
        self.refresh_parent = refresh_parent_callback
        self.mitglieder_daten = []
        
        add_frame = ctk.CTkFrame(self)
        add_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(add_frame, text="Neue Schicht zuteilen", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=5, padx=10, sticky="w")
        ctk.CTkLabel(add_frame, text="Mitglied:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.combo_mitglied = ctk.CTkComboBox(add_frame, values=[], width=250)
        self.combo_mitglied.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(add_frame, text="Stand / Aufgabe:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.ent_stand = ctk.CTkEntry(add_frame, placeholder_text="z.B. Bierstand, Kasse", width=250)
        self.ent_stand.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(add_frame, text="Von (HH:MM):").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.ent_von = ctk.CTkEntry(add_frame, placeholder_text="08:00", width=100)
        self.ent_von.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(add_frame, text="Bis (HH:MM):").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.ent_bis = ctk.CTkEntry(add_frame, placeholder_text="12:00", width=100)
        self.ent_bis.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        btn_add = ctk.CTkButton(add_frame, text="Schicht eintragen", fg_color="green", command=self.add_schicht)
        btn_add.grid(row=5, column=0, columnspan=2, pady=15, padx=10, sticky="ew")
        
        ctk.CTkLabel(self, text="Eingeteilte Schichten für dieses Event:", font=("Arial", 13, "bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=10)
        self.load_mitglieder_dropdown()
        self.load_current_schichten()

    def load_mitglieder_dropdown(self):
        try:
            res = supabase.table("mitglieder").select("id, vorname, nachname").order("nachname").execute()
            self.mitglieder_daten = res.data
            names = [f"{m['nachname']}, {m['vorname']}" for m in self.mitglieder_daten]
            self.combo_mitglied.configure(values=names)
            if names:
                self.combo_mitglied.set(names[0])
        except Exception as e:
            print("Fehler beim Laden der Mitglieder:", e)

    def load_current_schichten(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        try:
            res = supabase.table("event_schichten").select("*, mitglieder(vorname, nachname)").eq("event_id", self.event_id).order("von_zeit").execute()
            for s in res.data:
                frame = ctk.CTkFrame(self.scroll)
                frame.pack(fill="x", pady=3, padx=2)
                m_name = f"{s['mitglieder']['nachname']}, {s['mitglieder']['vorname']}"
                lbl_text = f"{s['stand_name']}\n{m_name} ({s['von_zeit'][:5]} - {s['bis_zeit'][:5]} Uhr)"
                ctk.CTkLabel(frame, text=lbl_text, font=("Arial", 12), justify="left").pack(side="left", padx=10, pady=5)
                ctk.CTkButton(frame, text="Entfernen", fg_color="red", width=80, command=lambda sid=s['id']: self.delete_schicht(sid)).pack(side="right", padx=10)
        except Exception as e:
            print("Fehler beim Laden der Schichten:", e)

    def add_schicht(self):
        selected_idx = self.combo_mitglied.get()
        mitglied_id = next((m['id'] for m in self.mitglieder_daten if f"{m['nachname']}, {m['vorname']}" == selected_idx), None)
        if not mitglied_id or not self.ent_stand.get() or not self.ent_von.get() or not self.ent_bis.get():
            messagebox.showwarning("Fehler", "Bitte alle Felder ausfüllen!")
            return
        data = {"event_id": self.event_id, "mitglied_id": mitglied_id, "stand_name": self.ent_stand.get(), "von_zeit": self.ent_von.get(), "bis_zeit": self.ent_bis.get()}
        try:
            supabase.table("event_schichten").insert(data).execute()
            self.load_current_schichten()
            self.refresh_parent()
            self.ent_von.delete(0, 'end'); self.ent_bis.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")

    def delete_schicht(self, schicht_id):
        try:
            supabase.table("event_schichten").delete().eq("id", schicht_id).execute()
            self.load_current_schichten()
            self.refresh_parent()
        except Exception as e:
            messagebox.showerror("Fehler", f"Löschen fehlgeschlagen: {e}")


class MaterialManagementModal(ctk.CTkToplevel):
    # ... (Bleibt unverändert wie in deinem Code)
    def __init__(self, master, event_id, refresh_parent_callback):
        super().__init__(master)
        self.title("Material verwalten")
        self.geometry("500x550")
        self.grab_set()
        
        self.event_id = event_id
        self.refresh_parent = refresh_parent_callback
        self.inventar_daten = []
        
        add_frame = ctk.CTkFrame(self)
        add_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(add_frame, text="Inventar hinzufügen", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10, padx=10, sticky="w")
        ctk.CTkLabel(add_frame, text="Gegenstand:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.combo_inventar = ctk.CTkComboBox(add_frame, values=["Lade..."])
        self.combo_inventar.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(add_frame, text="Menge:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.ent_menge = ctk.CTkEntry(add_frame, placeholder_text="z.B. 2")
        self.ent_menge.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        btn_add = ctk.CTkButton(add_frame, text="Hinzufügen", fg_color="green", command=self.add_material)
        btn_add.grid(row=3, column=0, columnspan=2, pady=15, padx=10, sticky="ew")
        
        ctk.CTkLabel(self, text="Aktuelle Liste:", font=("Arial", 12, "bold")).pack(anchor="w", padx=20)
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=15, pady=10)
        
        self.load_inventar_dropdown()
        self.load_current_material()

    def load_inventar_dropdown(self):
        try:
            res = supabase.table("inventar").select("id, name, menge_verfuegbar").order("name").execute()
            self.inventar_daten = res.data
            names = [item['name'] for item in self.inventar_daten]
            if names:
                self.combo_inventar.configure(values=names)
                self.combo_inventar.set(names[0])
            else:
                self.combo_inventar.configure(values=["Kein Inventar"])
        except Exception as e:
            print("Fehler beim Laden:", e)

    def load_current_material(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        try:
            res = supabase.table("event_material").select("*, inventar(name)").eq("event_id", self.event_id).execute()
            for m in res.data:
                frame = ctk.CTkFrame(self.scroll)
                frame.pack(fill="x", pady=3, padx=2)
                inv_name = m['inventar']['name'] if m['inventar'] else "Unbekannt"
                ctk.CTkLabel(frame, text=f"{inv_name} (Menge: {m['menge']})", font=("Arial", 12)).pack(side="left", padx=10, pady=5)
                ctk.CTkButton(frame, text="Entfernen", fg_color="red", width=80, command=lambda mid=m['id']: self.delete_material(mid)).pack(side="right", padx=10)
        except Exception as e:
            print("Fehler bei load_current_material:", e)

    def add_material(self):
        selected_name = self.combo_inventar.get()
        item = next((i for i in self.inventar_daten if i['name'] == selected_name), None)
        menge_str = self.ent_menge.get()

        if not item or not menge_str.isdigit():
            messagebox.showwarning("Fehler", "Bitte Artikel wählen und Menge als Zahl eingeben!")
            return
        
        menge_request = int(menge_str)
        if item['menge_verfuegbar'] < menge_request:
            messagebox.showerror("Fehler", f"Nicht genug Bestand! Verfügbar: {item['menge_verfuegbar']}")
            return

        try:
            neuer_bestand = item['menge_verfuegbar'] - menge_request
            supabase.table("inventar").update({"menge_verfuegbar": neuer_bestand}).eq("id", item['id']).execute()
            supabase.table("event_material").insert({"event_id": self.event_id, "inventar_id": item['id'], "menge": menge_request}).execute()
            
            self.load_current_material()
            self.refresh_parent()
            self.load_inventar_dropdown()
            self.ent_menge.delete(0, 'end')
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")

    def delete_material(self, material_id):
        try:
            mat_item = supabase.table("event_material").select("menge, inventar_id").eq("id", material_id).single().execute().data
            inv_item = supabase.table("inventar").select("menge_verfuegbar").eq("id", mat_item['inventar_id']).single().execute().data
            neuer_bestand = inv_item['menge_verfuegbar'] + mat_item['menge']
            
            supabase.table("inventar").update({"menge_verfuegbar": neuer_bestand}).eq("id", mat_item['inventar_id']).execute()
            supabase.table("event_material").delete().eq("id", material_id).execute()
            
            self.load_current_material()
            self.refresh_parent()
            self.load_inventar_dropdown()
        except Exception as e:
            messagebox.showerror("Fehler", f"Löschen fehlgeschlagen: {e}")


class EventEditModal(ctk.CTkToplevel):
    def __init__(self, master, event=None, callback=None):
        super().__init__(master)
        self.title("Event bearbeiten / erstellen")
        self.geometry("500x750")
        self.grab_set()
        self.event = event
        self.callback = callback
        
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 1. Name
        ctk.CTkLabel(scroll, text="Name der Veranstaltung:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10,0))
        self.ent_name = ctk.CTkEntry(scroll)
        self.ent_name.pack(fill="x", pady=5)
        
        # 2. Datum
        ctk.CTkLabel(scroll, text="Start-Datum (TT.MM.JJJJ):").pack(anchor="w", pady=(10,0))
        self.ent_start_d = ctk.CTkEntry(scroll)
        self.ent_start_d.pack(fill="x", pady=5)
        
        ctk.CTkLabel(scroll, text="End-Datum (TT.MM.JJJJ):").pack(anchor="w", pady=(10,0))
        self.ent_end_d = ctk.CTkEntry(scroll)
        self.ent_end_d.pack(fill="x", pady=5)
        
        # 3. Zeiten
        ctk.CTkLabel(scroll, text="Start-Uhrzeit (HH:MM):").pack(anchor="w", pady=(10,0))
        self.ent_start_t = ctk.CTkEntry(scroll)
        self.ent_start_t.pack(fill="x", pady=5)
        
        ctk.CTkLabel(scroll, text="End-Uhrzeit (HH:MM):").pack(anchor="w", pady=(10,0))
        self.ent_end_t = ctk.CTkEntry(scroll)
        self.ent_end_t.pack(fill="x", pady=5)
        
        ctk.CTkLabel(scroll, text="Treffen-Uhrzeit (HH:MM):").pack(anchor="w", pady=(10,0))
        self.ent_treff_t = ctk.CTkEntry(scroll)
        self.ent_treff_t.pack(fill="x", pady=5)
        
        # 4. Ort / Treffpunkt
        ctk.CTkLabel(scroll, text="Ort der Veranstaltung:").pack(anchor="w", pady=(10,0))
        self.ent_ort = ctk.CTkEntry(scroll)
        self.ent_ort.pack(fill="x", pady=5)
        
        ctk.CTkLabel(scroll, text="Treffpunkt:").pack(anchor="w", pady=(10,0))
        self.ent_treffpunkt = ctk.CTkEntry(scroll)
        self.ent_treffpunkt.pack(fill="x", pady=5)
        
        # --- NEU: 5. Ansprechperson mit Adressbuch ---
        ctk.CTkLabel(scroll, text="Ansprechperson:").pack(anchor="w", pady=(10,0))
        ansprech_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        ansprech_frame.pack(fill="x", pady=5)
        self.ent_ansprechperson = ctk.CTkEntry(ansprech_frame, placeholder_text="Name eingeben oder aus Adressbuch wählen")
        self.ent_ansprechperson.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(ansprech_frame, text="Aus Adressbuch", width=120, command=self.open_addressbook).pack(side="right")
        
        # 6. Bemerkungen
        ctk.CTkLabel(scroll, text="Bemerkungen / Tagesplan:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10,0))
        self.ent_bemerkungen = ctk.CTkTextbox(scroll, height=100)
        self.ent_bemerkungen.pack(fill="x", pady=5)
        
        # Daten füllen, falls wir bearbeiten
        if event:
            self.ent_name.insert(0, event['name'])
            self.ent_start_d.insert(0, format_date(event['start_datum']))
            self.ent_end_d.insert(0, format_date(event['end_datum']))
            self.ent_start_t.insert(0, event.get('uhrzeit_start', '')[:5])
            self.ent_end_t.insert(0, event.get('uhrzeit_ende', '')[:5])
            self.ent_treff_t.insert(0, event.get('uhrzeit_treffen', '')[:5])
            self.ent_ort.insert(0, event.get('ort', ''))
            self.ent_treffpunkt.insert(0, event.get('treffpunkt', ''))
            ansprech = event.get('ansprechperson')
            self.ent_ansprechperson.insert(0, str(ansprech) if ansprech else "")
            self.ent_bemerkungen.insert("0.0", event.get('bemerkungen', ''))
            
        ctk.CTkButton(scroll, text="Speichern", fg_color="green", command=self.save_event, height=40).pack(fill="x", pady=30)    
        
    def open_addressbook(self):
        # Öffnet das Adressbuch-Modal und übergibt die set_ansprechperson als Callback
        AddressBookModal(self, self.set_ansprechperson)
        
    def set_ansprechperson(self, name):
        # Wird vom Adressbuch aufgerufen, wenn ein Name ausgewählt wurde
        self.ent_ansprechperson.delete(0, 'end')
        self.ent_ansprechperson.insert(0, name)

    def save_event(self):
        start_dt = parse_flexible_date(self.ent_start_d.get())
        end_dt = parse_flexible_date(self.ent_end_d.get())
        
        if isinstance(start_dt, str) or isinstance(end_dt, str):
            messagebox.showerror("Fehler", "Bitte Datum im Format TT.MM.JJJJ eingeben!")
            return

        data = {
            "name": self.ent_name.get(),
            "start_datum": start_dt.strftime("%Y-%m-%d"),
            "end_datum": end_dt.strftime("%Y-%m-%d"),
            "uhrzeit_start": self.ent_start_t.get(),
            "uhrzeit_ende": self.ent_end_t.get(),
            "uhrzeit_treffen": self.ent_treff_t.get(),
            "ort": self.ent_ort.get(),
            "treffpunkt": self.ent_treffpunkt.get(),
            "ansprechperson": self.ent_ansprechperson.get(), # Neu speichern
            "bemerkungen": self.ent_bemerkungen.get("0.0", "end").strip()
        }
        
        try:
            if self.event:
                supabase.table("events").update(data).eq("id", self.event['id']).execute()
            else:
                supabase.table("events").insert(data).execute()
            
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Fehler", f"Speichern fehlgeschlagen: {e}")


class EventsWindow(ctk.CTkFrame):
    def __init__(self, master, role, aktuelle_mitglieder_id=1):
        super().__init__(master)
        # 1. Hier 'role' in 'rolle' speichern
        self.rolle = role 
        self.user_id = aktuelle_mitglieder_id
        self.selected_event = None
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)
        
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(self.left_frame, text="Veranstaltungen", font=("Arial", 18, "bold")).pack(pady=10)
        if self.rolle in ["admin", "vorstand"]:
            ctk.CTkButton(self.left_frame, text="+ Neues Event", fg_color="green", command=self.open_create_modal).pack(pady=5, padx=10, fill="x")
        self.event_scroll = ctk.CTkScrollableFrame(self.left_frame)
        self.event_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.right_frame = ctk.CTkScrollableFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.load_events_list()

    def check_edit_permission(self, event_id):
        if self.rolle in ["admin", "vorstand"]: return True
        res = supabase.table("event_freigaben").select("*").eq("event_id", event_id).eq("mitglied_id", self.user_id).execute()
        return len(res.data) > 0

    def load_events_list(self):
        for w in self.event_scroll.winfo_children(): w.destroy()
        res = supabase.table("events").select("*").order("start_datum").execute()
        for ev in res.data:
            datum_str = format_date(ev['start_datum'])
            ctk.CTkButton(
                self.event_scroll, 
                text=f"{ev['name']}\n{datum_str}", 
                command=lambda e=ev: self.show_event_details(e)
            ).pack(fill="x", pady=4)

    def show_event_details(self, event):
        self.selected_event = event
        for w in self.right_frame.winfo_children(): w.destroy()
        datum_str = format_date(event['start_datum'])
        has_edit_rights = self.check_edit_permission(event['id'])
        
        ctk.CTkLabel(self.right_frame, text=event['name'], font=("Arial", 22, "bold")).pack(anchor="w", pady=5)
        
        # Ansprechperson in den Info-Text mit aufnehmen (falls vorhanden)
        ansprechperson = event.get('ansprechperson', '')
        ansprech_text = f"\n👤 Ansprechperson: {ansprechperson}" if ansprechperson else ""
        
        info_text = f"📅 Datum: {datum_str} bis {format_date(event['end_datum'])}\n📍 Ort: {event['ort']}\n⏰ Beginn: {event['uhrzeit_start']} Uhr\n Ende: {event['uhrzeit_ende']} Uhr\n📍 Treffpunkt: {event['treffpunkt']} um {event['uhrzeit_treffen']} Uhr{ansprech_text}"
        ctk.CTkLabel(self.right_frame, text=info_text, font=("Arial", 14), justify="left").pack(anchor="w", pady=10)
        
        export_bar = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        export_bar.pack(fill="x", pady=5)
        ctk.CTkButton(export_bar, text="📄 PDF Export", fg_color="#4F4F4F", width=100, command=self.export_as_pdf).pack(side="left", padx=2)
        ctk.CTkButton(export_bar, text="💬 WhatsApp", fg_color="#25D366", text_color="white", width=100, command=self.share_whatsapp).pack(side="left", padx=2)
        ctk.CTkButton(export_bar, text="✉️ E-Mail", fg_color="#0078D4", width=100, command=self.share_email).pack(side="left", padx=2)
        
        self.render_rsvp_section(event['id'])
        
        # NEU: Allgemeine Rückmeldungsübersicht (Wer hat sich wie gemeldet)
        self.render_all_rsvps(event['id'])
        
        ctk.CTkLabel(self.right_frame, text="⛺ Schichtplan / Einteilung", font=("Arial", 16, "bold")).pack(anchor="w", pady=(20, 5))
        self.render_schichten(event['id'])
        ctk.CTkLabel(self.right_frame, text="📦 Benötigtes Material", font=("Arial", 16, "bold")).pack(anchor="w", pady=(20, 5))
        self.render_material(event['id'])
        
        if has_edit_rights:
            admin_bar = ctk.CTkFrame(self.right_frame, fg_color="transparent")
            admin_bar.pack(fill="x", pady=20)
            ctk.CTkButton(admin_bar, text="Event Bearbeiten", fg_color="#1f538d", command=self.open_edit_modal).pack(side="left", padx=5)
            ctk.CTkButton(admin_bar, text="Schichten planen", fg_color="#2b7a78", command=self.open_manage_schichten_modal).pack(side="left", padx=5)
            ctk.CTkButton(admin_bar, text="Material planen", fg_color="#4F4F4F", command=self.open_manage_material_modal).pack(side="left", padx=5)
            if self.rolle in ["admin", "vorstand"]:
                ctk.CTkButton(admin_bar, text="Rechte verwalten", fg_color="#b8860b", command=self.open_rights_modal).pack(side="left", padx=5)
                ctk.CTkButton(admin_bar, text="Event Löschen", fg_color="red", command=self.delete_event).pack(side="right", padx=5)

    def open_manage_material_modal(self): MaterialManagementModal(self, self.selected_event['id'], lambda: self.show_event_details(self.selected_event))
    def open_manage_schichten_modal(self): SchichtenManagementModal(self, self.selected_event['id'], lambda: self.show_event_details(self.selected_event))
    def open_rights_modal(self): EventRightsModal(self, self.selected_event['id'])
    def open_create_modal(self): EventEditModal(self, None, self.load_events_list)
    def open_edit_modal(self): EventEditModal(self, self.selected_event, lambda: self.refresh_after_edit())

    def refresh_after_edit(self):
        self.load_events_list()
        res = supabase.table("events").select("*").eq("id", self.selected_event['id']).execute()
        if res.data: self.show_event_details(res.data[0])

    def delete_event(self):
        if messagebox.askyesno("Löschen", f"Wirklich löschen?"):
            supabase.table("events").delete().eq("id", self.selected_event['id']).execute()
            self.selected_event = None
            for w in self.right_frame.winfo_children(): w.destroy()
            self.load_events_list()

    def render_rsvp_section(self, event_id):
        from tkinter import simpledialog # Stelle sicher, dass dies oben im Skript oder hier importiert ist
        
        rsvp_frame = ctk.CTkFrame(self.right_frame)
        rsvp_frame.pack(fill="x", pady=10)

        # 1. Datenbank: Aktuellen Status abrufen (nur wenn wir eine ID haben)
        current_status = None
        if self.user_id:
            res = supabase.table("event_rsvps").select("status").eq("event_id", event_id).eq("mitglied_id", self.user_id).execute()
            if res.data and len(res.data) > 0:
                current_status = res.data[0]['status']

        
        def set_rsvp(status):
            # HIER DIE ECHTE DATENBANK-ID EINTRAGEN (NICHT DIE MITGLIEDSNUMMER!)
            # Laut deinem CSV ist die ID in der Datenbank die 7
            ADMIN_DB_ID = 7 
            
            target_id = self.user_id
            
            # Wenn Admin und keine ID, nimm die Admin-DB-ID
            if self.rolle == "admin" and target_id is None:
                target_id = ADMIN_DB_ID
            
            # Sicherheitscheck
            if target_id is None:
                messagebox.showerror("Fehler", "Keine gültige Mitglieds-ID gefunden.")
                return

            # A) Alles alte löschen
            supabase.table("event_rsvps").delete().eq("event_id", event_id).eq("mitglied_id", target_id).execute()
            
            # B) Neu einfügen (Jetzt mit der ID 7, die existiert!)
            supabase.table("event_rsvps").insert({
                "event_id": event_id, 
                "mitglied_id": target_id, 
                "status": status
            }).execute()
            
            # C) Oberfläche aktualisieren
            self.show_event_details(self.selected_event)

        # 3. Buttons rendern
        statuses = [("Kann", "kann", "green"), ("Kann nicht", "kann nicht", "red"), ("Unsicher", "unsicher", "orange")]
        
        for label, db_val, color in statuses:
            # Farbe bestimmen (Nur markiert, wenn dies der aktuelle Status ist)
            btn_color = color if current_status == db_val else "#3a3a3a"
            
            ctk.CTkButton(
                rsvp_frame, 
                text=label, 
                width=80, 
                fg_color=btn_color, 
                hover_color=color, 
                command=lambda v=db_val: set_rsvp(v)
            ).pack(side="left", padx=5, pady=10)
        
    # --- NEU: Übersicht aller Rückmeldungen ---
    def render_all_rsvps(self, event_id):
        print(f"[DEBUG] Aktuelle User-ID: {self.user_id}")
        ctk.CTkLabel(self.right_frame, text="📋 Bisherige Rückmeldungen", font=("Arial", 16, "bold")).pack(anchor="w", pady=(20, 5))
        frame = ctk.CTkFrame(self.right_frame)
        frame.pack(fill="x", pady=5)
        
        try:
            # Wir laden die Daten
            res = supabase.table("event_rsvps").select("status, mitglieder(vorname, nachname)").eq("event_id", event_id).execute()
            
            kann_liste = []
            kann_nicht_liste = []
            unsicher_liste = []
            
            for r in res.data:
                # Prüfen, ob eine Verknüpfung zu 'mitglieder' existiert
                m_data = r.get('mitglieder')
                if m_data:
                    name = f"{m_data['vorname']} {m_data['nachname']}"
                else:
                    # Fallback für Admins oder gelöschte Mitglieder
                    name = "Admin / Unbekannt"
                
                if r['status'] == 'kann':
                    kann_liste.append(name)
                elif r['status'] == 'kann nicht':
                    kann_nicht_liste.append(name)
                elif r['status'] == 'unsicher':
                    unsicher_liste.append(name)
                    
            if not res.data:
                ctk.CTkLabel(frame, text="Noch keine Rückmeldungen vorhanden.", font=("Arial", 12, "italic")).pack(pady=10, padx=10, anchor="w")
                return

            # Anzeige... (bleibt wie gehabt, nutzt jetzt aber unsere sichere Namensvariable)
            if kann_liste:
                ctk.CTkLabel(frame, text=f"✅ Zugesagt ({len(kann_liste)}):", font=("Arial", 12, "bold"), text_color="green").pack(anchor="w", padx=10, pady=(10, 0))
                ctk.CTkLabel(frame, text=", ".join(kann_liste), font=("Arial", 12), wraplength=400).pack(anchor="w", padx=20, pady=(0, 5))
                
            if unsicher_liste:
                ctk.CTkLabel(frame, text=f"🤔 Unsicher ({len(unsicher_liste)}):", font=("Arial", 12, "bold"), text_color="orange").pack(anchor="w", padx=10, pady=(5, 0))
                ctk.CTkLabel(frame, text=", ".join(unsicher_liste), font=("Arial", 12), wraplength=400).pack(anchor="w", padx=20, pady=(0, 5))

            if kann_nicht_liste:
                ctk.CTkLabel(frame, text=f"❌ Abgesagt ({len(kann_nicht_liste)}):", font=("Arial", 12, "bold"), text_color="red").pack(anchor="w", padx=10, pady=(5, 0))
                ctk.CTkLabel(frame, text=", ".join(kann_nicht_liste), font=("Arial", 12), wraplength=400).pack(anchor="w", padx=20, pady=(0, 10))
                
        except Exception as e:
            ctk.CTkLabel(frame, text="Fehler beim Laden der Rückmeldungen.", text_color="red").pack(pady=10)
            print("Fehler in render_all_rsvps:", e)

    def render_schichten(self, event_id):
        frame = ctk.CTkFrame(self.right_frame); frame.pack(fill="x", pady=5)
        res = supabase.table("event_schichten").select("*, mitglieder(vorname, nachname)").eq("event_id", event_id).execute()
        if not res.data: ctk.CTkLabel(frame, text="Noch keine Schichten.", font=("Arial", 12, "italic")).pack(pady=10)
        else:
            for s in res.data: ctk.CTkLabel(frame, text=f"• {s['stand_name']}: {s['mitglieder']['vorname']} {s['mitglieder']['nachname']} ({s['von_zeit'][:5]} - {s['bis_zeit'][:5]} Uhr)", font=("Arial", 13)).pack(anchor="w", padx=10, pady=2)

    def render_material(self, event_id):
        frame = ctk.CTkFrame(self.right_frame); frame.pack(fill="x", pady=5)
        res = supabase.table("event_material").select("*, inventar(name)").eq("event_id", event_id).execute()
        if not res.data: ctk.CTkLabel(frame, text="Kein Material angefordert.", font=("Arial", 12, "italic")).pack(pady=10)
        else:
            for mat in res.data: ctk.CTkLabel(frame, text=f"• {mat['inventar']['name']} (Menge: {mat['menge']})", font=("Arial", 13)).pack(anchor="w", padx=10, pady=2)

    def generate_event_summary_text(self):
        ev = self.selected_event
        ansprech_text = f"\n👤 Ansprechperson: {ev.get('ansprechperson', '')}" if ev.get('ansprechperson', '') else ""
        text = f"📢 *EVENT-ÜBERSICHT: {ev['name']}*\n📅 Datum: {ev['start_datum']} bis {ev['end_datum']}\n📍 Ort: {ev['ort']}\n⏰ Beginn: {ev['uhrzeit_start'][:5]} Uhr | Treffen: {ev['uhrzeit_treffen'][:5]} Uhr ({ev['treffpunkt']}){ansprech_text}\n\n⛺ *SCHICHTPLAN:*\n"
        schichten = supabase.table("event_schichten").select("*, mitglieder(vorname, nachname)").eq("event_id", ev['id']).execute().data
        for s in schichten: text += f"- {s['stand_name']}: {s['mitglieder']['vorname']} {s['mitglieder']['nachname']} ({s['von_zeit'][:5]}-{s['bis_zeit'][:5]} Uhr)\n"
        text += "\n📦 *BENÖTIGTES MATERIAL:*\n"
        material = supabase.table("event_material").select("*, inventar(name)").eq("event_id", ev['id']).execute().data
        for m in material: text += f"- {m['inventar']['name']} (Menge: {m['menge']})\n"
        return text

    def share_whatsapp(self):
        raw_text = self.generate_event_summary_text()
        self.clipboard_clear(); self.clipboard_append(raw_text)
        webbrowser.open(f"https://wa.me/?text={quote(raw_text)}")
        messagebox.showinfo("WhatsApp", "In Zwischenablage kopiert!")

    def share_email(self):
        raw_text = self.generate_event_summary_text()
        webbrowser.open(f"mailto:?subject=Einsatzplan: {self.selected_event['name']}&body={quote(raw_text.replace('*', ''))}")

    def export_as_pdf(self):
        ev = self.selected_event
        filename = f"Event_{ev['name'].replace(' ', '_')}_Plan.pdf"
        try:
            doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=20, textColor=colors.HexColor("#1f538d"))
            h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=16, spaceBefore=15, spaceAfter=10, textColor=colors.HexColor("#2b7a78"))
            body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, spaceAfter=6)
            story = [Paragraph(f"Veranstaltungsplan: {ev['name']}", title_style), Spacer(1, 10)]
            
            ansprechperson = ev.get('ansprechperson', '-')
            
            data_basis = [
                [Paragraph("<b>Datum:</b>", body_style), Paragraph(f"{ev['start_datum']} bis {ev['end_datum']}", body_style)], 
                [Paragraph("<b>Ort:</b>", body_style), Paragraph(ev['ort'], body_style)],
                [Paragraph("<b>Ansprechperson:</b>", body_style), Paragraph(ansprechperson, body_style)]
            ]
            story.append(Table(data_basis, colWidths=[120, 380]))
            doc.build(story)
            messagebox.showinfo("PDF", "PDF erstellt!")
        except Exception as e: messagebox.showerror("Fehler", f"PDF-Erstellung fehlgeschlagen: {e}")
        
    def check_and_return_material(self, event):
        end_datum = datetime.strptime(event['end_datum'], "%Y-%m-%d")
        
        if end_datum < datetime.now():
            material_liste = supabase.table("event_material").select("*").eq("event_id", event['id']).execute().data
            if material_liste:
                for item in material_liste:
                    inv = supabase.table("inventar").select("menge_verfuegbar").eq("id", item['inventar_id']).single().execute().data
                    neuer_bestand = inv['menge_verfuegbar'] + item['menge']
                    supabase.table("inventar").update({"menge_verfuegbar": neuer_bestand}).eq("id", item['inventar_id']).execute()
                    supabase.table("event_material").delete().eq("id", item['id']).execute()
                self.show_event_details(event)