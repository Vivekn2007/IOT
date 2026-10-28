# Advanced Multi-Modal Perception System for Real-Time Pothole Detection in Adverse Weather

**Official Project Root**: `E:\IOT project`  
**Target OS**: Windows 11 (100% Native Architecture, Python 3.12, CARLA 0.9.16)

---

## 1. Complete Multi-Modal Architecture (6 Team Members)

```
[Person 1: CARLA 0.9.16 Digital Twin] (Port 5555 Broadcast)
       │
       ├── Topic 'camera'     ──► [Person 2: YOLOv8 Adverse Weather Detector] ──► Port 5556 (2D BBoxes)
       │                                                                                │
       ├── Topic 'radar'      ──► [Person 3: 77GHz mmWave SFCC DSP Node]      ──► Port 5557 (3D Radar)
       │                                                                                │
       └── Topic 'ultrasonic' ──► [Person 4: Acoustic Sonar ToF + IMU Shock]  ──► Port 5558 (Depth Profile)
           & Topic 'imu'                                                                │
                                                                                        ▼
                                                             [Person 5: 3D Frustum + Adaptive EKF Fusion]
                                                                                        │ (Port 5559: Fused Hazards)
                                                                                        ▼
                                           ┌────────────────────────────────────────────┴──────────────────────────┐
                                           ▼                                                                       ▼
                   [Pothole Sense: Driver HUD & Engineer Console]                     [Person 6: MZH010 NB-IoT Cloud Telemetry]
                   (Web & Cockpit: Countdown, Radar Scope, Sonar Trace)               (Geo-Tagged Municipal Hazard Registry)
```

---

## 2. Dedicated Branches & Roles

| Branch Folder | Member Role | Primary Function & Technology |
| :--- | :--- | :--- |
| [`branch-01-carla-simulation-bringup`](./branches/branch-01-carla-simulation-bringup/) | **Person 1** (Simulation Architect) | CARLA 0.9.16 Digital Twin, 4-sensor rig, monsoon weather, ZeroMQ Port 5555 |
| [`branch-02-vision-yolov8-rdd2022`](./branches/branch-02-vision-yolov8-rdd2022/) | **Person 2** (Computer Vision) | CLAHE + Bilateral filtering, RDD2022 taxonomy, YOLOv8 detector |
| [`branch-03-radar-77ghz-sfcc-dsp`](./branches/branch-03-radar-77ghz-sfcc-dsp/) | **Person 3** (Radar DSP) | 77 GHz FMCW physics, SFCC cross-correlation, +20dB RCS water contrast |
| [`branch-04-acoustic-tof-chassis-imu`](./branches/branch-04-acoustic-tof-chassis-imu/) | **Person 4** (Acoustics & IMU) | Dual-media ToF (air 343m/s, water 1480m/s), AUV Matsya logic, IMU shock |
| [`branch-05-sensor-fusion-ekf-frustum`](./branches/branch-05-sensor-fusion-ekf-frustum/) | **Person 5** (Sensor Fusion) | 3D Frustum RoI Gating (88% compute reduction), Adaptive inverse-covariance EKF |
| [`branch-06-jetson-tensorrt-hmi-telemetry`](./branches/branch-06-jetson-tensorrt-hmi-telemetry/) | **Person 6** (HMI & Cloud IoT) | In-cabin automotive TFT HUD display, audio buzzer, NB-IoT municipal cloud sync |

---

## 3. How to Run the System (1-Click Launchers)

### Step 1: Simulator & World (Terminals 1, 2 & 3)
1. Double-click `start_carla.bat` *(starts CARLA 0.9.16 simulator)*
2. Double-click `start_broadcaster.bat` *(spawns vehicle rig, chase cam, and starts streaming)*
3. Double-click `spawn_potholes.bat` *(spawns 30+ potholes across lanes)*

### Step 2: Launch the Dashboards

* **🌟 New "Pothole Sense" Web Dashboard (Driver HUD & Engineer Console)**:
  * Double-click **`start_pothole_sense_dashboard.bat`**
  * Opens automatically in your browser at `http://localhost:8080`
  * Features two tabs:
    1. **Driver HUD**: Next hazard distance, depth, what to do prompt, speed widget, animated alert pill, and toggle between synthesized road vs live camera feed!
    2. **Engineer Console**: Live 77 GHz radar scope, ground truth verification metrics, sensor confidence bars, downward sonar trace & chassis shock graph, and fusion events log.
    3. Works both **Live with CARLA** and in **Offline Interactive Demo Mode**!

* **Desktop OpenCV Cockpit**:
  * Double-click `start_unified_dashboard.bat`

* **View Evaluation Benchmark Figures**:
  * Double-click `view_evaluation_graphs.bat` *(opens `evaluation_figures` folder)*
