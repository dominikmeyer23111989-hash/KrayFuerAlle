from database import supabase

# ==========================================
# 1. EVENTS CRUD
# ==========================================

def get_alle_events():
    """Gibt alle Events sortiert nach Startdatum zurück."""
    response = supabase.table("events").select("*").order("start_datum").execute()
    return response.data if response.data else []

def event_erstellen(daten):
    """Legt ein neues Event an."""
    response = supabase.table("events").insert(daten).execute()
    return response.data

def event_aktualisieren(event_id, daten):
    """Aktualisiert ein bestehendes Event."""
    response = supabase.table("events").update(daten).eq("id", event_id).execute()
    return response.data

def event_loeschen(event_id):
    """Löscht ein Event (Cascades löschen automatisch Schichten, RSVPs, Material & Freigaben)."""
    response = supabase.table("events").delete().eq("id", event_id).execute()
    return response.data


# ==========================================
# 2. SCHICHTEN
# ==========================================

def get_schichten_fuer_event(event_id):
    """Gibt alle Schichten eines Events inklusive der Mitglieder-Details zurück."""
    response = supabase.table("event_schichten").select("*, mitglieder(vorname, nachname)").eq("event_id", event_id).execute()
    return response.data if response.data else []

def schicht_erstellen(daten):
    """Fügt eine neue Schicht hinzu."""
    response = supabase.table("event_schichten").insert(daten).execute()
    return response.data

def schicht_loeschen(schicht_id):
    """Löscht eine Schicht."""
    response = supabase.table("event_schichten").delete().eq("id", schicht_id).execute()
    return response.data


# ==========================================
# 3. RSVPS (RÜCKMELDUNGEN)
# ==========================================

def get_rsvps_fuer_event(event_id):
    """Gibt alle Rückmeldungen (RSVPs) für ein Event zurück."""
    response = supabase.table("event_rsvps").select("*, mitglieder(vorname, nachname, rolle)").eq("event_id", event_id).execute()
    return response.data if response.data else []

def setze_rsvp(event_id, mitglied_id, status):
    """Setzt oder aktualisiert die Zusage eines Mitglieds (nutzt den Unique Constraint)."""
    daten = {
        "event_id": event_id,
        "mitglied_id": mitglied_id,
        "status": status
    }
    # Nutzt Supabase Upsert anhand des Unique Keys (event_id, mitglied_id)
    response = supabase.table("event_rsvps").upsert(daten, on_conflict="event_id,mitglied_id").execute()
    return response.data


# ==========================================
# 4. EVENT MATERIAL
# ==========================================

def get_material_fuer_event(event_id):
    """Gibt das verknüpfte Inventar-Material für ein Event zurück."""
    response = supabase.table("event_material").select("*, inventar(name, lagerort, menge_verfuegbar)").eq("event_id", event_id).execute()
    return response.data if response.data else []

def event_material_hinzufuegen(daten):
    """Verknüpft Inventar mit einem Event."""
    response = supabase.table("event_material").insert(daten).execute()
    return response.data

def event_material_loeschen(material_id):
    """Entfernt die Material-Verknüpfung."""
    response = supabase.table("event_material").delete().eq("id", material_id).execute()
    return response.data


# ==========================================
# 5. EVENT FREIGABEN
# ==========================================

def get_freigaben_fuer_event(event_id):
    """Gibt alle Freigaben (Sichtbarkeit/Berechtigungen) für ein Event zurück."""
    response = supabase.table("event_freigaben").select("*, mitglieder(vorname, nachname, email)").eq("event_id", event_id).execute()
    return response.data if response.data else []

def freigabe_hinzufuegen(daten):
    """Fügt eine Freigabe für ein Mitglied hinzu."""
    response = supabase.table("event_freigaben").insert(daten).execute()
    return response.data

def freigabe_loeschen(freigabe_id):
    """Entfernt eine Freigabe."""
    response = supabase.table("event_freigaben").delete().eq("id", freigabe_id).execute()
    return response.data