"""
Script di Backfill: scansiona tutte le email storiche da giugno 2026 a oggi
ed estrae l'intera serie storica reale delle quotazioni del Grano Duro.
"""

import os
import sys
import imaplib
import email
from email.header import decode_header
import tempfile
from dotenv import load_dotenv

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

load_dotenv()

# Import moduli di esecuzione
try:
    from execution.parse_pdf_quotazioni import extract_quotes_from_pdf, extract_quotes_from_text, parse_data_string
    from execution.storage_manager import add_quotes, load_quotes
except ImportError:
    from parse_pdf_quotazioni import extract_quotes_from_pdf, extract_quotes_from_text, parse_data_string
    from storage_manager import add_quotes, load_quotes

user = os.getenv("GMAIL_USER")
pwd = os.getenv("GMAIL_APP_PASSWORD")

def decode_mime(s):
    if not s:
        return ""
    fragments = decode_header(s)
    res = []
    for frag, enc in fragments:
        if isinstance(frag, bytes):
            res.append(frag.decode(enc or 'utf-8', errors='replace'))
        else:
            res.append(str(frag))
    return "".join(res)

print(f"=== AVVIO BACKFILL STORICO GMAIL PER {user} ===")
mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(user, pwd)
mail.select("INBOX")

# Cerca email con 'Quotazioni' o 'Prezzi' o da CAI
status, data = mail.search(None, 'ALL')
if status != 'OK' or not data[0]:
    print("Nessuna email trovata.")
    sys.exit(0)

all_ids = data[0].split()
print(f"Scansione di {len(all_ids)} email totali...")

all_extracted = []

for idx, mid in enumerate(all_ids):
    res, msg_data = mail.fetch(mid, '(RFC822)')
    if res != 'OK':
        continue
        
    msg = email.message_from_bytes(msg_data[0][1])
    subject = decode_mime(msg.get("Subject", ""))
    sender = decode_mime(msg.get("From", ""))
    date_hdr = msg.get("Date", "")
    
    # Filtra solo email inerenti quotazioni
    if not ("quotazion" in subject.lower() or "prezzi" in subject.lower() or "mancini" in sender.lower() or "citroni" in sender.lower()):
        continue
        
    # Estrai data da email header come data fallback
    email_date = None
    try:
        parsed_tuple = email.utils.parsedate_to_datetime(date_hdr)
        if parsed_tuple:
            email_date = parsed_tuple.strftime("%Y-%m-%d")
    except Exception:
        pass
        
    quotes_from_mail = []
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disp = str(part.get("Content-Disposition"))
            
            # Se allegato PDF
            if "attachment" in content_disp or content_type == "application/pdf":
                filename = decode_mime(part.get_filename() or "")
                if filename.lower().endswith(".pdf"):
                    fpath = os.path.join(tmp_dir, filename)
                    with open(fpath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    try:
                        q_pdf = extract_quotes_from_pdf(fpath)
                        # Se il parser non ha trovato la data nel PDF, usa la data dell'email
                        for q in q_pdf:
                            if email_date and (not q.get("data") or q.get("data") == email_date):
                                q["data"] = email_date
                        quotes_from_mail.extend(q_pdf)
                    except Exception as e:
                        pass
                        
            # Se non trovato nel PDF, prova nel corpo testo
            elif content_type in ["text/plain", "text/html"] and not quotes_from_mail:
                try:
                    payload = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    if "grano duro" in payload.lower() and ("eur/ton" in payload.lower() or "€/t" in payload.lower()):
                        q_txt = extract_quotes_from_text(payload, source_name="Corpo Email")
                        for q in q_txt:
                            if email_date and (not q.get("data") or q.get("data") == email_date):
                                q["data"] = email_date
                        quotes_from_mail.extend(q_txt)
                except Exception:
                    pass

    if quotes_from_mail:
        print(f"[{idx+1}/{len(all_ids)}] {email_date} | {subject[:45]} -> Trovate {len(quotes_from_mail)} quotazioni:")
        for q in quotes_from_mail:
            print(f"    • Scadenza: {q['scadenza']} | Prezzo: {q['prezzo']} €/t (Data: {q['data']})")
        all_extracted.extend(quotes_from_mail)

mail.logout()

print(f"\nTotale quotazioni estratte da Gmail: {len(all_extracted)}")
if all_extracted:
    # Salviamo nel database
    added = add_quotes(all_extracted)
    print(f"✅ Database aggiornato: {added} record scritti o aggiornati.")
    
quotes_final = load_quotes()
print(f"Totale quotazioni complessive nel database: {len(quotes_final)}")
