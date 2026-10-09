@echo off
REM ==============================================================================
REM Launcher for CARLA Simulator 0.9.16 on Windows
REM Path: D:\CARLA_0.9.16\CarlaUE4.exe
REM ==============================================================================

echo [INFO] Starting CARLA Simulator 0.9.16 on port 2000...
cd /d "D:\CARLA_0.9.16"
start "" "CarlaUE4.exe" -world-port=2000 -quality-level=Low

echo [OK] CARLA launched. Please wait 5-10 seconds for the window to load,
echo      then run "start_broadcaster.bat".
pause
