@echo off
REM ==============================================================================
REM Launcher for Person 2: Live YOLOv8 Road Defect & Pothole Detector
REM ==============================================================================

echo [INFO] Starting Person 2: YOLOv8 Adverse Weather Pothole Detector...
echo [INFO] Ingesting from tcp://127.0.0.1:5555 ('camera')
echo [INFO] Publishing detections to tcp://127.0.0.1:5556 ('vision_detections')

python "E:\IOT project\branches\branch-02-vision-yolov8-rdd2022\scripts\yolo_pothole_detector.py"
pause
