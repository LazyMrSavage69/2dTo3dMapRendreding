# 5G Planner MVP (Cesium + FastAPI)

MVP de planification 5G avec carte 3D, ajout manuel de stations gNB, et simulation de couverture RF simplifiée (distance + atténuation de base).

## Structure

```text
3dMap/
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── state.py
│       ├── models/schemas.py
│       ├── routers/
│       │   ├── cities.py
│       │   ├── antennas.py
│       │   └── simulation.py
│       ├── services/rf_simulation.py
│       └── ai/optimizer.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── App.css
        └── index.css
```

## Démarrage rapide

### 1) Backend

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2) Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`  
Backend API: `http://127.0.0.1:8000`

## Endpoints API MVP

- `GET /api/v1/cities`
- `GET /api/v1/antennas?city=Paris`
- `POST /api/v1/antennas`
- `DELETE /api/v1/antennas/{antenna_id}?city=Paris`
- `GET /api/v1/simulation/coverage?city=Paris`

## Modèles de données

- **City**: `name`, `latitude`, `longitude`, `default_zoom_m`, `bbox_half_size_km`
- **Antenna**: `id`, `city`, `latitude`, `longitude`, `tx_power_dbm`, `coverage_radius_km`, `frequency_mhz`
- **Coverage KPI**: `covered_points`, `total_points`, `coverage_percent`, `antennas_count`
# 5gTowerOptimisationWithAi
