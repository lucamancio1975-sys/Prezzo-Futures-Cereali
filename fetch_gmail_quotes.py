"""
Modulo Deterministico per la connessione IMAP a Gmail e il recupero delle email con allegati PDF delle quotazioni.
Conforme all'architettura a 3 livelli (Livello 3 - Execution).
"""

import os
import imaplib
import email
from email.header import decode_header
import tempfile
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Import dei moduli di esecuzione locali
try:
    from execution.parse_pdf_quotazioni import extract_quotes_from_pdf, extract_quotes_from_text
    from execution.storage_manager import add_quotes
except ImportError:
    from parse_pdf_quotazioni import extract_quotes_from_pdf, extract_quotes_from_text
    from storage_manager import add_quotes

load_dotenv()

def decode_mime_words(s: str) -> str:
    """Decodifica oggetti email codificati (es. =?utf-8?B?...?=)"""
    if not s:
        return ""
    decoded_fragments = decode_header(s)
    res = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            res.append(fragment.decode(encoding or 'utf-8', errors='replace'))
        else:
            res.append(str(fragment))
    return "".join(res)

def fetch_quotes_from_gmail(
    user: str = None,
    password: str = None,
    server: str = "imap.gmail.com",
    folder: str = "INBOX",
    search_criteria: str = 'ALL',
    max_emails: int = 15
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Si connette a Gmail via IMAP SSL, scansiona le ultime email ricevute,
    estrae gli allegati PDF o il testo, ricava le quotazioni di Grano Duro
    e le inserisce nel database.
    
    Ritorna una tupla: (quotazioni_estratte, log_messaggi)
    """
    logs = []
    user = user or os.getenv("GMAIL_USER")
    password = password or os.getenv("GMAIL_APP_PASSWORD")

    # Supporto per Streamlit Cloud Secrets
    if not user or not password:
        try:
            import streamlit as st
            if not user and "GMAIL_USER" in st.secrets:
                user = st.secrets["GMAIL_USER"]
            if not password and "GMAIL_APP_PASSWORD" in st.secrets:
                password = st.secrets["GMAIL_APP_PASSWORD"]
        except Exception:
            pass

    if not user or not password:
        logs.append("⚠️ Credenziali Gmail non configurate (impostare GMAIL_USER e GMAIL_APP_PASSWORD nel file .env o nei Secrets di Streamlit).")
        return [], logs

    all_extracted_quotes = []
    import socket
    socket.setdefaulttimeout(10.0)

    try:
        logs.append(f"Connessione sicura a {server} per l'account {user}...")
        mail = imaplib.IMAP4_SSL(server, timeout=10.0)
        mail.login(user, password)
        mail.select(folder)
        logs.append("Connessione IMAP stabilita con successo.")

        # Ricerca email
        status, data = mail.search(None, search_criteria)
        if status != 'OK' or not data[0]:
            logs.append("Nessuna email trovata con i criteri specificati.")
            mail.logout()
            return [], logs

        mail_ids = data[0].split()
        logs.append(f"Trovate {len(mail_ids)} email totali. Esame delle ultime {min(len(mail_ids), max_emails)}...")

        # Esamina a ritroso (dalla più recente)
        recent_ids = mail_ids[-max_emails:]
        recent_ids.reverse()

        for mid in recent_ids:
            res, msg_data = mail.fetch(mid, '(RFC822)')
            if res != 'OK':
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject = decode_mime_words(msg.get("Subject", ""))
            sender = decode_mime_words(msg.get("From", ""))
            date_hdr = msg.get("Date", "")

            # Controlla se la mail è inerente (quotazioni, futures, pdt, o mittente consorzi)
            is_relevant = any(k in subject.lower() for k in ["quotazion", "futures", "pdt", "pmg", "grano", "prezzi"]) or \
                          "consorziagrari" in sender.lower()

            # Estrai data da email header come data fallback
            email_date = None
            try:
                parsed_tuple = email.utils.parsedate_to_datetime(date_hdr)
                if parsed_tuple:
                    email_date = parsed_tuple.strftime("%Y-%m-%d")
            except Exception:
                pass

            # Estrai corpo e allegati
            extracted_from_this_email = []
            with tempfile.TemporaryDirectory() as tmp_dir:
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    # Caso A: Allegato PDF
                    if "attachment" in content_disposition or content_type == "application/pdf":
                        filename = part.get_filename()
                        if filename:
                            filename = decode_mime_words(filename)
                            if filename.lower().endswith(".pdf"):
                                filepath = os.path.join(tmp_dir, filename)
                                with open(filepath, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                                logs.append(f"Trovato allegato PDF: '{filename}' (Email del {date_hdr}, Oggetto: '{subject}')")
                                try:
                                    quotes = extract_quotes_from_pdf(filepath)
                                    for q in quotes:
                                        if email_date and (not q.get("data") or q.get("data") == email_date):
                                            q["data"] = email_date
                                    if quotes:
                                        extracted_from_this_email.extend(quotes)
                                        logs.append(f" -> Estratte {len(quotes)} quotazioni dal PDF '{filename}'.")
                                except Exception as err:
                                    logs.append(f" -> Errore parsing PDF: {err}")

                    # Caso B: Testo della mail (se non abbiamo ancora estratto nulla o come fallback)
                    elif content_type in ["text/plain", "text/html"] and not extracted_from_this_email and is_relevant:
                        try:
                            payload = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            if "grano duro" in payload.lower() and ("eur/ton" in payload.lower() or "€/t" in payload.lower()):
                                quotes = extract_quotes_from_text(payload, source_name=f"Email ({subject[:30]})")
                                for q in quotes:
                                    if email_date and (not q.get("data") or q.get("data") == email_date):
                                        q["data"] = email_date
                                if quotes:
                                    extracted_from_this_email.extend(quotes)
                                    logs.append(f" -> Estratte {len(quotes)} quotazioni dal testo dell'email: '{subject}'.")
                        except Exception:
                            pass

            if extracted_from_this_email:
                all_extracted_quotes.extend(extracted_from_this_email)

        mail.logout()

        # Deduplica e salva nel database
        if all_extracted_quotes:
            added = add_quotes(all_extracted_quotes)
            logs.append(f"✅ Sincronizzazione completata: {added} nuove quotazioni archiviate nel database.")
        else:
            logs.append("ℹ️ Nessuna nuova quotazione di Grano Duro rilevata nelle email scansionate.")

    except Exception as e:
        logs.append(f"❌ Errore durante il collegamento a Gmail: {str(e)}")

    return all_extracted_quotes, logs

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("Test modulo Gmail Fetcher...")
    q, l = fetch_quotes_from_gmail()
    for line in l:
        print(line)
