import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import calendar
from supabase import create_client
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

URL = "https://ythubjdnercyeyfedsam.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl0aHViamRuZXJjeWV5ZmVkc2FtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MjgzNTgsImV4cCI6MjA5OTEwNDM1OH0.loeU2abylobRmPJvuHwdZLbHNyTL4qlKOtIRk-qZp34"
supabase = create_client(URL, KEY)

class FinanceChartsFrame(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.selected_year = 2026
        self.selected_month = datetime.now().month
        self.months_names = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
        self.short_months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Matplotlib globaler Dark-Style
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['xtick.color'] = 'white'
        plt.rcParams['ytick.color'] = 'white'

        self.create_filter_bar()
        
        # Grid für die 3 Diagramme vorbereiten
        self.charts_container = ctk.CTkFrame(self, fg_color="transparent")
        self.charts_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.charts_container.grid_columnconfigure((0, 1, 2), weight=1)
        self.charts_container.grid_rowconfigure(0, weight=1)

        # Einzelne Frames für die Charts
        self.pie_frame = ctk.CTkFrame(self.charts_container, fg_color="#2b2b2b")
        self.pie_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.bar_frame = ctk.CTkFrame(self.charts_container, fg_color="#2b2b2b")
        self.bar_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        self.line_frame = ctk.CTkFrame(self.charts_container, fg_color="#2b2b2b")
        self.line_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        self.refresh_charts()

    def create_filter_bar(self):
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")

        ctk.CTkLabel(filter_frame, text="Visuelle Auswertungen", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=5)

        self.year_select = ctk.CTkComboBox(filter_frame, values=[str(y) for y in range(2024, 2031)], width=90, command=self.on_filter_changed)
        self.year_select.set(str(self.selected_year))
        self.year_select.pack(side="right", padx=5)

        self.month_select = ctk.CTkComboBox(filter_frame, values=self.months_names, width=120, command=self.on_filter_changed)
        self.month_select.set(self.months_names[self.selected_month - 1])
        self.month_select.pack(side="right", padx=5)
        
        ctk.CTkLabel(filter_frame, text="Auswertungszeitraum:").pack(side="right", padx=5)

    def on_filter_changed(self, event=None):
        self.selected_year = int(self.year_select.get())
        self.selected_month = self.months_names.index(self.month_select.get()) + 1
        self.refresh_charts()

    def refresh_charts(self):
        # Bestehende Widgets in den Chart-Frames löschen (verhindert Überlappung)
        for frame in [self.pie_frame, self.bar_frame, self.line_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

        try:
            # 1. Daten für das ausgewählte Jahr aus Supabase laden
            start_year = f"{self.selected_year}-01-01"
            end_year = f"{self.selected_year}-12-31"
            
            res = supabase.table("kassenbuch")\
                .select("*")\
                .gte("buchungs_datum", start_year)\
                .lte("buchungs_datum", end_year)\
                .execute()
            
            jahr_daten = res.data

            # 2. Vortrag aus vorherigen Jahren für das Liniendiagramm berechnen
            prev_res = supabase.table("kassenbuch")\
                .select("typ", "betrag")\
                .lt("buchungs_datum", start_year)\
                .execute()
            
            vortrag = sum(float(r["betrag"]) if r["typ"] == "Einnahme" else -float(r["betrag"]) for r in prev_res.data)

            # --- RENDER DIAGRAMME ---
            self.render_pie_chart(jahr_daten)
            self.render_bar_chart(jahr_daten)
            self.render_line_chart(jahr_daten, vortrag)

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Chart-Daten:\n{e}")

    # =========================================================================
    # KREISDIAGRAMM: Ausgabenverteilung im gewählten Monat
    # =========================================================================
    def render_pie_chart(self, daten):
        ctk.CTkLabel(self.pie_frame, text="Ausgaben nach Kategorie (Monat)", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Daten für den spezifischen Monat filtern
        monat_ausgaben = {}
        for row in daten:
            dt = datetime.strptime(row["buchungs_datum"], "%Y-%m-%d")
            if dt.month == self.selected_month and row["typ"] == "Ausgabe":
                kat = row["kategorie"] or "Sonstiges"
                monat_ausgaben[kat] = monat_ausgaben.get(kat, 0.0) + float(row["betrag"])

        if not monat_ausgaben:
            # Platzhalter falls keine Ausgaben getätigt wurden
            lbl = ctk.CTkLabel(self.pie_frame, text="\n\n\n\nKeine Ausgabendaten für\ndiesen Monat vorhanden.", text_color="gray")
            lbl.pack()
            return

        # Chart erstellen
        fig, ax = plt.subplots(figsize=(3.5, 3.5), facecolor='#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        labels = list(monat_ausgaben.keys())
        sizes = list(monat_ausgaben.values())
        colors = ["#e74c3c", "#e67e22", "#f1c40f", "#9b59b6", "#1abc9c", "#34495e"]

        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 8})
        ax.axis('equal')

        canvas = FigureCanvasTkAgg(fig, master=self.pie_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        plt.close(fig)

    # =========================================================================
    # SÄULENDIAGRAMM: Einnahmen vs. Ausgaben (12-Monate-Übersicht)
    # =========================================================================
    def render_bar_chart(self, daten):
        ctk.CTkLabel(self.bar_frame, text="Einnahmen vs. Ausgaben (Jahr)", font=("Arial", 14, "bold")).pack(pady=10)

        einnahmen = [0.0] * 12
        ausgaben = [0.0] * 12

        for row in daten:
            dt = datetime.strptime(row["buchungs_datum"], "%Y-%m-%d")
            m_idx = dt.month - 1
            betrag = float(row["betrag"])
            if row["typ"] == "Einnahme":
                einnahmen[m_idx] += betrag
            else:
                ausgaben[m_idx] += betrag

        fig, ax = plt.subplots(figsize=(4.5, 3.5), facecolor='#2b2b2b')
        ax.set_facecolor('#2b2b2b')

        x = range(12)
        width = 0.35

        ax.bar([i - width/2 for i in x], einnahmen, width, label='Einnahmen', color='#2ecc71')
        ax.bar([i + width/2 for i in x], ausgaben, width, label='Ausgaben', color='#e74c3c')

        ax.set_xticks(x)
        ax.set_xticklabels(self.short_months, fontsize=8)
        ax.legend(facecolor='#2b2b2b', edgecolor='none')
        ax.grid(True, linestyle='--', alpha=0.1)

        canvas = FigureCanvasTkAgg(fig, master=self.bar_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        plt.close(fig)

    # =========================================================================
    # LINIENDIAGRAMM: Kassenbestand Verlauf (Soll/Ist-Entwicklung)
    # =========================================================================
    def render_line_chart(self, daten, vortrag):
        ctk.CTkLabel(self.line_frame, text="Kassenbestand Verlauf (Jahr)", font=("Arial", 14, "bold")).pack(pady=10)

        monats_saldo = [0.0] * 12
        for row in daten:
            dt = datetime.strptime(row["buchungs_datum"], "%Y-%m-%d")
            m_idx = dt.month - 1
            betrag = float(row["betrag"])
            if row["typ"] == "Einnahme":
                monats_saldo[m_idx] += betrag
            else:
                monats_saldo[m_idx] -= betrag

        # Kumulativen Verlauf berechnen
        verlauf = []
        aktueller_bestand = vortrag
        for saldo in monats_saldo:
            aktueller_bestand += saldo
            verlauf.append(aktueller_bestand)

        fig, ax = plt.subplots(figsize=(4.5, 3.5), facecolor='#2b2b2b')
        ax.set_facecolor('#2b2b2b')

        ax.plot(self.short_months, verlauf, marker='o', color='#3498db', linewidth=2, label="Iststand")
        ax.fill_between(self.short_months, verlauf, color='#3498db', alpha=0.1)
        
        ax.grid(True, linestyle='--', alpha=0.1)
        ax.tick_params(axis='both', labelsize=8)

        canvas = FigureCanvasTkAgg(fig, master=self.line_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        plt.close(fig)