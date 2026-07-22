from database import supabase

def finde_email_zu_benutzer(identifier):
    """
    Ermittelt die zugehörige E-Mail-Adresse oder interne Auth-Kennung 
    zu einem eingegebenen Identifier (E-Mail, Benutzername, Telefonnummer oder Mitgliedsnummer).
    """
    if not identifier:
        return None
        
    identifier = str(identifier).strip()
    
    # 1. SUCHE IN 'BENUTZER' (E-Mail case-insensitive oder Benutzername)
    try:
        res = supabase.table("benutzer").select("email").ilike("email", identifier).maybe_single().execute()
        if res and res.data:
            return res.data["email"]

        res = supabase.table("benutzer").select("email").eq("benutzername", identifier).maybe_single().execute()
        if res and res.data:
            return res.data["email"]
    except Exception as e:
        print(f"[Debug] Fehler bei 'benutzer'-Suche: {e}")
        
    # 2. SUCHE IN 'MITGLIEDER' (E-Mail, Telefonnummer, Mitgliedsnummer)
    try:
        # A) E-Mail (case-insensitive)
        res = supabase.table("mitglieder").select("email, mitgliedsnummer, telefonnummer").ilike("email", identifier).maybe_single().execute()
        if res and res.data:
            if res.data.get("email"): 
                return res.data["email"]
            return f"{res.data['mitgliedsnummer']}@krayfueralle.intern"

        # B) Mitgliedsnummer (wenn numerisch)
        if identifier.isdigit():
            res = supabase.table("mitglieder").select("email, mitgliedsnummer, telefonnummer").eq("mitgliedsnummer", int(identifier)).maybe_single().execute()
            if res and res.data:
                if res.data.get("email"): 
                    return res.data["email"]
                return f"{res.data['mitgliedsnummer']}@krayfueralle.intern"

        # C) Telefonnummer (Exakter Abgleich)
        res = supabase.table("mitglieder").select("email, mitgliedsnummer, telefonnummer").eq("telefonnummer", identifier).maybe_single().execute()
        if res and res.data:
            if res.data.get("email"): 
                return res.data["email"]
            return f"{res.data['mitgliedsnummer']}@krayfueralle.intern"

    except Exception as e:
        print(f"[Debug] Fehler bei 'mitglieder'-Suche: {e}")
        
    return None

def login_user(identifier, password):
    """Login-Prozess."""
    email = finde_email_zu_benutzer(identifier)
    
    if not email:
        return {"success": False, "message": "Benutzername, Telefon oder Mitgliedsnummer nicht gefunden."}

    try:
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return {"success": True, "data": auth_response}
    except Exception as e: 
        print(f"[Debug] Auth-Fehler: {e}")
        return {"success": False, "message": "Passwort falsch oder Login fehlgeschlagen."}

def erstes_passwort_setzen(identifier, password):
    """
    1. Prüft, ob das Mitglied existiert.
    2. Erstellt Auth-Account.
    3. Trägt das Mitglied in die 'benutzer'-Tabelle ein.
    """
    try:
        identifier_str = str(identifier).strip()
        
        res = None
        res = supabase.table("mitglieder").select("*").ilike("email", identifier_str).maybe_single().execute()
        
        if (not res or not res.data) and identifier_str.isdigit():
            res = supabase.table("mitglieder").select("*").eq("mitgliedsnummer", int(identifier_str)).maybe_single().execute()
            
        if not res or not res.data:
            res = supabase.table("mitglieder").select("*").eq("telefonnummer", identifier_str).maybe_single().execute()
        
        if not res or not res.data:
            return False, "Mitgliedsdaten nicht gefunden. Bitte Vorstand kontaktieren."
        
        member = res.data
        email = member.get("email") if member.get("email") else f"{member['mitgliedsnummer']}@krayfueralle.intern"
        
        try:
            supabase.auth.sign_up({"email": email, "password": password})
        except Exception as e:
            return False, f"Auth-Fehler: {str(e)}"
        
        try:
            supabase.table("benutzer").insert({
                "email": email,
                "benutzername": str(member["mitgliedsnummer"])
            }).execute()
        except Exception as e:
            if "duplicate key" not in str(e).lower():
                return False, f"Datenbank-Fehler beim User-Anlegen: {str(e)}"
        
        return True, "Account erfolgreich aktiviert! Du kannst dich jetzt einloggen."
        
    except Exception as e:
        return False, f"Allgemeiner Fehler: {str(e)}"

def passwort_zuruecksetzen_mit_sicherheitsfrage(identifier, antwort, neues_passwort):
    """
    Prüft die Sicherheitsantwort und setzt das Passwort administrativ zurück.
    """
    identifier_str = str(identifier).strip()
    res = None
    try:
        res = supabase.table("mitglieder").select("sicherheitsantwort, mitgliedsnummer, email").ilike("email", identifier_str).maybe_single().execute()
        if (not res or not res.data) and identifier_str.isdigit():
            res = supabase.table("mitglieder").select("sicherheitsantwort, mitgliedsnummer, email").eq("mitgliedsnummer", int(identifier_str)).maybe_single().execute()
        if not res or not res.data:
            res = supabase.table("mitglieder").select("sicherheitsantwort, mitgliedsnummer, email").eq("telefonnummer", identifier_str).maybe_single().execute()
    except Exception:
        pass
    
    if not res or not res.data or res.data.get("sicherheitsantwort") != antwort:
        return False, "Falsche Antwort oder Benutzer nicht gefunden."
    
    email = res.data.get("email") if res.data.get("email") else f"{res.data['mitgliedsnummer']}@krayfueralle.intern"
    
    try:
        user = supabase.auth.admin.list_users()
        target_user = [u for u in user.users if u.email == email]
        if not target_user:
            return False, "Auth-Account nicht gefunden."
            
        supabase.auth.admin.update_user_by_id(target_user[0].id, {"password": neues_passwort})
        return True, "Passwort wurde erfolgreich zurückgesetzt."
    except Exception as e:
        return False, f"Fehler: {str(e)}"

def passwort_zuruecksetzen(identifier):
    """Sendet Reset-Link, sofern eine echte E-Mail hinterlegt ist."""
    email = finde_email_zu_benutzer(identifier)
    
    if not email or "@krayfueralle.intern" in email:
        return False, "Für dieses Konto ist keine echte E-Mail hinterlegt. Bitte wende dich an den Vorstand."
        
    try:
        supabase.auth.reset_password_email(email)
        return True, "E-Mail mit Reset-Link wurde versendet."
    except Exception as e:
        return False, f"Fehler: {str(e)}"

def update_user_role(mitgliedsnummer, neue_rolle):
    """Ändert die Rolle eines Mitglieds."""
    try:
        res = supabase.table("mitglieder").update({
            "rolle": neue_rolle
        }).eq("mitgliedsnummer", mitgliedsnummer).execute()
        return True, "Rolle erfolgreich aktualisiert."
    except Exception as e:
        return False, f"Fehler: {str(e)}"