# Hardware & Firmware Integration Guide: ESP32 Microcontroller

This guide provides technical specifications, wiring pinouts, voltage conditioning, and firmware architecture for interfacing physical water quality sensors with the ESP32 and transmitting telemetry to the FastAPI backend.

---

## 1. ESP32 Pinout & Sensor Interfacing Diagram

| Sensor Module | Type / Interface | ESP32 GPIO Pin | Operating Voltage | Voltage Conditioning Needed? |
| :--- | :--- | :--- | :--- | :--- |
| **Analog pH Sensor (e.g. SEN0161 / PH-4502C)** | Analog (0.0V - 3.0V) | **GPIO 34** (ADC1_CH6, Input-only) | 5.0V VCC | **Yes** (Resistor Divider if output > 3.3V) |
| **Analog Turbidity Sensor (e.g. SEN0189 / TSW-20/30)** | Analog (0.0V - 4.5V) | **GPIO 35** (ADC1_CH7, Input-only) | 5.0V VCC | **Yes: CRITICAL** (10k / 20k Voltage Divider) |
| **Waterproof Temperature (DS18B20)** | Digital 1-Wire | **GPIO 4** (Pull-up with 4.7k resistor) | 3.3V or 5.0V | No (Native 3.3V logic) |
| **Dissolved Oxygen (DO) (e.g. Gravity DO Kit)** | Analog / I2C | **GPIO 32** (or I2C SDA=21, SCL=22) | 3.3V / 5.0V | Optional / Future Phase |

---

## 2. ESP32 ADC & Voltage Conditioning Considerations

> [!WARNING]
> **ESP32 ADC Maximum Input Voltage is 3.3V (Absolute Max 3.6V).**
> Many analog turbidity and pH modules are powered by **5.0V** and output analog voltages up to **4.5V** in pure clean water.
> Connecting 4.5V directly to ESP32 analog pins will damage the ESP32 silicon permanently!

### Voltage Divider Circuit for 5V Analog Sensors:
```
Sensor Vout (0 - 4.5V)
       │
      [R1: 10 kΩ]
       │
       ├───> ESP32 ADC Pin (GPIO 34 or 35) [Max: ~3.0V safe]
       │
      [R2: 20 kΩ]
       │
      GND
```
*Formula:*
$$V_{ADC} = V_{sensor} \times \frac{R_2}{R_1 + R_2} = 4.5V \times \frac{20}{10 + 20} = 3.0V$$

---

## 3. Sensor Calibration Procedures

### A. Analog pH Sensor
1. Soak probe in neutral buffer solution (**pH 7.00**). Record raw ADC voltage $V_7$.
2. Soak probe in acidic buffer solution (**pH 4.01**). Record raw ADC voltage $V_4$.
3. Compute slope $m$ and intercept $b$:
   $$pH = 7.0 + \frac{V_{raw} - V_7}{m}$$

### B. Turbidity Sensor (SEN0189)
1. In clean distilled water, output voltage is typically highest (~4.1V - 4.5V before divider).
2. Turbidity curve is non-linear and calibrated against Formazin Nephelometric standards:
   $$NTU = -1120.4 \times V_{actual}^2 + 5742.3 \times V_{actual} - 4352.9$$
   *(Ensure values are clamped to 0.0 NTU for clean clear water).*

---

## 4. HTTP Telemetry Payload Specification

The ESP32 firmware transmits data via HTTP `POST` to:
`http://<BACKEND_HOST_IP>:8000/api/readings`

### Required HTTP Headers:
- `Content-Type: application/json`
- `X-Device-Token: dev-secret-token-123`

### JSON Request Body Schema:
```json
{
  "device_id": "ESP32-NODE-01",
  "is_simulated": false,
  "ph": 7.35,
  "turbidity": 0.85,
  "temperature": 24.2,
  "dissolved_oxygen": null
}
```
*Note: When Dissolved Oxygen is uninstalled, send `null` or omit the field. Never transmit fake placeholder values (e.g. 0.0 or 999.0).*

---

## 5. ESP32 Arduino / C++ Firmware Scaffold

Save as `firmware/esp32/aqua_watch_node.ino`:

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>

// Wi-Fi Credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server Configuration
const char* serverUrl = "http://192.168.1.100:8000/api/readings";
const char* deviceToken = "dev-secret-token-123";
const char* deviceId = "ESP32-NODE-01";

// Pin Allocations
#define PH_PIN 34
#define TURBIDITY_PIN 35
#define ONE_WIRE_BUS 4

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensors(&oneWire);

void setup() {
  Serial.begin(115200);
  tempSensors.begin();
  
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // 1. Read Temperature
    tempSensors.requestTemperatures();
    float temperature = tempSensors.getTempCByIndex(0);

    // 2. Read pH (Averaged 10 samples)
    long phSum = 0;
    for(int i = 0; i < 10; i++) {
      phSum += analogRead(PH_PIN);
      delay(10);
    }
    float phVoltage = (phSum / 10.0) * (3.3 / 4095.0);
    float ph = 3.5 * phVoltage; // Replace with calibrated equation

    // 3. Read Turbidity
    long turbSum = 0;
    for(int i = 0; i < 10; i++) {
      turbSum += analogRead(TURBIDITY_PIN);
      delay(10);
    }
    float turbVoltage = (turbSum / 10.0) * (3.3 / 4095.0);
    float turbidity = map(turbVoltage, 0.0, 3.0, 100.0, 0.0); // Calibrated NTU curve

    // 4. Construct JSON
    StaticJsonDocument<256> doc;
    doc["device_id"] = deviceId;
    doc["is_simulated"] = false;
    doc["ph"] = ph;
    doc["turbidity"] = turbidity;
    doc["temperature"] = temperature;
    doc["dissolved_oxygen"] = nullptr; // Uninstalled

    String jsonString;
    serializeJson(doc, jsonString);

    // 5. Send HTTP POST
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-Device-Token", deviceToken);

    int httpCode = http.POST(jsonString);
    if (httpCode > 0) {
      Serial.printf("Telemetry dispatched. HTTP Code: %d\n", httpCode);
    } else {
      Serial.printf("HTTP Error: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
  }

  delay(5000); // Send reading every 5 seconds
}
```
