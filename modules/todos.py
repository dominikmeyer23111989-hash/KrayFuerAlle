from database import supabase
from datetime import datetime

def get_todos_fuer_nutzer(user_rolle, user_id):
    try:
        # Versuche Daten inklusive verknüpfter Mitglieder zu laden
        res = supabase.table("todo").select("""
            *,
            ersteller:mitglieder!todo_erstellt_von_fkey(vorname, nachname),
            zugewiesener:mitglieder!todo_zugewiesen_an_fkey(vorname, nachname)
        """).order("created_at", desc=True).execute()
        
        todos = res.data if res.data else []
        
        # Wenn kein Admin/Vorstand, filtern wir im Python-Code nach Sichtbarkeit (Erstellt von oder zugewiesen an)
        if user_rolle not in ["admin", "administrator", "vorstand"]:
            todos = [
                t for t in todos 
                if t.get("erstellt_von") == user_id or t.get("zugewiesen_an") == user_id
            ]
        return todos
    except Exception as e:
        # Fallback falls die Aliasing-Relationen in Supabase Probleme machen
        try:
            res = supabase.table("todo").select("*").order("created_at", desc=True).execute()
            return res.data if res.data else []
        except Exception as e2:
            print(f"Fehler beim Laden der Todos: {e2}")
            return []

def get_alle_mitglieder():
    try:
        res = supabase.table("mitglieder").select("id, vorname, nachname").execute()
        return res.data if res.data else []
    except Exception:
        return []

def todo_erstellen(daten):
    return supabase.table("todo").insert(daten).execute()

def todo_aktualisieren(todo_id, daten):
    return supabase.table("todo").update(daten).eq("id", todo_id).execute()

def todo_loeschen(todo_id):
    return supabase.table("todo").delete().eq("id", todo_id).execute()