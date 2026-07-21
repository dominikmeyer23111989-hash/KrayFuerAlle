import dropbox
import streamlit as st
from database import supabase

def get_dropbox_client():
    try:
        token = st.secrets.get("DROPBOX_ACCESS_TOKEN")
        if not token:
            return None
        return dropbox.Dropbox(token)
    except Exception as e:
        print(f"Fehler beim Initialisieren von Dropbox: {e}")
        return None

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

def dokument_hochladen_dropbox(datei_bytes, dateiname):
    dbx = get_dropbox_client()
    if not dbx:
        return False, "Dropbox Access Token fehlt in den Streamlit Secrets!"
    try:
        path = f"/{dateiname}"
        dbx.files_upload(datei_bytes, path, mode=dropbox.files.WriteMode.overwrite)
        return True, "Erfolgreich hochgeladen"
    except Exception as e:
        return False, f"Fehler beim Dropbox-Upload: {e}"

def dokument_loeschen_dropbox(dateipfad):
    dbx = get_dropbox_client()
    if not dbx:
        return False
    try:
        path = f"/{dateipfad}"
        dbx.files_delete_v2(path)
        return True
    except Exception as e:
        print(f"Fehler beim Löschen aus Dropbox: {e}")
        return False

def datei_herunterladen_dropbox(dateipfad):
    dbx = get_dropbox_client()
    if not dbx:
        return None
    try:
        path = f"/{dateipfad}"
        _, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"Fehler beim Dropbox-Download: {e}")
        return None

def dokument_db_eintragen(daten):
    return supabase.table("dokumente").insert(daten).execute()

def dokument_db_loeschen(dok_id):
    return supabase.table("dokumente").delete().eq("id", dok_id).execute()