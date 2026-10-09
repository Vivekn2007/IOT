#!/usr/bin/env python3
"""
visual_hud_win11.py
-------------------------------------------------------------------------------
Live Multi-Modal Graphical HUD (OpenCV) for Windows 11.
Subscribes to tcp://127.0.0.1:5555.
Displays:
  - Live front camera feed through monsoon rain/fog.
  - Driver telemetry HUD: Speed, Camera FPS, 77 GHz Radar targets, Sonar depth.
  - Top-right 2D Radar Scope plotting obstacles.
Press 'q' inside the window to exit.
-------------------------------------------------------------------------------
"""

import zmq
import json
import cv2
import numpy as np
import time

def main():
    print("==========================================================================")
    print("  OPENING MULTI-MODAL VISUAL HUD (Press 'q' in window to exit)             ")
    print("==========================================================================")

    # 1. ZeroMQ Subscriber
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.setsockopt(zmq.RCVHWM, 50)
    sub_socket.connect("tcp://127.0.0.1:5555")
    sub_socket.setsockopt(zmq.SUBSCRIBE, b'') # Receive all topics

    window_name = "Pothole Perception System - Multi-Modal HUD (Windows 11)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)

    current_frame = None
    radar_info = {"count": 0, "points": []}
    sonar_info = {"points_count": 0}
    imu_info = {"az": -9.81}
    fps_counter = 0
    fps_time = time.time()
    display_fps = 0.0

    # Default placeholder screen while waiting for first camera frame
    placeholder = np.zeros((720, 1280, 3), dtype=np.uint8)
    placeholder[:] = (20, 20, 30)
    cv2.putText(placeholder, "CONNECTING TO LIVE MULTI-MODAL SENSOR FEED...", (250, 340),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    cv2.putText(placeholder, "tcp://127.0.0.1:5555", (480, 390),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 1)
    cv2.imshow(window_name, placeholder)
    cv2.waitKey(1)

    try:
        while True:
            # Drain socket queue
            while sub_socket.poll(timeout=5):
                parts = sub_socket.recv_multipart()
                topic = parts[0].decode('utf-8')

                if topic == 'camera':
                    raw_bytes = parts[2]
                    # Check if JPEG or raw buffer
                    if raw_bytes[:2] == b'\xff\xd8': # JPEG magic bytes
                        nparr = np.frombuffer(raw_bytes, np.uint8)
                        current_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    else:
                        header = json.loads(parts[1].decode('utf-8'))
                        w, h = header['width'], header['height']
                        arr = np.frombuffer(raw_bytes, dtype=np.uint8)
                        if arr.size == w * h * 4:
                            bgra = arr.reshape((h, w, 4))
                            current_frame = cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)
                    fps_counter += 1

                elif topic == 'radar':
                    radar_info = json.loads(parts[1].decode('utf-8'))

                elif topic == 'ultrasonic':
                    sonar_info = json.loads(parts[1].decode('utf-8'))

                elif topic == 'imu':
                    imu_data = json.loads(parts[1].decode('utf-8'))
                    imu_info['az'] = imu_data['accel']['z']

            # Calculate FPS
            now = time.time()
            if now - fps_time >= 1.0:
                display_fps = fps_counter / (now - fps_time)
                fps_counter = 0
                fps_time = now

            # Render display
            if current_frame is not None:
                display_img = current_frame.copy()
            else:
                display_img = placeholder.copy()

            # Top telemetry banner
            overlay = display_img.copy()
            cv2.rectangle(overlay, (0, 0), (display_img.shape[1], 80), (15, 23, 42), -1)
            cv2.addWeighted(overlay, 0.8, display_img, 0.2, 0, display_img)

            # Title & Metrics
            cv2.putText(display_img, "MULTI-MODAL ROAD HAZARD PERCEPTION (MONSOON RIG)", (25, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)

            hud_str = f"CAM: {display_fps:.1f} FPS | 77GHz RADAR: {radar_info.get('count', 0)} targets | SONAR: ACTIVE (50Hz) | CHASSIS IMU Az: {imu_info['az']:+.2f} m/s2"
            cv2.putText(display_img, hud_str, (25, 62),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)

            # Top-Right Radar Scope
            scope_x, scope_y, scope_r = display_img.shape[1] - 90, 115, 55
            cv2.circle(display_img, (scope_x, scope_y), scope_r, (25, 35, 45), -1)
            cv2.circle(display_img, (scope_x, scope_y), scope_r, (0, 255, 0), 1)
            cv2.circle(display_img, (scope_x, scope_y), int(scope_r / 2), (0, 255, 0), 1)
            cv2.line(display_img, (scope_x, scope_y - scope_r), (scope_x, scope_y + scope_r), (0, 100, 0), 1)
            cv2.line(display_img, (scope_x - scope_r, scope_y), (scope_x + scope_r, scope_y), (0, 100, 0), 1)
            cv2.putText(display_img, "77GHz RADAR", (scope_x - 38, scope_y - scope_r - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 0), 1)

            # Plot radar targets
            for pt in radar_info.get('points', []):
                depth = pt.get('depth', 0.0)
                az = pt.get('azimuth', 0.0)
                if 0 < depth < 100:
                    norm_d = (depth / 100.0) * (scope_r - 4)
                    px = int(scope_x + norm_d * np.sin(az))
                    py = int(scope_y - norm_d * np.cos(az))
                    cv2.circle(display_img, (px, py), 2, (0, 0, 255), -1)

            cv2.imshow(window_name, display_img)

            key = cv2.waitKey(10) & 0xFF
            if key == ord('q') or key == 27: # 'q' or Esc
                break

    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        sub_socket.close()
        context.term()
        print("HUD closed.")

if __name__ == '__main__':
    main()
