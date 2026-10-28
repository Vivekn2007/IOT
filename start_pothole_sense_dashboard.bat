@echo off
REM ==============================================================================
REM POTHOLE SENSE: Modern Driver HUD & Engineer Console (Web Dashboard)
REM Serves at http://localhost:8080 and automatically opens your web browser.
REM ==============================================================================

cd /d "E:\IOT project\dashboard"
echo [INFO] Starting Pothole Sense Dashboard Server on http://localhost:8080...
echo [INFO] Connecting to CARLA 0.9.16 ZeroMQ Perception Bridge (port 5555)...
echo [INFO] Automatically opening default browser...
python "E:\IOT project\dashboard\server.py"
pause
