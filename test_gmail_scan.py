import os
import sys
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

load_dotenv()

user = os.getenv("GMAIL_USER")
pwd = os.getenv("GMAIL_APP_PASSWORD")

print(f"Tentativo connessione IMAP per: {user}...")

try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(user, pwd)
    mail.select("INBOX")
    print("Connessione riuscita con successo!")

    # Cerca tutte le email
    status, data = mail.search(None, "ALL")
    if status == "OK" and data[0]:
        mail_ids = data[0].split()
        print(f"Totale email trovate nella casella INBOX: {len(mail_ids)}")
        
        # Ispeziona le email (fino a 50)
        to_inspect = mail_ids[-50:]
        print(f"Esame delle ultime {len(to_inspect)} email:")
        for mid in to_inspect:
            res, msg_data = mail.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
            if res == 'OK':
                header_data = msg_data[0][1].decode('utf-8', errors='ignore')
                print("--------------------------------------------------")
                print(f"ID {mid.decode()}:")
                for line in header_data.strip().split('\r\n'):
                    if any(line.startswith(k) for k in ["Subject:", "From:", "Date:"]):
                        print(" ", line)
    else:
        print("Nessuna email presente nella INBOX.")

    mail.logout()

except Exception as e:
    print(f"Errore connessione: {e}")
