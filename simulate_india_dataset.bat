@echo off
REM ==============================================================================
REM Simulate Indian Road Damage Dataset (RDD) Environment in CARLA 0.9.16
REM Injects Monsoon Weather (100% rain, 100% puddles, 65% fog, low-angle glare)
REM Spawns calibrated D40 Pothole clusters matching the India dataset.
REM ==============================================================================

echo [INFO] Simulating Indian Road Damage Dataset conditions in CARLA...
echo [INFO] Preset: Monsoon Rain + Specular Water Glare + Calibrated D40 Clusters
python "E:\IOT project\branches\branch-01-carla-simulation-bringup\scripts\india_rdd_carla_simulation.py" --weather monsoon
echo.
pause
