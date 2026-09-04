# WeatherGPT ☁️
### Conversational Weather Intelligence & Decision-Support Platform
**Smart India Hackathon (SIH 2026)**

> *"WeatherGPT does not replace the forecast. It replaces the complexity between the forecast and the decision."*

---

## 🌟 Core Concept: Data → Context → Risk → Decision

Traditional meteorological portals output complex numerical grids, charts, and bulletins that are difficult for farmers, fishermen, citizens, and local disaster teams to immediately act upon.

**WeatherGPT** serves as an intelligent conversational layer over existing meteorological infrastructure (IMD, ECMWF, NOAA, and mesoscale NWP models). Users can interact in **8 Indian languages** via voice or text and receive verified, actionable, risk-grounded decisions.

> [!IMPORTANT]
> **Zero Hallucination Principle**: The AI never fabricates weather metrics or warnings. All data is retrieved through verified backend adapters and evaluated against agronomic and disaster risk thresholds.

---

## 🚀 Key Features

1. **Real-Time Weather & 24h/7-Day Projections**: High-resolution hourly and daily forecasts.
2. **Zero-Hallucination Conversational AI**: Strictly grounded reasoning engine with tool call transparency.
3. **Official Warning Supremacy**: Prominent IMD color-coded alerts (Red, Orange, Yellow) with actionable safety instructions.
4. **Sector-Specific Decision Engines**:
   - 🌾 **Agriculture**: Irrigation delaying, pesticide spray wash-off & drift constraints, crop sensitivity (paddy, cotton, wheat).
   - 🚨 **Disaster Management**: Flood risk, cyclonic wind squalls, and heat action plans.
   - 🚗 **Citizen & Commute**: Road wetness, visibility, and travel recommendations.
   - 🌊 **Marine & Fishermen**: Sea-state, wave swell, and coastal squall advisories.
   - ✈️ **Aviation & Drones**: Visual flight rules (VFR) and gust thresholds.
5. **Trust & Uncertainty Layer**: Every answer cites source authority, data age in minutes, confidence ratings, and model agreement.
6. **Multilingual Voice & Text Support**: English, Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, and Marathi.
7. **Interactive GIS Map**: OpenStreetMap Leaflet map with hazard zone polygons and IMD station locations.
8. **Historical & Climate Trends**: 7-day rainfall trend analysis with seasonal anomaly baselines.
9. **Real-Time WebSocket Notifications**: Instant push broadcasts for newly detected weather bulletins.
10. **Admin & Observability Dashboard**: Tracks source health, API latencies, query counts, and user feedback ratings.

---

## 🛠️ Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Vanilla CSS Design System with Glassmorphism, Leaflet GIS, Web Speech STT/TTS.
- **Backend**: Python 3.13, FastAPI, Pydantic v2, SQLAlchemy, WebSockets, Uvicorn.
- **Data & Cache**: PostgreSQL / PostGIS, SQLite fallback, Redis with in-memory TTL cache fallback.
- **Weather Adapters**: Open-Meteo (live verified grid), IMD Adapter, GFS NWP, WRF 3km Model, Mock Provider.
- **DevOps**: Docker, Docker Compose, Kubernetes manifests, Nginx reverse proxy.

---

## 🏃 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Launch Backend
```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Launch Frontend
```powershell
cd frontend
npm run dev
```
Open your browser to: [http://localhost:5173](http://localhost:5173)

### 3. Run Automated Tests
```powershell
python -m pytest backend/tests
```

### 4. Docker Deployment
```bash
docker compose up --build -d
```

---

## 🎯 SIH Demonstration Scenarios

| Scenario | User Input | System Action & Output |
|---|---|---|
| **Scenario 1: Forecast** | *"Will it rain tomorrow in Hyderabad?"* | Resolves location → Queries 24h NWP forecast → Grounded answer with source citation & timestamp. |
| **Scenario 2: Farmer Advisory** | *"Should I irrigate my paddy field tomorrow?"* | Evaluates rain probability & soil moisture → Advises delay or scheduled watering with crop-specific agronomic rationale. |
| **Scenario 3: Severe Weather** | *"Is there any severe weather near me?"* | Checks GPS against IMD warning zones → Displays official color-coded alert & safety instructions. |
| **Scenario 4: Multilingual** | *"రేపు హైదరాబాద్ లో వర్షం పడుతుందా?"* (Telugu) | Detects Telugu script → Extracts intent → Returns accurate Telugu response with preserved numerical values. |
| **Scenario 5: Climate Trend** | *"Show rainfall trend for the last 7 days."* | Retrieves daily historical precipitation → Renders interactive bar graph with departure norm. |
| **Scenario 6: Voice Interaction** | Click 🎙️ Microphone button | Transcribes audio via Speech-to-Text → Runs decision pipeline → Speaks response via Text-to-Speech. |

---

## 🏛️ Monorepo Structure

```
WeatherGPT/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Endpoints: weather, chat, alerts, advisories, climate, map, voice, admin
│   │   ├── core/            # Config, database, cache, logging, security
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── schemas/         # Normalized weather, alert, intent, and chat schemas
│   │   ├── weather/         # Open-Meteo, IMD, GFS, WRF, Mock, and Fusion services
│   │   ├── alerts/          # WarningService & criteria evaluation
│   │   ├── advisory/        # Agriculture, Disaster, Citizen, Marine, Aviation engines
│   │   ├── ai/              # IntentParser, WeatherTools, Orchestrator, RAG, Translations
│   │   ├── gis/             # Geocoding and reverse geocoding
│   │   ├── voice/           # STT & TTS services
│   │   └── main.py          # FastAPI application & WebSockets
│   ├── tests/               # Pytest suite (10/10 automated tests passing)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/      # WeatherCard, ChatDrawer, GISMapView, SectorAdvisory, AdminView, etc.
│   │   ├── services/        # API client
│   │   ├── types/           # TypeScript contracts
│   │   ├── App.tsx          # Master dashboard
│   │   └── index.css        # Modern glassmorphic styling system
│   └── package.json
│
├── data/                    # Pre-seeded IMD stations and sample cyclone datasets
├── infra/                   # Dockerfiles, Nginx configs, Kubernetes manifests
├── docs/                    # Architecture, API, AI pipeline, Weather data, Deployment docs
├── docker-compose.yml
└── README.md
```

---

## 📄 License
Created for Smart India Hackathon (SIH 2026). All rights reserved.
