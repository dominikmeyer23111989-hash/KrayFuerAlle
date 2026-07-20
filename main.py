from app_desktop.login_window import LoginWindow # Import aus deinem Login-Modul
from main_dashboard import MainDashboard

def main():
    # 1. Login starten
    login = LoginWindow()
    login.mainloop()

    # 2. Wenn Login erfolgreich war (und das Fenster geschlossen wurde),
    # würden wir hier das Dashboard starten.
    # Da wir für Anfänger-Übersichtlichkeit erst mal klein starten:
    # Das Dashboard wird später direkt aus dem Login-Fenster aufgerufen.

if __name__ == "__main__":
    main()