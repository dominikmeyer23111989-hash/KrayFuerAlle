import sys
import time
import requests
import shutil
import os
import subprocess

def main():
    if len(sys.argv) < 2:
        return # Keine Download-URL übergeben
        
    download_url = sys.argv[1]
    ziel_datei = "KrayFuerAlle.exe"
    temp_datei = "KrayFuerAlle_new.exe"
    
    # 1. Kurz warten, damit sich das Hauptprogramm komplett beenden kann
    time.sleep(2)
    
    try:
        # 2. Die neue .exe aus Supabase herunterladen
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            with open(temp_datei, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            
            # 3. Die alte .exe durch die neue ersetzen
            if os.path.exists(ziel_datei):
                os.remove(ziel_datei)
            os.rename(temp_datei, ziel_datei)
            
            # 4. Das frisch aktualisierte Hauptprogramm wieder starten!
            subprocess.Popen([ziel_datei])
            
    except Exception as e:
        # Falls was schiefgeht, Fehler loggen (optional)
        with open("updater_error.txt", "w") as f:
            f.write(str(e))

if __name__ == "__main__":
    main()