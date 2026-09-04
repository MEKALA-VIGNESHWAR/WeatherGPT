# WeatherGPT Architecture Documentation

WeatherGPT is a conversational weather intelligence and decision-support platform designed for the **Smart India Hackathon (SIH 2026)**.

The guiding product design principle is:
> **"Data → Context → Risk → Decision"**

WeatherGPT is explicitly positioned not as a replacement for meteorological bodies (e.g. IMD, ECMWF, NOAA), but as:
> **"A conversational intelligence and decision-support layer over existing meteorological infrastructure."**

---

## 1. System Architecture Diagram

```mermaid
graph TD
    User([User: Voice / Text / Mobile / Web]) --> UI[Modern React 19 + TypeScript + Vite Dashboard & GIS Map]
    UI -->|REST / WebSocket| Gateway[FastAPI API Gateway]
    
    subgraph GatewayLayer [API Gateway & Ingestion]
        Gateway --> Auth[JWT Authentication & RBAC]
        Gateway --> Telemetry[Request-ID Tracing & Latency Telemetry]
        Gateway --> RateLimit[Rate Limiter & Session Manager]
    end

    GatewayLayer --> QUnderstanding[Query Understanding & Intent Extraction]

    subgraph IntelligenceCore [WeatherGPT Intelligence Engine]
        QUnderstanding --> Orchestrator[Weather Intelligence Orchestrator]

        subgraph ToolRegistry [Verified Backend Tool Layer]
            Orchestrator --> ToolForecast[get_forecast: lat, lon, days]
            Orchestrator --> ToolCurrent[get_current_weather: lat, lon]
            Orchestrator --> ToolAlerts[get_active_alerts: lat, lon]
            Orchestrator --> ToolHistory[get_historical_weather: lat, lon]
            Orchestrator --> ToolAgri[get_agriculture_advisory: crop, context]
            Orchestrator --> ToolGIS[search_places / reverse_geocode]
            Orchestrator --> ToolRAG[rag_search: bulletins, SOPs]
        end

        subgraph Providers [Meteorological Provider Adapters]
            ToolForecast --> OpenMeteo[Open-Meteo High-Resolution Grid]
            ToolForecast --> IMD[IMD Mausam & AWS Network]
            ToolForecast --> GFS[NOAA GFS 0.25° NWP]
            ToolForecast --> WRF[WRF Mesoscale 3km Model]
            ToolForecast --> Mock[WeatherGPT Demo Provider]
        end

        ToolRegistry --> Fusion[Data Validation & Multi-Source Fusion Engine]
        Fusion --> Trust[Trust & Provenance Layer: Data Age, Source, Confidence]
        Trust --> ContextEngine[Domain Context & Risk Scoring Engine]
        
        ContextEngine --> SectorEngines[Sector Advisory Engines]
        SectorEngines --> AgriMod[Agriculture: Irrigation & Spraying]
        SectorEngines --> DisasterMod[Disaster: Floods, Cyclones & Heatwaves]
        SectorEngines --> CitizenMod[Citizen: Commute & Road Wetness]
        SectorEngines --> MarineMod[Marine: Sea-State & Coastal Squalls]
        SectorEngines --> AviationMod[Aviation: Drone Flight Constraints]

        SectorEngines --> GroundedLLM[Grounded LLM Reasoning Engine]
        GroundedLLM --> Multilingual[Multilingual Engine: 8 Indian Languages]
        Multilingual --> Formatter[Structured Response Formatter]
    end

    Formatter -->|Structured JSON / SSE Streaming| UI
    ToolAlerts -->|WebSocket Push Broadcasts| UI

    subgraph DataStorage [Storage & Caching]
        PostgreSQL[(PostgreSQL + PostGIS / SQLite)]
        RedisCache[(Redis Cache / In-Memory TTL)]
    end

    Auth --- PostgreSQL
    Fusion --- RedisCache
```

---

## 2. Zero-Hallucination Guarantee

The LLM is **never** permitted to generate or interpolate raw numerical weather metrics or manufacture emergency alerts. 

1. **Retrieval First**: All weather parameters (temperature, humidity, precipitation sum, probability, wind speed, pressure, UV index) must be returned by verified adapters.
2. **Deterministic Context**: Rules regarding irrigation suitability (soil moisture and rain probability thresholds) and pesticide drift (wind speed and 24h rainwash risk) are calculated deterministically by domain algorithms before being presented to the reasoning layer.
3. **Official Warning Supremacy**: Government alerts issued by IMD Regional Meteorological Centers take highest precedence and cannot be softened or downgraded by the AI.

---

## 3. Data Flow

1. **User Query**: User submits `"Should I irrigate my paddy field tomorrow in Hyderabad?"` via text or voice.
2. **Query Understanding**: `IntentParser` identifies:
   - Intent: `agriculture_advisory`
   - Location: `Hyderabad (17.3850° N, 78.4867° E)`
   - Time: `Tomorrow`
   - Sector: `Agriculture / Farmer`
   - Crop: `Paddy`
   - Language: `en`
3. **Tool Dispatching**: Orchestrator calls:
   - `get_forecast(17.3850, 78.4867, days=7)`
   - `get_active_alerts(17.3850, 78.4867)`
4. **Data Fusion & Validation**: Cache check, coordinate validation, data freshness calculation (`data_age_minutes = 2.5`), and confidence assessment (`HIGH`).
5. **Context Evaluation**: Tomorrow's precipitation probability evaluated:
   - If rainfall probability $\ge 50\%$ or rainfall $\ge 5.0\text{ mm}$, verdict is `DELAY_IRRIGATION`.
6. **Multilingual Formatting**: Translates response if user language is Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, or Marathi while preserving exact numerical metrics.
7. **Response Delivery**: Frontend renders structured card with action badge, weather summary chips, official citations, and text-to-speech audio.
