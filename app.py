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

    /* Riduzione drastica padding Streamlit per mobile viewport */
    .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        max-width: 680px !important;
    }

    /* Sfondo scuro globale */
    .stApp {
        background-color: #030712;
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #f1f5f9;
    }

    /* Header Streamlit: trasparente e discreto per preservare solo il simbolo del creator */
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.2rem !important;
        padding-right: 0.75rem !important;
        z-index: 99 !important;
    }

    /* Rimuovi la striscia colorata decorativa in cima */
    [data-testid="stDecoration"] {
        display: none !important;
    }

    /* Nascondi il pulsante Deploy e il menu hamburger Streamlit */
    .stDeployButton,
    [data-testid="stDeployButton"],
    #MainMenu {
        display: none !important;
    }

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
    svg[aria-label*="GitHub"],
    /* Nascondi footer Streamlit e badge viewer */
    footer,
    .viewerBadge_container__1QSob,
    [class*="viewerBadge"] {
        display: none !important;
    }

    /* Header compatto */
    .app-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0b1120;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 8px 14px;
        margin-bottom: 10px;
    }
    .app-title-text {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.98rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.01em;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .app-sync-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 5px;
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

    /* Hero Card Prezzo Compatta (Ottimizzata Mobile) */
    .hero-box {
        background: linear-gradient(135deg, #090e1a 0%, #0f172a 100%);
        border: 1.5px solid #1e293b;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
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
    .hero-content-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
    }
    .hero-left-col {
        flex: 0 0 auto;
    }
    .hero-price-val {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.35rem;
        font-weight: 800;
        color: #00ff88; /* Verde brillante luminoso */
        text-shadow: 0 0 20px rgba(0, 255, 136, 0.4);
        line-height: 1.0;
        letter-spacing: -0.03em;
    }
    .hero-date-val {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.82rem;
        color: #cbd5e1;
        font-weight: 600;
        margin-top: 4px;
    }

    /* Colonna centrale: note qualitative spostate verso il centro */
    .hero-center-col {
        flex: 1 1 auto;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding-left: 10px;
        margin-left: 4px;
        border-left: 1px solid rgba(255, 255, 255, 0.12);
        min-width: 0;
    }
    .hero-subnote-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        font-weight: 700;
        color: #e2e8f0;
        line-height: 1.2;
    }
    .hero-subnote-params {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.67rem;
        color: #94a3b8;
        line-height: 1.25;
        margin-top: 2px;
    }

    /* Colonna destra: Tasto bilancia della legge */
    .hero-right-col {
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
        width: 50px;
        height: 50px;
        border-radius: 10px;
        border: 1.5px solid rgba(245, 158, 11, 0.35);
        text-decoration: none !important;
        transition: all 0.25s ease;
        animation: law-pulse 2.2s infinite ease-in-out;
        cursor: pointer;
        padding: 4px;
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
        width: 22px;
        height: 22px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .law-btn-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.52rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        margin-top: 1px;
        line-height: 1;
        text-transform: uppercase;
    }

    .hero-badge-delta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.84rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        white-space: nowrap;
    }
    .delta-up { background: rgba(16, 185, 129, 0.2); color: #34d399; }
    .delta-down { background: rgba(244, 63, 94, 0.2); color: #f43f5e; }
    .delta-zero { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }
    
    .hero-subnote {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        color: #94a3b8;
    }

    .hero-delta-row {
        margin-top: 8px;
        padding-top: 7px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 7px;
    }
    .hero-delta-label {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.78rem;
        font-weight: 600;
        color: #94a3b8;
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

# ----------------- 1. TOP BAR COMPATTA CON LOGO -----------------
status_badge = (
    '<span class="app-sync-status status-today">🟢 Aggiornato a Oggi</span>'
    if is_today else
    f'<span class="app-sync-status status-wait">⏳ {data_dt.strftime("%d/%m")} (In attesa oggi)</span>'
)

st.markdown(f"""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 8px;">
    <div>
        <div class="app-title-text">
            <span>QUOTAZIONE FUTURES 🌾 GRANO DURO</span>
            <span style="color:#f59e0b; font-size:0.85rem; font-weight:700;">LUG-27</span>
        </div>
        <div style="margin-top: 4px;">
            {status_badge}
        </div>
    </div>
    <div>
        {logo_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- 2. HERO CARD PREZZO ATTUALE + DATA -----------------
st.markdown(f"""
<div class="hero-box">
    <div class="hero-content-row">
        <div class="hero-left-col">
            <div class="hero-price-val">{last_p:.2f} <span style="font-size:1.4rem; font-weight:700; color:#34d399;">€/t</span></div>
            <div class="hero-date-val">📅 <b>{data_estesa}</b></div>
        </div>
        <div class="hero-center-col">
            <div class="hero-subnote-title">Prezzo base PDT</div>
            <div class="hero-subnote-params">P.S. &ge; 78 | Prot. &ge; 13,5%</div>
        </div>
        <div class="hero-right-col">
            <a href="app/static/Guida_Impegni_e_Conferimento_Grano_Duro.pdf" target="_blank" rel="noopener noreferrer" class="hero-law-btn" title="Apri Guida agli Impegni e Conferimento Grano Duro (PDF)">
                <div class="law-btn-icon">
                    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
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
    <div class="hero-delta-row">
        <span class="hero-delta-label">Rispetto a ieri ({prev_date_fmt} @ {prev_p:.2f} €/t):</span>
        <span class="hero-badge-delta {delta_class}">
            {delta_sign}{delta_p:.2f} €/t ({delta_sign}{pct_p:.2f}%)
        </span>
        {last_move_info}</div>
</div>
""", unsafe_allow_html=True)

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

# Creazione Grafico Plotly Wall Street (Puro, senza riferimenti storici o medie)
fig = go.Figure()

# Linea Prezzo Fluorescente con Area Sfumata
fig.add_trace(go.Scatter(
    x=df["data"],
    y=df["prezzo"],
    mode='lines+markers',
    name='Luglio 2027',
    line=dict(color='#00ff88', width=2.4),
    marker=dict(size=4, color='#00ff88'),
    fill='tozeroy',
    fillcolor='rgba(0, 255, 136, 0.08)',
    hovertemplate="<b>%{x|%d/%m/%Y}:</b> %{y:.2f} €/t<extra></extra>"
))

# Callout sull'ultimo prezzo
fig.add_annotation(
    x=last_row["data"],
    y=last_p,
    text=f"<b>{last_row['data'].strftime('%d %b').lower()} @ {last_p:.1f} €/t</b>",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.0,
    arrowwidth=1.2,
    arrowcolor="#fbbf24",
    ax=-40,
    ay=-35,
    bgcolor="rgba(0, 0, 0, 0.9)",
    bordercolor="#fbbf24",
    borderwidth=1.2,
    font=dict(color="#fbbf24", size=11, family="Space Grotesk")
)

# Layout Wall Street Dark (Altezza ottimizzata per stare nella medesima schermata smartphone)
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor='#000000',
    plot_bgcolor='#000000',
    height=370,  # Perfetto per la visualizzazione verticale su smartphone insieme alla Hero Card
    margin=dict(l=5, r=48, t=10, b=20),
    xaxis=dict(
        showgrid=True,
        gridcolor='#172033',
        gridwidth=0.6,
        linecolor='#334155',
        tickfont=dict(family="JetBrains Mono", color="#94a3b8", size=10),
        tickformat="%b %y"
    ),
    yaxis=dict(
        side='right', # Quotazioni a destra stile terminale
        range=[y_min_dyn, y_max_dyn], # Scalatura dinamica con Deviazione Standard
        showgrid=True,
        gridcolor='#172033',
        gridwidth=0.6,
        linecolor='#334155',
        tickfont=dict(family="JetBrains Mono", color="#94a3b8", size=10),
        ticksuffix=" €",
        zeroline=False
    ),
    hovermode='x unified',
    showlegend=False
)

try:
    st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})
except TypeError:
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


