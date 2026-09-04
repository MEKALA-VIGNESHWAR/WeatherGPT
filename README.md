# WeatherGPT ☁️
### Conversational Weather Intelligence & Decision-Support Platform
**Smart India Hackathon (SIH 2026)**

> *"WeatherGPT does not replace the forecast. It replaces the complexity between the forecast and the decision."*

---

## 🌟 Core Concept: Data → Context → Risk → Decision

Traditional meteorological portals output complex numerical grids, raw weather charts, and technical bulletins that are difficult for farmers, fishermen, commuters, and disaster responders to quickly understand and act upon.

**WeatherGPT** is an authoritative, zero-fabrication conversational weather intelligence platform. It treats **Open-Meteo** as the single source of truth for factual numerical metrics and numerical weather predictions (NWP), and uses **Google Gemini** for natural language understanding, reasoning, and context-rich explanations under strict anti-hallucination guardrails.

> [!IMPORTANT]
> **Zero-Fabrication & Anti-Hallucination Principle**:
> - Open-Meteo is the factual source of truth for all observed, hourly, and daily metrics.
> - Gemini never independently predicts weather, invents forecasts, fabricates precipitation probabilities, or creates artificial government warnings.
> - The backend performs numerical analysis and risk assessment **before** the LLM generates the response.
> - High-availability architecture with zero-downtime fallback to a deterministic rule engine if LLM rate limits (429) or outages occur.

---

## 🚀 Key Features

### 1. 🧠 Weather Intelligence Agent
- **Universal Phrasing & Natural Language Understanding**: Extracts constraints (locations, dates, target hours, horizons, variables, activities, crops, and thresholds) regardless of phrasing.
- **Multi-Location Comparisons & Rankings**:
  - Compares 2+ locations concurrently (e.g. *"Is Mumbai warmer than Delhi?"*, *"Which has less rain: Pune or Goa?"*).
  - Ranks locations by temperature, rainfall risk, wind speed, or outdoor suitability without limiting analysis to just the first location.
- **Route & En-Route Weather Intelligence**:
  - Automatically identifies origin and destination (e.g. *"Weather driving from Chennai to Bangalore"*).
  - Generates travel advisories, highlights temperature transitions, and flags wet road hazards.
- **Physical Meteorological Explanations ("Why" Questions)**:
  - Explains the physical atmospheric drivers behind weather conditions (relative humidity %, cloud cover %, convective pressure drops in hPa, and horizontal pressure gradients).
- **Direct Answers First**: Always answers the user's actual question in the very first sentence before providing structured details.

### 2. 🌾 Dynamic Sector Decision Support System
A fully dynamic, explainable decision engine that evaluates current weather, hourly trajectories, 7-day forecasts, crop sensitivities, and verified alerts without hardcoded strings:
- **Agriculture**:
  - Configurable crop profiles for **Paddy (Rice)**, **Cotton**, **Wheat**, **Sugarcane**, and **Chilli / Spices**.
  - Intelligent irrigation advice (`IRRIGATE`, `DELAY_IRRIGATION`, `MONITOR_SOIL_MOISTURE`) based on rainfall probabilities, accumulation, and soil dry windows.
  - Chemical & foliar spraying windows (`RECOMMENDED`, `POSTPONE`, `CAUTION_DRIFT`) evaluating rain wash-off risk, wind speed drift limits, and humidity-induced fungal pressure.
  - Multi-day agricultural horizon breakdowns (e.g. 4-day trajectory tables).
- **Disaster Response**:
  - Differentiates between numerical thresholds and official government warnings.
  - Flood waterlogging, heatwave stress, and high wind advisories.
- **Citizen & Commute**:
  - Practical daily commuting advice, umbrella recommendations, and two-wheeler crosswind warnings.
- **Marine & Fishermen**:
  - Sea-state and squall wind assessments with explicit mandatory INCOIS/IMD sea-state disclaimers.
- **Aviation & Drone Operations**:
  - Visual flight rules (VFR) and drone suitability assessments with explicit METAR/TAF disclaimers.
- **Explainable Risk Engine**:
  - Computes numerical risk scores (0–100), risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and specific contributing risk factors.

### 3. 🚨 Official Warning Supremacy
- **Official Bulletin Ingestion**: Ingests official IMD cyclone bulletins (e.g. `data/sample/cyclone_bulletin.json` for *Cyclonic Storm BOB/03/2026* over Westcentral Bay of Bengal).
- **Geospatial Proximity Matching**: Binds warnings to affected coastal ports (Visakhapatnam, Paradip) and regions within active hazard radii.
- **Color-Coded Alert Levels**: Red, Orange, and Yellow warnings displayed with authoritative instructions and sources.

### 4. 🗺️ Precision GIS & Global Geocoding
- **Global Geocoding Engine**: Open-Meteo Geocoding API with OpenStreetMap Nominatim fallback.
- **Native Indic Script Aliases**: Expanded registry supporting Telugu (`హైదరాబాద్`, `ముంబై`, `విశాఖపట్నం`), Hindi (`हैदराबाद`, `मुंबई`, `दिल्ली`), Tamil (`சென்னை`), and regional city aliases.
- **Strict Error Handling**: Rejects invalid locations immediately with helpful suggestions instead of silently defaulting to Hyderabad.

### 5. 🌐 Multilingual & Multimodal
- **8 Indian Languages**: English, Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, and Marathi.
- **Voice Support**: Integrated Web Speech API for real-time Speech-to-Text (STT) and Text-to-Speech (TTS).

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, TypeScript, Vite, Vanilla CSS Design System with Glassmorphism, Leaflet GIS, Lucide Icons, Web Speech API |
| **Backend** | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy, WebSockets, Uvicorn, asyncio |
| **AI & NLP** | Google Gemini API (`gemini-flash-latest`, `gemini-3.6-flash`), High-Fidelity Deterministic Fallback Engine |
| **Data & Cache** | Open-Meteo API (Source of Truth), In-Memory TTL Cache, SQLite / PostgreSQL |
| **Testing** | Pytest, pytest-asyncio (20/20 Passing Automated Unit & Integration Tests) |
| **DevOps** | Docker, Docker Compose, Kubernetes Manifests, Nginx |

---

## 🏃 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- Active internet connection for Open-Meteo API

### 1. Configure Environment
Create a `.env` file in `backend/`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
PORT=8000
ENVIRONMENT=development
```

### 2. Launch Backend
```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Launch Frontend
```powershell
cd frontend
npm install
npm run dev
```
Open your browser at: [http://localhost:5173](http://localhost:5173)

### 4. Run Automated Test Suite
```powershell
cd backend
pytest -v
```
*All 20 test cases will execute and pass, verifying multi-location intelligence, routing, meteorological explanations, dynamic advisories, and API endpoints.*

---

## 🎯 Verification & Demonstration Scenarios

| Scenario | User Query | System Action & Grounded Output |
|---|---|---|
| **Forecast** | *"Will it rain tomorrow in Hyderabad?"* | Resolves Hyderabad → Queries Open-Meteo → Evaluates precipitation probability and peak timing → Grounded answer with source citation. |
| **Multi-Location Comparison** | *"Is Mumbai warmer than Delhi?"* | Concurrently fetches forecasts for Mumbai and Delhi → Ranks temperatures → Direct comparative answer (*"Delhi is warmer than Mumbai: 38.2°C vs 32.0°C"*). |
| **Rain Avoidance** | *"Which has less rain: Pune or Goa?"* | Retrieves weather for Pune and Goa → Evaluates rain probability and accumulation → Recommends location with lowest precipitation risk. |
| **Route Intelligence** | *"Weather driving from Chennai to Bangalore"* | Identifies origin & destination → Evaluates road wetness & temperature difference → Generates en-route travel advisory. |
| **Meteorological "Why"** | *"Why is it raining in Mumbai?"* | Analyzes atmospheric parameters → Explains physical boundary layer drivers (relative humidity %, cloud cover %, convective pressure drop). |
| **Crop Decision Support** | *"Should I irrigate my paddy field tomorrow?"* | Evaluates Paddy `CropRuleConfig` against rainfall probability & soil moisture → Advises `IRRIGATE` or `DELAY_IRRIGATION` with agronomic basis. |
| **Chemical Spraying** | *"Can I spray pesticide on cotton today in Warangal?"* | Checks cotton wind limit (15 km/h) & rain wash-off window → Recommends `RECOMMENDED` or `POSTPONE` with actionable steps. |
| **Official Cyclone Warning** | *"Is there any cyclone alert in Visakhapatnam?"* | Matches location coordinates against official IMD bulletin `BOB/03/2026` → Displays official Red Alert, wind speeds, and port signals. |
| **Multilingual Query** | *"రేపు హైదరాబాద్ లో వర్షం పడుతుందా?"* (Telugu) | Detects Telugu script → Processes intent → Responds in accurate Telugu with preserved numerical metrics. |
| **Voice Query** | Click 🎙️ Microphone button | Transcribes audio via Speech-to-Text → Runs decision pipeline → Synthesizes response via Text-to-Speech. |

---

## 🏛️ Monorepo Structure

```
WeatherGPT/
├── backend/
│   ├── app/
│   │   ├── advisory/        # Decision engine, CropRuleConfig, RiskEngine, Sector modules
│   │   │   ├── advisory_engine.py  # Multi-sector advisory logic (Agri, Disaster, Marine, Aviation)
│   │   │   ├── config.py           # Crop profile rules (Paddy, Cotton, Wheat, Sugarcane, Chilli)
│   │   │   └── risk_engine.py      # Explainable risk scoring (0-100) and factor attribution
│   │   ├── ai/              # AI intelligence orchestration and intent parsing
│   │   │   ├── intent_parser.py    # Multi-location, route, relational goal, and constraint extraction
│   │   │   ├── llm_provider.py     # Gemini client with fallback to GroundedRuleLLMProvider
│   │   │   ├── orchestrator.py     # Weather Intelligence Agent orchestrator & concurrent retrieval
│   │   │   └── tools.py            # Weather & alert retrieval tools
│   │   ├── alerts/          # Official WarningService & CAP/IMD bulletin ingestion
│   │   ├── api/v1/          # Endpoints: /chat, /weather, /advisories, /alerts, /map, /voice
│   │   ├── gis/             # Geocoding, reverse geocoding, and INDIAN_CITIES_REGISTRY
│   │   ├── models/          # Database models (AdvisoryRecord, etc.)
│   │   ├── schemas/         # Pydantic schemas (weather, chat, intent, advisory, alert)
│   │   ├── weather/         # Open-Meteo client, WMO mappings, WeatherAnalyzer (analysis.py)
│   │   └── main.py          # FastAPI application & WebSocket broadcast
│   ├── tests/               # Pytest suite (20 automated unit and integration tests)
│   │   ├── test_intelligence_agent.py   # Multi-location, route, why, and cyclone alert tests
│   │   ├── test_advisories.py           # Sector decision logic & crop profiles
│   │   ├── test_ai_orchestrator.py      # Intent parsing & grounded synthesis
│   │   ├── test_api_endpoints.py        # Health, weather, alerts, search endpoints
│   │   └── test_weather_providers.py    # Open-Meteo & WMO mappings
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/      # WeatherCard, ChatDrawer, SectorAdvisoryView, GISMapView, etc.
│   │   ├── services/        # API client & WebSocket listener
│   │   ├── types/           # TypeScript data contracts
│   │   ├── App.tsx          # Master dashboard
│   │   └── index.css        # Vanilla CSS Glassmorphism design system
│   └── package.json
│
├── data/                    # Sample official cyclone bulletins & IMD station datasets
├── docs/                    # Architecture, API, and weather data specifications
├── docker-compose.yml
└── README.md
```

---

## 📄 License
Created for Smart India Hackathon (SIH 2026). All rights reserved.
