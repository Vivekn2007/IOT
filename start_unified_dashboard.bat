@echo off
REM ==============================================================================
REM MASTER UNIFIED COCKPIT & GROUND TRUTH COMPARISON DASHBOARD
REM Single merged high-definition window combining all perception nodes!
REM ==============================================================================

echo [INFO] Starting Master Unified Multi-Modal Cockpit...
echo [INFO] Merging Camera, Ground Truth Comparison, Radar Scope, Acoustic Sonar, and Driver HMI!
python "E:\IOT project\branches\branch-05-sensor-fusion-ekf-frustum\scripts\master_unified_cockpit.py"
pause
