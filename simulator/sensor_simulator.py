"""
Water Quality Telemetry Simulator
=================================
Generates physically plausible synthetic sensor readings and transmits them
to the FastAPI backend via HTTP REST API.

Key Design Points:
1. 'is_simulated' flag is strictly set to True so simulated data is never
   mistaken for genuine physical hardware readings.
2. Supports various simulation modes:
   - 'normal': clean, compliant water values.
   - 'acidic_spike': sudden pH drop (acid contamination).
   - 'turbidity_spike': sudden silt/runoff spike (> 5.0 NTU).
   - 'mixed': random transitions between clean water and occasional advisory spikes.
3. Supports uninstalled sensors (DO left as None).
"""

import time
import random
import argparse
import requests
from datetime import datetime, timezone

DEFAULT_API_URL = "http://127.0.0.1:8000/api/readings"
DEFAULT_API_KEY = "dev-secret-token-123"
DEFAULT_DEVICE_ID = "SIMULATOR-01"


def generate_reading(mode: str = "normal") -> dict:
    now_utc = datetime.now(timezone.utc).isoformat()

    if mode == "normal":
        # Compliant baseline
        ph = round(random.uniform(7.1, 7.8), 2)
        turbidity = round(random.uniform(0.3, 0.9), 2)
        temperature = round(random.uniform(23.0, 26.5), 1)
        # Dissolved oxygen can optionally be omitted (simulating uninstalled physical sensor)
        do = round(random.uniform(6.5, 7.8), 2) if random.random() > 0.5 else None

    elif mode == "acidic_spike":
        # Chemical acid runoff violation
        ph = round(random.uniform(4.5, 5.8), 2)
        turbidity = round(random.uniform(0.8, 1.8), 2)
        temperature = round(random.uniform(24.0, 27.0), 1)
        do = round(random.uniform(5.0, 6.2), 2)

    elif mode == "turbidity_spike":
        # Heavy sedimentation / storm runoff violation (> 5.0 NTU)
        ph = round(random.uniform(7.2, 7.9), 2)
        turbidity = round(random.uniform(6.2, 18.5), 2)
        temperature = round(random.uniform(22.0, 25.0), 1)
        do = round(random.uniform(3.5, 5.0), 2)

    elif mode == "mixed":
        roll = random.random()
        if roll < 0.70:
            # 70% normal
            ph = round(random.uniform(7.0, 8.2), 2)
            turbidity = round(random.uniform(0.4, 0.95), 2)
            temperature = round(random.uniform(22.5, 27.0), 1)
            do = round(random.uniform(6.2, 7.5), 2) if random.random() > 0.3 else None
        elif roll < 0.85:
            # 15% turbidity warning/critical
            ph = round(random.uniform(7.0, 8.0), 2)
            turbidity = round(random.uniform(2.5, 8.5), 2)
            temperature = round(random.uniform(23.0, 26.0), 1)
            do = None
        else:
            # 15% pH abnormal (acidic or alkaline)
            ph = round(random.choice([random.uniform(5.5, 6.2), random.uniform(8.8, 9.6)]), 2)
            turbidity = round(random.uniform(0.8, 2.2), 2)
            temperature = round(random.uniform(25.0, 31.0), 1)
            do = round(random.uniform(5.0, 6.8), 2)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return {
        "device_id": DEFAULT_DEVICE_ID,
        "timestamp": now_utc,
        "is_simulated": True,
        "ph": ph,
        "turbidity": turbidity,
        "temperature": temperature,
        "dissolved_oxygen": do
    }


def send_reading(api_url: str, api_key: str, payload: dict) -> bool:
    headers = {
        "Content-Type": "application/json",
        "X-Device-Token": api_key
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=5)
        if response.status_code == 201:
            data = response.json()
            print(f"[{payload['timestamp'][11:19]}] Sent: pH={payload['ph']}, Turb={payload['turbidity']} NTU, Temp={payload['temperature']}°C | Risk={data.get('risk_level')}")
            return True
        else:
            print(f"[ERROR] API returned HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[CONNECTION FAILURE] Could not reach backend at {api_url}: {e}")
        return False


def run_simulator(api_url: str, api_key: str, interval: float, count: int, mode: str):
    print("=" * 65)
    print("[AquaWatch] Automated Water Quality Monitoring - Telemetry Simulator")
    print(f"Target Endpoint : {api_url}")

    print(f"Simulation Mode : {mode.upper()}")
    print(f"Interval        : {interval} seconds")
    print(f"Reading Limit   : {'Infinite' if count <= 0 else count}")
    print("=" * 65)

    sent = 0
    try:
        while True:
            payload = generate_reading(mode=mode)
            send_reading(api_url, api_key, payload)
            sent += 1
            if count > 0 and sent >= count:
                print(f"\n[DONE] Finished sending {sent} simulated readings.")
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[STOPPED] Simulator interrupted by user.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AquaWatch Water Quality Telemetry Simulator")
    parser.add_argument("--url", default=DEFAULT_API_URL, help="Backend ingestion endpoint")
    parser.add_argument("--key", default=DEFAULT_API_KEY, help="X-Device-Token security header")
    parser.add_argument("--interval", type=float, default=2.5, help="Seconds between readings (default: 2.5s)")
    parser.add_argument("--count", type=int, default=0, help="Total readings to send (0 = infinite)")
    parser.add_argument("--mode", default="mixed", choices=["normal", "acidic_spike", "turbidity_spike", "mixed"], help="Simulation profile")

    args = parser.parse_args()
    run_simulator(
        api_url=args.url,
        api_key=args.key,
        interval=args.interval,
        count=args.count,
        mode=args.mode
    )
