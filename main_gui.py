import customtkinter as ctk
from modules.mitglieder import alle_mitglieder_anzeigen

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vereinsverwaltung")
        self.geometry("400x300")

        self.btn = ctk.CTkButton(self, text="Mitglieder laden", command=self.load_data)
        self.btn.pack(pady=20)
        
        self.textbox = ctk.CTkTextbox(self, width=350, height=150)
        self.textbox.pack(pady=10)

    def load_data(self):
        data = alle_mitglieder_anzeigen()
        self.textbox.insert("0.0", str(data))

if __name__ == "__main__":
    app = App()
    app.mainloop()