from database import supabase
from datetime import datetime

def formatiere_datum_fuer_db(datum_str):
    """Wandelt 'DD.MM.YYYY' in 'YYYY-MM-DD' für Supabase um."""
    if not datum_str or not datum_str.strip():
        return None  # Leere Felder sicher als NULL in der DB speichern
    
    try:
        return datetime.strptime(datum_str.strip(), "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None  # Bei komplett falschen Eingaben ebenfalls NULL setzen

def formatiere_datum_fuer_anzeige(datum_str):
    """Wandelt 'YYYY-MM-DD' aus Supabase in 'DD.MM.YYYY' für die UI um."""
    if not datum_str:
        return ""  # Keine 'None' Texte in der UI anzeigen, sondern leere Felder
        
    try:
        return datetime.strptime(datum_str.strip(), "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return datum_str

def get_alle_mitglieder():
    """Holt alle Mitglieder (ohne Filter für den Test) und gibt Debug-Infos im Terminal aus."""
    try:
        # Zum Testen: Wir holen erst mal ALLES ohne Filter, um zu sehen, ob überhaupt Daten fließen!
        response = supabase.table("mitglieder").select("*").execute()
        
        print("\n=== [DEBUG MITGLIEDER LADEN START] ===")
        print(f"[Debug] Anzahl gefundener Zeilen in Supabase: {len(response.data)}")
        if response.data:
            print(f"[Debug] Erstes Mitglied im Datensatz: {response.data[0]}")
        else:
            print("[Debug] Die Datenbank hat eine komplett leere Liste zurückgegeben!")
        print("=== [DEBUG MITGLIEDER LADEN ENDE] ===\n")
        
        return response.data
    except Exception as e:
        print(f"\n[DEBUG FEHLER] Fehler beim Abrufen der Mitglieder: {e}\n")
        return []

def mitglied_hinzufuegen(daten):
    # Datum konvertieren
    if "geburtsdatum" in daten:
        daten["geburtsdatum"] = formatiere_datum_fuer_db(daten["geburtsdatum"])
    if "beitrittsdatum" in daten:
        daten["beitrittsdatum"] = formatiere_datum_fuer_db(daten["beitrittsdatum"])
    
        
    # NEU: Falls keine Rolle definiert oder diese leer ist, Standard auf "Mitglied" setzen.
    # Das verhindert, dass der Wert NULL wird und aus den .neq()-Filtern fliegt!
    if not daten.get("rolle") or str(daten["rolle"]).strip() == "":
        daten["rolle"] = "Mitglied"
        
    response = supabase.table("mitglieder").insert(daten).execute()
    return response

def mitglied_aktualisieren(mitglieder_id, daten):
    # Datum konvertieren
    if "geburtsdatum" in daten:
        daten["geburtsdatum"] = formatiere_datum_fuer_db(daten["geburtsdatum"])
    if "beitrittsdatum" in daten:
        daten["beitrittsdatum"] = formatiere_datum_fuer_db(daten["beitrittsdatum"])
        
    return supabase.table("mitglieder").update(daten).eq("id", mitglieder_id).execute()

def get_mitglied_by_id(mitglieder_id):
    response = supabase.table("mitglieder").select("*").eq("id", mitglieder_id).execute()
    return response.data[0] if response.data else {}

def mitglied_loeschen(mitglieder_id):
    return supabase.table("mitglieder").delete().eq("id", mitglieder_id).execute()

def get_naechste_mitgliedsnummer():
    """Holt die höchste Mitgliedsnummer (ignoriert den Vorstand) und zählt +1."""
    response = supabase.table("mitglieder").select("mitgliedsnummer").neq("rolle", "Vorstand").order("mitgliedsnummer", desc=True).limit(1).execute()
    
    if response.data and response.data[0]['mitgliedsnummer']:
        try:
            return str(int(response.data[0]['mitgliedsnummer']) + 1)
        except ValueError:
            return "1"
            
    return "1"

def update_user_role(mitgliedsnummer, neue_rolle):
    """Ändert die Rolle eines Mitglieds in der Datenbank."""
    try:
        supabase.table("mitglieder").update({"rolle": neue_rolle}).eq("mitgliedsnummer", mitgliedsnummer).execute()
        return True
    except Exception as e:
        print(f"Fehler beim Rollen-Update: {e}")
        return False