"""
Applicazione Web Streamlit: Monitoraggio Quotazioni Futures Grano Duro
Scadenza Target: Luglio 2027 (lug-27)
Design: Bloomberg / Wall Street Mobile-First (Prezzo e Grafico nella stessa schermata dello smartphone).
"""

import os
import io
import math
import time
import base64
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

# Import moduli di esecuzione locali
try:
    from execution.storage_manager import load_quotes, add_quotes
    from execution.fetch_gmail_quotes import fetch_quotes_from_gmail
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "execution"))
    from storage_manager import load_quotes, add_quotes
    from fetch_gmail_quotes import fetch_quotes_from_gmail

load_dotenv()

# Configurazione Pagina Streamlit
st.set_page_config(
    page_title="Grano Duro lug-27 | Quotazioni Futures",
    page_icon="🌾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS Mobile-First: massimizza lo spazio verticale per visualizzare Prezzo + Grafico senza scroll
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700;800&display=swap');

    *, *::before, *::after {
        box-sizing: border-box;
    }

    html, body {
        overflow-x: hidden;
        max-width: 100vw;
    }

    /* Riduzione drastica padding Streamlit per mobile viewport */
    .block-container {
        padding-top: 0.35rem !important;
        padding-bottom: 0.8rem !important;
        padding-left: clamp(0.4rem, 2.5vw, 0.85rem) !important;
        padding-right: clamp(0.4rem, 2.5vw, 0.85rem) !important;
        max-width: 680px !important;
    }

    /* Sfondo scuro globale */
    .stApp {
        background-color: #030712;
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #f1f5f9;
        overflow-x: hidden;
    }

    /* Nascondi completamente l'header nativo Streamlit per evitare collisioni con toolbar/share */
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Rimuovi la striscia colorata decorativa in cima */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* Nascondi toolbar e pulsanti Streamlit nativi */
    [data-testid="stToolbar"],
    .stDeployButton,
    [data-testid="stDeployButton"],
    .stAppDeployButton,
    #MainMenu,
    [data-testid="stMainMenu"],
    .stMainMenu,
    [data-testid="main-menu-list"],
    div[data-testid="stStatusWidget"],
    div[data-testid="stConnectionStatus"],
    /* Nascondi tasto Manage App (pannello log/codice) e badge Streamlit */
    [data-testid="manage-app-button"],
    [data-testid="stManageAppButton"],
    .stManageAppButton,
    #manage-app-button,
    button[kind="manageAppButton"],
    [class*="manageApp" i],
    [class*="ManageApp" i],
    [id*="manageApp" i],
    [aria-label*="manage app" i],
    [title*="Manage app" i],
    div:has(> button[data-testid="manage-app-button"]),
    footer,
    .viewerBadge_container__1QSob,
    [class*="viewerBadge"],
    [class*="ViewerBadge"],
    /* Nascondi tassativamente tutte le icone GitHub e i link alla repository */
    [data-testid="stToolbar"] a[href*="github.com"],
    [data-testid="stToolbar"] button[title*="GitHub"],
    [data-testid="stToolbar"] [title*="GitHub"],
    [data-testid="stToolbar"] [aria-label*="GitHub" i],
    [data-testid="stToolbar"] [title*="source" i],
    [data-testid="stToolbar"] [aria-label*="source" i],
    [data-testid="stToolbar"] [title*="repository" i],
    [data-testid="stToolbar"] [title*="Fork" i],
    [data-testid="stToolbarActions"] a[href*="github.com"],
    [data-testid="stToolbarActions"] button[title*="GitHub"],
    [data-testid="stToolbarActions"] [title*="GitHub"],
    [data-testid="stToolbarActions"] [aria-label*="GitHub" i],
    [data-testid="stToolbarActions"] [title*="source" i],
    [data-testid="stToolbarActions"] [aria-label*="source" i],
    [data-testid="stToolbarActions"] [title*="repository" i],
    [data-testid="stToolbarActions"] [title*="Fork" i],
    a[href*="github.com"],
    button[title*="GitHub"],
    svg[title*="GitHub"],
    svg[aria-label*="GitHub"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Top bar compatto e fluido */
    .app-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0b1120;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 6px 12px;
        margin-bottom: 8px;
        gap: 8px;
    }
    .app-title-text {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(0.82rem, 3.6vw, 1.02rem);
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.01em;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
        line-height: 1.25;
    }
    .app-expiry-pill {
        color: #f59e0b;
        font-size: clamp(0.70rem, 2.6vw, 0.82rem);
        font-weight: 800;
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.35);
        padding: 1px 6px;
        border-radius: 4px;
        white-space: nowrap;
    }
    .app-sync-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: clamp(0.64rem, 2.4vw, 0.72rem);
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 5px;
        display: inline-block;
        width: fit-content;
    }
    .status-today {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.35);
    }
    .status-wait {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }

    /* Hero Card Prezzo Dinamica (Design fluido anti-schiacciamento) */
    .hero-box {
        background: linear-gradient(135deg, #090e1a 0%, #0f172a 100%);
        border: 1.5px solid #1e293b;
        border-radius: 10px;
        padding: clamp(10px, 3vw, 14px) clamp(12px, 3.5vw, 16px);
        margin-bottom: 8px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .hero-box::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2.5px;
        background: linear-gradient(90deg, #10b981, #f59e0b);
    }

    /* RIGA 1: Prezzo & Data (Sinistra) + Tasto Guida (Destra) */
    .hero-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
    }
    .hero-price-section {
        display: flex;
        flex-direction: column;
        min-width: 0;
    }
    .hero-price-val {
        font-family: 'Space Grotesk', sans-serif;
        font-size: clamp(1.85rem, 7.2vw, 2.45rem);
        font-weight: 800;
        color: #00ff88;
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
        line-height: 1.0;
        letter-spacing: -0.03em;
        white-space: nowrap;
    }
    .hero-price-unit {
        font-size: clamp(1.1rem, 4.2vw, 1.4rem);
        font-weight: 700;
        color: #34d399;
    }
    .hero-date-val {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: clamp(0.74rem, 2.6vw, 0.84rem);
        color: #cbd5e1;
        font-weight: 600;
        margin-top: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Tasto Guida a destra */
    .hero-action-section {
        flex: 0 0 auto;
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }

    /* Tasto Bilancia della Legge con Lampeggio Tenue */
    @keyframes law-pulse {
        0% {
            border-color: rgba(245, 158, 11, 0.35);
            box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.15), 0 2px 6px rgba(0, 0, 0, 0.4);
            color: #f59e0b;
            background: rgba(245, 158, 11, 0.08);
        }
        50% {
            border-color: rgba(245, 158, 11, 0.85);
            box-shadow: 0 0 12px 2px rgba(245, 158, 11, 0.45), inset 0 0 8px rgba(245, 158, 11, 0.2);
            color: #fef08a;
            background: rgba(245, 158, 11, 0.20);
        }
        100% {
            border-color: rgba(245, 158, 11, 0.35);
            box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.15), 0 2px 6px rgba(0, 0, 0, 0.4);
            color: #f59e0b;
            background: rgba(245, 158, 11, 0.08);
        }
    }

    .hero-law-btn {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: 10px;
        border: 1.5px solid rgba(245, 158, 11, 0.35);
        text-decoration: none !important;
        transition: all 0.25s ease;
        animation: law-pulse 2.2s infinite ease-in-out;
        cursor: pointer;
        padding: 3px;
        user-select: none;
    }
    .hero-law-btn:hover {
        transform: scale(1.08);
        border-color: #fbbf24 !important;
        box-shadow: 0 0 18px rgba(245, 158, 11, 0.7) !important;
        background: rgba(245, 158, 11, 0.3) !important;
        color: #ffffff !important;
    }
    .hero-law-btn:active {
        transform: scale(0.96);
    }
    .law-btn-icon {
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .law-btn-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.50rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        margin-top: 1px;
        line-height: 1;
        text-transform: uppercase;
    }

    /* RIGA 2: Specifiche Tecniche Orizzontali a larghezza piena (anti-schiacciamento) */
    .hero-specs-bar {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
        background: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 6px;
        padding: 4px 8px;
        margin-top: 7px;
        font-family: 'JetBrains Mono', monospace;
        font-size: clamp(0.66rem, 2.3vw, 0.73rem);
    }
    .hero-spec-tag {
        font-weight: 700;
        color: #f1f5f9;
    }
    .hero-spec-dot {
        color: #64748b;
        font-size: 0.7rem;
    }
    .hero-spec-detail {
        color: #94a3b8;
    }

    /* RIGA 3: Delta rispetto a ieri */
    .hero-delta-row {
        margin-top: 7px;
        padding-top: 6px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
    }
    .hero-delta-label {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: clamp(0.70rem, 2.4vw, 0.78rem);
        font-weight: 600;
        color: #94a3b8;
    }
    .hero-badge-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: clamp(0.74rem, 2.5vw, 0.82rem);
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 6px;
        white-space: nowrap;
    }
    .delta-up { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .delta-down { background: rgba(244, 63, 94, 0.2); color: #f43f5e; }
    .delta-zero { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }

    /* Ottimizzazione Grafico Touch: nessun blocco dello scroll nativo della pagina */
    [data-testid="stPlotlyChart"],
    .js-plotly-plot,
    .plot-container {
        touch-action: pan-y !important;
        user-select: none !important;
        -webkit-user-select: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- STATO GLOBALE E CACHE DATI -----------------
@st.cache_resource
def get_sync_state():
    return {"last_check_ts": 0}

@st.cache_data(ttl=60)
def get_cached_quotes():
    quotes = load_quotes()
    if quotes:
        return quotes
    # Ricerca di emergenza nei percorsi noti
    import json
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "data", "storico_prezzi.json"),
        os.path.join(base_dir, "storico_prezzi.json"),
        os.path.join(os.getcwd(), "data", "storico_prezzi.json"),
        os.path.join(os.getcwd(), "storico_prezzi.json"),
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    q = json.load(f)
                    if q:
                        return q
            except Exception:
                pass
    # Scansione ricorsiva completa
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.lower() == "storico_prezzi.json":
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as fp:
                        q = json.load(fp)
                        if q:
                            return q
                except Exception:
                    pass
    return []

def auto_sync_if_needed(quotes):
    """Verifica e sincronizza da Gmail nei giorni feriali se la data odierna non è presente."""
    now = datetime.now()
    # Le quotazioni vengono pubblicate solo dal lunedì al venerdì
    if now.weekday() > 4:
        return False
        
    oggi_str = now.strftime("%Y-%m-%d")
    last_date = max([q.get("data", "") for q in quotes if q.get("scadenza", "").lower() == "lug-27"], default="")
    if last_date == oggi_str:
        return False
        
    # Rate-limit GLOBALE di 10 minuti tra tutte le sessioni utente
    sync_state = get_sync_state()
    now_ts = time.time()
    if (now_ts - sync_state["last_check_ts"]) < 600:
        return False
        
    sync_state["last_check_ts"] = now_ts
    try:
        with st.spinner("⏳ Controllo nuove quotazioni Futures..."):
            extracted, _ = fetch_quotes_from_gmail(max_emails=5)
            if extracted:
                st.cache_data.clear()
                return True
    except Exception as e:
        print(f"Errore auto-sync Gmail: {e}")
    return False

# Caricamento quotazioni con cache
quotes_raw = get_cached_quotes()
if auto_sync_if_needed(quotes_raw):
    quotes_raw = get_cached_quotes()

# Filtro rigoroso su Grano Duro Luglio 2027
quotes_target = [q for q in quotes_raw if q.get("scadenza", "").lower() == "lug-27"]

if not quotes_target:
    if not quotes_raw:
        st.error("⚠️ Il database delle quotazioni (`storico_prezzi.json`) non è stato trovato.")
        st.info(f"Directory di esecuzione: `{os.getcwd()}` | File presenti: `{', '.join(os.listdir(os.getcwd())[:10])}`")
    else:
        scadenze_trovate = ", ".join(set(q.get("scadenza", "N/D") for q in quotes_raw))
        st.warning(f"Nessuna quotazione trovata per 'lug-27'. Scadenze nel file: {scadenze_trovate}")
    st.stop()

df = pd.DataFrame(quotes_target)
df["data"] = pd.to_datetime(df["data"])
df = df.sort_values("data")

# Dati ultima quotazione
last_row = df.iloc[-1]
prev_row = df.iloc[-2] if len(df) > 1 else last_row

last_p = last_row["prezzo"]
prev_p = prev_row["prezzo"]
delta_p = last_p - prev_p
pct_p = (delta_p / prev_p * 100) if prev_p else 0.0

delta_class = "delta-up" if delta_p > 0 else ("delta-down" if delta_p < 0 else "delta-zero")
delta_sign = "+" if delta_p > 0 else ""

prev_date_fmt = prev_row["data"].strftime("%d/%m")

# Rileva l'ultimo movimento reale di mercato se l'attuale è invariato
diff_rows = df[df["prezzo"] != last_p]
last_move_info = ""
if not diff_rows.empty and delta_p == 0:
    diff_r = diff_rows.iloc[-1]
    m_delta = last_p - diff_r["prezzo"]
    m_pct = (m_delta / diff_r["prezzo"] * 100) if diff_r["prezzo"] else 0.0
    m_sign = "+" if m_delta > 0 else ""
    m_class = "delta-up" if m_delta > 0 else "delta-down"
    m_date = diff_r["data"].strftime("%d/%m")
    last_move_info = f'<span style="color:#64748b; font-size:0.75rem; margin-left:6px;">(Ultimo cambio vs {m_date}: <b style="color:{"#34d399" if m_delta>0 else "#f43f5e"}">{m_sign}{m_delta:.2f} €/t</b>)</span>'

oggi_str = datetime.now().strftime("%Y-%m-%d")
last_date_str = last_row["data"].strftime("%Y-%m-%d")
is_today = (last_date_str == oggi_str)

# Traduzione mese in italiano
data_dt = last_row["data"]
mesi_it = {
    1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
    5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
    9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
}
giorni_it = {
    0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì",
    4: "Venerdì", 5: "Sabato", 6: "Domenica"
}
data_estesa = f"{giorni_it[data_dt.weekday()]} {data_dt.day} {mesi_it[data_dt.month]} {data_dt.year}"

# Logo compatto con cache ed esportazione ottimizzata (riduzione del payload del 99.8%)
@st.cache_data
def get_optimized_logo():
    base_dir = os.path.dirname(__file__)
    opt_path = os.path.join(base_dir, "logo_optimized.webp")
    src_path = os.path.join(base_dir, "Gemini_Generated_Image_6qe5g36qe5g36qe5.jfif")
    
    if not os.path.exists(opt_path) and os.path.exists(src_path):
        try:
            from PIL import Image
            img = Image.open(src_path)
            img.thumbnail((160, 160))
            img.save(opt_path, "WEBP", quality=90)
        except Exception:
            pass
            
    target = opt_path if os.path.exists(opt_path) else src_path
    if os.path.exists(target):
        with open(target, "rb") as f:
            mime = "image/webp" if target.endswith(".webp") else "image/jpeg"
            return mime, base64.b64encode(f.read()).decode()
    return None, None

logo_mime, logo_b64 = get_optimized_logo()
logo_html = f'<img src="data:{logo_mime};base64,{logo_b64}" style="width:48px; height:48px; border-radius:8px; border:1px solid #334155; object-fit:cover; box-shadow:0 2px 8px rgba(0,0,0,0.5);">' if logo_b64 else ''

# Assicura disponibilità PDF Guida Impegni in static/
# Carica il PDF autentico in memoria e preparalo per download diretto (zero 404)
@st.cache_data
def get_pdf_payload():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "Guida agli Impegni e Conferimento Grano Duro.pdf"),
        os.path.join(base_dir, "static", "Guida_Impegni_e_Conferimento_Grano_Duro.pdf"),
        os.path.join(base_dir, "static", "Guida agli Impegni e Conferimento Grano Duro.pdf"),
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "rb") as f:
                    data = f.read()
                    return data, base64.b64encode(data).decode("utf-8")
            except Exception:
                pass
    return None, ""

pdf_bytes, pdf_b64 = get_pdf_payload()

# ----------------- 1. TOP BAR COMPATTA CON LOGO -----------------
status_badge = (
    '<span class="app-sync-status status-today">🟢 Aggiornato a Oggi</span>'
    if is_today else
    f'<span class="app-sync-status status-wait">⏳ {data_dt.strftime("%d/%m")} (In attesa oggi)</span>'
)

topbar_html = f"""<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px;">
<div>
<div class="app-title-text">
<span>QUOTAZIONE FUTURES 🌾 GRANO DURO</span>
<span class="app-expiry-pill">LUG-27</span>
</div>
<div style="margin-top: 4px;">
{status_badge}
</div>
</div>
<div style="flex: 0 0 auto;">
{logo_html}
</div>
</div>"""
st.markdown(topbar_html, unsafe_allow_html=True)

# ----------------- 2. HERO CARD PREZZO ATTUALE + DATA (RESPONSIVE ANTI-SCHIACCIAMENTO) -----------------
pdf_link_attr = f'href="data:application/pdf;base64,{pdf_b64}" target="_blank" rel="noopener noreferrer"' if pdf_b64 else 'href="#"'

hero_html = f"""<div class="hero-box">
<div class="hero-top-row">
<div class="hero-price-section">
<div class="hero-price-val">{last_p:.2f} <span class="hero-price-unit">€/t</span></div>
<div class="hero-date-val">📅 <b>{data_estesa}</b></div>
</div>
<div class="hero-action-section">
<a {pdf_link_attr} class="hero-law-btn" title="Apri Guida agli Impegni e Conferimento Grano Duro (PDF)">
<div class="law-btn-icon">
<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
<path d="M12 3v18"/>
<path d="M7 21h10"/>
<path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>
<path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>
</svg>
</div>
<span class="law-btn-text">GUIDA</span>
</a>
</div>
</div>
<div class="hero-specs-bar">
<span class="hero-spec-tag">Prezzo base PDT</span>
<span class="hero-spec-dot">•</span>
<span class="hero-spec-detail">P.S. &ge; 78</span>
<span class="hero-spec-dot">•</span>
<span class="hero-spec-detail">Prot. &ge; 13,5%</span>
</div>
<div class="hero-delta-row">
<span class="hero-delta-label">Rispetto a ieri ({prev_date_fmt} @ {prev_p:.2f} €/t):</span>
<span class="hero-badge-delta {delta_class}">{delta_sign}{delta_p:.2f} €/t ({delta_sign}{pct_p:.2f}%)</span>
{last_move_info}
</div>
</div>"""
st.markdown(hero_html, unsafe_allow_html=True)

# ----------------- 3. GRAFICO WALL STREET CON SCALATURA DINAMICA BASATA SU DEVIAZIONE STANDARD -----------------

# Calcolo statistiche per la sola scalatura dinamica dell'asse Y
p_min = df["prezzo"].min()
p_max = df["prezzo"].max()
p_std = df["prezzo"].std()
if pd.isna(p_std) or p_std == 0:
    p_std = 3.0

# SCALATURA DINAMICA ASSE Y:
pad_y = 1.25 * p_std
y_min_dyn = max(0, math.floor((p_min - pad_y) / 5) * 5)
y_max_dyn = math.ceil((p_max + pad_y) / 5) * 5

# Creazione Grafico Plotly Wall Street BLOCCATO (Statico, anti-zoom touch)
fig = go.Figure()

# Linea Prezzo Fluorescente con Area Sfumata (Nessun tooltip o hover interattivo)
fig.add_trace(go.Scatter(
    x=df["data"],
    y=df["prezzo"],
    mode='lines+markers',
    name='Luglio 2027',
    line=dict(color='#00ff88', width=2.4),
    marker=dict(size=4, color='#00ff88'),
    fill='tozeroy',
    fillcolor='rgba(0, 255, 136, 0.08)',
    hoverinfo='none',
    hovertext=None
))

# Callout fisso sull'ultimo prezzo (in italiano, chiaramente visibile senza toccare)
mese_abbr = mesi_it[last_row['data'].month][:3].lower()
callout_label = f"{last_row['data'].day} {mese_abbr} @ {last_p:.2f} €/t"

fig.add_annotation(
    x=last_row["data"],
    y=last_p,
    text=f"<b>{callout_label}</b>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.0,
    arrowwidth=1.2,
    arrowcolor="#fbbf24",
    ax=-42,
    ay=-32,
    bgcolor="rgba(0, 0, 0, 0.9)",
    bordercolor="#fbbf24",
    borderwidth=1.2,
    font=dict(color="#fbbf24", size=11, family="Space Grotesk")
)

# Layout Wall Street Dark BLOCCATO:
# Nessuna barra verticale scorrevole, nessun cursore, nessun zoom o pan touch
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor='#000000',
    plot_bgcolor='#000000',
    height=350,  # Perfetto per stare nella medesima schermata smartphone insieme alla Hero Card
    margin=dict(l=8, r=48, t=12, b=24),
    hovermode=False,  # Disattiva completamente la barra verticale cursore e i tooltip
    dragmode=False,   # Disattiva il drag/box-zoom
    xaxis=dict(
        fixedrange=True, # Blocca qualsiasi zoom/pan sull'asse X
        showgrid=True,
        gridcolor='#172033',
        gridwidth=0.6,
        linecolor='#334155',
        tickfont=dict(family="JetBrains Mono", color="#94a3b8", size=10),
        tickformat="%b %y",
        showspikes=False
    ),
    yaxis=dict(
        side='right', # Quotazioni a destra stile terminale
        range=[y_min_dyn, y_max_dyn], # Scalatura dinamica con Deviazione Standard
        fixedrange=True, # Blocca qualsiasi zoom/pan sull'asse Y
        showgrid=True,
        gridcolor='#172033',
        gridwidth=0.6,
        linecolor='#334155',
        tickfont=dict(family="JetBrains Mono", color="#94a3b8", size=10),
        ticksuffix=" €",
        zeroline=False,
        showspikes=False
    ),
    showlegend=False
)

# Configurazione Plotly statica pura (staticPlot=True disattiva tutti i gesti touch/mouse)
plotly_config = {
    'displayModeBar': False,
    'staticPlot': True,
    'scrollZoom': False,
    'doubleClick': False,
    'showAxisDragHandles': False,
    'showAxisRangeEntryBoxes': False
}

try:
    st.plotly_chart(fig, width="stretch", config=plotly_config)
except TypeError:
    st.plotly_chart(fig, use_container_width=True, config=plotly_config)


