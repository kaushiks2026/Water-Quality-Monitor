# End-to-End System Walkthrough: Trace of a Sensor Measurement

This document traces the lifecycle of a single sensor observation as it travels across each layer of the AquaWatch system.

```
[1. Sensor / Simulator]
          │  Generates: {"device_id": "SIMULATOR-01", "ph": 5.96, "turbidity": 2.1, ...}
          ▼
[2. HTTP Transport Layer]
          │  POST /api/readings
          │  Header: X-Device-Token: dev-secret-token-123
          ▼
[3. FastAPI Backend Ingestion] (backend/app/api/endpoints.py)
          │  Token authenticated against settings.DEVICE_API_KEY
          ▼
[4. Schema & Plausibility Validation] (backend/app/schemas/sensor.py)
          │  Checked: 0.0 <= ph <= 14.0, turbidity >= 0.0
          ▼
[5. Water Quality Risk Evaluation] (backend/app/services/risk_service.py)
          │  pH 5.96 < 6.5 (BIS 10500:2012) -> WARNING: Acidic water
          │  Turbidity 2.1 > 1.0 NTU -> WARNING: Elevated turbidity
          │  Overall Status: WARNING
          ▼
[6. Database Persistence] (backend/app/database/session.py)
          │  Row inserted into 'sensor_readings' table
          │  Two alert records inserted into 'alerts' table
          ▼
[7. Dashboard Presentation] (frontend/app.js)
          │  GET /api/readings/latest -> updates status banner and metric gauges
          │  GET /api/alerts -> renders alert cards with standard references
          │  GET /api/readings -> updates Chart.js historical line chart
```

### Trace Details
1. **Telemetry Generation**: The ESP32 or `sensor_simulator.py` reads analog voltages or synthetic values, sets `is_simulated`, and serializes the JSON payload.
2. **Security & Boundary Enforcement**: FastAPI inspects the `X-Device-Token` header. If absent or incorrect, it immediately returns `401 Unauthorized`.
3. **Plausibility Guard**: Pydantic checks boundary conditions. If an electrical fault produces an impossible reading (e.g. pH = 22.0), the request is rejected with `422 Unprocessable Entity` before entering the database.
4. **Risk & Standard Verification**: `evaluate_water_quality()` parses the numbers against documented Bureau of Indian Standards (BIS 10500:2012) criteria.
5. **Storage**: The reading is committed to SQLite along with corresponding timestamped alerts.
6. **Live Visualization**: The browser dashboard polls the API every 3 seconds, updating the live banner, warning badges, and the historical trend graph.
