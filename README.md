# AquaWatch: Automated Water Quality Monitoring & Early-Warning System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![SQLite](https://img.shields.io/badge/SQLite-Local-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An end-to-end, local-first IoT water quality telemetry and early-warning software platform developed for a multidisciplinary engineering team.

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
Ensure Python 3.11+ is installed, then run:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy the example configuration:
```bash
cp .env.example .env
```

### 3. Launch the Backend Server
Start FastAPI with Uvicorn:
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Web Dashboard:** Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
- **Interactive Swagger API Docs:** Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 4. Run the Data Simulator
In a second terminal, start the telemetry simulator to generate realistic sensor readings:
```bash
# Continuous mixed telemetry (clean water with occasional spikes)
python simulator/sensor_simulator.py --interval 2.5 --mode mixed

# Or send a fixed batch of 15 readings
python simulator/sensor_simulator.py --count 15 --interval 1.0 --mode normal
```

### 5. Run the Test Suite
Execute the automated test suite:
```bash
python -m pytest backend/tests/test_backend.py -v
```

---

## 🏛️ System Architecture & Workflow

```
[ ESP32 Hardware or Simulator ]
             │  (HTTP POST JSON with X-Device-Token)
             ▼
[ FastAPI Backend /api/readings ]
             │  1. Plausibility Validation (Pydantic)
             │  2. Risk Classification (BIS 10500:2012 / WHO)
             │  3. Database Persistence (SQLAlchemy + SQLite)
             ▼
[ Responsive Web Dashboard ]
   - Real-time parameter cards (pH, Turbidity, Temp, DO)
   - Dynamic historical line chart (Chart.js)
   - Threshold safety alerts and provenance indicators
```

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── api/endpoints.py       # Ingestion, latest, history, and alert routes
│   │   ├── database/session.py    # SQLAlchemy engine, sessionmaker, and table setup
│   │   ├── models/                # Database models (Device, Reading, Alert)
│   │   ├── schemas/sensor.py      # Pydantic schemas with physical plausibility guards
│   │   ├── services/risk_service.py # Documented water quality risk logic
│   │   ├── config.py              # Environment settings (Pydantic Settings)
│   │   └── main.py                # FastAPI entry point & static frontend mount
│   └── tests/test_backend.py      # Automated pytest suite
├── frontend/
│   ├── index.html                 # Modern dashboard layout & cards
│   ├── styles.css                 # Dark theme design system
│   └── app.js                     # Telemetry polling, status indicators & Chart.js
├── simulator/
│   └── sensor_simulator.py        # Realistic synthetic telemetry generator
├── docs/
│   ├── ARCHITECTURE.md            # System data flow and regulatory standards
│   ├── HARDWARE_GUIDE.md          # ESP32 pinouts, voltage dividers, and C++ firmware
│   ├── LEARNING_GUIDE.md          # 9-module beginner learning guide & defense prep
│   └── PROJECT_WALKTHROUGH.md     # Step-by-step trace of a sensor measurement
├── .env.example                   # Baseline configuration template
├── requirements.txt               # Pinned Python package dependencies
└── README.md                      # Project documentation
```

---

## ⚖️ Scientific & Safety Transparency

> [!NOTE]
> Monitoring pH, turbidity, temperature, and dissolved oxygen serves as an **early-warning system** for gross physicochemical contamination and environmental anomalies. **These four parameters alone do not prove drinking water potability.** Microbiological pathogens (*E. coli*, coliforms) and heavy metals (lead, arsenic) require certified laboratory testing. Reference thresholds are derived from **BIS IS 10500:2012** and **WHO Guidelines**.
