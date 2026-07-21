from database import supabase

def get_termine_fuer_nutzer(user_rolle, user_id):
    """
    Gibt alle Termine zurück, die der Nutzer sehen darf.
    - Admin, Administrator und Vorstand sehen alle Termine.
    - Normale Mitglieder sehen Termine mit sichtbarkeit == 'alle' 
      oder wenn die Sichtbarkeit exakt ihrer Rolle entspricht.
    """
    try:
        response = supabase.table("termine").select("*").order("datum").execute()
        alle_termine = response.data if response.data else []
        
        leitung_rollen = ["admin", "administrator", "vorstand"]
        rolle_clean = str(user_rolle).strip().lower()
        
        if rolle_clean in leitung_rollen:
            return alle_termine
            
        sichtbare_termine = []
        for t in alle_termine:
            sichtbarkeit = str(t.get("sichtbarkeit", "alle")).strip().lower()
            if sichtbarkeit == "alle" or sichtbarkeit == rolle_clean:
                sichtbare_termine.append(t)
                
        return sichtbare_termine
    except Exception as e:
        print(f"Fehler beim Laden der Termine: {e}")
        return []

def termin_erstellen(daten):
    """Erstellt einen neuen Termin."""
    response = supabase.table("termine").insert(daten).execute()
    return response.data

def termin_aktualisieren(termin_id, daten):
    """Aktualisiert einen bestehenden Termin."""
    response = supabase.table("termine").update(daten).eq("id", termin_id).execute()
    return response.data

def termin_loeschen(termin_id):
    """Löscht einen Termin (Teilnahmen werden dank CASCADE automatisch gelöscht)."""
    response = supabase.table("termine").delete().eq("id", termin_id).execute()
    return response.data

def get_teilnahmen_fuer_termin(termin_id):
    """Gibt alle Teilnahmen für einen bestimmten Termin inklusive Mitglieder-Details zurück."""
    response = supabase.table("teilnahmen").select("*, mitglieder(vorname, nachname, rolle, email)").eq("termin_id", termin_id).execute()
    return response.data if response.data else []

def setze_teilnahme(termin_id, user_id, status):
    """Setzt oder aktualisiert die Teilnahme (RSVP) eines Mitglieds für einen Termin."""
    # Prüfen, ob bereits ein Eintrag existiert
    existing = supabase.table("teilnahmen").select("id").eq("termin_id", termin_id).eq("user_id", user_id).execute()
    
    if existing.data and len(existing.data) > 0:
        # Update
        teilnahme_id = existing.data[0]["id"]
        response = supabase.table("teilnahmen").update({"status": status}).eq("id", teilnahme_id).execute()
    else:
        # Insert
        daten = {
            "termin_id": termin_id,
            "user_id": user_id,
            "status": status
        }
        response = supabase.table("teilnahmen").insert(daten).execute()
    return response.data