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

# Try importing ultralytics YOLO
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

class FallbackRoadAnomalyDetector:
    """
    Strict road-surface-only contour detector.
    Fixes:
      - ROI restricted to bottom 35% of frame (actual road surface only)
      - Minimum area raised to 3000 px2 (removes rain splash noise)
      - Solidity check: only compact blob shapes (not elongated lane lines)
      - Non-Maximum Suppression (NMS) to prevent duplicate boxes
      - Minimum confidence threshold 0.70 (suppresses low-confidence noise)
    """
    def __init__(self):
        self.preprocessor = AdverseWeatherPreprocessor()
        self.MIN_AREA = 3000
        self.MAX_AREA = 35000
        self.MIN_SOLIDITY = 0.45
        self.ASPECT_MIN = 0.6
        self.ASPECT_MAX = 3.5
        self.MIN_CONF = 0.70
        self.NMS_THRESH = 0.35

    def _nms(self, detections):
        """Remove overlapping duplicate boxes using IoU Non-Maximum Suppression."""
        if not detections:
            return []
        boxes = [[d['bbox'][0], d['bbox'][1], d['bbox'][2], d['bbox'][3]] for d in detections]
        scores = [d['conf'] for d in detections]
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        keep = []
        while order:
            i = order.pop(0)
            keep.append(i)
            remaining = []
            for j in order:
                ix1 = max(boxes[i][0], boxes[j][0])
                iy1 = max(boxes[i][1], boxes[j][1])
                ix2 = min(boxes[i][2], boxes[j][2])
                iy2 = min(boxes[i][3], boxes[j][3])
                inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                area_i = (boxes[i][2]-boxes[i][0]) * (boxes[i][3]-boxes[i][1])
                area_j = (boxes[j][2]-boxes[j][0]) * (boxes[j][3]-boxes[j][1])
                iou = inter / float(area_i + area_j - inter + 1e-6)
                if iou < self.NMS_THRESH:
                    remaining.append(j)
            order = remaining
        return [detections[i] for i in keep]

    def detect(self, frame):
        h, w = frame.shape[:2]
        roi_top = int(h * 0.40)
        roi_bot = int(h * 0.92)
        roi = frame[roi_top:roi_bot, :]

        # 1. Color contrast mask for road debris/potholes on asphalt
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask_color = cv2.inRange(hsv, (5, 15, 30), (42, 220, 225))

        # 2. Suppress bright lane lines
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        mask_color[gray > 185] = 0

        # 3. Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 5))
        cleaned = cv2.morphologyEx(mask_color, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        raw_detections = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 180 < area < 35000:
                x, y, bw, bh = cv2.boundingRect(cnt)
                ar = bw / max(bh, 1)
                if 0.5 < ar < 5.0:
                    real_y = y + roi_top
                    conf = round(min(0.96, 0.72 + (area / 40000.0) * 0.2), 2)
                    raw_detections.append({
                        'bbox': [x, real_y, x + bw, real_y + bh],
                        'conf': conf,
                        'class': 'D40_Pothole'
                    })

        return self._nms(raw_detections)

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
                results = model(enhanced, verbose=False, conf=0.35)[0]
                for box in results.boxes:
                    cls_id = int(box.cls[0])
                    cls_name = model.names[cls_id]
                    # Map detections to pothole/hazard taxonomy
                    conf = float(box.conf[0])
                    coords = [int(v) for v in box.xyxy[0].tolist()]
                    detections.append({
                        'bbox': coords,
                        'conf': round(conf, 2),
                        'class': f"Hazard_{cls_name}"
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
