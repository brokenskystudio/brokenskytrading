# Trading Research

Local-only portfolio research MVP. The current foundation uses SQLite, FastAPI, Next.js, and yfinance for local market-data experiments.

## Run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend creates `backend/trading_adviser.db` on first database access. Check it at `http://localhost:8000/health`.

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend expects the backend at `http://localhost:8000`; override it with `NEXT_PUBLIC_API_BASE_URL` when needed.

Portfolio models and migrations are the next implementation phase. This application is informational and does not execute trades.

## Market data

The local MVP uses Yahoo Finance through `yfinance`. Quotes may be delayed, unofficial, or unavailable. The backend keeps this integration behind a provider adapter so it can later be replaced with a licensed market-data service.

Security autocomplete uses the local SQLite catalog in `backend/app/data/securities.csv`; it does not call an external API while typing. The catalog is generated from the public Nasdaq Trader `nasdaqlisted` and `otherlisted` directories. It includes active, non-test listings for NASDAQ, NYSE, NYSE American, NYSE Arca, and Cboe BZX as of the snapshot date recorded in each row's `source` field.

Market responses are cached in SQLite to reduce repeated yfinance requests. Quote data is cached briefly, historical charts for one hour, and fundamentals for one day.

Refresh the catalog from the `backend` directory when network access is available:

```bash
.venv/bin/python scripts/update_security_catalog.py
```

Restart the backend after refreshing so it seeds missing entries into the existing database. The directory only exposes an ETF flag, so entries are classified as `etf` when flagged and `equity` otherwise; the latter category can include non-common-share listed instruments such as warrants or preferred shares.
