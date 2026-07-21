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
        print(f"Fehler bei Dropbox: {e}")
        return None

def foto_hochladen_dropbox(datei_bytes, dateiname):
    dbx = get_dropbox_client()
    if not dbx:
        return False, "Dropbox Access Token fehlt!"
    try:
        path = f"/mitglieder_fotos/{dateiname}"
        dbx.files_upload(datei_bytes, path, mode=dropbox.files.WriteMode.overwrite)
        return True, path
    except Exception as e:
        return False, f"Fehler beim Upload: {e}"

def foto_herunterladen_dropbox(dateipfad):
    dbx = get_dropbox_client()
    if not dbx:
        return None
    try:
        _, res = dbx.files_download(dateipfad)
        return res.content
    except Exception as e:
        print(f"Fehler beim Foto-Download: {e}")
        return None

def get_mitglied_daten(user_id):
    try:
        res = supabase.table("mitglieder").select("*").eq("id", user_id).single().execute()
        return res.data if res.data else None
    except Exception as e:
        print(f"Fehler beim Laden des Mitglieds: {e}")
        return None

def get_alle_mitglieder():
    try:
        res = supabase.table("mitglieder").select("*").order("nachname").execute()
        return res.data if res.data else []
    except Exception as e:
        print(f"Fehler beim Laden aller Mitglieder: {e}")
        return []

def mitglied_ausweis_aktualisieren(mitglied_id, daten):
    try:
        supabase.table("mitglieder").update(daten).eq("id", mitglied_id).execute()
        return True
    except Exception as e:
        print(f"Fehler beim Aktualisieren: {e}")
        return False