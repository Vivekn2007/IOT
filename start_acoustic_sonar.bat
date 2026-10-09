@echo off
REM Person 4: Downward Acoustic Sonar + Chassis IMU Node Launcher
echo [INFO] Starting Person 4: Downward Acoustic Sonar + IMU Shock Node...
echo [INFO] Ingesting from tcp://127.0.0.1:5555 ('ultrasonic', 'imu')
echo [INFO] Publishing depth profiles to tcp://127.0.0.1:5558 ('acoustic_depth')
python "E:\IOT project\branches\branch-04-acoustic-tof-chassis-imu\scripts\acoustic_tof_node.py"
pause
