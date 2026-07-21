from database import supabase

def get_alle_kontakte():
    """Holt alle Kontakte sortiert nach Nachname und Vorname."""
    try:
        response = supabase.table("adressbuch").select("*").order("nachname").order("vorname").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Fehler beim Laden des Adressbuchs: {e}")
        return []

def kontakt_hinzufuegen(daten):
    """Fügt einen neuen Kontakt hinzu."""
    try:
        return supabase.table("adressbuch").insert(daten).execute()
    except Exception as e:
        print(f"Fehler beim Hinzufügen des Kontakts: {e}")
        raise e

def kontakt_aktualisieren(kontakt_id, daten):
    """Aktualisiert einen bestehenden Kontakt."""
    try:
        return supabase.table("adressbuch").update(daten).eq("id", kontakt_id).execute()
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Kontakts: {e}")
        raise e

def kontakt_loeschen(kontakt_id):
    """Löscht einen Kontakt."""
    try:
        return supabase.table("adressbuch").delete().eq("id", kontakt_id).execute()
    except Exception as e:
        print(f"Fehler beim Löschen des Kontakts: {e}")
        raise e