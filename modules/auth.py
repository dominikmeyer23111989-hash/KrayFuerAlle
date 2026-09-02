from database import supabase

def finde_email_zu_benutzer(identifier):
    """
    Ermittelt die zugehörige E-Mail-Adresse oder interne Auth-Kennung 
    zuerst aus der 'benutzer'-Tabelle (nach Benutzername) und danach aus 'mitglieder'.
    """
    if not identifier:
        return None
        
    identifier_str = str(identifier).strip()
    print(f"\n--- [DEBUG LOGIN] Suche nach: '{identifier_str}' ---")
    
    # 0. Zuerst in der 'benutzer'-Tabelle nach dem Benutzernamen suchen (z.B. "admin")
    try:
        res_benutzer = supabase.table("benutzer").select("email, benutzername").ilike("benutzername", identifier_str).maybe_single().execute()
        if res_benutzer and res_benutzer.data:
            print("[Debug] Treffer in 'benutzer'-Tabelle via Benutzername!")
            if res_benutzer.data.get("email"):
                return res_benutzer.data["email"]
    except Exception as e:
        print(f"[Debug] Fehler bei Benutzername-Suche übersprungen: {e}")

    # 1. Suche nach E-Mail (case-insensitive) in 'mitglieder'
    try:
        res = supabase.table("mitglieder").select("email, mitgliedsnummer, telefonnummer").ilike("email", identifier_str).maybe_single().execute()
        if res and res.data:
            print("[Debug] Treffer in 'mitglieder' via E-Mail!")
            if res.data.get("email"): 
                return res.data["email"]
            return f"{res.data['mitgliedsnummer']}@krayfueralle.intern"
    except Exception as e:
        print(f"[Debug] Fehler bei E-Mail-Suche übersprungen: {e}")

    # 2. Suche nach Mitgliedsnummer (wenn numerisch) in 'mitglieder'
    if identifier_str.isdigit():
        try:
            res = supabase.table("mitglieder").select("email, mitgliedsnummer, telefonnummer").eq("mitgliedsnummer", int(identifier_str)).maybe_single().execute()
            if res and res.data:
                print("[Debug] Treffer in 'mitglieder' via Mitgliedsnummer!")
                if res.data.get("email"): 
                    return res.data["email"]
                return f"{res.data['mitgliedsnummer']}@krayfueralle.intern"
        except Exception as e:
            print(f"[Debug] Fehler bei Mitgliedsnummer-Suche übersprungen: {e}")

    # 3. Flexible Telefonnummern-Suche in 'mitglieder'
    try:
        res_tel = supabase.table("mitglieder").select("email, mitgliedsnummer, telefonnummer").not_("telefonnummer", "is", "null").execute()
        if res_tel and res_tel.data:
            clean_input = "".join(filter(str.isdigit, identifier_str))
            if clean_input:
                for row in res_tel.data:
                    db_tel = row.get("telefonnummer")
                    if db_tel:
                        clean_db = "".join(filter(str.isdigit, str(db_tel)))
                        if clean_input == clean_db:
                            print(f"[Debug] Treffer in 'mitglieder' via Telefon ({db_tel})!")
                            if row.get("email"): 
                                return row["email"]
                            return f"{row['mitgliedsnummer']}@krayfueralle.intern"
    except Exception as e:
        print(f"[Debug] Fehler bei Telefon-Suche: {e}")
        
    print("[Debug] --- NICHT GEFUNDEN ---")
    return None

def login_user(identifier, password):
    """Login-Prozess inklusive Prüfung auf Inaktivität/Sperre."""
    email = finde_email_zu_benutzer(identifier)
    
    if not email:
        return {"success": False, "message": "Benutzername, Telefon oder Mitgliedsnummer nicht gefunden."}

    # Prüfen, ob das Mitglied inaktiv / gesperrt ist
    try:
        query = supabase.table("mitglieder").select("ist_gesperrt")
        if "@krayfueralle.intern" in email:
            m_nr = email.split("@")[0]
            if m_nr.isdigit():
                res_gesperrt = query.eq("mitgliedsnummer", int(m_nr)).maybe_single().execute()
            else:
                res_gesperrt = query.eq("mitgliedsnummer", m_nr).maybe_single().execute()
        else:
            res_gesperrt = query.ilike("email", email).maybe_single().execute()

        if res_gesperrt and res_gesperrt.data and res_gesperrt.data.get("ist_gesperrt", False):
            return {"success": False, "message": "Dieses Konto ist inaktiv / gesperrt. Ein Login ist nicht möglich."}
    except Exception as e:
        print(f"[Debug] Sperr-Prüfung Fehler: {e}")

    try:
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return {"success": True, "data": auth_response}
    except Exception as e: 
        print(f"[Debug] Auth-Fehler: {e}")
        return {"success": False, "message": "Passwort falsch oder Login fehlgeschlagen."}

def erstes_passwort_setzen(identifier, password):
    """
    1. Prüft, ob das Mitglied in der 'mitglieder'-Tabelle existiert.
    2. Erstellt den Auth-Account direkt als bestätigt (umgeht E-Mail-Bestätigung via Admin API).
    3. Trägt das Mitglied sicher in die 'benutzer'-Tabelle ein (mit upsert).
    """
    try:
        identifier_str = str(identifier).strip()
        res = None
        
        # A) E-Mail Suche
        res = supabase.table("mitglieder").select("*").ilike("email", identifier_str).maybe_single().execute()
        
        # B) Mitgliedsnummer Suche
        if (not res or not res.data) and identifier_str.isdigit():
            res = supabase.table("mitglieder").select("*").eq("mitgliedsnummer", int(identifier_str)).maybe_single().execute()
            
        # C) Telefonnummer Suche
        if not res or not res.data:
            res_tel = supabase.table("mitglieder").select("*").not_("telefonnummer", "is", "null").execute()
            if res_tel and res_tel.data:
                clean_input = "".join(filter(str.isdigit, identifier_str))
                for row in res_tel.data:
                    if clean_input and clean_input == "".join(filter(str.isdigit, str(row.get("telefonnummer", "")))):
                        res = type('obj', (object,), {'data': row})()
                        break
        
        if not res or not res.data:
            return False, "Mitgliedsdaten nicht gefunden. Bitte Vorstand kontaktieren."
        
        member = res.data
        email = member.get("email") if member.get("email") else f"{member['mitgliedsnummer']}@krayfueralle.intern"
        
        # 1. Auth-Account per Admin-API anlegen (Sofort aktiv / bestätigt, keine Bestätigungsmail nötig)
        try:
            supabase.auth.admin.create_user({
                "email": email, 
                "password": password,
                "email_confirm": True  # Verhindert, dass der User unbestätigt bleibt und der Login fehlschlägt!
            })
        except Exception as e:
            if "already registered" not in str(e).lower():
                return False, f"Auth-Fehler: {str(e)}"
        
        # 2. In 'benutzer'-Tabelle eintragen (upsert verhindert Duplikat-Crashs)
        try:
            supabase.table("benutzer").upsert({
                "email": email,
                "benutzername": str(member["mitgliedsnummer"])
            }, on_conflict="email").execute()
        except Exception as e:
            return False, f"Datenbank-Fehler beim User-Anlegen: {str(e)}"
        
        return True, "Account erfolgreich aktiviert! Du kannst dich jetzt einloggen."
        
    except Exception as e:
        return False, f"Allgemeiner Fehler: {str(e)}"

def passwort_zuruecksetzen_mit_sicherheitsfrage(identifier, antwort, neues_passwort):
    """
    Prüft die Sicherheitsantwort direkt über die 'mitglieder'-Tabelle und setzt das Passwort zurück.
    """
    identifier_str = str(identifier).strip()
    res = None
    try:
        res = supabase.table("mitglieder").select("sicherheitsantwort, mitgliedsnummer, email").ilike("email", identifier_str).maybe_single().execute()
        if (not res or not res.data) and identifier_str.isdigit():
            res = supabase.table("mitglieder").select("sicherheitsantwort, mitgliedsnummer, email").eq("mitgliedsnummer", int(identifier_str)).maybe_single().execute()
        if not res or not res.data:
            res_tel = supabase.table("mitglieder").select("sicherheitsantwort, mitgliedsnummer, email, telefonnummer").not_("telefonnummer", "is", "null").execute()
            if res_tel and res_tel.data:
                clean_input = "".join(filter(str.isdigit, identifier_str))
                for row in res_tel.data:
                    if clean_input and clean_input == "".join(filter(str.isdigit, str(row.get("telefonnummer", "")))):
                        res = type('obj', (object,), {'data': row})()
                        break
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
        supabase.table("mitglieder").update({
            "rolle": neue_rolle
        }).eq("mitgliedsnummer", mitgliedsnummer).execute()
        return True, "Rolle erfolgreich aktualisiert."
    except Exception as e:
        return False, f"Fehler: {str(e)}"
