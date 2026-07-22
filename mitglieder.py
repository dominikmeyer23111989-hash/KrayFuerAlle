import os
from datetime import datetime
from supabase import create_client
import streamlit as st

# ==========================================
# SUPABASE VERBINDUNG INITIALISIEREN
# ==========================================
@st.cache_resource
def init_supabase():
    """Initialisiert die Supabase-Verbindung über st.secrets oder Umgebungsvariablen."""
    url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
    key = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY", ""))
    if not url or not key:
        return None
    return create_client(url, key)

supabase = init_supabase()

# ==========================================
# DATENBANK-FUNKTIONEN FÜR MITGLIEDER
# ==========================================

def get_alle_mitglieder():
    """Gibt eine Liste aller Mitglieder aus der Supabase-Tabelle zurück (inklusive Status und Sperrstatus)."""
    if not supabase:
        st.error("Supabase-Zugangsdaten fehlen in den Streamlit Secrets!")
        return []
    try:
        # Alle relevanten Spalten inklusive ist_gesperrt und status abrufen
        response = supabase.table("mitglieder").select(
            "id, mitgliedsnummer, vorname, nachname, geburtsdatum, geschlecht, email, telefonnummer, strasse, plz, ort, beitrittsdatum, rolle, status, ist_gesperrt, hat_inventar_rechte"
        ).order("nachname").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Fehler beim Laden der Mitglieder: {e}")
        return []

def get_mitglied_by_id(mitglied_id):
    """Gibt ein einzelnes Mitglied anhand seiner ID zurück."""
    if not supabase:
        return {}
    try:
        response = supabase.table("mitglieder").select("*").eq("id", mitglied_id).execute()
        data = response.data
        return data[0] if data else {}
    except Exception as e:
        st.error(f"Fehler beim Laden des Mitglieds: {e}")
        return {}

def mitglied_hinzufuegen(data):
    """Fügt ein neues Mitglied in die Supabase-Tabelle ein."""
    if not supabase:
        return False
    try:
        supabase.table("mitglieder").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern des Mitglieds: {e}")
        return False

def mitglied_aktualisieren(mitglied_id, data):
    """Aktualisiert die Daten eines bestehenden Mitglieds."""
    if not supabase:
        return False
    try:
        supabase.table("mitglieder").update(data).eq("id", mitglied_id).execute()
        return True
    except Exception as e:
        st.error(f"Fehler beim Aktualisieren: {e}")
        return False

def mitglied_loeschen(mitglied_id):
    """Löscht ein Mitglied anhand seiner ID permanent aus der Datenbank."""
    if not supabase:
        return False
    try:
        supabase.table("mitglieder").delete().eq("id", mitglied_id).execute()
        return True
    except Exception as e:
        st.error(f"Fehler beim Löschen: {e}")
        return False

def get_naechste_mitgliedsnummer():
    """Ermittelt automatisch die nächste freie Mitgliedsnummer."""
    mitglieder = get_alle_mitglieder()
    if not mitglieder:
        return "1001"
    
    nummern = []
    for m in mitglieder:
        nr = m.get("mitgliedsnummer")
        if nr and str(nr).isdigit():
            nummern.append(int(nr))
            
    if not nummern:
        return "1001"
    return str(max(nummern) + 1)

def formatiere_datum_fuer_anzeige(datum_str):
    """Formatiert ein Datenbank-Datum (YYYY-MM-DD) für die deutsche Anzeige."""
    if not datum_str:
        return ""
    try:
        if " " in datum_str:
            datum_str = datum_str.split(" ")[0]
        dt = datetime.strptime(datum_str, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return datum_str