from database import supabase

def get_dokumente(bereich=None):
    try:
        query = supabase.table("dokumente").select("*, mitglieder(vorname, nachname)").order("created_at", desc=True)
        if bereich:
            query = query.eq("bereich", bereich)
        res = query.execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Fehler beim Laden der Dokumente: {e}")
        return []

def dokument_hochladen_storage(datei_bytes, dateiname):
    try:
        supabase.storage.from_("verein-dateien").upload(dateiname, datei_bytes, file_options={"upsert": "true"})
        return True
    except Exception as e:
        print(f"Fehler beim Storage-Upload: {e}")
        return False

def dokument_loeschen_storage(dateipfad):
    try:
        supabase.storage.from_("verein-dateien").remove([dateipfad])
        return True
    except Exception as e:
        print(f"Fehler beim Löschen aus Storage: {e}")
        return False

def dokument_db_eintragen(daten):
    return supabase.table("dokumente").insert(daten).execute()

def dokument_db_loeschen(dok_id):
    return supabase.table("dokumente").delete().eq("id", dok_id).execute()

def datei_herunterladen(dateipfad):
    try:
        return supabase.storage.from_("verein-dateien").download(dateipfad)
    except Exception as e:
        print(f"Fehler beim Download: {e}")
        return None