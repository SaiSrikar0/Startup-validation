# LaunchIQ — Startup Intelligence Platform

A full-stack web app that lets you analyze startups, predict success probability, and find competitors — powered by a dataset of 600+ real companies.

---

## Features

- **Success Prediction** — enter your startup's profile and get an instant success probability score with a visual gauge and key contributing factors
- **Competition Analysis** — find your closest competitors from the database based on shared categories and location
- **Startup Explorer** — browse, filter, search, and manage 600+ startups with full CRUD
- **Startup Detail** — view founders, investors, funding rounds, and categories for any company

---

## Tech Stack

| Layer     | Technology                              |
|-----------|-----------------------------------------|
| Frontend  | React 18, Vite, Tailwind CSS, Zustand   |
| Backend   | FastAPI, Pydantic v2, Uvicorn           |
| ML        | scikit-learn (KMeans, cosine similarity)|
| Data      | CSV seed — 688 cleaned startup records  |

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app + CORS
│   │   ├── api/
│   │   │   ├── routes.py            # All API endpoints
│   │   │   ├── schemas.py           # Pydantic models
│   │   │   └── store.py             # In-memory store + business logic
│   │   └── features/
│   │       └── success_prediction/  # ANN pipeline (train.py, predict.py)
│   ├── competitor_analysis/         # KMeans clustering + similarity engine
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                   # Dashboard, Predict, Compete, Startups
│   │   ├── components/              # Navbar, TagInput, StatusBadge, Spinner
│   │   ├── services/api.js          # Axios API client
│   │   └── store/useStartupStore.js # Zustand global state
│   ├── index.html
│   └── package.json
├── database/
│   ├── data/cleaned/Startups_cleaned.csv  # 688-row training dataset
│   └── schema.sql
└── docs/
    └── architecture.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API will be running at `http://localhost:8000`.  
Interactive docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App will be running at `http://localhost:5173`.

---

## API Endpoints

| Method | Endpoint                  | Description                        |
|--------|---------------------------|------------------------------------|
| GET    | `/api/health`             | Health check + startup count       |
| GET    | `/api/startups`           | List startups (filter + paginate)  |
| GET    | `/api/startups/{id}`      | Get startup by ID                  |
| POST   | `/api/startups`           | Create a startup                   |
| PUT    | `/api/startups/{id}`      | Update a startup                   |
| DELETE | `/api/startups/{id}`      | Delete a startup                   |
| POST   | `/api/predict/success`    | Predict startup success probability|
| POST   | `/api/analysis/competition` | Find similar competitors          |

---

## Training the ML Competitor Model

The competitor analysis ML module uses KMeans clustering + cosine similarity. To train it on the dataset:

```bash
cd backend
python -m competitor_analysis.clustering --data ../database/data/cleaned/Startups_cleaned.csv
```

This saves a model to `backend/competitor_analysis/models/cluster_model.pkl`.

---

## Notes

- The backend uses **in-memory storage** — data resets on server restart (seeded from CSV on each start)
- The success prediction engine uses a **heuristic scoring model** — an ANN pipeline exists in `features/success_prediction/` but requires training
- No authentication is implemented — suitable for local/demo use
