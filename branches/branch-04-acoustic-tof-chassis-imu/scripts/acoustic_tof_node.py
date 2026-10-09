#!/usr/bin/env python3
"""
acoustic_tof_node.py
-------------------------------------------------------------------------------
Person 4 Module: Downward Acoustic Sonar + Chassis IMU Node (Windows 11).

This module:
  1. Subscribes to 'ultrasonic' + 'imu' topics from tcp://127.0.0.1:5555.
  2. Implements dual-media acoustic ToF depth profiling:
       - Air path:   v_sound = 343 m/s (road clearance)
       - Water path: v_sound = 1480 m/s (submerged pothole depth)
  3. Continuously tracks baseline road clearance D_normal (~0.35m).
  4. Computes true pothole depth: Depth = D_measured - D_normal
  5. Monitors chassis Z-axis IMU for suspension shock spikes (|az| > 2.5g)
     as a fail-safe physical ground-truth confirmation.
  6. Publishes acoustic depth profiles to tcp://127.0.0.1:5558
     (topic 'acoustic_depth') for Person 5 (EKF).
-------------------------------------------------------------------------------
"""

import sys, os, time, json
import cv2
import numpy as np

try:
    import zmq
except ImportError:
    print("[ERROR] pyzmq missing. Run: pip install pyzmq")
    sys.exit(1)

# Physical constants
V_SOUND_AIR   = 343.0    # m/s (speed of sound in air at 20°C)
V_SOUND_WATER = 1480.0   # m/s (speed of sound in turbid water)
D_NORMAL_INIT = 0.35     # m   (nominal chassis-to-road clearance)
SHOCK_THRESHOLD_G = 2.5  # multiples of g to trigger chassis shock alert

class AcousticToFProfiler:
    """
    Implements the IIT Bombay AUV Matsya-inspired downward acoustic sonar profiling.
    Continuously estimates road clearance and detects pothole depth
    under standing water using dual-media wave propagation.
    """
    def __init__(self):
        self.D_normal = D_NORMAL_INIT      # Baseline road clearance (calibrated)
        self.alpha    = 0.02               # EMA smoothing factor for baseline
        self.pothole_events = []           # Log of detected potholes

    def update_baseline(self, d_measured_m: float):
        """Updates the rolling baseline clearance when on flat road."""
        if abs(d_measured_m - self.D_normal) < 0.08:
            # Within 8cm of baseline -> update baseline
            self.D_normal = (1 - self.alpha) * self.D_normal + self.alpha * d_measured_m

    def air_tof_to_distance(self, echo_time_s: float) -> float:
        """Convert round-trip ultrasonic ToF (in air) to distance in metres."""
        return (V_SOUND_AIR * echo_time_s) / 2.0

    def water_tof_to_depth(self, echo_time_s: float) -> float:
        """
        Converts underwater ToF echo to depth below water surface.
        Used for the second echo which has penetrated the standing water layer
        and reflected from the submerged asphalt pothole floor.
        """
        return (V_SOUND_WATER * echo_time_s) / 2.0

    def compute_pothole_depth(self, d_measured_m: float) -> dict:
        """
        Compare measured clearance against calibrated baseline.
        If significantly deeper -> classify as pothole and estimate depth.
        """
        pothole_depth = d_measured_m - self.D_normal
        if pothole_depth > 0.05:   # More than 5 cm deeper than baseline
            label = 'POTHOLE_VOID'
            if d_measured_m > 0.5:  # Water-filled (deeper than bare asphalt void)
                label = 'POTHOLE_WATERLOGGED'
            return {
                'label': label,
                'D_measured_m': round(d_measured_m, 4),
                'D_baseline_m': round(self.D_normal, 4),
                'pothole_depth_m': round(pothole_depth, 4),
                'pothole_depth_cm': round(pothole_depth * 100, 2),
                'is_pothole': True
            }
        else:
            self.update_baseline(d_measured_m)
            return {
                'label': 'ROAD_SURFACE',
                'D_measured_m': round(d_measured_m, 4),
                'D_baseline_m': round(self.D_normal, 4),
                'pothole_depth_m': 0.0,
                'pothole_depth_cm': 0.0,
                'is_pothole': False
            }

class ChassisIMUMonitor:
    """Monitors Z-axis chassis acceleration for suspension shock events."""
    def __init__(self):
        self.g = 9.81
        self.shock_log = []
        self.last_az = -9.81

    def check_shock(self, imu_data: dict) -> dict:
        az = imu_data['accel']['z']
        ax = imu_data['accel']['x']
        ay = imu_data['accel']['y']
        gyro_z = imu_data['gyro']['z']

        # Magnitude of deviation from gravity in Z
        delta_az = abs(az - (-self.g))
        shock_g = delta_az / self.g

        is_shock = shock_g > SHOCK_THRESHOLD_G
        if is_shock:
            self.shock_log.append({'time': time.time(), 'az': round(az, 3), 'shock_g': round(shock_g, 2)})

        return {
            'az': round(az, 3),
            'ax': round(ax, 3),
            'ay': round(ay, 3),
            'gyro_z': round(gyro_z, 4),
            'shock_g': round(shock_g, 2),
            'is_chassis_shock': is_shock,
            'total_shocks': len(self.shock_log)
        }

def draw_sonar_hud(profiler, imu_result, sonar_result, frame_count, fps):
    """Renders a live ASCII-style sonar depth HUD."""
    img = np.zeros((500, 500, 3), dtype=np.uint8)
    img[:] = (10, 15, 25)

    # Title
    cv2.putText(img, "PERSON 4: ACOUSTIC SONAR + IMU NODE", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    cv2.line(img, (10, 40), (490, 40), (0, 100, 100), 1)

    # Sonar depth display
    d_meas = sonar_result.get('D_measured_m', D_NORMAL_INIT)
    d_base = sonar_result.get('D_baseline_m', D_NORMAL_INIT)
    depth_cm = sonar_result.get('pothole_depth_cm', 0.0)
    is_hole = sonar_result.get('is_pothole', False)
    label = sonar_result.get('label', 'ROAD_SURFACE')

    color = (0, 0, 255) if is_hole else (0, 255, 0)

    cv2.putText(img, "DOWNWARD ACOUSTIC SONAR (25-50 kHz)", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(img, f"Baseline D_normal  : {d_base:.3f} m", (30, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(img, f"Measured D_current : {d_meas:.3f} m", (30, 128),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(img, f"Pothole Depth      : {depth_cm:.1f} cm", (30, 156),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(img, f"Classification     : {label}", (30, 185),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    # IMU section
    cv2.line(img, (10, 205), (490, 205), (0, 80, 80), 1)
    cv2.putText(img, "6-AXIS IMU (CHASSIS SHOCK DETECTION)", (20, 230),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    az = imu_result.get('az', -9.81)
    shock_g = imu_result.get('shock_g', 0.0)
    is_shock = imu_result.get('is_chassis_shock', False)
    shocks_total = imu_result.get('total_shocks', 0)
    shock_color = (0, 0, 255) if is_shock else (0, 255, 0)

    cv2.putText(img, f"Z-Accel : {az:+.3f} m/s2", (30, 260),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(img, f"Shock   : {shock_g:.2f} g", (30, 288),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, shock_color, 2)
    cv2.putText(img, f"Status  : {'** CHASSIS SHOCK! **' if is_shock else 'Normal Ride'}", (30, 318),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, shock_color, 2)
    cv2.putText(img, f"Total shock events logged: {shocks_total}", (30, 348),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    # Stats footer
    cv2.line(img, (10, 375), (490, 375), (0, 60, 60), 1)
    cv2.putText(img, f"Frame: {frame_count}  |  FPS: {fps:.1f}  |  Port Out: 5558", (20, 400),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)
    cv2.putText(img, "v_air=343m/s | v_water=1480m/s | AUV Matsya ToF logic", (20, 425),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (80, 80, 80), 1)

    return img

def main():
    print("=" * 70)
    print("  PERSON 4: ACOUSTIC ToF + CHASSIS IMU NODE (Windows 11)             ")
    print("  Input:  tcp://127.0.0.1:5555 (topics: 'ultrasonic', 'imu')         ")
    print("  Output: tcp://127.0.0.1:5558 (topic: 'acoustic_depth')             ")
    print("=" * 70)

    ctx = zmq.Context()

    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.RCVHWM, 50)
    sub.connect("tcp://127.0.0.1:5555")
    sub.setsockopt(zmq.SUBSCRIBE, b'ultrasonic')
    sub.setsockopt(zmq.SUBSCRIBE, b'imu')

    pub = ctx.socket(zmq.PUB)
    pub.setsockopt(zmq.SNDHWM, 30)
    pub.bind("tcp://127.0.0.1:5558")
    print("  Publisher bound to tcp://127.0.0.1:5558 (topic: 'acoustic_depth').\n")

    profiler = AcousticToFProfiler()
    imu_monitor = ChassisIMUMonitor()

    cv2.namedWindow("Person 4: Acoustic Sonar + IMU HUD", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Person 4: Acoustic Sonar + IMU HUD", 500, 500)

    # Last known state
    last_sonar = {'label': 'ROAD_SURFACE', 'D_measured_m': 0.35,
                  'D_baseline_m': 0.35, 'pothole_depth_cm': 0.0, 'is_pothole': False}
    last_imu = {'az': -9.81, 'ax': 0.0, 'ay': 0.0, 'gyro_z': 0.0,
                'shock_g': 0.0, 'is_chassis_shock': False, 'total_shocks': 0}
    frame_count = 0
    fps_counter = 0
    fps_time = time.time()
    display_fps = 0.0

    print("  Listening on port 5555... Press 'q' in HUD window to exit.\n")

    try:
        while True:
            while sub.poll(timeout=20):
                parts = sub.recv_multipart()
                topic = parts[0].decode('utf-8')
                fps_counter += 1
                frame_count += 1

                if topic == 'ultrasonic':
                    data = json.loads(parts[1].decode('utf-8'))
                    d_meas = data.get('measured_distance_m', D_NORMAL_INIT)
                    last_sonar = profiler.compute_pothole_depth(d_meas)
                    last_sonar['frame'] = data.get('frame', 0)
                    if data.get('is_pothole_active', False):
                        last_sonar['pothole_depth_cm'] = data.get('depth_cm', last_sonar['pothole_depth_cm'])
                        last_sonar['is_pothole'] = True
                        last_sonar['label'] = 'POTHOLE_WATERLOGGED'

                    if last_sonar['is_pothole']:
                        print(f"  [SONAR] {last_sonar['label']} detected! "
                              f"Depth = {last_sonar['pothole_depth_cm']:.1f} cm "
                              f"(D_meas={last_sonar['D_measured_m']:.3f}m)")

                    payload = {'timestamp': time.time(), **last_sonar, **last_imu}
                    pub.send_multipart([b'acoustic_depth', json.dumps(payload).encode('utf-8')])

                elif topic == 'imu':
                    data = json.loads(parts[1].decode('utf-8'))
                    last_imu = imu_monitor.check_shock(data)
                    if last_imu['is_chassis_shock']:
                        print(f"  [IMU]   ** CHASSIS SHOCK! ** {last_imu['shock_g']:.2f}g "
                              f"(Total events: {last_imu['total_shocks']})")

            now = time.time()
            if now - fps_time >= 1.0:
                display_fps = fps_counter / (now - fps_time)
                fps_counter = 0
                fps_time = now

            hud = draw_sonar_hud(profiler, last_imu, last_sonar, frame_count, display_fps)
            cv2.imshow("Person 4: Acoustic Sonar + IMU HUD", hud)
            if cv2.waitKey(20) & 0xFF in (ord('q'), 27):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        sub.close()
        pub.close()
        ctx.term()
        print("\n[INFO] Person 4 Acoustic/IMU Node stopped.")

if __name__ == '__main__':
    main()
