from database import supabase

def get_chronik_eintraege():
    try:
        # Sortiert nach Datum absteigend (neueste/jüngste Ereignisse zuerst)
        res = supabase.table("chronik").select("*").order("datum", desc=True).execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Fehler beim Laden der Chronik: {e}")
        return []

def chronik_erstellen(daten):
    return supabase.table("chronik").insert(daten).execute()

def chronik_loeschen(eintrag_id):
    return supabase.table("chronik").delete().eq("id", eintrag_id).execute()