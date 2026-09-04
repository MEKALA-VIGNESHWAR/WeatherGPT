# WeatherGPT API Specification

Base URL: `http://localhost:8000/api/v1`

---

## 1. Authentication Endpoints

### `POST /auth/register`
Registers a new user account with role-based access.

**Request Body:**
```json
{
  "email": "farmer.ramesh@agri.in",
  "password": "SecurePassword123!",
  "full_name": "Ramesh Kumar",
  "role": "farmer",
  "preferred_language": "te"
}
```

**Response (200 OK):**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "farmer.ramesh@agri.in",
    "role": "farmer",
    "preferred_language": "te"
  }
}
```

### `POST /auth/login`
Authenticates a user and returns signed JWT tokens.

---

## 2. Weather Endpoints

### `GET /weather/forecast`
Returns normalized 7-day or multi-day forecasts with hourly data points and trust metadata.

**Parameters:**
- `latitude` (float, required): e.g. `17.3850`
- `longitude` (float, required): e.g. `78.4867`
- `days` (int, optional, default: `7`)
- `provider` (string, optional): `open_meteo` | `imd` | `gfs` | `wrf` | `mock`

**Sample Response:**
```json
{
  "location": {
    "name": "Hyderabad",
    "latitude": 17.3850,
    "longitude": 78.4867,
    "state": "Telangana",
    "country": "India"
  },
  "current": {
    "temperature_c": 28.4,
    "feels_like_c": 31.2,
    "relative_humidity_pct": 74,
    "wind_speed_kmh": 14.5,
    "precipitation_mm": 0.0,
    "precipitation_probability_pct": 65,
    "surface_pressure_hpa": 1008.4,
    "weather_code": 61,
    "weather_condition": "Light rain",
    "weather_icon": "🌦️"
  },
  "hourly": [...],
  "daily": [...],
  "trust": {
    "source": "Open-Meteo (Global NWP Ensemble & IMD Resolution)",
    "observed_at": "2026-09-04T12:00:00Z",
    "retrieved_at": "2026-09-04T12:02:30Z",
    "data_age_minutes": 2.5,
    "source_authority": "verified_meteorological_grid",
    "confidence": "high",
    "model_agreement": "high",
    "is_demo_data": false
  }
}
```

### `GET /weather/current`
Returns current weather observations for coordinates.

---

## 3. Alerts & Official Warnings

### `GET /alerts/active`
Returns active official warnings within proximity of the target location.

**Sample Response:**
```json
{
  "location": "Hyderabad",
  "count": 1,
  "alerts": [
    {
      "id": "IMD-HYD-2026-001",
      "headline": "Thunderstorm with Gusty Winds Warning",
      "description": "Thunderstorm accompanied with lightning and gusty winds (speed 30-40 kmph) very likely to occur.",
      "instruction": "Stay indoors during lightning. Farmers must avoid open fields.",
      "severity": "yellow",
      "alert_type": "thunderstorm",
      "source": "India Meteorological Department (IMD Hyd)",
      "color_code": "#FFCC00"
    }
  ],
  "highest_severity": "yellow"
}
```

---

## 4. Conversational Intelligence & Chat

### `POST /chat`
Processes natural-language queries through the zero-hallucination grounded pipeline.

**Request Body:**
```json
{
  "message": "Should I irrigate my paddy field tomorrow morning?",
  "latitude": 17.3850,
  "longitude": 78.4867,
  "location_name": "Hyderabad",
  "user_role": "farmer",
  "language": "en"
}
```

**Response (200 OK):**
```json
{
  "conversation_id": "9f243...",
  "message_id": "c138b...",
  "answer": "🌧️ Rainfall is expected in Hyderabad tomorrow.\n\nTemperature is expected to be around 31.0°C with 74% humidity.\n\nRecommendation: Delay scheduled irrigation. Expected rainfall (18.4 mm) will provide sufficient soil moisture.",
  "location": "Hyderabad",
  "time_range": "Tomorrow",
  "risk_level": "low",
  "advisories": [
    {
      "sector": "agriculture",
      "recommendation": "Delay scheduled irrigation.",
      "action_type": "delay"
    }
  ],
  "warnings": [],
  "sources": ["Open-Meteo (Global NWP Ensemble & IMD Resolution)"],
  "confidence": "High",
  "tools_called": [
    { "tool_name": "get_forecast", "execution_time_ms": 42.1 },
    { "tool_name": "get_active_alerts", "execution_time_ms": 1.2 }
  ]
}
```

### `POST /chat/feedback`
Records user satisfaction (`is_helpful: true/false`, comments).

---

## 5. Sector Advisories

### `GET /advisories`
- `sector`: `agriculture` | `disaster` | `citizen` | `marine` | `aviation`
- `latitude`, `longitude`
- `crop` (e.g. `paddy`, `cotton`, `wheat`)

---

## 6. Real-Time WebSockets

### `WS /ws/alerts`
Client connects to receive real-time push bulletins whenever an IMD or meteorological event is detected. Sends initial alert status on connect.
