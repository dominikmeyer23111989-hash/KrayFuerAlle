import streamlit as st
import requests
from supabase import create_client
from supabase.lib.client_options import ClientOptions
from database import supabase

# --- ADMIN CLIENT SETUP ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = st.secrets["SUPABASE_KEY"]

supabase_admin = create_client(
    SUPABASE_URL, 
    SUPABASE_SERVICE_ROLE_KEY,
    options=ClientOptions(
        auto_refresh_token=False,
        persist_session=False,
    )
)

def finde_email_zu_benutzer(identifier):
    if not identifier:
        return None
    identifier_str = str(identifier).strip()
    
    try:
        res_benutzer = supabase.table("benutzer").select("email, benutzername").ilike("benutzername", identifier_str).maybe_single().execute()
        if res_benutzer and res_benutzer.data and res_benutzer.data.get("email"):
            return res_benutzer.data["email"]
    except Exception:
        pass

    try:
        res = supabase.table("mitglieder").select("email, mitgliedsnummer, telefonnummer").ilike("email", identifier_str).maybe_single().execute()
        if res and res.data:
            if res.data.get("email"): 
                return res.data["email"]
            return f"{res.data['mitgliedsnummer']}@krayfueralle.intern"
    except Exception:
        pass

    if identifier_str.isdigit():
        try:
            res = supabase.table("mitglieder").select("email, mitgliedsnummer, telefonnummer").eq("mitgliedsnummer", int(identifier_str)).maybe_single().execute()
            if res and res.data:
                if res.data.get("email"): 
                    return res.data["email"]
                return f"{res.data['mitgliedsnummer']}@krayfueralle.intern"
        except Exception:
            pass

    try:
        res_tel = supabase.table("mitglieder").select("email, mitgliedsnummer, telefonnummer").not_("telefonnummer", "is", "null").execute()
        if res_tel and res_tel.data:
            clean_input = "".join(filter(str.isdigit, identifier_str))
            if clean_input:
                for row in res_tel.data:
                    db_tel = row.get("telefonnummer")
                    if db_tel and clean_input == "".join(filter(str.isdigit, str(db_tel))):
                        if row.get("email"): 
                            return row["email"]
                        return f"{row['mitgliedsnummer']}@krayfueralle.intern"
    except Exception:
        pass
        
    return None

def login_user(identifier, password):
    email = finde_email_zu_benutzer(identifier)
    if not email:
        return {"success": False, "message": f"Benutzer '{identifier}' wurde nicht gefunden."}

    try:
        query = supabase.table("mitglieder").select("ist_gesperrt")
        if "@krayfueralle.intern" in email:
            m_nr = email.split("@")[0]
            res_gesperrt = query.eq("mitgliedsnummer", int(m_nr) if m_nr.isdigit() else m_nr).maybe_single().execute()
        else:
            res_gesperrt = query.ilike("email", email).maybe_single().execute()

        if res_gesperrt and res_gesperrt.data and res_gesperrt.data.get("ist_gesperrt", False):
            return {"success": False, "message": "Dieses Konto ist gesperrt."}
    except Exception:
        pass

    try:
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return {"success": True, "data": auth_response}
    except Exception as e: 
        return {"success": False, "message": f"Login-Fehler: {str(e)}"}

def erstes_passwort_setzen(identifier, password):
    try:
        identifier_str = str(identifier).strip()
        res = None
        
        res = supabase.table("mitglieder").select("*").ilike("email", identifier_str).maybe_single().execute()
        if (not res or not res.data) and identifier_str.isdigit():
            res = supabase.table("mitglieder").select("*").eq("mitgliedsnummer", int(identifier_str)).maybe_single().execute()
            
        if not res or not res.data:
            res_tel = supabase.table("mitglieder").select("*").not_("telefonnummer", "is", "null").execute()
            if res_tel and res_tel.data:
                clean_input = "".join(filter(str.isdigit, identifier_str))
                for row in res_tel.data:
                    if clean_input and clean_input == "".join(filter(str.isdigit, str(row.get("telefonnummer", "")))):
                        res = type('obj', (object,), {'data': row})()
                        break
        
        if not res or not res.data:
            return False, f"Mitglied mit Kennung '{identifier}' existiert nicht!"
        
        member = res.data
        email = member.get("email") if member.get("email") else f"{member['mitgliedsnummer']}@krayfueralle.intern"
        
        # Direkter REST-Aufruf zur Umgehung des supabase-py Client-Bugs
        url = f"{SUPABASE_URL}/auth/v1/admin/users"
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "email": email, 
            "password": password,
            "email_confirm": True
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code not in [200, 201]:
            err_data = response.json()
            err_msg = err_data.get("msg") or err_data.get("message") or response.text
            if "already registered" not in err_msg.lower():
                return False, f"Auth-Fehler: {err_msg}"
        
        try:
            supabase.table("benutzer").upsert({
                "email": email,
                "benutzername": str(member["mitgliedsnummer"])
            }, on_conflict="email").execute()
        except Exception as db_err:
            return False, f"Datenbank-Fehler: {str(db_err)}"
        
        return True, "Account erfolgreich aktiviert!"
        
    except Exception as e:
        return False, f"Unerwarteter Fehler: {str(e)}"

def passwort_zuruecksetzen_mit_sicherheitsfrage(identifier, antwort, neues_passwort):
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
        user = supabase_admin.auth.admin.list_users()
        target_user = [u for u in user.users if u.email == email]
        if not target_user:
            return False, "Auth-Account nicht gefunden."
            
        supabase_admin.auth.admin.update_user_by_id(target_user[0].id, {"password": neues_passwort})
        return True, "Passwort wurde erfolgreich zurückgesetzt."
    except Exception as e:
        return False, f"Fehler: {str(e)}"

def passwort_zuruecksetzen(identifier):
    email = finde_email_zu_benutzer(identifier)
    if not email or "@krayfueralle.intern" in email:
        return False, "Für dieses Konto ist keine echte E-Mail hinterlegt."
        
    try:
        supabase.auth.reset_password_email(email)
        return True, "E-Mail mit Reset-Link wurde versendet."
    except Exception as e:
        return False, f"Fehler: {str(e)}"

def update_user_role(mitgliedsnummer, neue_rolle):
    try:
        supabase.table("mitglieder").update({
            "rolle": neue_rolle
        }).eq("mitgliedsnummer", mitgliedsnummer).execute()
        return True, "Rolle erfolgreich aktualisiert."
    except Exception as e:
        return False, f"Fehler: {str(e)}"
