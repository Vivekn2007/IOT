# Person 1 Master Guide: Simulation Architect & System Integration

**Module Branch**: `E:\IOT project\branches\branch-01-carla-simulation-bringup\`  
**Local CARLA Executable**: `D:\CARLA_0.9.16\CarlaUE4.exe`  
**Host Environment**: Windows 11 (64-bit) with Python 3.12 (`carla-0.9.16` + `pyzmq` installed)  
**Linux / Ubuntu / WSL2 Requirement**: **NOT REQUIRED (100% Windows 11 Native)**

---

## 1. Operating System Clarification: Why Ubuntu is NOT Required
In academic robotics papers, authors frequently cite **ROS 2 on Ubuntu** solely because ROS 2 originated on Linux. However, at its core, ROS 2 is simply a **Publish/Subscribe messaging bus** connecting separate software programs.

On **Windows 11**, we achieve the exact same publish/subscribe architecture natively using **Python + ZeroMQ (`pyzmq`)** over local TCP ports (`127.0.0.1`):
* **Zero Overhead**: No virtual machines, no dual-booting, and no complex Linux compilation errors.
* **Full Hardware Support**: Your GPU (DirectX 11/12, CUDA), CARLA 0.9.16, PyTorch, and OpenCV all run at maximum native performance on Windows 11.
* **Instant Inter-Process Streaming**: Person 1 publishes sensor feeds to `tcp://127.0.0.1:5555`, and Persons 2–6 subscribe with just 4 lines of Python.

*(Note: If your institution strictly mandates ROS 2 for grading, the exact same nodes can be bridged into ROS 2 on WSL2 at any time without changing sensor logic, as detailed in Section 5).*

---

## 2. Directory Structure of this Branch
```
E:\IOT project\branches\branch-01-carla-simulation-bringup\
├── README_PERSON1_GUIDE.md               # This step-by-step master manual
├── config\
│   └── sensors.json                      # Exact sensor mounting coordinates & parameters
├── scripts\
│   ├── run_carla_win.bat                 # One-click Windows CARLA 0.9.16 launcher
│   ├── carla_win11_publisher.py          # Native Windows 11 4-sensor broadcaster (ZeroMQ)
│   ├── test_client_win11.py              # Test subscriber client to verify incoming streams
│   ├── carla_standalone_runner.py        # Standalone HUD and autopilot simulation runner
│   ├── weather_and_pothole_spawner.py    # Dedicated monsoon weather & pothole spawner
│   └── telemetry_health_monitor.py       # Topic frequency and health analyzer
├── launch\
│   └── simulation_bringup.launch.py      # ROS 2 master launch file (optional alternative)
├── package.xml                           # ROS 2 package definition (optional alternative)
└── setup.py                              # ROS 2 Python setup script (optional alternative)
```

---

## 3. Step-by-Step Instructions: Pure Windows 11 Execution

### STEP 1: Verify Python Environment
Open PowerShell or Command Prompt on Windows 11 and verify that `carla` and `pyzmq` are present:
```powershell
python -c "import carla, zmq; print('Environment Ready! CARLA:', carla.__file__)"
```
*(If either package is missing, run: `pip install pyzmq` and `pip install D:\CARLA_0.9.16\PythonAPI\carla\dist\carla-0.9.16-cp312-cp312-win_amd64.whl`)*

---

### STEP 2: Mount the Multi-Modal Sensor Rig
The exact physical coordinate offsets for the vehicle rig are defined as follows:

| Sensor | CARLA Blueprint | Mount Position $(X, Y, Z)$ | Orientation $(\text{Roll}, \text{Pitch}, \text{Yaw})$ | Output Channel / Topic | Target Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Front Optical Camera** | `sensor.camera.rgb` | $(1.2, 0.0, 1.3)\text{ m}$ (Windshield) | $(0^\circ, -2^\circ, 0^\circ)$ | `tcp://127.0.0.1:5555` [`camera`] | 30 FPS |
| **77 GHz mmWave Radar** | `sensor.other.radar` | $(2.3, 0.0, 0.5)\text{ m}$ (Bumper) | $(0^\circ, -1.5^\circ, 0^\circ)$ | `tcp://127.0.0.1:5555` [`radar`] | 20 Hz |
| **Downward Ultrasonic** | `sensor.lidar.ray_cast` | $(1.0, 0.0, 0.35)\text{ m}$ (Under-chassis) | $(0^\circ, -90^\circ, 0^\circ)$ *(pointing down)* | `tcp://127.0.0.1:5555` [`ultrasonic`] | 50 Hz |
| **Chassis 6-Axis IMU** | `sensor.other.imu` | $(0.0, 0.0, 0.2)\text{ m}$ (Center of mass) | $(0^\circ, 0^\circ, 0^\circ)$ | `tcp://127.0.0.1:5555` [`imu`] | 100 Hz |

---

### STEP 3: Launch CARLA 0.9.16
In **Terminal 1** (or double-click the file in Windows File Explorer):
```cmd
"E:\IOT project\branches\branch-01-carla-simulation-bringup\scripts\run_carla_win.bat"
```
*This launches `D:\CARLA_0.9.16\CarlaUE4.exe` on port 2000 with optimal rendering settings.*

---

### STEP 4: Start the Windows Sensor Broadcaster
In **Terminal 2**, start the main simulation and telemetry broadcaster:
```powershell
python "E:\IOT project\branches\branch-01-carla-simulation-bringup\scripts\carla_win11_publisher.py"
```

**What this automatically executes:**
1. Connects to CARLA 0.9.16 on `127.0.0.1:2000`.
2. Injects the **Indian Monsoon Weather Profile**:
   * Precipitation: $100\%$ (Torrential rain)
   * Road Deposits: $100\%$ (Deep standing water & puddles)
   * Atmospheric Fog: $75\%$ (Dense optical occlusion)
   * Low sun elevation ($15^\circ$) creating road water glare.
3. Spawns the ego-vehicle on the road and engages autopilot.
4. Mounts the 4 sensors with exact coordinates.
5. Broadcasts live serialized data over `tcp://127.0.0.1:5555`.

---

### STEP 5: Verify the Live Telemetry Feeds
In **Terminal 3**, run the verification listener client:
```powershell
python "E:\IOT project\branches\branch-01-carla-simulation-bringup\scripts\test_client_win11.py"
```
You will see all 4 streams flowing in real time:
```
[RECV: CAMERA] Frame 1420 | Size: 1280x720 (921600 bytes)
[RECV: RADAR] Frame 1420 | Targets: 148 points detected
[RECV: SONAR] Frame 1420 | Points: 4
[RECV: IMU] Frame 1420 | Z-Accel: -9.81 m/s²
```
When this stream is running, **your job as Person 1 is complete!**

---

## 4. Handoff to Team Members on Windows 11

Explain to your teammates that they do **not** need to install complex software or Ubuntu. They simply connect to your local broadcaster using Python:

```python
import zmq, json

# 1. Connect to Person 1's broadcaster
context = zmq.Context()
sub = context.socket(zmq.SUB)
sub.connect("tcp://127.0.0.1:5555")

# 2. Select topics of interest
sub.setsockopt(zmq.SUBSCRIBE, b"camera")  # For Person 2 (Vision)
# sub.setsockopt(zmq.SUBSCRIBE, b"radar")       # For Person 3 (Radar DSP)
# sub.setsockopt(zmq.SUBSCRIBE, b"ultrasonic")  # For Person 4 (Acoustics)
# sub.setsockopt(zmq.SUBSCRIBE, b"imu")         # For Person 4 (Chassis Shock)

# 3. Receive live frames in a loop
while True:
  topic, header, payload = sub.recv_multipart()
  # Process live frame!
```

---

## 5. (Optional) Alternative ROS 2 Bridge via WSL2
If you ever need to interface directly with external ROS 2 tools (e.g. RViz2 or Nav2) on Linux/WSL2:
1. Open WSL2 (Ubuntu 22.04).
2. Install ROS 2 Humble and `carla-ros-bridge`:
   ```bash
   sudo apt install -y ros-humble-desktop ros-humble-carla-ros-bridge
   ```
3. Run the ROS 2 launch file pointing to your Windows CARLA host:
   ```bash
   ros2 launch pothole_simulation_bringup simulation_bringup.launch.py host:=127.0.0.1 port:=2000
   ```
4. Run the health monitor:
   ```bash
   python3 scripts/telemetry_health_monitor.py
   ```
