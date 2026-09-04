# WeatherGPT AI & Grounding Pipeline

## 1. Zero Hallucination Principle

Weather intelligence can be safety-critical (cyclone alerts, severe thunderstorms, pesticide spraying during rainfall, drone aviation). Hallucinated weather numbers can cause severe economic or physical harm.

WeatherGPT operates on a strict multi-stage deterministic pipeline:

```
USER QUERY
    ↓
QUERY UNDERSTANDING (Structured QueryIntent)
    ↓
EXPLICIT TOOL SELECTION & EXECUTION (No AI improvisation)
    ↓
DATA VALIDATION & FUSION (Quality, Range, Stale detection)
    ↓
RISK & CONTEXT ENGINE (Agronomic & Disaster thresholds)
    ↓
GROUNDED REASONING & TRANSLATION (8 Indian Languages)
    ↓
FINAL STRUCTURED RESPONSE
```

---

## 2. Query Understanding & Intent Classification

The `IntentParser` translates natural language into a validated `QueryIntent` Pydantic model:

- **Supported Intents**:
  - `current_weather`
  - `forecast`
  - `rainfall`
  - `temperature`
  - `wind`
  - `severe_weather`
  - `warning`
  - `agriculture_advisory`
  - `travel_advisory`
  - `aviation_advisory`
  - `marine_advisory`
  - `historical_weather`
  - `climate_trend`

- **Extraction Logic**:
  - Automatically identifies Indian cities (Hyderabad, Amaravati, Delhi, Bengaluru, etc.)
  - Resolves temporal targets (`today`, `tomorrow`, `last 7 days`)
  - Identifies target crops (`paddy`, `cotton`, `wheat`, `chilli`)
  - Detects native Indian script (Telugu `0x0C00-0x0C7F`, Devanagari/Hindi `0x0900-0x097F`, Tamil, Kannada, Malayalam, Bengali).

---

## 3. Tool Calling Registry

The AI layer invokes strictly defined backend tools:
1. `get_forecast(latitude, longitude, days)`
2. `get_current_weather(latitude, longitude)`
3. `get_active_alerts(latitude, longitude)`
4. `get_historical_weather(latitude, longitude)`
5. `get_climate_trend(latitude, longitude, period)`
6. `get_agriculture_advisory(latitude, longitude, crop)`
7. `get_location(place_name)`

---

## 4. Multilingual Translation & Numerical Preservation

When translating into Indian languages (Telugu, Hindi, Tamil, Kannada, Malayalam, Bengali, Marathi), all numerical measurements (temperature, rainfall in mm, wind in km/h, probabilities) are injected into validated grammatical templates to ensure zero metric corruption across languages.
