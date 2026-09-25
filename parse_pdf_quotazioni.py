"""
Modulo Deterministico per l'estrazione delle quotazioni Grano Duro da PDF CAI (PDT/PMG) e da testo email.
Conforme all'architettura a 3 livelli (Livello 3 - Execution).
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import pypdf

# Mapping mesi in italiano per parsing date
MESI_IT = {
    'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6,
    'lug': 7, 'ago': 8, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12,
    'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
    'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
}

def parse_data_string(data_str: str) -> Optional[str]:
    """Converte date come '18-set-26' o '18 settembre 2026' in 'YYYY-MM-DD'."""
    data_str = data_str.strip().lower()
    
    # Formato '18-set-26' o '18-set-2026'
    m_short = re.search(r'(\d{1,2})[-/\s]([a-z]{3})[-/\s](\d{2,4})', data_str)
    if m_short:
        giorno, mese_txt, anno_raw = m_short.groups()
        mese = MESI_IT.get(mese_txt)
        if mese:
            anno = int(anno_raw)
            if anno < 100:
                anno += 2000
            return f"{anno:04d}-{mese:02d}-{int(giorno):02d}"
            
    # Formato '18 settembre 2026'
    m_long = re.search(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})', data_str)
    if m_long:
        giorno, mese_txt, anno = m_long.groups()
        mese = MESI_IT.get(mese_txt)
        if mese:
            return f"{int(anno):04d}-{mese:02d}-{int(giorno):02d}"
            
    return None

def extract_quotes_from_text(text: str, source_name: str = "Email/PDF") -> List[Dict[str, Any]]:
    """
    Estrae le quotazioni di GRANO DURO da un blocco di testo (estratto da PDF o corpo email).
    Ritorna una lista di dizionari con i dati strutturati.
    """
    results = []
    
    # 1. Trova la data delle quotazioni
    data_quotazione = None
    
    # Prova a cercare 'Quotazioni valide il: 18-set-26' o 'Quotazioni indicative del: 18-set-26'
    m_valide = re.search(r'Quotazioni\s+(?:valide|indicative)\s+(?:il|del)\s*:\s*([0-9]{1,2}-[a-z]{3}-[0-9]{2,4})', text, re.IGNORECASE)
    if m_valide:
        data_quotazione = parse_data_string(m_valide.group(1))
        
    if not data_quotazione:
        # Cerca 'odierne: 18 settembre 2026'
        m_odierne = re.search(r'odierne\s*:\s*([0-9]{1,2}\s+[a-z]+\s+[0-9]{4})', text, re.IGNORECASE)
        if m_odierne:
            data_quotazione = parse_data_string(m_odierne.group(1))

    if not data_quotazione:
        # Fallback a oggi
        data_quotazione = datetime.now().strftime("%Y-%m-%d")

    # 2. Cerca la sezione GRANO DURO
    # Cerca la sezione GRANO DURO fino alla successiva sezione merceologica o note
    pattern_sezione = re.search(r'GRANO\s+DURO\b(.*?)(?:GRANO\s+TENERO|MAIS|SOIA|COLZA|Ricordiamo|$)', text, re.DOTALL | re.IGNORECASE)
    blocco_gd = pattern_sezione.group(1) if pattern_sezione else text

    # 3. Estrazione righe di scadenza e prezzo, es.:
    # lug-27 261 Eur/ton
    # lug-28 263 Eur/ton
    # oppure: ott-27 203 Eur/ton 225 Eur/ton
    righe_scadenza = re.findall(r'([a-z]{3}-\d{2})\s+([0-9]+(?:\.[0-9]+)?)\s*(?:Eur/ton|€/t|€/ton)', blocco_gd, re.IGNORECASE)
    
    for scadenza, prezzo_str in righe_scadenza:
        scad = scadenza.lower()
        # Escludi lug-26 come da specifica utente (manteniamo solo lug-27 e lug-28)
        if scad == 'lug-26':
            continue
        prezzo = float(prezzo_str)
        results.append({
            "data": data_quotazione,
            "scadenza": scad,
            "prezzo": prezzo,
            "tipo": "PDT",
            "prodotto": "GRANO DURO",
            "fonte": source_name
        })

    return results

def extract_quotes_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """Estrae le quotazioni direttamente da un file PDF allegato."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File PDF non trovato: {pdf_path}")
        
    full_text = ""
    with open(pdf_path, 'rb') as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

    filename = os.path.basename(pdf_path)
    return extract_quotes_from_text(full_text, source_name=f"PDF ({filename})")

if __name__ == "__main__":
    # Test locale con il file di esempio
    sample_pdf = os.path.join(os.path.dirname(__file__), "..", "PDT  PMG.pdf")
    if os.path.exists(sample_pdf):
        print(f"Collaudo estrazione su: {sample_pdf}")
        quotes = extract_quotes_from_pdf(sample_pdf)
        print("Risultato estrazione:")
        for q in quotes:
            print(f" - Data: {q['data']} | Scadenza: {q['scadenza']} | Prezzo: {q['prezzo']} €/t | Tipo: {q['tipo']}")
    else:
        print("File di esempio non trovato.")
