# modules/mitglieder_db.py
from database import supabase

def get_mitglied_daten(email):
    """Holt alle Infos eines Mitglieds anhand der E-Mail."""
    try:
        response = supabase.table("mitglieder").select("*").eq("email", email).single().execute()
        return response.data
    except Exception as e:
        print(f"Fehler beim Abrufen der Mitgliederdaten: {e}")
        return None
