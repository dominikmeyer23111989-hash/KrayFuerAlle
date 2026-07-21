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
    try:
        # 1. Teilnahmen für den Termin laden
        res_t = supabase.table("teilnahmen").select("*").eq("termin_id", termin_id).execute()
        teilnahmen = res_t.data if res_t.data else []
        
        if not teilnahmen:
            return []
            
        # 2. Zugehörige Mitglieder-IDs sammeln
        user_ids = [t.get("user_id") for t in teilnahmen if t.get("user_id")]
        if not user_ids:
            return teilnahmen
            
        # 3. Mitglieder-Details separat laden
        res_m = supabase.table("mitglieder").select("id, vorname, nachname, rolle, email").in_("id", user_ids).execute()
        mitglieder_map = {m["id"]: m for m in res_m.data} if res_m.data else {}
        
        # 4. Datenstruktur für das Frontend zusammenführen
        for t in teilnahmen:
            u_id = t.get("user_id")
            t["mitglieder"] = mitglieder_map.get(u_id, {})
            
        return teilnahmen
    except Exception as e:
        print(f"Fehler beim Laden der Teilnahmen: {e}")
        return []

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