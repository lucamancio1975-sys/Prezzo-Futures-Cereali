# 🌾 Futures Grano Duro — Terminale di Monitoraggio Quotazioni (Stile Wall Street)

Applicazione web in **Streamlit** per il monitoraggio e l'archiviazione automatica delle quotazioni Futures del Grano Duro emesse da Consorzi Agrari d'Italia (CAI), con estrazione deterministica da email Gmail e allegati PDF (`PDT  PMG.pdf`).

Grafica e visualizzazione analitica ispirata ai terminali finanziari di **Wall Street / Bloomberg**.

---

## 🚀 Funzionalità Principali

1. **Dashboard Stile Bloomberg Terminal:**
   - Tema Dark Navy / Black ad alto contrasto;
   - Grafico interattivo Plotly con linea neon, area sfumata e asse quotazioni sulla destra;
   - Box statistico Bloomberg in alto: `Last Price`, `High`, `Average`, `Low`;
   - Callout dinamici per massimi, minimi e variazione percentuale.
2. **Estrazione Automatica da Gmail & PDF:**
   - Connessione IMAP SSL protetta;
   - Parser deterministico che estrae data, scadenze (`lug-27`, `lug-28`) e prezzi in €/ton dal PDF e dal corpo email;
3. **Database Versionato su GitHub:**
   - I dati risiedono in `data/storico_prezzi.json` e `data/storico_prezzi.csv`;
   - Deduplicazione automatica dei record per data e scadenza;
4. **Automazione Gratuita con GitHub Actions:**
   - Workflow schedulato (`.github/workflows/daily_sync.yml`) che gira dal lunedì al venerdì, estrae le nuove quotazioni da Gmail ed effettua il `git commit` automatico;
5. **Esportazione Dati:**
   - Download immediato dello storico completo in formato Excel (.xlsx) e CSV (.csv).

---

## 🔑 Cosa Serve da Gmail (Istruzioni per l'Utente)

Per collegare la casella di posta servono **2 soli parametri**:
1. **L'indirizzo Gmail:** ad esempio `tuaemail@gmail.com`;
2. **Una Password per le app (16 caratteri):**
   - Vai su [myaccount.google.com/security](https://myaccount.google.com/security);
   - Assicurati che sia attiva la **Verifica in due passaggi**;
   - Cerca *"Password per le app"* (oppure visita direttamente [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords));
   - Inserisci un nome (es. `Futures Grano`) e clicca su **Crea**;
   - Copia la password generata di 16 caratteri (es. `xxxx yyyy zzzz wwww`).

---

## 💻 Esecuzione in Locale

1. **Clona o apri la cartella del progetto:**
   ```bash
   cd "APP ON LINE PER VISUALIZZARE PREZZO GIORNALIERO"
   ```

2. **Crea il file `.env` con le tue credenziali Gmail:**
   ```bash
   copy .env.example .env
   ```
   Compila con i tuoi dati:
   ```env
   GMAIL_USER=tuaemail@gmail.com
   GMAIL_APP_PASSWORD=xxxx yyyy zzzz wwww
   ```

3. **Installa le dipendenze:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Avvia l'applicazione Streamlit:**
   ```bash
   streamlit run app.py
   ```

---

## 🌐 Pubblicazione su GitHub e Streamlit Community Cloud

### Passo 1: Caricamento su GitHub
1. Crea un nuovo repository su GitHub (es. `futures-grano-duro`);
2. Esegui il push dei file:
   ```bash
   git init
   git add .
   git commit -m "Primo commit: App Futures Grano Duro"
   git branch -M main
   git remote add origin https://github.com/TUO-USERNAME/futures-grano-duro.git
   git push -u origin main
   ```

### Passo 2: Configurazione Secret su GitHub (per l'automazione)
Nel repository GitHub:
- Vai su **Settings > Secrets and variables > Actions**;
- Aggiungi i due Secret:
  * `GMAIL_USER`: la tua email Gmail;
  * `GMAIL_APP_PASSWORD`: la password per le app di 16 lettere.

### Passo 3: Deploy su Streamlit Community Cloud (Gratuito)
1. Vai su [share.streamlit.io](https://share.streamlit.io);
2. Clicca su **New app**;
3. Seleziona il tuo repository GitHub, branch `main` e file principale `app.py`;
4. Clicca su **Advanced settings > Secrets** e incolla:
   ```toml
   GMAIL_USER = "tuaemail@gmail.com"
   GMAIL_APP_PASSWORD = "xxxx yyyy zzzz wwww"
   ```
5. Clicca **Deploy**: l'app sarà online, accessibile da qualsiasi computer o smartphone!
