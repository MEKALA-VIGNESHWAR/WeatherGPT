# Weather Data Adapters & Fusion Engine

WeatherGPT interfaces with multiple heterogeneous meteorological sources through a standardized adapter architecture.

---

## 1. Provider Implementations

| Provider | Description | Resolution | Key Required |
|---|---|---|---|
| **Open-Meteo** | Live verified ensemble (ECMWF, GFS, DWD, IMD grids) | 1-11 km | No (Free / Open) |
| **IMD Adapter** | India Meteorological Department AWS stations & Mausam Grid | District / AWS | Optional |
| **GFS Provider** | NOAA Global Forecast System (0.25° NWP) | 25 km | No |
| **WRF Provider** | Weather Research & Forecasting mesoscale run | 3 km | Institutional |
| **Mock Provider** | Deterministic synthetic benchmark with labelled sample data | Point | No |

---

## 2. Multi-Source Data Fusion

The `DataFusionService` is responsible for:
1. **Coordinate Sanity Checks**: Enforces $-90 \le \text{lat} \le 90$ and $-180 \le \text{lon} \le 180$.
2. **Unit Normalization**: Standardizes temperatures into Celsius, precipitation in millimeters (mm), and wind in km/h.
3. **Data Freshness Tracking**: Computes observation age in minutes. Data older than 45 minutes reduces the confidence rating to `MEDIUM`; data older than 120 minutes is flagged as `LOW`.
4. **Ensemble Agreement**: Compares multi-model forecasts to calculate model agreement (`high`, `moderate`, `low`).
5. **Failover Execution**: If a primary source fails or times out, the system automatically falls back to secondary grids without interrupting user service.

---

## 3. Trust Layer Metadata

Every response provides user-facing provenance transparency:
```json
{
  "source": "Open-Meteo (Global NWP Ensemble & IMD Resolution)",
  "observed_at": "2026-09-04T12:00:00Z",
  "data_age_minutes": 2.5,
  "source_authority": "verified_meteorological_grid",
  "confidence": "high",
  "is_demo_data": false
}
```
