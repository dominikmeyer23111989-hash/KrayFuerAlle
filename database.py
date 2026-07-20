from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# Hier deine festen Werte (falls die .env nicht gefunden wird)
URL_FALLBACK = "https://ythubjdnercyeyfedsam.supabase.co"
KEY_FALLBACK = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl0aHViamRuZXJjeWV5ZmVkc2FtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM1MjgzNTgsImV4cCI6MjA5OTEwNDM1OH0.loeU2abylobRmPJvuHwdZLbHNyTL4qlKOtIRk-qZp34"

# Er lädt aus der Umgebung, wenn vorhanden, sonst nimmt er die Fallback-Werte
url = os.environ.get("SUPABASE_URL") or URL_FALLBACK
key = os.environ.get("SUPABASE_KEY") or KEY_FALLBACK

# Zur Sicherheit prüfen, ob wir gültige Werte haben
if not url or not key:
    raise Exception("Fehler: Supabase URL oder KEY konnten nicht geladen werden!")

supabase: Client = create_client(url, key)