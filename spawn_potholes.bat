@echo off
REM Dense Pothole Spawner Launcher
echo [INFO] Spawning dense pothole grid on road ahead of vehicle...
echo [INFO] Make sure CARLA is running and the broadcaster is active first!
python "E:\IOT project\branches\branch-01-carla-simulation-bringup\scripts\weather_and_pothole_spawner.py" --host 127.0.0.1 --port 2000
pause
