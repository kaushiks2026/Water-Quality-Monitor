# Step-by-Step Multidisciplinary Project (MDP) Learning Guide

Welcome to AquaWatch! This guide is written specifically for you as a 1st-year CSE Cyber Security student and your multidisciplinary team (ECE, CSE Core, Cyber Security, Data Science, and Health Sciences).

---

## Module 1: Project Architecture & Data Flow

### 1. Concepts to Understand
- How an IoT ecosystem separates sensing, transport, computation, and presentation.
- Why the backend must serve as the single source of truth rather than letting the dashboard generate mock numbers.

### 2. Files to Inspect
- [ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- [main.py](../backend/app/main.py)

### 3. Practical Checkpoint
- Trace a single packet from `simulator/sensor_simulator.py` across HTTP into `backend/app/api/endpoints.py` down into `water_quality.db`.

---

## Module 2: Python Environment, Dependencies & Configuration

### 1. Concepts to Understand
- The role of `requirements.txt` and why pinning versions prevents breaking builds.
- The 12-Factor App philosophy: separating credentials (`.env`) from code to avoid leaking secrets on GitHub.

### 2. Files to Inspect
- [requirements.txt](../requirements.txt)
- [.env.example](../.env.example)
- [config.py](../backend/app/config.py)

### 3. Hands-On Exercise
Change `PORT=8000` to `PORT=8080` in `.env` and verify how `settings.PORT` loads the new setting without modifying Python source code.

---

## Module 3: HTTP, REST APIs & Telemetry Ingestion

### 1. Concepts to Understand
- HTTP Verbs: `POST` for submitting new sensor observations; `GET` for retrieving state.
- HTTP Status Codes: `201 Created` vs `401 Unauthorized` vs `422 Unprocessable Entity`.
- Custom request headers: Using `X-Device-Token` as a light pre-shared key (PSK) check for IoT nodes.

### 2. Files to Inspect
- [endpoints.py](../backend/app/api/endpoints.py)

### 3. Debugging Exercise
Run `curl` or a Python script to send a POST request without the `X-Device-Token` header. Notice that the backend returns `401 Unauthorized`.

---

## Module 4: Pydantic Validation & Physical Plausibility

### 1. Concepts to Understand
- Why input validation is critical for Cyber Security and IoT reliability.
- Preventing garbage-in, garbage-out: If a loose wire causes the ADC to read a pH of 25.0 or a turbidity of -10.0 NTU, Pydantic `@field_validator` rejects it with HTTP 422 before it corrupts the database.

### 2. Files to Inspect
- [sensor.py](../backend/app/schemas/sensor.py)

---

## Module 5: Relational Databases & SQLAlchemy ORM

### 1. Concepts to Understand
- What an ORM (Object-Relational Mapping) does: Maps Python classes to SQL tables.
- Primary Keys (`id`), Foreign Keys (`device_id`), and Indexes (`ix_device_timestamp`) to keep historical queries fast.
- Handling uninstalled sensors: allowing `ph`, `turbidity`, or `dissolved_oxygen` columns to store `NULL` until installed.

### 2. Files to Inspect
- [session.py](../backend/app/database/session.py)
- [reading.py](../backend/app/models/reading.py)
- [alert.py](../backend/app/models/alert.py)

---

## Module 6: Rule-Based Water Quality Classification

### 1. Concepts to Understand
- Why rule-based safety checks must remain separate from ML models: A neural net can make statistical mistakes; drinking water safety limits are strictly defined by regulatory statute.
- Documented limits: **BIS 10500:2012** (pH 6.5 - 8.5; Turbidity &le; 1 NTU acceptable, &le; 5 NTU permissible).
- The difference between an exceeded threshold and a verified toxic hazard.

### 2. Files to Inspect
- [risk_service.py](../backend/app/services/risk_service.py)

---

## Module 7: Frontend Dashboard & Chart.js

### 1. Concepts to Understand
- Asynchronous polling (`fetch` API) every 3 seconds to update the DOM without full page refreshes.
- Dual-axis Chart.js setup: plotting pH (0-14 scale) and Turbidity (0-100 NTU scale) on different Y-axes so both remain readable.
- Provenance tracking: Visually differentiating between simulated test data and real physical ESP32 data.

### 2. Files to Inspect
- [index.html](../frontend/index.html)
- [styles.css](../frontend/styles.css)
- [app.js](../frontend/app.js)

---

## Module 8: Hardware Architecture & ESP32 Integration

### 1. Concepts to Understand
- ESP32 ADC limits: Max input voltage is 3.3V.
- Why 5V analog sensors require a resistor voltage divider (10k / 20k) before connecting to GPIO 34/35.
- Calibration math: Converting raw ADC voltage into pH and NTU values.

### 2. Files to Inspect
- [HARDWARE_GUIDE.md](../docs/HARDWARE_GUIDE.md)

---

## Module 9: Review Defense Q&A (Preparing for Faculty Evaluation)

1. **Question:** *Can you claim this water is safe to drink because your dashboard shows SAFE?*
   - **Answer:** *No. Our station measures physicochemical indicators (pH, turbidity, temp, DO) for early warning. Potability certification requires laboratory microbiological assays for pathogens (E. coli) and heavy metals (lead/arsenic).*
2. **Question:** *What happens if the DO sensor is not connected? Does the system break?*
   - **Answer:** *No. In our database schema and Pydantic validation, missing sensor channels remain `NULL`. The risk engine evaluates only installed channels and labels missing ones as 'UNINSTALLED'.*
3. **Question:** *How do you prevent malicious nodes from injecting bogus readings?*
   - **Answer:** *Requests require an `X-Device-Token` authentication header, and all payloads pass physical plausibility validation (e.g. pH must be between 0 and 14).*
