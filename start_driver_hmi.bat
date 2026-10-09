@echo off
REM Person 6: Automotive Driver HMI GUI Launcher
echo [INFO] Starting Person 6: Driver HMI Display & Audio Alert System...
echo [INFO] Ingesting fused hazards from tcp://127.0.0.1:5559 ('fused_hazards')
python "E:\IOT project\branches\branch-06-jetson-tensorrt-hmi-telemetry\scripts\driver_hud_gui.py"
pause
