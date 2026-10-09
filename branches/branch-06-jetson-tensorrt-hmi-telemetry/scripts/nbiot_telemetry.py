#!/usr/bin/env python3
"""
nbiot_telemetry.py
-------------------------------------------------------------------------------
Person 6 Module: MZH010 NB-IoT Wireless Municipal Cloud Telemetry Client.
Subscribes to:
  - tcp://127.0.0.1:5559 ('fused_hazards' from Person 5)
  - tcp://127.0.0.1:5558 ('acoustic_depth' from Person 4)

Simulates the cellular uplink transmission:
  - Geo-tags detected potholes with simulated GPS coordinates (Delhi/Haryana Highway).
  - Encapsulates severity metrics, physical depth (cm), and sensor confidence.
  - Automatically deduplicates encounters.
  - Logs payloads to local municipal database: 'data/municipal_road_hazard_registry.json'.
-------------------------------------------------------------------------------
"""

import sys
import os
import time
import json
import random

try:
    import zmq
except ImportError:
    print("[ERROR] pyzmq missing. Run: pip install pyzmq")
    sys.exit(1)

REGISTRY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(REGISTRY_DIR, exist_ok=True)
REGISTRY_FILE = os.path.join(REGISTRY_DIR, "municipal_road_hazard_registry.json")

class NBIoTCloudGateway:
    def __init__(self):
        # Base simulated GPS near Delhi-Gurgaon Expressway
        self.base_lat = 28.4595
        self.base_lon = 77.0266
        self.reported_ids = set()
        self.registry = []
        self._load_existing()

    def _load_existing(self):
        if os.path.exists(REGISTRY_FILE):
            try:
                with open(REGISTRY_FILE, "r") as f:
                    self.registry = json.load(f)
            except Exception:
                self.registry = []

    def dispatch_telemetry(self, hazard):
        dist = hazard.get('fused_distance_m', 50.0)
        # Only log when vehicle is passing closely (< 10m) to confirm encounter
        if dist > 12.0:
            return

        depth_cm = hazard.get('sonar_depth_cm', 0.0)
        severity = hazard.get('severity', 'LOW')
        hazard_key = f"{round(dist, 0)}_{round(depth_cm, 0)}"

        if hazard_key in self.reported_ids:
            return

        self.reported_ids.add(hazard_key)

        # Generate localized GPS
        lat = self.base_lat + random.uniform(-0.005, 0.005)
        lon = self.base_lon + random.uniform(-0.005, 0.005)

        record = {
            "incident_id": f"POTH-IND-{int(time.time())}-{random.randint(100, 999)}",
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "gps_coordinates": {
                "latitude": round(lat, 6),
                "longitude": round(lon, 6)
            },
            "pothole_metrics": {
                "depth_cm": round(depth_cm, 1),
                "lateral_offset_m": hazard.get('lateral_offset_m', 0.0),
                "severity_level": severity,
                "confidence": hazard.get('vision_conf', 0.85)
            },
            "sensors_fused": hazard.get('sources_used', []),
            "chassis_shock_confirmed": hazard.get('imu_shock_confirm', False),
            "telemetry_protocol": "NB-IoT (MZH010 Module / CoAP-JSON)",
            "status": "DISPATCHED_TO_MUNICIPAL_AUTHORITY"
        }

        self.registry.append(record)
        with open(REGISTRY_FILE, "w") as f:
            json.dump(self.registry, f, indent=2)

        print(f"\n[NB-IoT UPLINK] Dispatched Incident #{record['incident_id']}")
        print(f"               GPS: ({lat:.5f}, {lon:.5f}) | Depth: {depth_cm:.1f} cm | Severity: {severity}")
        print(f"               Sensors: {', '.join(record['sensors_fused'])}")

def main():
    print("==========================================================================")
    print("    PERSON 6: MZH010 NB-IoT CELLULAR TELEMETRY CLIENT                     ")
    print("    Subscribing to: tcp://127.0.0.1:5559 ('fused_hazards')                ")
    print("    Logging to:     data/municipal_road_hazard_registry.json              ")
    print("==========================================================================")

    ctx = zmq.Context()
    sub = ctx.socket(zmq.SUB)
    sub.setsockopt(zmq.RCVHWM, 20)
    sub.connect("tcp://127.0.0.1:5559")
    sub.setsockopt(zmq.SUBSCRIBE, b'fused_hazards')

    gateway = NBIoTCloudGateway()
    print(">>> NB-IoT Gateway online. Monitoring for close-proximity encounters...\n")

    try:
        while True:
            parts = sub.recv_multipart()
            payload = json.loads(parts[1].decode('utf-8'))
            hazards = payload.get('hazards', [])
            for h in hazards:
                gateway.dispatch_telemetry(h)

    except KeyboardInterrupt:
        pass
    finally:
        sub.close()
        ctx.term()
        print("\n[INFO] NB-IoT Telemetry client terminated.")

if __name__ == '__main__':
    main()
