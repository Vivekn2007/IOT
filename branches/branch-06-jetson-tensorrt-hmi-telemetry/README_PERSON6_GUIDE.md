# Person 6 Master Guide: Driver HMI Display & NB-IoT Cloud Telemetry

**Module Branch**: `E:\IOT project\branches\branch-06-jetson-tensorrt-hmi-telemetry\`  
**Role**: Edge Computing, Driver HMI & Municipal IoT Specialist  
**Input**: Subscribes to `tcp://127.0.0.1:5559` (topic `'fused_hazards'`) from Person 5  
**Outputs**:
  1. In-cabin TFT LCD Driver HUD Interface (OpenCV graphical display with deceleration prompts & audio alerts)
  2. MZH010 NB-IoT wireless telemetry registry: `data/municipal_road_hazard_registry.json`

---

## 1. System Components
* **`driver_hud_gui.py`**:
  * Automotive TFT LCD Cockpit display layout.
  * Real-time distance countdown (e.g. `14.2 M`).
  * Dynamic threat banner: Green (Safe), Amber (Caution), Red (Critical Waterlogged Pothole).
  * Audio buzzer alert trigger (via `winsound.Beep`).
  * Sub-surface acoustic depth profile and lateral offset metrics.
* **`nbiot_telemetry.py`**:
  * Encapsulates geo-tagged incident records with Delhi/Gurgaon GPS coordinates.
  * Dispatches JSON telemetry payloads to local municipal authority registry.

---

## 2. Launch Commands (1-Click)
* Start Driver HUD: Double-click `E:\IOT project\start_driver_hmi.bat`
* Start NB-IoT Cloud Telemetry: Double-click `E:\IOT project\start_nbiot_telemetry.bat`
