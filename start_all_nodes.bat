@echo off
REM ==============================================================================
REM MASTER LAUNCHER: ADVANCED MULTI-MODAL POTHOLE PERCEPTION SYSTEM
REM Launches all perception nodes on Windows 11 cleanly
REM ==============================================================================

cd /d "E:\IOT project"

echo [STEP 1/6] Launching Person 3: 77GHz SFCC Radar DSP Node...
start "Person 3: Radar DSP" call "E:\IOT project\start_radar_dsp.bat"
timeout /t 2 /nobreak >nul

echo [STEP 2/6] Launching Person 4: Downward Acoustic Sonar + IMU Node...
start "Person 4: Acoustic Sonar" call "E:\IOT project\start_acoustic_sonar.bat"
timeout /t 2 /nobreak >nul

echo [STEP 3/6] Launching Person 2: YOLOv8 Adverse Weather Vision Detector...
start "Person 2: Vision Detector" call "E:\IOT project\start_pothole_detector.bat"
timeout /t 2 /nobreak >nul

echo [STEP 4/6] Launching Person 5: 3D Frustum + Adaptive EKF Sensor Fusion...
start "Person 5: Sensor Fusion" call "E:\IOT project\start_sensor_fusion.bat"
timeout /t 2 /nobreak >nul

echo [STEP 5/6] Launching Person 6: NB-IoT Cloud Telemetry Dispatcher...
start "Person 6: NB-IoT Cloud" call "E:\IOT project\start_nbiot_telemetry.bat"
timeout /t 2 /nobreak >nul

echo [STEP 6/6] Launching Person 6: Automotive Driver Cockpit HMI Display...
start "Person 6: Driver HMI" call "E:\IOT project\start_driver_hmi.bat"

echo.
echo ==============================================================================
echo [SUCCESS] Full Multi-Modal Perception System launched across all ports!
echo ==============================================================================
