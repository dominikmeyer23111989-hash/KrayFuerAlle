import sys
import subprocess
from supabase import create_client

# FÜR DEN TEST: Auf "0.9.0" setzen, damit er merkt, dass die "1.0.0" in der DB neuer ist!
CURRENT_VERSION = "1.0.4"

URL = "https://ythubjdnercyeyfedsam.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl0aHViamRuZXJjeWV5ZmVkc2FtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MjgzNTgsImV4cCI6MjA5OTEwNDM1OH0.loeU2abylobRmPJvuHwdZLbHNyTL4qlKOtIRk-qZp34"

supabase = create_client(URL, KEY)

def check_for_updates():
    try:
        # 1. Wir fragen nach "version" und "file" (Spaltenname an DB angepasst!)
        response = supabase.table("app_version") \
            .select("version", "file") \
            .eq("released", True) \
            .order("id", desc=True) \
            .limit(1) \
            .execute()
        
        if response.data:
            latest_version = response.data[0]["version"]
            
            # NEU: Wir holen uns direkt den kompletten Dropbox-Link aus der Spalte "file"
            download_url = response.data[0]["file"] 
            
            # 2. Wenn die freigegebene Version ungleich der lokalen Version ist -> Update!
            if latest_version != CURRENT_VERSION:
                
                # Externe updater.exe starten und die Dropbox-URL übergeben
                subprocess.Popen(["updater.exe", download_url])
                
                # Hauptprogramm sofort beenden, damit Windows die Datei zum Überschreiben freigibt
                sys.exit()
                
    except Exception as e:
        print(f"Update-Fehler: {e}")