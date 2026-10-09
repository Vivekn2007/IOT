@echo off
REM Launcher to generate and view evaluation figures
echo [INFO] Generating and opening evaluation benchmark figures...
python "E:\IOT project\branches\branch-05-sensor-fusion-ekf-frustum\scripts\generate_benchmark_figures.py"
start "" "E:\IOT project\evaluation_figures"
pause
