@echo off
REM Person 5: 3D Frustum + Adaptive EKF Sensor Fusion Node Launcher
echo [INFO] Starting Person 5: 3D Frustum + Adaptive EKF Sensor Fusion Node...
echo [INFO] Ingesting from:
echo        - Port 5556: Vision Detections (Person 2)
echo        - Port 5557: 77GHz Radar Targets (Person 3)
echo        - Port 5558: Acoustic Depth & IMU (Person 4)
echo [INFO] Publishing Fused State to tcp://127.0.0.1:5559 ('fused_hazards')
python "E:\IOT project\branches\branch-05-sensor-fusion-ekf-frustum\scripts\ekf_fusion_node.py"
pause
