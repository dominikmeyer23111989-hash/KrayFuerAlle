from database import supabase

def create_test_admin():
    email = "admin2@verein.de"
    password = "SuperSicheresPasswort123!"
    
    # 1. Benutzer in der Supabase Auth registrieren
    try:
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        print("Erfolg: Admin in Auth angelegt.")
    except Exception as e:
        print(f"Fehler bei Auth: {e}")
        return

    # 2. Eintrag in der eigenen 'benutzer' Tabelle erstellen
    user_data = {
        "benutzername": "admin",
        "email": email,
        "telefonnummer": "000000000"
    }
    try:
        supabase.table("benutzer").insert(user_data).execute()
        print("Erfolg: Admin in 'benutzer'-Tabelle angelegt.")
    except Exception as e:
        print(f"Fehler bei Tabellen-Eintrag: {e}")

if __name__ == "__main__":
    create_test_admin()