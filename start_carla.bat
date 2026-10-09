@echo off
REM ==============================================================================
REM Quick launcher for CARLA Simulator 0.9.16
REM Path: D:\CARLA_0.9.16\CarlaUE4.exe
REM ==============================================================================

echo [INFO] Starting CARLA 0.9.16 on port 2000...
cd /d "D:\CARLA_0.9.16"
start "" "CarlaUE4.exe" -world-port=2000 -quality-level=Low
echo [OK] CARLA process launched. Wait 5-10 seconds for the Unreal window to fully load,
echo      then run "start_broadcaster.bat".
