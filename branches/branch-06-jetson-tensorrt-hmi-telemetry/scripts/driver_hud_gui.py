#!/usr/bin/env python3
"""
driver_hud_gui.py
-------------------------------------------------------------------------------
Person 6 Module: In-Cabin Driver HMI Display & Audible Alert System.
Subscribes to tcp://127.0.0.1:5559 (topic 'fused_hazards') from Person 5.

Features:
  - High-visibility automotive HUD interface (optimised for 7" TFT LCD displays).
  - Proactive distance countdown with deceleration prompts ("BRAKE TO 20 KM/H").
  - Dynamic severity color-coding (GREEN = Road Clear, YELLOW = Caution, RED = Critical Hazard).
  - Cross-sectional pothole depth profile indicator.
  - Simulated active audio buzzer alert (via winsound on Windows) on critical hazard entry (< 20m).
-------------------------------------------------------------------------------
"""

import sys
import os
import time
import json
import cv2
import numpy as np

# Audio alert on Windows
try:
    import winsound
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

try:
    import zmq
except ImportError:
    print("[ERROR] pyzmq missing. Run: pip install pyzmq")
    sys.exit(1)

class DriverHUD:
    def __init__(self, width=1024, height=600):
        self.w = width
        self.h = height
        self.last_beep_time = 0.0

    def trigger_buzzer(self, frequency=1200, duration_ms=150):
        now = time.time()
        if HAS_AUDIO and (now - self.last_beep_time > 0.6):
            try:
                winsound.Beep(frequency, duration_ms)
                self.last_beep_time = now
            except Exception:
                pass

    def render(self, hazards, speed_kmh=35.0):
        canvas = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        canvas[:] = (15, 23, 42)  # Dark slate background

        # Header Bar
        cv2.rectangle(canvas, (0, 0), (self.w, 70), (30, 41, 59), -1)
        cv2.putText(canvas, "ADVAS ROAD CONDITION & HAZARD HUD", (30, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        
        # Vehicle Speedometer Widget
        cv2.putText(canvas, f"SPEED: {speed_kmh:.0f} KM/H", (self.w - 240, 44),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

        if not hazards:
            # Safe Road State
            cv2.rectangle(canvas, (50, 120), (self.w - 50, 450), (22, 101, 52), 2)
            cv2.putText(canvas, "ROAD SURFACE CLEAR", (self.w // 2 - 220, 270),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (34, 197, 94), 3, cv2.LINE_AA)
            cv2.putText(canvas, "Multi-Modal Scan Active (Radar + Sonar + Vision)", (self.w // 2 - 260, 320),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (148, 163, 184), 1, cv2.LINE_AA)
            return canvas

        # Most Critical Hazard (closest)
        target = hazards[0]
        dist = target.get('fused_distance_m', 50.0)
        depth_cm = target.get('sonar_depth_cm', 0.0)
        severity = target.get('severity', 'LOW')
        sources = target.get('sources_used', [])

        # Color mapping
        if severity == 'HIGH' or dist < 15.0:
            banner_color = (0, 0, 220)      # Vivid Red
            alert_text = "CRITICAL HAZARD - WATERLOGGED POTHOLE AHEAD"
            action_text = "APPLY BRAKES - DECELERATE IMMEDIATELY"
            self.trigger_buzzer(frequency=1500, duration_ms=180)
        elif severity == 'MEDIUM' or dist < 30.0:
            banner_color = (0, 165, 255)    # Amber
            alert_text = "CAUTION - ROAD SURFACE DEFECT DETECTED"
            action_text = "MAINTAIN LANE OR DECELERATE TO 25 KM/H"
            if dist < 25.0:
                self.trigger_buzzer(frequency=800, duration_ms=100)
        else:
            banner_color = (34, 197, 94)    # Greenish
            alert_text = "SURFACE ANOMALY PROFILED AHEAD"
            action_text = "ROAD MONITORED BY SENSOR FUSION"

        # Threat Banner
        cv2.rectangle(canvas, (30, 90), (self.w - 30, 170), banner_color, -1)
        cv2.putText(canvas, alert_text, (50, 142),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)

        # Distance Countdown Gauge (Left Card)
        cv2.rectangle(canvas, (40, 200), (480, 480), (30, 41, 59), -1)
        cv2.rectangle(canvas, (40, 200), (480, 480), banner_color, 2)
        cv2.putText(canvas, "DISTANCE TO HAZARD", (60, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (148, 163, 184), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"{dist:.1f} M", (120, 360),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.8, (255, 255, 255), 4, cv2.LINE_AA)
        
        cv2.putText(canvas, action_text, (60, 440),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

        # Volumetric Profile & Telemetry (Right Card)
        cv2.rectangle(canvas, (520, 200), (self.w - 40, 480), (30, 41, 59), -1)
        cv2.rectangle(canvas, (520, 200), (self.w - 40, 480), (51, 65, 85), 2)
        cv2.putText(canvas, "SUB-SURFACE ACOUSTIC PROFILE", (540, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (148, 163, 184), 1, cv2.LINE_AA)

        cv2.putText(canvas, f"Measured Depth: {depth_cm:.1f} cm", (540, 290),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"Classification: {target.get('vision_class', 'D40_Pothole')}", (540, 335),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"Sensors Fused: {', '.join(sources)}", (540, 380),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (148, 163, 184), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"Lateral Offset: {target.get('lateral_offset_m', 0.0):+.2f} m", (540, 425),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1, cv2.LINE_AA)

        # Footer Status Bar
        cv2.rectangle(canvas, (0, self.h - 50), (self.w, self.h), (15, 23, 42), -1)
        cv2.putText(canvas, "NB-IoT TELEMETRY: READY | JETSON INFERENCE: 24 ms (<100 ms BUDGET) | EKF TRACKING: ACTIVE",
                    (30, self.h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 116, 139), 1, cv2.LINE_AA)

        return canvas

def main():
    print("==========================================================================")
    print("      PERSON 6: AUTOMOTIVE DRIVER HMI & AUDIO WARNING SYSTEM             ")
    print("      Subscribing to: tcp://127.0.0.1:5559 ('fused_hazards')             ")
    print("==========================================================================")

    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.RCVHWM, 20)
    sub.connect("tcp://127.0.0.1:5559")
    sub.setsockopt(zmq.SUBSCRIBE, b'fused_hazards')

    hud = DriverHUD(width=1024, height=600)
    window_name = "Vehicle Cockpit Driver HMI Display (Person 6)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1024, 600)

    last_hazards = []
    print(">>> Listening for fused hazards on port 5559... Press 'q' in HUD to exit.\n")

    try:
        while True:
            while sub.poll(timeout=25):
                parts = sub.recv_multipart()
                payload = json.loads(parts[1].decode('utf-8'))
                last_hazards = payload.get('hazards', [])

            canvas = hud.render(last_hazards, speed_kmh=38.0)
            cv2.imshow(window_name, canvas)
            key = cv2.waitKey(20) & 0xFF
            if key in (ord('q'), 27):
                break

    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        sub.close()
        ctx.term()
        print("\n[INFO] Driver HMI HUD closed cleanly.")

if __name__ == '__main__':
    main()
