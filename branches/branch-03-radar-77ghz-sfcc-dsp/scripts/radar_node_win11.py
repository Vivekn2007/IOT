#!/usr/bin/env python3
"""
radar_node_win11.py
-------------------------------------------------------------------------------
Person 3 Module: Live 77 GHz Radar DSP Node for Windows 11.

Pipeline:
  1. Subscribes to tcp://127.0.0.1:5555 (topic 'radar') from Person 1.
  2. Feeds each raw radar frame through the SFCC DSP Engine.
  3. Classifies each target: POTHOLE_WATERLOGGED | POTHOLE_DRY | CLUTTER.
  4. Renders a live terminal table AND an OpenCV radar scope visualization.
  5. Publishes cleaned targets to tcp://127.0.0.1:5557 (topic 'radar_targets')
     for Person 5 (Sensor Fusion / EKF).
-------------------------------------------------------------------------------
"""

import sys
import os
import time
import json
import math
import cv2
import numpy as np

try:
    import zmq
except ImportError:
    print("[ERROR] pyzmq missing. Run: pip install pyzmq")
    sys.exit(1)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sfcc_dsp import SFCCProcessor
from fmcw_physics import RADAR_PARAMS, range_resolution, max_range

def draw_radar_scope(targets, frame_id, fps):
    """Renders a 2D polar radar scope showing SFCC-classified targets."""
    scope_size = 600
    center_x, center_y = scope_size // 2, scope_size - 60
    max_range_m = 100.0
    img = np.zeros((scope_size, scope_size, 3), dtype=np.uint8)

    # Draw range rings
    for ring_m in [20, 40, 60, 80, 100]:
        r_px = int((ring_m / max_range_m) * (scope_size - 80))
        cv2.ellipse(img, (center_x, center_y), (r_px, r_px), 0, 180, 360, (0, 50, 0), 1)
        cv2.putText(img, f"{ring_m}m", (center_x + r_px + 4, center_y - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 100, 0), 1)

    # Draw azimuth lines: ±30° and ±60°
    for angle_deg in [-60, -30, 0, 30, 60]:
        angle_rad = math.radians(90 + angle_deg)
        x2 = int(center_x + (scope_size // 2 - 30) * math.cos(angle_rad))
        y2 = int(center_y - (scope_size // 2 - 30) * abs(math.sin(angle_rad)))
        cv2.line(img, (center_x, center_y), (x2, y2), (0, 40, 0), 1)
        cv2.putText(img, f"{angle_deg}°", (x2 - 12, y2 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 80, 0), 1)

    # Plot each classified target
    color_map = {
        'POTHOLE_WATERLOGGED': (0, 0, 255),   # RED  = water-filled pothole
        'POTHOLE_DRY':         (0, 165, 255), # ORANGE = dry pothole void
        'CLUTTER':             (60, 60, 60),  # DARK GREY = filtered noise
    }
    label_map = {
        'POTHOLE_WATERLOGGED': 'W',
        'POTHOLE_DRY':         'D',
        'CLUTTER':             'C',
    }

    for t in targets:
        depth = t['depth_m']
        az    = t['azimuth']
        label = t['label']
        if depth > max_range_m:
            continue
        r_px = int((depth / max_range_m) * (scope_size - 80))
        angle_rad = math.radians(90 + math.degrees(az))
        px = int(center_x + r_px * math.cos(angle_rad))
        py = int(center_y - r_px * math.sin(angle_rad))
        color = color_map.get(label, (100, 100, 100))
        cv2.circle(img, (px, py), 7, color, -1)
        cv2.putText(img, label_map.get(label, '?'), (px + 5, py - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

    # Legend
    cv2.rectangle(img, (10, 10), (200, 90), (20, 20, 20), -1)
    cv2.putText(img, "SFCC RADAR SCOPE", (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
    cv2.circle(img, (20, 48), 5, (0, 0, 255), -1)
    cv2.putText(img, "POTHOLE (Water)", (30, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
    cv2.circle(img, (20, 66), 5, (0, 165, 255), -1)
    cv2.putText(img, "POTHOLE (Dry)", (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 165, 255), 1)
    cv2.putText(img, f"Frame: {frame_id}  FPS: {fps:.1f}", (10, scope_size - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 180, 0), 1)

    # Ego vehicle marker
    cv2.polygon = None
    pts = np.array([[center_x, center_y - 12], [center_x - 7, center_y],
                    [center_x + 7, center_y]], np.int32)
    cv2.fillPoly(img, [pts], (0, 200, 255))

    return img

def main():
    print("=" * 72)
    print("   PERSON 3: 77 GHz SFCC RADAR DSP NODE (Windows 11)                  ")
    print("   Input:  tcp://127.0.0.1:5555 (topic: 'radar')                      ")
    print("   Output: tcp://127.0.0.1:5557 (topic: 'radar_targets')              ")
    print("=" * 72)

    p = RADAR_PARAMS
    print(f"\n  FMCW Parameters: fc={p['f_c']/1e9:.0f}GHz | BW={p['bandwidth']/1e9:.0f}GHz "
          f"| Range Res={range_resolution()*100:.1f}cm | Max Range={max_range():.0f}m\n")

    # ZeroMQ setup
    ctx = zmq.Context()

    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.RCVHWM, 30)
    sub.connect("tcp://127.0.0.1:5555")
    sub.setsockopt(zmq.SUBSCRIBE, b'radar')

    pub = ctx.socket(zmq.PUB)
    pub.setsockopt(zmq.SNDHWM, 30)
    pub.bind("tcp://127.0.0.1:5557")
    print("  Publisher bound to tcp://127.0.0.1:5557 (topic: 'radar_targets').\n")

    # SFCC DSP Processor
    processor = SFCCProcessor()

    # OpenCV scope window
    window_name = "Person 3: 77GHz SFCC Radar DSP Scope"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 600, 600)

    fps_counter = 0
    fps_time = time.time()
    display_fps = 0.0
    last_targets = []

    print("  Awaiting radar frames on port 5555... Press 'q' in scope to exit.\n")
    print(f"  {'LABEL':25s} | {'RANGE':8s} | {'AZIMUTH':10s} | {'VELOCITY':10s} | "
          f"{'RCS dB':8s} | {'ABOVE BG':10s} | CONF")
    print("-" * 90)

    try:
        while True:
            if sub.poll(timeout=30):
                parts = sub.recv_multipart()
                if parts[0] != b'radar':
                    continue

                raw_frame = json.loads(parts[1].decode('utf-8'))
                fps_counter += 1
                now = time.time()
                if now - fps_time >= 1.0:
                    display_fps = fps_counter / (now - fps_time)
                    fps_counter = 0
                    fps_time = now

                # Run SFCC DSP
                targets = processor.process_frame(raw_frame)
                last_targets = targets

                # Print terminal table
                for t in targets:
                    marker = "🔴" if "WATER" in t['label'] else ("🟠" if "DRY" in t['label'] else "  ")
                    print(f"  {t['label']:25s} | {t['depth_m']:5.1f} m  | "
                          f"{math.degrees(t['azimuth']):+6.1f}°    | "
                          f"{t['velocity_ms']:+6.2f} m/s  | "
                          f"{t['rcs_db']:+5.1f} dB | "
                          f"+{t['rcs_above_bg_db']:4.1f} dB    | "
                          f"{t['confidence']:.2f}")

                if targets:
                    print("-" * 90)

                # Publish to Person 5 Sensor Fusion
                payload = {
                    'frame': raw_frame.get('frame', 0),
                    'timestamp': time.time(),
                    'target_count': len(targets),
                    'targets': targets
                }
                pub.send_multipart([b'radar_targets', json.dumps(payload).encode('utf-8')])

            # Render and show scope
            scope_img = draw_radar_scope(last_targets, 
                                         raw_frame.get('frame', 0) if 'raw_frame' in dir() else 0,
                                         display_fps)
            cv2.imshow(window_name, scope_img)
            key = cv2.waitKey(10) & 0xFF
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        sub.close()
        pub.close()
        ctx.term()
        print("\n[INFO] Person 3 Radar DSP Node stopped cleanly.")

if __name__ == '__main__':
    main()
