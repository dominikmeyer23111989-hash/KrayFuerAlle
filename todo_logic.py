import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from database import supabase 

# ==========================================
# KONFIGURATION
# ==========================================
SMTP_SERVER = "smtp.dein-provider.de" # Dein SMTP Server (z.B. smtp.gmail.com)
SMTP_PORT = 465
EMAIL_SENDER = "verein@dein-verein.de"
EMAIL_PASSWORD = "dein-app-passwort" # WICHTIG: App-Passwort, kein normales Passwort!

def send_todo_email(recipient_email, subject, body):
    """Sendet eine E-Mail über den konfigurierten SMTP-Server."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = recipient_email
    
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, recipient_email, msg.as_string())

def perform_maintenance():
    """Bereinigt alte Daten und sendet Erinnerungen für überfällige Aufgaben."""
    
    # 1. Alte Aufgaben löschen (> 6 Monate erledigt)
    try:
        six_months_ago = (datetime.now() - timedelta(days=180)).isoformat()
        supabase.table("todo") \
            .delete() \
            .eq("status", "Erledigt") \
            .lt("finished_at", six_months_ago) \
            .execute()
    except Exception as e:
        print(f"Fehler bei der Bereinigung: {e}")
    
    # 2. Erinnerungen für überfällige Aufgaben senden
    today = datetime.now().date().isoformat()
    
    # Query: Hole offene Aufgaben, die vor heute fällig waren
    # Hinweis: 'mitglieder!todo_zugewiesen_an_fkey' muss mit deinem DB-Constraint übereinstimmen!
    response = supabase.table("todo") \
        .select("titel, deadline, mitglieder!todo_zugewiesen_an_fkey(email)") \
        .eq("status", "Offen") \
        .lt("deadline", today) \
        .execute()
    
    for task in response.data:
        # Sicherheits-Check: Deadline vorhanden?
        if not task.get('deadline'):
            continue
            
        # E-Mail-Adresse extrahieren (Foreign Key Join Handling)
        member_data = task.get("mitglieder")
        recipient = None
        
        if isinstance(member_data, list) and len(member_data) > 0:
            recipient = member_data[0].get("email")
        elif isinstance(member_data, dict):
            recipient = member_data.get("email")
            
        # Nur senden, wenn wir eine E-Mail haben
        if recipient:
            subject = f"Erinnerung: To-Do '{task['titel']}' ist überfällig!"
            body = (f"Hallo,\n\ndein To-Do '{task['titel']}' hätte bis zum "
                    f"{task['deadline']} erledigt sein sollen. "
                    f"Bitte kümmere dich zeitnah darum.\n\nViele Grüße\nDein Verein")
            
            try:
                send_todo_email(recipient, subject, body)
                print(f"Erinnerung gesendet an {recipient} für Aufgabe {task['titel']}")
            except Exception as e:
                print(f"Fehler beim Mailversand an {recipient}: {e}")