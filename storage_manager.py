"""
Modulo Deterministico per la gestione dello Storage e Statistiche delle quotazioni (Livello 3 - Execution).
Gestisce la persistenza in JSON/CSV, la deduplicazione e il calcolo dei KPI finanziari in stile Bloomberg/Wall Street.
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_JSON_PATH = os.path.join(DATA_DIR, "storico_prezzi.json")
DB_CSV_PATH = os.path.join(DATA_DIR, "storico_prezzi.csv")

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_quotes() -> List[Dict[str, Any]]:
    """Carica tutte le quotazioni salvate nel database JSON."""
    ensure_data_dir()
    if not os.path.exists(DB_JSON_PATH):
        return []
    try:
        with open(DB_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Errore caricamento database JSON: {e}")
        return []

def save_quotes(quotes: List[Dict[str, Any]]) -> bool:
    """Salva le quotazioni nel database JSON e aggiorna l'esportazione CSV."""
    ensure_data_dir()
    try:
        # Ordina per data crescente e scadenza
        quotes.sort(key=lambda x: (x.get("data", ""), x.get("scadenza", "")))
        
        # Scrittura JSON
        with open(DB_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)
            
        # Scrittura CSV
        if quotes:
            df = pd.DataFrame(quotes)
            df.to_csv(DB_CSV_PATH, index=False, sep=";", encoding="utf-8-sig")
            
        return True
    except Exception as e:
        print(f"Errore salvataggio database: {e}")
        return False

def add_quotes(new_quotes: List[Dict[str, Any]]) -> int:
    """
    Aggiunge nuove quotazioni deduplicando per (data, scadenza, tipo).
    Ritorna il numero di nuovi record aggiunti o aggiornati.
    """
    current_quotes = load_quotes()
    
    # Chiave univoca: data + scadenza + tipo
    existing_map = {
        f"{q.get('data')}_{q.get('scadenza')}_{q.get('tipo', 'PDT')}": q
        for q in current_quotes
    }
    
    added_count = 0
    for nq in new_quotes:
        key = f"{nq.get('data')}_{nq.get('scadenza')}_{nq.get('tipo', 'PDT')}"
        if key not in existing_map:
            existing_map[key] = nq
            added_count += 1
        else:
            # Aggiorna il record se il prezzo o la fonte differiscono
            if existing_map[key].get("prezzo") != nq.get("prezzo"):
                existing_map[key] = nq
                added_count += 1
                
    if added_count > 0:
        save_quotes(list(existing_map.values()))
        
    return added_count

def get_stats_for_scadenza(scadenza: Optional[str] = None) -> Dict[str, Any]:
    """
    Calcola statistiche avanzate in stile terminale finanziario:
    - Last Price
    - High (con data)
    - Low (con data)
    - Average
    - Variazione assoluta e percentuale (vs rilevazione precedente e vs inizio periodo)
    """
    quotes = load_quotes()
    if not quotes:
        return {}
        
    df = pd.DataFrame(quotes)
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values("data")
    
    if scadenza and scadenza != "Tutte":
        df = df[df["scadenza"].str.lower() == scadenza.lower()]
        
    if df.empty:
        return {}
        
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2] if len(df) > 1 else last_row
    first_row = df.iloc[0]
    
    high_val = df["prezzo"].max()
    high_row = df[df["prezzo"] == high_val].iloc[-1]
    
    low_val = df["prezzo"].min()
    low_row = df[df["prezzo"] == low_val].iloc[-1]
    
    avg_val = df["prezzo"].mean()
    last_price = last_row["prezzo"]
    prev_price = prev_row["prezzo"]
    first_price = first_row["prezzo"]
    
    delta_prev = last_price - prev_price
    pct_prev = (delta_prev / prev_price * 100) if prev_price else 0.0
    
    delta_total = last_price - first_price
    pct_total = (delta_total / first_price * 100) if first_price else 0.0
    
    return {
        "last_price": last_price,
        "last_date": last_row["data"].strftime("%d/%m/%Y"),
        "scadenza": last_row["scadenza"],
        "high_price": high_val,
        "high_date": high_row["data"].strftime("%d/%m/%Y"),
        "low_price": low_val,
        "low_date": low_row["data"].strftime("%d/%m/%Y"),
        "avg_price": round(avg_val, 2),
        "delta_prev": delta_prev,
        "pct_prev": pct_prev,
        "delta_total": delta_total,
        "pct_total": pct_total,
        "total_records": len(df)
    }

if __name__ == "__main__":
    quotes = load_quotes()
    print(f"Totale quotazioni caricate: {len(quotes)}")
    stats = get_stats_for_scadenza("lug-27")
    print("Statistiche lug-27:", stats)
