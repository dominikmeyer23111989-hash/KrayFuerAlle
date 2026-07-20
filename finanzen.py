import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar
from supabase import create_client
from pdf_export import export_kassenbuch_pdf

URL = "https://ythubjdnercyeyfedsam.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl0aHViamRuZXJjeWV5ZmVkc2FtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MjgzNTgsImV4cCI6MjA5OTEwNDM1OH0.loeU2abylobRmPJvuHwdZLbHNyTL4qlKOtIRk-qZp34"
supabase = create_client(URL, KEY)

# =========================================================================
# CLASS 1: NUr KASSENBUCH & BERICHTE
# =========================================================================
class FinanceFrame(ctk.CTkFrame):
    def __init__(self, parent, current_user_name="Unbekannt"):
        super().__init__(parent)
        self.current_user_name = current_user_name
        
        self.selected_year = 2026
        self.selected_month = datetime.now().month
        self.months_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Die Tabelle bekommt den meisten Platz

        self.setup_kassenbuch_layout()
        self.refresh_kassenbuch()

    def setup_kassenbuch_layout(self):
        # Filter-Leiste
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(filter_frame, text="Kassenbuch filtern:", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=5)
        
        self.year_select = ctk.CTkComboBox(filter_frame, values=[str(y) for y in range(2024, 2031)], width=90, command=self.on_filter_changed)
        self.year_select.set(str(self.selected_year))
        self.year_select.pack(side="left", padx=5)

        self.month_select = ctk.CTkComboBox(filter_frame, values=self.months_names, width=120, command=self.on_filter_changed)
        self.month_select.set(self.months_names[self.selected_month - 1])
        self.month_select.pack(side="left", padx=5)

        # Buttons
        ctk.CTkButton(filter_frame, text="PDF Export 📄", fg_color="#34495e", command=self.export_pdf).pack(side="right", padx=5)
        ctk.CTkButton(filter_frame, text="+ Neue Buchung", fg_color="#2ecc71", hover_color="#27ae60", command=self.open_add_dialog).pack(side="right", padx=5)

        # Karten für Zahlen
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        stats_frame.grid_columnconfigure((0,1,2), weight=1)

        self.card_in = ctk.CTkFrame(stats_frame, fg_color="#1e272c", border_color="#2ecc71", border_width=1)
        self.card_in.grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkLabel(self.card_in, text="Einnahmen (Monat)").pack(pady=2)
        self.lbl_in = ctk.CTkLabel(self.card_in, text="0,00 €", font=("Arial", 18, "bold"), text_color="#2ecc71")
        self.lbl_in.pack(pady=5)

        self.card_out = ctk.CTkFrame(stats_frame, fg_color="#1e272c", border_color="#e74c3c", border_width=1)
        self.card_out.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(self.card_out, text="Ausgaben (Monat)").pack(pady=2)
        self.lbl_out = ctk.CTkLabel(self.card_out, text="0,00 €", font=("Arial", 18, "bold"), text_color="#e74c3c")
        self.lbl_out.pack(pady=5)

        self.card_total = ctk.CTkFrame(stats_frame, fg_color="#1e272c", border_color="#3498db", border_width=1)
        self.card_total.grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkLabel(self.card_total, text="Kassenbestand (Iststand)").pack(pady=2)
        self.lbl_total = ctk.CTkLabel(self.card_total, text="0,00 €", font=("Arial", 18, "bold"), text_color="#3498db")
        self.lbl_total.pack(pady=5)

        # Treeview Tabelle
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("datum", "typ", "betrag", "kategorie", "person", "zweck", "erfasser")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("datum", text="Datum")
        self.tree.heading("typ", text="Typ")
        self.tree.heading("betrag", text="Betrag")
        self.tree.heading("kategorie", text="Kategorie")
        self.tree.heading("person", text="Zahler/Empfänger")
        self.tree.heading("zweck", text="Verwendungszweck")
        self.tree.heading("erfasser", text="Erfasst von")
        
        self.tree.column("datum", width=90, anchor="center")
        self.tree.column("typ", width=80, anchor="center")
        self.tree.column("betrag", width=90, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def on_filter_changed(self, event=None):
        self.selected_year = int(self.year_select.get())
        self.selected_month = self.months_names.index(self.month_select.get()) + 1
        self.refresh_kassenbuch()

    def refresh_kassenbuch(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        _, last_day = calendar.monthrange(self.selected_year, self.selected_month)
        start_date = f"{self.selected_year}-{self.selected_month:02d}-01"
        end_date = f"{self.selected_year}-{self.selected_month:02d}-{last_day}"

        try:
            res = supabase.table("kassenbuch").select("*").gte("buchungs_datum", start_date).lte("buchungs_datum", end_date).order("buchungs_datum", desc=True).execute()
            
            einnahmen_monat = 0.0
            ausgaben_monat = 0.0

            for row in res.data:
                betrag = float(row["betrag"])
                if row["typ"] == "Einnahme":
                    einnahmen_monat += betrag
                    display_betrag = f"+{betrag:.2f} €"
                else:
                    ausgaben_monat += betrag
                    display_betrag = f"-{betrag:.2f} €"

                self.tree.insert("", "end", values=(
                    datetime.strptime(row["buchungs_datum"], "%Y-%m-%d").strftime("%d.%m.%Y"),
                    row["typ"], display_betrag, row["kategorie"], row["person"], row["verwendungszweck"] or "-", row["entgegengenommen_von"]
                ))

            # Kassenbestand (Iststand)
            total_res = supabase.table("kassenbuch").select("typ", "betrag").execute()
            self.gesamt_iststand = sum(float(r["betrag"]) if r["typ"] == "Einnahme" else -float(r["betrag"]) for r in total_res.data)

            self.lbl_in.configure(text=f"{einnahmen_monat:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            self.lbl_out.configure(text=f"{ausgaben_monat:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
            self.lbl_total.configure(text=f"{self.gesamt_iststand:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))

        except Exception as e:
            print("Fehler beim Laden des Kassenbuchs:", e)

    def export_pdf(self):
        daten = []
        for child in self.tree.get_children():
            row = self.tree.item(child, "values")
            daten.append({
                "datum": row[0],
                "typ": row[1],
                "betrag": row[2].replace("+", "").replace("-", "").replace(" €", "").replace(",", "."),
                "kategorie": row[3],
                "person": row[4],
                "zweck": row[5]
            })
        export_kassenbuch_pdf(daten, self.selected_year, self.month_select.get(), self.gesamt_iststand)

    def open_add_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Neue Buchung")
        dialog.geometry("400x500")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Kassenbucheintrag", font=("Arial", 16, "bold")).pack(pady=15)

        ctk.CTkLabel(dialog, text="Typ:").pack(anchor="w", padx=40)
        typ_var = ctk.StringVar(value="Einnahme")
        ctk.CTkSegmentedButton(dialog, values=["Einnahme", "Ausgabe"], variable=typ_var).pack(pady=5)

        ctk.CTkLabel(dialog, text="Betrag (€):").pack(anchor="w", padx=40)
        entry_betrag = ctk.CTkEntry(dialog, placeholder_text="z.B. 45.00")
        entry_betrag.pack(pady=5, fill="x", padx=40)

        ctk.CTkLabel(dialog, text="Zahler / Empfänger:").pack(anchor="w", padx=40)
        entry_person = ctk.CTkEntry(dialog, placeholder_text="Name")
        entry_person.pack(pady=5, fill="x", padx=40)

        ctk.CTkLabel(dialog, text="Kategorie:").pack(anchor="w", padx=40)
        combo_kat = ctk.CTkComboBox(dialog, values=["Spende", "Miete", "Veranstaltung", "Büromaterial", "Mitgliedsbeitrag", "Sonstiges"])
        combo_kat.pack(pady=5, fill="x", padx=40)

        ctk.CTkLabel(dialog, text="Verwendungszweck:").pack(anchor="w", padx=40)
        entry_zweck = ctk.CTkEntry(dialog, placeholder_text="Details")
        entry_zweck.pack(pady=5, fill="x", padx=40)

        def speichern():
            try:
                betrag = round(float(entry_betrag.get().replace(",", ".")), 2)
                neue_buchung = {
                    "buchungs_datum": datetime.now().strftime("%Y-%m-%d"),
                    "typ": typ_var.get(),
                    "betrag": betrag,
                    "person": entry_person.get().strip(),
                    "kategorie": combo_kat.get(),
                    "verwendungszweck": entry_zweck.get().strip() or None,
                    "entgegengenommen_von": self.current_user_name
                }
                supabase.table("kassenbuch").insert(neue_buchung).execute()
                self.refresh_kassenbuch()
                dialog.destroy()
                messagebox.showinfo("Erfolg", "Buchung verbucht!")
            except Exception as e:
                messagebox.showerror("Fehler", f"Eingabe prüfen:\n{e}")

        ctk.CTkButton(dialog, text="Buchen", fg_color="#2e3b4e", command=speichern).pack(pady=20)


# =========================================================================
# CLASS 2: NUr MITGLIEDSBEITRÄGE
# =========================================================================
class BeitragFrame(ctk.CTkFrame):
    def __init__(self, parent, current_user_name="Unbekannt"):
        super().__init__(parent)
        self.current_user_name = current_user_name
        
        self.selected_year = 2026
        self.selected_month = datetime.now().month
        self.months_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Tabelle bekommt den meisten Platz

        self.setup_beitraege_layout()
        self.refresh_beitraege()

    def setup_beitraege_layout(self):
        # Obere Filter- & Einstellungsleiste
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(top_frame, text="Beitragszeitraum:", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=5)

        self.year_select = ctk.CTkComboBox(top_frame, values=[str(y) for y in range(2024, 2031)], width=90, command=self.on_filter_changed)
        self.year_select.set(str(self.selected_year))
        self.year_select.pack(side="left", padx=5)

        self.month_select = ctk.CTkComboBox(top_frame, values=self.months_names, width=120, command=self.on_filter_changed)
        self.month_select.set(self.months_names[self.selected_month - 1])
        self.month_select.pack(side="left", padx=5)

        # Gebühren-Button
        self.btn_set_rates = ctk.CTkButton(top_frame, text="Gebühren verwalten ⚙️", width=150, fg_color="#7f8c8d", command=self.open_rates_dialog)
        self.btn_set_rates.pack(side="left", padx=15)

        # Erinnerungs- & Bezahl-Buttons
        self.btn_remind = ctk.CTkButton(top_frame, text="Ausstehende mahnen ✉️", fg_color="#d35400", hover_color="#e67e22", command=self.send_reminders)
        self.btn_remind.pack(side="right", padx=5)

        self.btn_pay = ctk.CTkButton(top_frame, text="Als bezahlt markieren ✓", fg_color="#2ecc71", hover_color="#27ae60", command=self.mark_as_paid)
        self.btn_pay.pack(side="right", padx=5)

        # Tabelle für Beitrags-Soll/Ist
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("id", "name", "beitragstyp", "beitritt", "soll", "status", "zahldatum")
        self.tree_beitraege = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree_beitraege.heading("id", text="ID")
        self.tree_beitraege.heading("name", text="Name")
        self.tree_beitraege.heading("beitragstyp", text="Beitragsklasse")
        self.tree_beitraege.heading("beitritt", text="Beitrittsdatum")
        self.tree_beitraege.heading("soll", text="Soll-Betrag")
        self.tree_beitraege.heading("status", text="Status")
        self.tree_beitraege.heading("zahldatum", text="Bezahlt am")

        self.tree_beitraege.column("id", width=50, anchor="center")
        self.tree_beitraege.column("status", width=120, anchor="center")
        self.tree_beitraege.column("soll", width=100, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_beitraege.yview)
        self.tree_beitraege.configure(yscrollcommand=scrollbar.set)
        self.tree_beitraege.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def on_filter_changed(self, event=None):
        self.selected_year = int(self.year_select.get())
        self.selected_month = self.months_names.index(self.month_select.get()) + 1
        self.refresh_beitraege()

    def refresh_beitraege(self):
        for item in self.tree_beitraege.get_children():
            self.tree_beitraege.delete(item)

        try:
            # 1. Beitragssätze abrufen
            rates_res = supabase.table("beitragssaetze").select("*").execute()
            preise = {r["typ"]: float(r["betrag"]) for r in rates_res.data}

            # 2. Alle Mitglieder holen
            mitglieder_res = supabase.table("mitglieder").select("id", "vorname", "nachname", "beitritts_datum", "beitrags_typ").execute()

            # 3. Bereits bezahlte Beiträge holen
            zeitraum = f"{self.selected_year}-{self.selected_month:02d}"
            zahlungen_res = supabase.table("kassenbuch").select("mitglied_id", "buchungs_datum").eq("beitrags_zeitraum", zeitraum).execute()
            bezahlte_ids = {z["mitglied_id"]: z["buchungs_datum"] for z in zahlungen_res.data}

            for m in mitglieder_res.data:
                m_id = m["id"]
                name = f"{m['vorname']} {m['nachname']}"
                beitrags_typ = m["beitrags_typ"] or "Mitglied"
                beitritt_str = m["beitritts_datum"] or "2026-01-01"

                # 15.-des-Monats-Regel anwenden
                beitritt_date = datetime.strptime(beitritt_str, "%Y-%m-%d").date()
                ziel_date_start = datetime(self.selected_year, self.selected_month, 1).date()

                if beitritt_date > ziel_date_start:
                    if beitritt_date.year == self.selected_year and beitritt_date.month == self.selected_month:
                        if beitritt_date.day > 15:
                            continue # Nach dem 15. -> Erst Folgemonat
                    else:
                        continue

                soll_betrag = preise.get(beitrags_typ, 15.00)

                if m_id in bezahlte_ids:
                    status = "Bezahlt ✓"
                    zahldatum = datetime.strptime(bezahlte_ids[m_id], "%Y-%m-%d").strftime("%d.%m.%Y")
                else:
                    status = "Ausstehend ❌"
                    zahldatum = "-"

                self.tree_beitraege.insert("", "end", values=(
                    m_id, name, beitrags_typ, beitritt_date.strftime("%d.%m.%Y"), f"{soll_betrag:.2f} €", status, zahldatum
                ))

        except Exception as e:
            print("Fehler beim Laden der Beiträge:", e)

    def mark_as_paid(self):
        selected = self.tree_beitraege.selection()
        if not selected:
            messagebox.showwarning("Warnung", "Bitte wähle ein Mitglied aus der Liste aus!")
            return

        item_data = self.tree_beitraege.item(selected[0], "values")
        m_id = item_data[0]
        name = item_data[1]
        soll_str = item_data[4].replace(" €", "")
        status = item_data[5]

        if "Bezahlt" in status:
            messagebox.showinfo("Info", "Dieses Mitglied hat bereits bezahlt.")
            return

        zeitraum = f"{self.selected_year}-{self.selected_month:02d}"
        
        try:
            neue_buchung = {
                "buchungs_datum": datetime.now().strftime("%Y-%m-%d"),
                "typ": "Einnahme",
                "betrag": float(soll_str),
                "person": name,
                "kategorie": "Mitgliedsbeitrag",
                "verwendungszweck": f"Beitrag für {self.month_select.get()} {self.selected_year}",
                "entgegengenommen_von": self.current_user_name,
                "mitglied_id": int(m_id),
                "beitrags_zeitraum": zeitraum
            }
            supabase.table("kassenbuch").insert(neue_buchung).execute()
            messagebox.showinfo("Erfolg", f"Beitrag für {name} erfolgreich verbucht!")
            self.refresh_beitraege()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Buchen:\n{e}")

    def send_reminders(self):
        unbezahlt = []
        for child in self.tree_beitraege.get_children():
            row = self.tree_beitraege.item(child, "values")
            if "Ausstehend" in row[5]:
                unbezahlt.append(f"• {row[1]} ({row[2]} - {row[4]})")

        if not unbezahlt:
            messagebox.showinfo("Erinnerung", "Hervorragend! Alle Beiträge für diesen Monat wurden bezahlt!")
            return

        liste = "\n".join(unbezahlt)
        messagebox.showinfo("Ausstehende Beiträge", f"Folgende Mitglieder müssen noch bezahlen:\n\n{liste}")

    def open_rates_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Gebühren verwalten")
        dialog.geometry("350x300")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Beitragshöhe festlegen", font=("Arial", 16, "bold")).pack(pady=15)

        inputs = {}
        try:
            rates_res = supabase.table("beitragssaetze").select("*").execute()
            aktuelle_preise = {r["typ"]: float(r["betrag"]) for r in rates_res.data}
        except Exception:
            aktuelle_preise = {"Mitglied": 15.0, "Familie": 30.0, "Kinder": 5.0}

        for typ in ["Mitglied", "Familie", "Kinder"]:
            frame = ctk.CTkFrame(dialog, fg_color="transparent")
            frame.pack(pady=5, fill="x", padx=30)
            ctk.CTkLabel(frame, text=f"{typ}:").pack(side="left")
            entry = ctk.CTkEntry(frame, width=100)
            entry.insert(0, f"{aktuelle_preise.get(typ, 0.0):.2f}")
            entry.pack(side="right")
            inputs[typ] = entry

        def speichern():
            try:
                for typ, entry in inputs.items():
                    neuer_preis = round(float(entry.get().replace(",", ".")), 2)
                    supabase.table("beitragssaetze").upsert({"typ": typ, "betrag": neuer_preis}, on_conflict="typ").execute()
                messagebox.showinfo("Erfolg", "Beitragssätze erfolgreich aktualisiert!")
                self.refresh_beitraege()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Fehler", "Bitte gib überall gültige Zahlen ein!")

        ctk.CTkButton(dialog, text="Speichern", fg_color="#2ecc71", command=speichern).pack(pady=20)