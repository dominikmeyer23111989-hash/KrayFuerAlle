from database import supabase
from datetime import datetime

def formatiere_datum_fuer_db(datum_str):
    """Wandelt 'DD.MM.YYYY' oder Date-Objekte in 'YYYY-MM-DD' für Supabase um."""
    if not datum_str or not str(datum_str).strip():
        return None
    
    if isinstance(datum_str, datetime) or hasattr(datum_str, "strftime"):
        return datum_str.strftime("%Y-%m-%d")
        
    try:
        return datetime.strptime(str(datum_str).strip(), "%d.%m.%Y").strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Fallback falls bereits im YYYY-MM-DD Format
            return datetime.strptime(str(datum_str).strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return None

def formatiere_datum_fuer_anzeige(datum_str):
    """Wandelt 'YYYY-MM-DD' aus Supabase in 'DD.MM.YYYY' für die UI um."""
    if not datum_str:
        return ""
        
    try:
        s = str(datum_str).split("T")[0].split(" ")[0]
        return datetime.strptime(s, "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return str(datum_str)

# ==========================================
# 1. INVENTAR CRUD-FUNKTIONEN
# ==========================================

def get_alle_inventar():
    """Holt alle Inventar-Gegenstände sortiert nach Namen."""
    try:
        response = supabase.table("inventar").select("*").order("name").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Fehler beim Laden des Inventars: {e}")
        return []

def inventar_hinzufuegen(daten):
    """Fügt einen neuen Inventar-Gegenstand hinzu."""
    for feld in ["ablaufdatum", "anschaffungs_datum", "pruefdatum"]:
        if feld in daten and daten[feld]:
            daten[feld] = formatiere_datum_fuer_db(daten[feld])
            
    try:
        return supabase.table("inventar").insert(daten).execute()
    except Exception as e:
        print(f"Fehler beim Hinzufügen des Inventars: {e}")
        raise e

def inventar_aktualisieren(inventar_id, daten):
    """Aktualisiert einen bestehenden Inventar-Gegenstand."""
    for feld in ["ablaufdatum", "anschaffungs_datum", "pruefdatum"]:
        if feld in daten and daten[feld]:
            daten[feld] = formatiere_datum_fuer_db(daten[feld])
            
    try:
        return supabase.table("inventar").update(daten).eq("id", inventar_id).execute()
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Inventars: {e}")
        raise e

def inventar_loeschen(inventar_id):
    """Löscht einen Inventar-Gegenstand."""
    try:
        return supabase.table("inventar").delete().eq("id", inventar_id).execute()
    except Exception as e:
        print(f"Fehler beim Löschen des Inventars: {e}")
        raise e

# ==========================================
# 2. AUSLEIHE & RÜCKGABE FUNKTIONEN
# ==========================================

def get_alle_ausleihen():
    """Holt alle Ausleihen inkl. Verknüpfung zu den Inventar-Details."""
    try:
        response = supabase.table("ausleihen").select("*, inventar(name, lagerort)").order("created_at", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Fehler beim Laden der Ausleihen: {e}")
        return []

def ausleihe_erstellen(daten):
    """
    Erstellt eine Ausleihe und reduziert automatisch 
    die verfügbare Menge des entsprechenden Inventar-Gegenstands.
    """
    if "ausleih_datum" in daten and daten["ausleih_datum"]:
        daten["ausleih_datum"] = formatiere_datum_fuer_db(daten["ausleih_datum"])
    if "rueckgabe_soll" in daten and daten["rueckgabe_soll"]:
        daten["rueckgabe_soll"] = formatiere_datum_fuer_db(daten["rueckgabe_soll"])
        
    try:
        # 1. Ausleihe in der Tabelle eintragen
        res = supabase.table("ausleihen").insert(daten).execute()
        
        # 2. Verfügbare Menge im Inventar anpassen
        inventar_id = daten.get("inventar_id")
        ausleih_menge = daten.get("menge", 1)
        
        if inventar_id:
            inv_res = supabase.table("inventar").select("menge_verfuegbar").eq("id", inventar_id).single().execute()
            if inv_res.data:
                akt_verfuegbar = inv_res.data.get("menge_verfuegbar", 0)
                neue_verfuegbar = max(0, akt_verfuegbar - ausleih_menge)
                
                neuer_status = "Verfügbar" if neue_verfuegbar > 0 else "Ausgeliehen"
                
                supabase.table("inventar").update({
                    "menge_verfuegbar": neue_verfuegbar,
                    "status": neuer_status
                }).eq("id", inventar_id).execute()
                
        return res
    except Exception as e:
        print(f"Fehler beim Erstellen der Ausleihe: {e}")
        raise e

def ausleihe_zuruecknehmen(ausleihe_id, rueckgabe_daten):
    """
    Nimmt eine Ausleihe zurück, aktualisiert den Status/Schadensbericht 
    und erhöht die verfügbare Menge im Inventar wieder.
    """
    if "rueckgabe_ist" in rueckgabe_daten and rueckgabe_daten["rueckgabe_ist"]:
        rueckgabe_daten["rueckgabe_ist"] = formatiere_datum_fuer_db(rueckgabe_daten["rueckgabe_ist"])
        
    try:
        # 1. Ausleihe-Infos abrufen (für Inventar-ID und Menge)
        ausl_res = supabase.table("ausleihen").select("inventar_id, menge").eq("id", ausleihe_id).single().execute()
        if not ausl_res.data:
            raise Exception("Ausleihe konnte nicht gefunden werden.")
            
        ausl_data = ausl_res.data
        inventar_id = ausl_data.get("inventar_id")
        ausgeleihene_menge = ausl_data.get("menge", 1)
        
        # 2. Ausleihe-Datensatz aktualisieren
        res = supabase.table("ausleihen").update(rueckgabe_daten).eq("id", ausleihe_id).execute()
        
        # 3. Inventar-Bestand anpassen
        if inventar_id:
            inv_res = supabase.table("inventar").select("menge_gesamt, menge_verfuegbar, menge_defekt").eq("id", inventar_id).single().execute()
            if inv_res.data:
                inv = inv_res.data
                gesamt = inv.get("menge_gesamt", 1)
                verfuegbar = inv.get("menge_verfuegbar", 0)
                defekt = inv.get("menge_defekt", 0)
                
                # Maximale verfügbare Menge berechnet sich aus Gesamtbestand minus defekter Bestand
                max_verfuegbar = max(0, gesamt - defekt)
                neue_verfuegbar = min(max_verfuegbar, verfuegbar + ausgeleihene_menge)
                
                neuer_status = "Verfügbar" if neue_verfuegbar > 0 else "Ausgeliehen"
                
                supabase.table("inventar").update({
                    "menge_verfuegbar": neue_verfuegbar,
                    "status": neuer_status
                }).eq("id", inventar_id).execute()
                
        return res
    except Exception as e:
        print(f"Fehler bei der Rücknahme: {e}")
        raise e

# ==========================================
# 3. EINSTELLUNGEN FUNKTIONEN
# ==========================================

def get_inventar_einstellungen():
    """Holt die Konfigurationseinstellungen für das Inventar."""
    try:
        response = supabase.table("inventar_einstellungen").select("*").limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Fehler beim Laden der Einstellungen: {e}")
        return None

def inventar_einstellungen_aktualisieren(einstellungen_id, daten):
    """Aktualisiert die Inventar-Einstellungen."""
    try:
        return supabase.table("inventar_einstellungen").update(daten).eq("id", einstellungen_id).execute()
    except Exception as e:
        print(f"Fehler beim Aktualisieren der Einstellungen: {e}")
        raise e