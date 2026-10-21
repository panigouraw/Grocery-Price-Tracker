# Gouraw Grocery Price Tracker

A full-stack web app that shows **daily vegetable, fruit and grocery prices, state and district wise**. Pick a state and a district, filter by category, search any item, see the price change since the previous day, and open a 30-day price history chart.

**Live demo:** https://panigouraw.github.io/Grocery-Price-Tracker/
**API docs:** https://grocery-price-tracker-fkn0.onrender.com/docs

> **Note:** The live demo currently uses **simulated (demo) prices** that refresh automatically every day. The project also includes an importer for the Government of India Agmarknet (data.gov.in) mandi price API, which needs a data.gov.in API key to run.
> The backend runs on a free Render instance, so the first load after a period of inactivity can take 30-60 seconds.

<!-- Add a screenshot later: ![App screenshot](docs/screenshot.png) -->

## Features

- State and district dropdowns (Andhra Pradesh, Telangana, Tamil Nadu, Karnataka)
- Category tabs: Vegetables, Fruits, Groceries
- Search by item name
- Price per kg with min and max range
- Price change (up or down, in %) compared with the previous day
- 30-day price history line chart for every item
- Prices auto-refresh in the browser every 5 minutes
- Demo prices are generated automatically every day, so the data keeps changing day by day
- Admin API to add or update prices manually (protected with an admin key)
- Agmarknet importer that converts quintal prices to price per kg
- Responsive layout that works on mobile

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Recharts |
| Backend | FastAPI, SQLAlchemy, APScheduler |
| Database | MySQL (Aiven in production) |
| Hosting | GitHub Pages (frontend), Render (backend), Aiven (database) |
| Data source | Agmarknet via data.gov.in (importer) and generated demo data |

## How It Works

```
React app (GitHub Pages)
        |  HTTPS requests
        v
FastAPI server (Render)  <---  daily demo refresh / Agmarknet importer
        |
        v
MySQL database (Aiven)
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/states` | List of states |
| GET | `/districts?state_id=1` | Districts of a state |
| GET | `/prices?district_id=1&category=fruit&q=man` | Latest prices with change vs previous day (`category` and `q` are optional) |
| GET | `/history?item_id=1&district_id=1&days=30` | Day-wise price history for the chart |
| POST | `/admin/prices` | Add or update a price manually (needs `X-Admin-Key` header) |
| POST | `/admin/refresh` | Start the Agmarknet import in the background (needs `X-Admin-Key` header) |

Interactive documentation is available at `/docs`.

## Project Structure

```
Grocery-Price-Tracker/
|-- backend/
|   |-- main.py               # FastAPI app and API routes
|   |-- database.py           # database connection (optional SSL)
|   |-- models.py             # tables: states, districts, items, prices
|   |-- categories.py         # vegetable / fruit / grocery classification
|   |-- helpers.py            # get-or-create helpers
|   |-- create_tables.py      # creates the tables
|   |-- seed_demo.py          # generates demo data
|   |-- demo_refresh.py       # adds new demo days automatically
|   |-- fetch_agmarknet.py    # Agmarknet importer
|   |-- clear_demo.py         # removes demo rows
|   `-- requirements.txt
`-- frontend/
    |-- index.html
    |-- vite.config.js
    |-- package.json
    `-- src/
        |-- main.jsx
        |-- App.jsx
        |-- api.js
        |-- styles.css
        `-- components/
            |-- PriceCard.jsx
            `-- HistoryModal.jsx
```

## Run Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- MySQL 8

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Create the database in MySQL:

```sql
CREATE DATABASE grocery_prices CHARACTER SET utf8mb4;
```

Create `backend/.env`:

```
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/grocery_prices
ADMIN_KEY=choose-a-secret-key
ENABLE_SCHEDULER=0
DEMO_AUTO_REFRESH=1
```

Create the tables, add demo data and start the server:

```bash
python create_tables.py
python seed_demo.py
uvicorn main:app --reload
```

The API runs at http://127.0.0.1:8000 (docs at `/docs`).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Environment Variables (backend)

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL, for example `mysql+pymysql://user:password@host:port/dbname` |
| `DB_SSL` | Set to `1` for cloud MySQL that requires SSL (for example Aiven) |
| `ADMIN_KEY` | Secret key for the admin endpoints |
| `DEMO_AUTO_REFRESH` | `1` adds new demo price days automatically when the server wakes up and every night |
| `ENABLE_SCHEDULER` | `1` runs the Agmarknet import twice a day (needs `DATA_GOV_API_KEY`) |
