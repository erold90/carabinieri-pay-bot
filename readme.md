# CarabinieriPayBot v3.0

Bot Telegram professionale per il calcolo automatico di stipendi, straordinari, indennità e missioni per il personale dell'Arma dei Carabinieri.

## 🚀 Caratteristiche Principali

- **Calcolo Automatico Stipendi**: Straordinari differenziati per tipologia, indennità giornaliere, missioni e scorte
- **Gestione Straordinari Non Pagati**: Tracciamento ore accumulate con proiezione pagamenti semestrali
- **Monitoraggio Fogli Viaggio**: Lista FV non pagati con alert automatici
- **Gestione Licenze**: Controllo licenze anno corrente/precedente con alert scadenze
- **Distinzione Viaggi Attivi/Passivi**: Calcolo automatico per servizi di scorta
- **Report Dettagliati**: Export Excel/PDF per commercialista

## 📋 Requisiti

- Python 3.11+
- PostgreSQL
- Account Railway.app
- Bot Token Telegram

## 🛠️ Installazione su Railway

1. **Fork questo repository** sul tuo GitHub

2. **Crea un nuovo progetto su Railway**
   - Vai su [railway.app](https://railway.app)
   - Clicca "New Project"
   - Seleziona "Deploy from GitHub repo"
   - Autorizza Railway e seleziona il repository

3. **Aggiungi PostgreSQL**
   - Nel progetto Railway, clicca "New"
   - Seleziona "Database" → "Add PostgreSQL"
   - Railway configurerà automaticamente `DATABASE_URL`

4. **Configura le variabili d'ambiente**
   - Vai in "Variables"
   - Aggiungi:
     ```
     BOT_TOKEN=your_telegram_bot_token
     TZ=Europe/Rome
     ENV=production
     ```

5. **Deploy**
   - Railway farà il deploy automaticamente
   - Controlla i logs per verificare che il bot sia partito

## 🤖 Creazione Bot Telegram

1. Apri Telegram e cerca `@BotFather`
2. Invia `/newbot`
3. Scegli un nome (es: "Carabinieri Pay Bot")
4. Scegli un username (deve finire con 'bot', es: `@CarabinieriPayBot`)
5. Copia il token e usalo come `BOT_TOKEN`

## 📱 Comandi Disponibili

### Comandi Base
- `/start` - Menu principale
- `/nuovo` - Registra nuovo servizio
- `/scorta` - Registra servizio di scorta
- `/oggi` - Riepilogo giornaliero
- `/mese` - Report mensile

### Gestione Straordinari
- `/straordinari` - Dashboard straordinari
- `/ore_pagate` - Inserisci ore pagate mensili
- `/accumulo` - Visualizza ore accumulate

### Gestione Fogli Viaggio
- `/fv` - Dashboard fogli viaggio
- `/fv_pagamento` - Registra pagamento FV

### Gestione Licenze
- `/licenze` - Dashboard licenze
- `/inserisci_licenza` - Nuova licenza

### Report e Utility
- `/export` - Scarica Excel
- `/impostazioni` - Configurazione

## 💾 Struttura Database

Il bot utilizza PostgreSQL con le seguenti tabelle principali:
- `users` - Dati utenti e configurazioni
- `services` - Servizi registrati
- `overtimes` - Dettaglio straordinari
- `travel_sheets` - Fogli viaggio
- `leaves` - Licenze e permessi

## 🔧 Configurazione Locale (Development)

1. Clona il repository
```bash
git clone https://github.com/yourusername/CarabinieriPayBot.git
cd CarabinieriPayBot
```

2. Crea ambiente virtuale
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Installa dipendenze
```bash
pip install -r requirements.txt
```

4. Crea file `.env`
```env
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql://user:pass@localhost/carabinieri_bot
TZ=Europe/Rome
ENV=development
```

5. Avvia il bot
```bash
python main.py
```

## 📊 Monitoraggio

- Railway fornisce logs in tempo reale
- Controlla metriche di utilizzo nel dashboard Railway
- Il bot logga automaticamente errori e attività

## 🆘 Supporto

Per problemi o suggerimenti:
1. Apri una Issue su GitHub
2. Contatta tramite Telegram

## 📄 License

Questo progetto è rilasciato sotto licenza MIT.

## 🙏 Credits

Sviluppato per il personale dell'Arma dei Carabinieri per semplificare la gestione amministrativa quotidiana.

---

**Nota**: Questo bot calcola importi NETTI basati sulle tabelle stipendiali ufficiali. Verificare sempre con l'ufficio amministrativo per conferme ufficiali.