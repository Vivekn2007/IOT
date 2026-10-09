@echo off
REM Person 3: 77 GHz SFCC Radar DSP Node Launcher
echo [INFO] Starting Person 3: 77 GHz SFCC Radar DSP Node...
echo [INFO] Ingesting radar from: tcp://127.0.0.1:5555 (topic: 'radar')
echo [INFO] Publishing targets to: tcp://127.0.0.1:5557 (topic: 'radar_targets')
python "E:\IOT project\branches\branch-03-radar-77ghz-sfcc-dsp\scripts\radar_node_win11.py"
pause
