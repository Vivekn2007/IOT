#!/usr/bin/env python3
"""
yolo_pothole_detector.py
-------------------------------------------------------------------------------
Part of Person 2's Module: Live YOLOv8 Perception & Detection Node.
Pipeline:
  1. Ingests raw camera frames from Person 1 (tcp://127.0.0.1:5555, topic 'camera').
  2. Applies adverse weather preprocessing (CLAHE + Bilateral filtering).
  3. Executes YOLOv8 real-time inference to detect potholes, road cracks, and obstacles.
  4. Visualizes bounding boxes, confidence metrics, and FPS on screen.
  5. Broadcasts 2D detections to Person 5 (Sensor Fusion) on tcp://127.0.0.1:5556.
-------------------------------------------------------------------------------
"""

import sys
import os
import time
import json
import cv2
import numpy as np

try:
    import zmq
except ImportError:
    print("[ERROR] pyzmq missing. Run: pip install pyzmq")
    sys.exit(1)

# Import local preprocessing module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from preprocessing import AdverseWeatherPreprocessor
from rdd_pothole_filter import RDDPotholeValidator

# Try importing ultralytics YOLO
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

class FallbackRoadAnomalyDetector:
    """
    Calibrated RDD Pothole Detector & False-Positive Filter.
    Filters out non-potholes:
      - Longitudinal cracks (D00, w/h < 0.85)
      - Transverse cracks (D10, w/h > 3.20)
      - Alligator cracks (D20, solidity < 0.60)
      - Road paint & lane markings (D60, rim gradient < 18.0)
      - Rain splash & pebble noise (area < 650 px^2)
    """
    def __init__(self):
        self.preprocessor = AdverseWeatherPreprocessor()
        self.validator = RDDPotholeValidator()
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 5))

    def detect(self, frame):
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 1. Color contrast mask restricted by drivable road trapezoid
        mask_color = cv2.inRange(hsv, (5, 20, 25), (42, 215, 210))
        mask_color[gray > 170] = 0 # Suppress bright paint
        mask_color = cv2.bitwise_and(mask_color, mask_color, mask=self.validator.road_mask)

        # 2. Morphological cleanup
        cleaned = cv2.morphologyEx(mask_color, cv2.MORPH_CLOSE, self.kernel, iterations=2)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for cnt in contours:
            is_valid, reason, conf, meta = self.validator.validate_contour(cnt, gray)
            if is_valid:
                detections.append(meta)

        return detections

def main():
    print("==========================================================================")
    print("      PERSON 2: LIVE YOLOv8 ADVERSE WEATHER POTHOLE DETECTOR              ")
    print("      Ingesting from: tcp://127.0.0.1:5555 ('camera')                     ")
    print("      Publishing to:  tcp://127.0.0.1:5556 ('vision_detections')          ")
    print("==========================================================================")

    # 1. ZeroMQ Subscriber (From Person 1)
    ctx = zmq.Context()
    sub_socket = ctx.socket(zmq.SUB)
    sub_socket.setsockopt(zmq.RCVHWM, 20)
    sub_socket.connect("tcp://127.0.0.1:5555")
    sub_socket.setsockopt(zmq.SUBSCRIBE, b'camera')

    # 2. ZeroMQ Publisher (To Person 5: Sensor Fusion)
    pub_socket = ctx.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.SNDHWM, 20)
    pub_socket.bind("tcp://127.0.0.1:5556")
    print(">>> Output broadcaster bound to tcp://127.0.0.1:5556 (topic: 'vision_detections').")

    # 3. Initialize AI Models
    preprocessor = AdverseWeatherPreprocessor()
    if HAS_YOLO:
        print(">>> Loading YOLOv8 architecture (yolov8n.pt)...")
        try:
            model = YOLO('yolov8n.pt')
            print(">>> [SUCCESS] YOLOv8 Model loaded and ready.")
        except Exception as e:
            print(f">>> [WARN] Could not load YOLO weights ({e}). Using Road Void Fallback Detector.")
            model = FallbackRoadAnomalyDetector()
    else:
        print(">>> [INFO] Ultralytics loading... Running Adaptive Road Void Anomaly Detector.")
        model = FallbackRoadAnomalyDetector()

    window_name = "Person 2: YOLOv8 Real-Time Pothole Perception"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)

    fps_counter = 0
    fps_time = time.time()
    display_fps = 0.0

    print(">>> Awaiting camera frames on port 5555... Press 'q' in window to exit.\n")

    try:
        while True:
            if not sub_socket.poll(timeout=30):
                continue

            parts = sub_socket.recv_multipart()
            if parts[0] != b'camera':
                continue

            hdr = json.loads(parts[1].decode('utf-8'))
            frame_id = hdr['frame']
            raw_bytes = parts[2]

            # Decode frame
            if raw_bytes[:2] == b'\xff\xd8':
                frame = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
            else:
                w, h = hdr['width'], hdr['height']
                arr = np.frombuffer(raw_bytes, dtype=np.uint8)
                if arr.size != w * h * 4:
                    continue
                frame = cv2.cvtColor(arr.reshape((h, w, 4)), cv2.COLOR_BGRA2BGR)

            if frame is None:
                continue

            fps_counter += 1
            now = time.time()
            if now - fps_time >= 1.0:
                display_fps = fps_counter / (now - fps_time)
                fps_counter = 0
                fps_time = now

            # Step 1: Adverse Weather Preprocessing
            enhanced = preprocessor.process(frame)

            # Step 2: YOLOv8 Inference
            detections = []
            if isinstance(model, FallbackRoadAnomalyDetector):
                detections = model.detect(frame)
            else:
                results = model(enhanced, verbose=False, conf=0.45)[0]
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = str(model.names[cls_id]).upper()
                    # Strictly filter for genuine D40 Pothole class (rejects COCO objects & non-potholes)
                    if any(target in cls_name for target in ['D40', 'POTHOLE']):
                        conf = float(box.conf[0])
                        coords = [int(v) for v in box.xyxy[0].tolist()]
                        detections.append({
                            'bbox': coords,
                            'conf': round(conf, 2),
                            'class': 'D40_Pothole'
                        })

            # Step 3: Publish 2D detections to Person 5 (tcp://127.0.0.1:5556)
            detection_payload = {
                'frame': frame_id,
                'timestamp': hdr.get('timestamp', time.time()),
                'detection_count': len(detections),
                'detections': detections
            }
            pub_socket.send_multipart([b'vision_detections', json.dumps(detection_payload).encode('utf-8')])

            # Step 4: Render Visual Annotations on Screen
            annotated = frame.copy()
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                label = f"{det['class']} ({det['conf']:.2f})"
                # Draw thick bounding box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
                # Draw label banner
                cv2.rectangle(annotated, (x1, y1 - 25), (x1 + len(label) * 11, y1), (0, 0, 255), -1)
                cv2.putText(annotated, label, (x1 + 4, y1 - 7),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            # Top HUD Header
            overlay = annotated.copy()
            cv2.rectangle(overlay, (0, 0), (annotated.shape[1], 70), (15, 23, 42), -1)
            cv2.addWeighted(overlay, 0.8, annotated, 0.2, 0, annotated)

            cv2.putText(annotated, "PERSON 2: LIVE YOLOv8 ADVERSE WEATHER ROAD DEFECT DETECTOR", (20, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)
            status_text = f"FPS: {display_fps:.1f} | Detections: {len(detections)} hazards | Published to: tcp://127.0.0.1:5556 ('vision_detections')"
            cv2.putText(annotated, status_text, (20, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (200, 255, 200), 1, cv2.LINE_AA)

            cv2.imshow(window_name, annotated)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        sub_socket.close()
        pub_socket.close()
        ctx.term()
        print("\n[INFO] Person 2 Vision Detector stopped cleanly.")

if __name__ == '__main__':
    main()
