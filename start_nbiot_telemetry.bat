@echo off
REM Person 6: NB-IoT Municipal Cloud Telemetry Launcher
echo [INFO] Starting Person 6: MZH010 NB-IoT Municipal Cloud Telemetry Client...
echo [INFO] Ingesting from tcp://127.0.0.1:5559 ('fused_hazards')
echo [INFO] Logging geo-tagged potholes to data/municipal_road_hazard_registry.json
python "E:\IOT project\branches\branch-06-jetson-tensorrt-hmi-telemetry\scripts\nbiot_telemetry.py"
pause
