# Person 2 Master Guide: Computer Vision & YOLOv8 Pothole Detection

**Module Branch**: `E:\IOT project\branches\branch-02-vision-yolov8-rdd2022\`  
**Role**: Computer Vision & Deep Learning Specialist  
**Input**: Consumes live 720p optical camera stream from `tcp://127.0.0.1:5555` (topic `'camera'`)  
**Output**: Publishes annotated 2D bounding boxes to `tcp://127.0.0.1:5556` (topic `'vision_detections'`) for Person 5 (Sensor Fusion)  

---

## 1. Pipeline Architecture
```
[Live Camera from Person 1 (Port 5555)]
                │
                ▼
[Adverse Weather Preprocessor]
  ├── Contrast Limited Adaptive Histogram Equalization (CLAHE)
  └── Bilateral Edge-Preserving Spatial Filter
                │
                ▼
[YOLOv8 Real-Time Inference Engine]
  ├── Detects Potholes (RDD2022 D40 class) & Obstacles
  └── Draws Bounding Boxes with Confidence Scores
                │
                ├─────────────────────────────────────────┐
                ▼                                         ▼
[Live Visual Annotated HUD Window]        [ZeroMQ Publisher (Port 5556)]
(Visual confirmation on your screen)     (Payload sent to Person 5 Sensor Fusion)
```

---

## 2. Directory Structure of this Branch
```
E:\IOT project\branches\branch-02-vision-yolov8-rdd2022\
├── README_PERSON2_GUIDE.md           # This master documentation
├── scripts\
│   ├── preprocessing.py              # CLAHE + Bilateral filtering module
│   ├── rdd_dataset_loader.py         # RDD2022 taxonomy & adverse weather augmentations
│   └── yolo_pothole_detector.py      # Real-time YOLOv8 detector node
├── models\                           # Weights repository (.pt / .onnx)
└── data\                             # Dataset storage
```

---

## 3. How to Run Person 2's Detector (1-Click)
Make sure CARLA and the broadcaster are running (`start_carla.bat` and `start_broadcaster.bat`), then run:

```cmd
"E:\IOT project\start_pothole_detector.bat"
```

### What You Will See:
1. An annotated graphical window will pop up showing the forward camera view.
2. In real time, any road depressions, potholes, and hazards ahead will be marked with **red/green bounding boxes**, labeling the detected hazard and detection confidence (e.g. `D40_Pothole (0.89)`).
3. The detector will automatically output the 2D pixel coordinates `[x1, y1, x2, y2]` to `tcp://127.0.0.1:5556` so Person 5 can project them into 3D Frustums!
