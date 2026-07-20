from database import supabase

try:
    # Wir versuchen, einen kleinen Test-Befehl an die Datenbank zu schicken
    response = supabase.table("mitglieder").select("count").execute()
    print("Erfolg! Verbindung zur Datenbank steht.")
except Exception as e:
    print(f"Verbindung fehlgeschlagen. Fehler: {e}")