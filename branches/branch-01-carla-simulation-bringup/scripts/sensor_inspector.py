#!/usr/bin/env python3
"""
sensor_inspector.py
-------------------------------------------------------------------------------
Interactive Multi-Modal Sensor Data Inspector for Windows 11.
Connects to tcp://127.0.0.1:5555 and allows you to view the exact raw data,
numbers, coordinates, and telemetry coming from each virtual sensor.

Usage:
  python sensor_inspector.py          (Interactive Menu)
  python sensor_inspector.py --radar  (Directly view Radar point cloud targets)
  python sensor_inspector.py --imu    (Directly view IMU 6-axis accelerations)
  python sensor_inspector.py --sonar  (Directly view Ultrasonic ground depth)
  python sensor_inspector.py --camera (Directly view Camera frame metadata)
-------------------------------------------------------------------------------
"""

import sys
import time
import json
import argparse

try:
    import zmq
except ImportError:
    print("[ERROR] pyzmq missing. Run: pip install pyzmq")
    sys.exit(1)

def inspect_all(sub):
    print("\n[STREAMING ALL SENSORS] Press Ctrl+C to stop...\n")
    print(f"{'TOPIC':<12} | {'FRAME':<8} | {'KEY METRICS / SENSOR PAYLOAD'}")
    print("-" * 75)
    
    while True:
        parts = sub.recv_multipart()
        topic = parts[0].decode('utf-8')
        
        if topic == 'camera':
            hdr = json.loads(parts[1].decode('utf-8'))
            size_kb = len(parts[2]) / 1024.0
            print(f"{'CAMERA':<12} | {hdr['frame']:<8} | Res: {hdr['width']}x{hdr['height']} | Size: {size_kb:5.1f} KB | Time: {hdr['timestamp']:.2f}s")
            
        elif topic == 'radar':
            data = json.loads(parts[1].decode('utf-8'))
            pts = data.get('points', [])
            summary = f"Detected {len(pts)} targets"
            if pts:
                closest = min(pts, key=lambda p: p['depth'])
                summary += f" | Closest: {closest['depth']:.1f}m (Vel: {closest['velocity']:+.1f} m/s, Az: {closest['azimuth']:+.2f} rad)"
            print(f"{'RADAR':<12} | {data['frame']:<8} | {summary}")
            
        elif topic == 'ultrasonic':
            data = json.loads(parts[1].decode('utf-8'))
            print(f"{'ULTRASONIC':<12} | {data['frame']:<8} | Ground clearance active | Rays returned: {data.get('points_count', 0)}")
            
        elif topic == 'imu':
            data = json.loads(parts[1].decode('utf-8'))
            acc = data['accel']
            gyro = data['gyro']
            print(f"{'IMU':<12} | {data['frame']:<8} | Accel (m/s²): X={acc['x']:+5.2f}, Y={acc['y']:+5.2f}, Z={acc['z']:+5.2f} | Gyro Z={gyro['z']:+5.2f}")

def inspect_radar(sub):
    sub.setsockopt(zmq.SUBSCRIBE, b'radar')
    print("\n[STREAMING 77 GHz RADAR POINT CLOUD DATA] Press Ctrl+C to stop...\n")
    while True:
        parts = sub.recv_multipart()
        if parts[0] == b'radar':
            data = json.loads(parts[1].decode('utf-8'))
            pts = data.get('points', [])
            print(f"\n=== RADAR FRAME {data['frame']} (Total Targets: {len(pts)}) ===")
            print(f"{'TARGET #':<10} | {'RANGE (Depth)':<15} | {'AZIMUTH':<15} | {'ELEVATION':<15} | {'DOPPLER VELOCITY'}")
            print("-" * 75)
            # Print up to the first 8 closest targets
            sorted_pts = sorted(pts, key=lambda p: p['depth'])[:8]
            for i, p in enumerate(sorted_pts):
                print(f"Target {i+1:<4} | {p['depth']:>6.2f} meters   | {p['azimuth']:>+6.3f} rad     | {p['altitude']:>+6.3f} rad     | {p['velocity']:>+6.2f} m/s")
            time.sleep(0.1)

def inspect_imu(sub):
    sub.setsockopt(zmq.SUBSCRIBE, b'imu')
    print("\n[STREAMING 6-AXIS IMU MOTION DATA] Press Ctrl+C to stop...\n")
    print(f"{'FRAME':<8} | {'ACCEL X (m/s²)':<16} | {'ACCEL Y (m/s²)':<16} | {'ACCEL Z (Shock)':<16} | {'GYRO Z (Yaw Rate)'}")
    print("-" * 80)
    while True:
        parts = sub.recv_multipart()
        if parts[0] == b'imu':
            data = json.loads(parts[1].decode('utf-8'))
            acc = data['accel']
            gyro = data['gyro']
            shock_alert = " <-- [CHASSIS SHOCK!]" if abs(acc['z']) > 12.0 or abs(acc['z']) < 7.0 else ""
            print(f"{data['frame']:<8} | {acc['x']:>+12.3f}      | {acc['y']:>+12.3f}      | {acc['z']:>+12.3f}     | {gyro['z']:>+10.4f} rad/s{shock_alert}")

def inspect_sonar(sub):
    sub.setsockopt(zmq.SUBSCRIBE, b'ultrasonic')
    print("\n[STREAMING DOWNWARD ACOUSTIC SONAR DATA] Press Ctrl+C to stop...\n")
    while True:
        parts = sub.recv_multipart()
        if parts[0] == b'ultrasonic':
            data = json.loads(parts[1].decode('utf-8'))
            pts_cnt = data.get('points_count', 0)
            print(f"Frame: {data['frame']:<8} | Transducer Returns: {pts_cnt} rays | Road Sounding: ACTIVE | Baseline: 0.35m nominal")

def inspect_camera(sub):
    sub.setsockopt(zmq.SUBSCRIBE, b'camera')
    print("\n[STREAMING OPTICAL CAMERA METADATA] Press Ctrl+C to stop...\n")
    while True:
        parts = sub.recv_multipart()
        if parts[0] == b'camera':
            hdr = json.loads(parts[1].decode('utf-8'))
            raw_len = len(parts[2])
            is_jpg = parts[2][:2] == b'\xff\xd8'
            fmt = "JPEG Compressed" if is_jpg else "Raw Uncompressed"
            print(f"Frame: {hdr['frame']:<8} | Resolution: {hdr['width']}x{hdr['height']} | Timestamp: {hdr['timestamp']:.3f}s | Payload: {raw_len/1024.0:.1f} KB ({fmt})")

def main():
    parser = argparse.ArgumentParser(description="Live Sensor Data Inspector")
    parser.add_argument("--radar", action="store_true", help="Inspect Radar stream only")
    parser.add_argument("--imu", action="store_true", help="Inspect IMU stream only")
    parser.add_argument("--sonar", action="store_true", help="Inspect Ultrasonic stream only")
    parser.add_argument("--camera", action="store_true", help="Inspect Camera stream only")
    args = parser.parse_args()

    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    sub.connect("tcp://127.0.0.1:5555")

    try:
        if args.radar:
            inspect_radar(sub)
        elif args.imu:
            inspect_imu(sub)
        elif args.sonar:
            inspect_sonar(sub)
        elif args.camera:
            inspect_camera(sub)
        else:
            # Interactive Menu
            print("==========================================================================")
            print("         MULTI-MODAL PERCEPTION RIG: LIVE SENSOR DATA INSPECTOR           ")
            print("         Connected to: tcp://127.0.0.1:5555                              ")
            print("==========================================================================")
            print(" Select which sensor data you want to inspect:")
            print("   [1] View ALL SENSORS Summary Stream")
            print("   [2] View 77 GHz RADAR Targets (Range, Azimuth, Doppler Velocity)")
            print("   [3] View 6-Axis IMU Data (X, Y, Z Accelerations & Chassis Shock)")
            print("   [4] View Downward ULTRASONIC Sonar Data (Ground Clearance)")
            print("   [5] View OPTICAL CAMERA Stream (Frames & Payload Bytes)")
            print("==========================================================================")
            
            choice = input("Enter choice (1-5) [Default: 1]: ").strip()
            if choice == '2':
                inspect_radar(sub)
            elif choice == '3':
                inspect_imu(sub)
            elif choice == '4':
                inspect_sonar(sub)
            elif choice == '5':
                inspect_camera(sub)
            else:
                sub.setsockopt(zmq.SUBSCRIBE, b'')
                inspect_all(sub)

    except KeyboardInterrupt:
        print("\n\nInspector stopped by user.")
    finally:
        sub.close()
        context.term()

if __name__ == '__main__':
    main()
